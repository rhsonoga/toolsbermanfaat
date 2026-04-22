import os
import json
import uuid
import tempfile
import requests
from flask import Flask, request, render_template, send_from_directory, send_file, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from datetime import datetime
from contextlib import contextmanager

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from boq_converter.main import convert
from hpdb_converter.session_engine import SessionEngine
from webapp.auth import (
    require_verified_email,
    signup_handler,
    login_handler,
    verify_email_handler,
    resend_verification_handler,
    logout_handler,
)

IS_VERCEL = os.environ.get('VERCEL', False) or os.environ.get('VERCEL_ENV', False)
BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
RESULT_FOLDER = os.path.join(BASE_DIR, 'results')
ALLOWED_EXTENSIONS = {'kmz'}

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', str(uuid.uuid4()))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['SUPABASE_URL'] = (os.environ.get('SUPABASE_URL') or '').rstrip('/')
app.config['SUPABASE_ANON_KEY'] = os.environ.get('SUPABASE_ANON_KEY', '')

HPDB_RUNTIME = {}

if not IS_VERCEL:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(RESULT_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def supabase_ready():
    return bool(app.config.get('SUPABASE_URL') and app.config.get('SUPABASE_ANON_KEY'))


def supabase_headers():
    return {
        'apikey': app.config['SUPABASE_ANON_KEY'],
        'Authorization': f"Bearer {app.config['SUPABASE_ANON_KEY']}",
        'Content-Type': 'application/json'
    }


def supabase_auth_post(path, payload):
    url = f"{app.config['SUPABASE_URL']}{path}"
    resp = requests.post(url, headers=supabase_headers(), json=payload, timeout=20)
    try:
        data = resp.json()
    except Exception:
        data = {'message': resp.text}
    return resp.status_code, data


def make_job_dir(tool_name):
    if IS_VERCEL:
        return tempfile.mkdtemp(prefix=f"{tool_name}_")
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(app.config['RESULT_FOLDER'], tool_name, job_id)
    os.makedirs(job_dir, exist_ok=True)
    return job_dir


@contextmanager
def in_workdir(path):
    old_cwd = os.getcwd()
    os.makedirs(path, exist_ok=True)
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)


def get_cable_config():
    json_path = os.path.join(os.path.dirname(__file__), '..', 'cable_calculator', 'OLTdata.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {
            'line_names': ['MAINFEEDER CABLE', 'HUBFEEDER CABLE', 'SUBFEEDER CABLE'],
            'cable_types': ['FO 144C/12T', 'FO 48C/4T'],
            'cable_categories': ['AE - AE Aerial']
        }


def get_runtime_id():
    if 'runtime_id' not in session:
        session['runtime_id'] = uuid.uuid4().hex
        session.modified = True
    return session['runtime_id']


def get_hpdb_runtime():
    runtime_id = get_runtime_id()
    if runtime_id not in HPDB_RUNTIME:
        HPDB_RUNTIME[runtime_id] = {
            'session_engine': None,
            'kmz_path': '',
            'workdir': '',
            'step1_file': '',
            'final_file': '',
            'log': [],
            'hpdb_path': ''
        }
    return HPDB_RUNTIME[runtime_id]


def add_hpdb_log(message):
    runtime = get_hpdb_runtime()
    runtime['log'].append(message)


def get_hpdb_log_text():
    runtime = get_hpdb_runtime()
    return "\n".join(runtime['log'])


def get_boq_session_state():
    return {
        'mid_file': session.get('boq_mid_file', ''),
        'final_file': session.get('boq_final_file', ''),
        'log': session.get('boq_log', []),
        'mode': session.get('boq_mode_last', 'CLUSTER')
    }


def build_cable_report(form):
    route_val = float(form.get('route', '0') or 0)
    fdt = int(form.get('fdt', '0') or 0)
    fat = int(form.get('fat', '0') or 0)
    tol = float(form.get('tol', '5.0') or 5.0)
    line_name = form.get('line_name', '')
    cable_type = form.get('cable_type', '')
    category = form.get('category', '')
    olt = (form.get('olt') or '').strip()
    code = form.get('code', '')
    segment = form.get('segment', '')

    total_unit = fdt + fat
    slack_m = total_unit * 20
    base = route_val + slack_m
    final = round(base + (base * (tol / 100)))
    cat_short = category.split(' - ')[0] if category else ''

    report = (
        f"Total Route = {int(route_val)} M\n"
        f"Total Slack = {total_unit} unit ({fdt} slack FDT & {fat} slack FAT/SF/MF) @20M\n"
        f"Toleransi = {int(tol)}%\n"
        f"Total Length Cable = {int(route_val)}+{slack_m} = {int(base)}M + ({int(base)} x {int(tol)}%) = {final} M\n"
        f"{'-' * 75}\n"
    )

    if 'SUBFEEDER' in line_name:
        report += f"{olt} - {code} - {line_name} ({cable_type}) - {cat_short} - {final} M"
    elif 'LINE' in line_name:
        report += f"{code} - {line_name} ({cable_type}) - {cat_short} - {final} M"
    else:
        report += f"{olt} - {line_name} {segment} ({cable_type}) - {cat_short} - {final} M"
    return report


def add_history(entry):
    if 'history' not in session:
        session['history'] = []
    session['history'].append(entry)
    session.modified = True


def base_context(active_menu='home', cable_report='', form_state=None):
    cfg = get_cable_config()
    form_state = form_state or {}
    if get_hpdb_runtime().get('source_name') and not form_state.get('hpdb_source_display'):
        form_state['hpdb_source_display'] = get_hpdb_runtime().get('source_name', '')
    if get_hpdb_runtime().get('hpdb_path') and not form_state.get('hpdb_path_display'):
        form_state['hpdb_path_display'] = get_hpdb_runtime().get('hpdb_path', '')
    if session.get('boq_source_display') and not form_state.get('boq_source_display'):
        form_state['boq_source_display'] = session.get('boq_source_display', '')
    if session.get('boq_mode_last') and not form_state.get('boq_mode'):
        form_state['boq_mode'] = session.get('boq_mode_last', '')
    return {
        'active_menu': active_menu,
        'disable_upload': bool(IS_VERCEL),
        'history': session.get('history', []),
        'cable_report': cable_report,
        'form_state': form_state or {},
        'hpdb_runtime': get_hpdb_runtime(),
        'hpdb_log_text': get_hpdb_log_text(),
        'boq_state': get_boq_session_state(),
        'line_names': cfg.get('line_names', []),
        'cable_types': cfg.get('cable_types', []),
        'categories': cfg.get('cable_categories', []),
        'auth_user': session.get('auth_user', {}),
        'supabase_ready': supabase_ready()
    }


def _menu_from_request_path(path):
    if path.startswith('/cable/'):
        return 'cable'
    if path.startswith('/boq/'):
        return 'boq'
    if path.startswith('/hpdb/'):
        return 'hpdb'
    return request.args.get('menu', 'home')


@app.errorhandler(Exception)
def handle_unexpected_error(err):
    # Keep explicit HTTP responses (404/405/etc) untouched.
    if isinstance(err, HTTPException):
        return err

    app.logger.exception('Unhandled exception: %s %s', request.method, request.path)

    if request.accept_mimetypes.get('application/json'):
        return jsonify({
            'ok': False,
            'error': 'Terjadi kesalahan internal server. Silakan coba lagi.'
        }), 500

    try:
        flash('Terjadi kesalahan internal server. Detail error sudah dicatat di log server.')
        return render_template(
            'main.html',
            **base_context(active_menu=_menu_from_request_path(request.path), form_state=request.form.to_dict(flat=True))
        ), 500
    except Exception:
        # Final fallback if template rendering also fails.
        return 'Internal Server Error', 500


@app.route('/auth/signup', methods=['POST'])
def auth_signup():
    if not supabase_ready():
        return jsonify({'ok': False, 'error': 'Supabase belum dikonfigurasi di server.'}), 500

    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip()
    password = payload.get('password') or ''
    full_name = (payload.get('full_name') or '').strip()

    status, response = signup_handler(
        email=email,
        password=password,
        full_name=full_name,
        supabase_url=app.config['SUPABASE_URL'],
        supabase_key=app.config['SUPABASE_ANON_KEY']
    )

    return jsonify(response), status


@app.route('/auth/login', methods=['POST'])
def auth_login():
    if not supabase_ready():
        return jsonify({'ok': False, 'error': 'Supabase belum dikonfigurasi di server.'}), 500

    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip()
    password = payload.get('password') or ''

    status, response = login_handler(
        email=email,
        password=password,
        supabase_url=app.config['SUPABASE_URL'],
        supabase_key=app.config['SUPABASE_ANON_KEY']
    )

    return jsonify(response), status


@app.route('/auth/verify', methods=['GET'])
def auth_verify():
    """Handle email verification link from email."""
    if not supabase_ready():
        return redirect(url_for('main_launcher') + '?verification_error=server_error')
    
    token = request.args.get('token', '').strip()
    
    if not token:
        return redirect(url_for('main_launcher') + '?verification_error=no_token')
    
    status, response = verify_email_handler(
        token=token,
        supabase_url=app.config['SUPABASE_URL'],
        supabase_key=app.config['SUPABASE_ANON_KEY']
    )
    
    if status >= 400:
        error_code = 'token_expired' if 'expired' in response.get('error', '').lower() else 'token_invalid'
        return redirect(url_for('main_launcher', menu='home') + f'?verified=false&error={error_code}')
    
    # Success - redirect to home with success message
    return redirect(url_for('main_launcher', menu='home') + '?verified=true')


@app.route('/auth/resend-verification', methods=['POST'])
def auth_resend_verification():
    """Handle resending verification email."""
    if not supabase_ready():
        return jsonify({'ok': False, 'error': 'Supabase belum dikonfigurasi di server.'}), 500
    
    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip()
    
    status, response = resend_verification_handler(
        email=email,
        supabase_url=app.config['SUPABASE_URL'],
        supabase_key=app.config['SUPABASE_ANON_KEY']
    )
    
    return jsonify(response), status


@app.route('/auth/logout', methods=['POST'])
def auth_logout():
    status, response = logout_handler()
    return jsonify(response), status


@app.route('/', methods=['GET'])
def main_launcher():
    menu = request.args.get('menu', 'home')
    return render_template('main.html', **base_context(active_menu=menu))


@app.route('/cable/calculate', methods=['POST'])
def cable_calculate():
    try:
        form_state = request.form.to_dict(flat=True)
        report = build_cable_report(request.form)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return jsonify({
                'ok': True,
                'report': report,
                'form_state': form_state,
            })
        return render_template('main.html', **base_context(active_menu='cable', cable_report=report, form_state=form_state))
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return jsonify({
                'ok': False,
                'error': str(e),
            }), 400
        return render_template('main.html', **base_context(active_menu='cable', form_state=request.form.to_dict(flat=True)))


@app.route('/boq/convert', methods=['POST'])
@require_verified_email
def boq_convert():
    try:
        action = (request.form.get('boq_action') or '').upper()
        if action == 'RESET':
            return boq_reset()

        file = request.files.get('boq_file')
        mode = (request.form.get('boq_mode') or action or 'CLUSTER').upper()
        if not file or not file.filename:
            flash('Pilih file KMZ untuk BOQ Converter.')
            session['boq_log'] = ['❌ ERROR: Pilih file KMZ terlebih dahulu.']
            session.modified = True
            return render_template('main.html', **base_context(active_menu='boq', form_state=request.form.to_dict(flat=True)))
        if not allowed_file(file.filename):
            flash('Format file BOQ harus .kmz')
            session['boq_log'] = ['❌ ERROR: Format file harus .kmz']
            session.modified = True
            return render_template('main.html', **base_context(active_menu='boq', form_state=request.form.to_dict(flat=True)))

        job_dir = make_job_dir('boq')
        filename = secure_filename(file.filename)
        kmz_path = os.path.join(job_dir, filename)
        file.save(kmz_path)

        session['boq_log'] = [
            f"MODE AKTIF: {mode}",
            "Sedang memproses... mohon tunggu.",
            f"[{mode}] Memulai Parsing KMZ...",
            f"[{mode}] Mengagregasi data struktur KML...",
            f"[{mode}] Membuat file konversi sementara...",
            f"[{mode}] Memulai Injeksi data ke Template Backend..."
        ]
        session.modified = True

        with in_workdir(job_dir):
            mid, final = convert(kmz_path, mode=mode)

        session['boq_mid_file'] = os.path.join(job_dir, mid)
        session['boq_final_file'] = os.path.join(job_dir, final)
        session['boq_source_display'] = filename
        session['boq_mode_last'] = mode
        session['boq_log'].extend([
            f"✅ PROSES {mode} BERHASIL!",
            f"File Konversi: {mid}",
            f"File BOQ Final: {final}",
            "Silakan klik tombol Download di bawah."
        ])
        session.modified = True
        flash(f'BOQ Converter berhasil ({mode}).')
    except Exception as e:
        app.logger.exception('BOQ converter failed')
        mode = (request.form.get('boq_mode') or request.form.get('boq_action') or 'CLUSTER').upper()
        session['boq_log'] = [
            f"MODE AKTIF: {mode}",
            "Sedang memproses... mohon tunggu.",
            f"❌ ERROR: {str(e)}"
        ]
        session.modified = True
        flash(f'BOQ Converter error: {e}')

    return render_template('main.html', **base_context(active_menu='boq', form_state=request.form.to_dict(flat=True)))


@app.route('/boq/download/mid')
@require_verified_email
def boq_download_mid():
    path = session.get('boq_mid_file', '')
    if not path or not os.path.exists(path):
        flash('Jalankan proses BOQ terlebih dahulu!')
        return redirect(url_for('main_launcher'))
    return send_from_directory(os.path.dirname(path), os.path.basename(path), as_attachment=True)


@app.route('/boq/download/final')
@require_verified_email
def boq_download_final():
    path = session.get('boq_final_file', '')
    if not path or not os.path.exists(path):
        flash('Jalankan proses BOQ terlebih dahulu!')
        return redirect(url_for('main_launcher'))
    return send_from_directory(os.path.dirname(path), os.path.basename(path), as_attachment=True)


@app.route('/boq/reset', methods=['POST'])
@require_verified_email
def boq_reset():
    for key in ['boq_mid_file', 'boq_final_file', 'boq_log', 'boq_mode_last', 'boq_source_display']:
        session.pop(key, None)
    session.modified = True
    flash('System Ready. Pilih file KMZ.')
    return redirect(url_for('main_launcher', menu='boq'))


def _hpdb_save_upload(file_storage):
    runtime = get_hpdb_runtime()
    job_id = runtime.get('job_id') or str(uuid.uuid4())
    runtime['job_id'] = job_id
    job_dir = make_job_dir('hpdb')
    filename = secure_filename(file_storage.filename)
    kmz_path = os.path.join(job_dir, filename)
    file_storage.save(kmz_path)
    runtime['kmz_path'] = kmz_path
    runtime['workdir'] = job_dir
    runtime['source_name'] = filename
    return runtime


@app.route('/hpdb/process', methods=['POST'])
@require_verified_email
def hpdb_process():
    action = (request.form.get('hpdb_action') or 'step1').lower()
    runtime = get_hpdb_runtime()
    try:
        if action == 'reset':
            return hpdb_reset()

        file = request.files.get('hpdb_file')
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('Format file HPDB harus .kmz')
                return render_template('main.html', **base_context(active_menu='hpdb', form_state=request.form.to_dict(flat=True)))
            runtime = _hpdb_save_upload(file)
            runtime['log'] = []

        if not runtime.get('kmz_path') or not os.path.exists(runtime.get('kmz_path', '')):
            flash('Pilih file KMZ terlebih dahulu (Browse), lalu klik STEP 1/2/3.')
            return render_template('main.html', **base_context(active_menu='hpdb', form_state=request.form.to_dict(flat=True)))

        with in_workdir(runtime['workdir']):
            se = SessionEngine(runtime['kmz_path'])

            if action == 'step1':
                add_hpdb_log('Tahap 1: Mengonversi KMZ...')
                se.step1_convert()
                runtime['step1_file'] = os.path.join(runtime['workdir'], '1.Hasil_Convert.xlsx')
                add_hpdb_log('✅ Tahap 1 Selesai!')
                flash('Tahap 1 HPDB selesai.')

            elif action == 'step2':
                add_hpdb_log('Tahap 1: Mengonversi KMZ...')
                se.step1_convert()
                runtime['step1_file'] = os.path.join(runtime['workdir'], '1.Hasil_Convert.xlsx')
                add_hpdb_log('✅ Tahap 1 Selesai!')
                add_hpdb_log('Tahap 2: Injeksi data dasar...')
                runtime['hpdb_file'] = se.step2_inject_basic()
                runtime['hpdb_path'] = os.path.abspath(runtime['hpdb_file'])
                add_hpdb_log(f"✅ Tahap 2 Selesai! File: {runtime['hpdb_file']}")
                flash('Tahap 2 HPDB selesai.')

            elif action == 'step3':
                add_hpdb_log('Tahap 1: Mengonversi KMZ...')
                se.step1_convert()
                runtime['step1_file'] = os.path.join(runtime['workdir'], '1.Hasil_Convert.xlsx')
                add_hpdb_log('✅ Tahap 1 Selesai!')
                add_hpdb_log('Tahap 2: Injeksi data dasar...')
                runtime['hpdb_file'] = se.step2_inject_basic()
                runtime['hpdb_path'] = os.path.abspath(runtime['hpdb_file'])
                add_hpdb_log(f"✅ Tahap 2 Selesai! File: {runtime['hpdb_file']}")
                add_hpdb_log('Tahap 3: Sinkronisasi Kolom A-K...')
                se.step3_sync_pole()
                runtime['final_file'] = runtime.get('hpdb_file') or os.path.join(runtime['workdir'], '2.HPDB_FINAL.xlsx')
                add_hpdb_log('✅ Tahap 3 Selesai!')
                flash('Semua tahapan selesai!')

            else:
                flash('Aksi HPDB tidak dikenali.')

        session.modified = True
    except Exception as e:
        add_hpdb_log(f"Error {action.upper()}: {e}")
        flash(f'HPDB error: {e}')

    return render_template('main.html', **base_context(active_menu='hpdb', form_state=request.form.to_dict(flat=True)))


@app.route('/hpdb/reset', methods=['POST'])
@require_verified_email
def hpdb_reset():
    runtime_id = get_runtime_id()
    HPDB_RUNTIME.pop(runtime_id, None)
    session.modified = True
    flash('Session HPDB di-reset.')
    return redirect(url_for('main_launcher', menu='hpdb'))


@app.route('/hpdb/download/step1')
@require_verified_email
def hpdb_download_step1():
    runtime = get_hpdb_runtime()
    path = runtime.get('step1_file')
    if not path or not os.path.exists(path):
        flash('Jalankan Tahap 1 terlebih dahulu!')
        return redirect(url_for('main_launcher'))
    return send_from_directory(os.path.dirname(path), os.path.basename(path), as_attachment=True)


@app.route('/hpdb/download/final')
@require_verified_email
def hpdb_download_final():
    runtime = get_hpdb_runtime()
    path = runtime.get('final_file') or runtime.get('hpdb_path')
    if not path or not os.path.exists(path):
        flash('Jalankan Tahap 2 & 3 terlebih dahulu!')
        return redirect(url_for('main_launcher'))
    return send_from_directory(os.path.dirname(path), os.path.basename(path), as_attachment=True)

@app.route('/history')
def history():
    return redirect(url_for('main_launcher'))

@app.route('/download/<id>')
def download(id):
    for item in session.get('history', []):
        if item['id'] == id:
            directory, filename = os.path.split(item['result'])
            return send_from_directory(directory, filename, as_attachment=True)
    flash('File tidak ditemukan')
    return redirect(url_for('history'))

@app.route('/delete/<id>', methods=['POST'])
def delete(id):
    history = session.get('history', [])
    for i, item in enumerate(history):
        if item['id'] == id:
            try:
                os.remove(item['result'])
            except Exception:
                pass
            extra = item.get('extra')
            if extra:
                try:
                    os.remove(extra)
                except Exception:
                    pass
            del history[i]
            session['history'] = history
            session.modified = True
            flash('File berhasil dihapus')
            break
    return redirect(url_for('history'))

if __name__ == '__main__':
    app.run(debug=True)
