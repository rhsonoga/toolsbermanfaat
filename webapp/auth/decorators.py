"""Decorators for authentication and authorization."""

from functools import wraps
from flask import session, redirect, url_for, request, jsonify, flash

def require_verified_email(f):
    """
    Decorator to require verified email for converter access.
    
    Checks if:
    1. User is logged in (auth_user in session)
    2. User's email is verified (email_verified_at is not None)
    
    If not verified:
    - For API endpoints: return JSON error
    - For page endpoints: redirect to home with error message
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is in session
        if 'auth_user' not in session or not session.get('auth_user'):
            # Not logged in - redirect to home and show login prompt
            if request.accept_mimetypes.get('application/json'):
                return jsonify({
                    'ok': False,
                    'error': 'Belum login. Silakan login terlebih dahulu.'
                }), 401
            flash('Silakan login terlebih dahulu untuk menggunakan converter ini.')
            return redirect(url_for('main_launcher', menu='home'))
        
        auth_user = session.get('auth_user', {})
        
        # Check if email is verified
        email_verified_at = auth_user.get('email_verified_at')
        
        if not email_verified_at:
            # Email not verified - block access
            if request.accept_mimetypes.get('application/json'):
                return jsonify({
                    'ok': False,
                    'error': 'Email belum diverifikasi. Silakan cek inbox Anda.'
                }), 403
            
            # For page endpoints, redirect to home with error message
            flash('Email belum diverifikasi. Cek inbox Anda lalu verifikasi akun untuk memakai converter ini.')
            return redirect(url_for('main_launcher', 
                                   menu='home',
                                   verification_error='not_verified'))
        
        # User is logged in AND verified - allow access
        return f(*args, **kwargs)
    
    return decorated_function


def require_login(f):
    """
    Decorator to require login (verified or not).
    
    Checks if user is logged in (auth_user in session).
    Does NOT check email verification.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'auth_user' not in session or not session.get('auth_user'):
            if request.accept_mimetypes.get('application/json'):
                return jsonify({
                    'ok': False,
                    'error': 'Belum login.'
                }), 401
            return redirect(url_for('main_launcher', menu='home'))
        
        return f(*args, **kwargs)
    
    return decorated_function
