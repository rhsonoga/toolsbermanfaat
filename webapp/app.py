import os
import json
import uuid
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from datetime import datetime
from contextlib import contextmanager

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from boq_converter.main import convert
from hpdb_converter.session_engine import SessionEngine

IS_VERCEL = os.environ.get('VERCEL', False) or os.environ.get('VERCEL_ENV', False)
BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
RESULT_FOLDER = os.path.join(BASE_DIR, 'results')
ALLOWED_EXTENSIONS = {'kmz'}

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', str(uuid.uuid4()))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

if not IS_VERCEL:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(RESULT_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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


def base_context(active_menu='home', cable_report=''):
    cfg = get_cable_config()
    return {
        'active_menu': active_menu,
        'disable_upload': bool(IS_VERCEL),
        'history': session.get('history', []),
        'cable_report': cable_report,
        'line_names': cfg.get('line_names', []),
        'cable_types': cfg.get('cable_types', []),
        'categories': cfg.get('cable_categories', [])
    }


@app.route('/', methods=['GET'])
def main_launcher():
    return render_template('main.html', **base_context())


@app.route('/cable/calculate', methods=['POST'])
def cable_calculate():
    try:
        report = build_cable_report(request.form)
        flash('Cable Calculator berhasil dihitung.')
        return render_template('main.html', **base_context(active_menu='cable', cable_report=report))
    except Exception as e:
        flash(f'Cable Calculator error: {e}')
        return render_template('main.html', **base_context(active_menu='cable'))


@app.route('/boq/convert', methods=['POST'])
def boq_convert():
    if IS_VERCEL:
        flash('Fitur file processing dinonaktifkan di Vercel karena filesystem read-only.')
        return render_template('main.html', **base_context(active_menu='boq'))

    file = request.files.get('boq_file')
    mode = (request.form.get('boq_mode') or 'CLUSTER').upper()
    if not file or not file.filename:
        flash('Pilih file KMZ untuk BOQ Converter.')
        return render_template('main.html', **base_context(active_menu='boq'))
    if not allowed_file(file.filename):
        flash('Format file BOQ harus .kmz')
        return render_template('main.html', **base_context(active_menu='boq'))

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(app.config['RESULT_FOLDER'], 'boq', job_id)
    os.makedirs(job_dir, exist_ok=True)
    filename = secure_filename(file.filename)
    kmz_path = os.path.join(job_dir, filename)
    file.save(kmz_path)

    try:
        with in_workdir(job_dir):
            mid, final = convert(kmz_path, mode=mode)
        add_history({
            'id': job_id,
            'tool': 'BOQ Converter',
            'filename': filename,
            'result': os.path.join(job_dir, final),
            'extra': os.path.join(job_dir, mid),
            'time': datetime.now().isoformat(timespec='seconds')
        })
        flash(f'BOQ Converter berhasil ({mode}).')
    except Exception as e:
        flash(f'BOQ Converter error: {e}')

    return render_template('main.html', **base_context(active_menu='boq'))


@app.route('/hpdb/process', methods=['POST'])
def hpdb_process():
    if IS_VERCEL:
        flash('Fitur file processing dinonaktifkan di Vercel karena filesystem read-only.')
        return render_template('main.html', **base_context(active_menu='hpdb'))

    file = request.files.get('hpdb_file')
    if not file or not file.filename:
        flash('Pilih file KMZ untuk HPDB Converter.')
        return render_template('main.html', **base_context(active_menu='hpdb'))
    if not allowed_file(file.filename):
        flash('Format file HPDB harus .kmz')
        return render_template('main.html', **base_context(active_menu='hpdb'))

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(app.config['RESULT_FOLDER'], 'hpdb', job_id)
    os.makedirs(job_dir, exist_ok=True)
    filename = secure_filename(file.filename)
    kmz_path = os.path.join(job_dir, filename)
    file.save(kmz_path)

    try:
        with in_workdir(job_dir):
            se = SessionEngine(kmz_path)
            se.step1_convert()
            final_file = se.step2_inject_basic()
            se.step3_sync_pole()
        add_history({
            'id': job_id,
            'tool': 'HPDB Converter',
            'filename': filename,
            'result': os.path.join(job_dir, final_file),
            'extra': os.path.join(job_dir, '1.Hasil_Convert.xlsx'),
            'time': datetime.now().isoformat(timespec='seconds')
        })
        flash('HPDB Converter selesai sampai Step 3 (Final).')
    except Exception as e:
        flash(f'HPDB Converter error: {e}')

    return render_template('main.html', **base_context(active_menu='hpdb'))

@app.route('/history')
def history():
    return render_template('main.html', **base_context(active_menu='history'))

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
