import os
import uuid
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from datetime import datetime
import socket
# Supabase client import (to be configured)
# from supabase import create_client, Client

# Import logic from existing converter

# Pastikan root project (.. dari webapp) ada di sys.path agar bisa import boq_converter
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from boq_converter.main import convert

IS_VERCEL = os.environ.get('VERCEL', False) or os.environ.get('VERCEL_ENV', False)
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'kmz'}

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', str(uuid.uuid4()))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

if not IS_VERCEL:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(RESULT_FOLDER, exist_ok=True)

# --- Supabase setup placeholder ---
# SUPABASE_URL = os.environ.get('SUPABASE_URL')
# SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Helper ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_client_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        ip = request.environ['HTTP_X_FORWARDED_FOR']
    else:
        ip = request.remote_addr
    return ip

# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if IS_VERCEL:
        if request.method == 'POST':
            flash('Fitur upload & konversi tidak tersedia di versi demo online. Silakan jalankan di server lokal untuk fitur penuh.')
        return render_template('index.html', disable_upload=True)
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_id + '_' + filename)
            file.save(upload_path)
            # Proses konversi
            try:
                mid, final = convert(upload_path, mode=request.form.get('mode', 'CLUSTER'))
                result_path = os.path.join(app.config['RESULT_FOLDER'], final)
                # Simpan hasil ke folder result
                os.rename(final, result_path)
                # Log ke Supabase (placeholder)
                # supabase.table('logs').insert({ ... })
                # Simpan riwayat ke session
                if 'history' not in session:
                    session['history'] = []
                session['history'].append({
                    'filename': filename,
                    'result': result_path,
                    'time': datetime.now().isoformat(),
                    'ip': get_client_ip(),
                    'id': unique_id
                })
                session.modified = True
                flash('Konversi berhasil!')
                return redirect(url_for('history'))
            except Exception as e:
                flash(f'Gagal konversi: {e}')
                return redirect(request.url)
        else:
            flash('File tidak valid!')
            return redirect(request.url)
    return render_template('index.html', disable_upload=False)

@app.route('/history')
def history():
    return render_template('history.html', history=session.get('history', []))

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
            del history[i]
            session['history'] = history
            session.modified = True
            flash('File berhasil dihapus')
            break
    return redirect(url_for('history'))

if __name__ == '__main__':
    app.run(debug=True)
