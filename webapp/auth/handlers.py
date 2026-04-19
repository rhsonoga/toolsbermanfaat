"""Authentication handlers for signup, login, verification, etc."""

import requests
from typing import Tuple, Dict, Any
from flask import session
from .utils import (
    validate_email,
    validate_password,
    validate_full_name,
    check_resend_rate_limit,
    record_resend_attempt,
    format_error_message,
)


def supabase_auth_post(supabase_url: str, supabase_key: str, path: str, payload: dict) -> Tuple[int, dict]:
    """
    Make POST request to Supabase Auth API.
    
    Args:
        supabase_url: Supabase project URL
        supabase_key: Supabase anon key
        path: API path (e.g., '/auth/v1/signup')
        payload: Request payload
        
    Returns:
        Tuple of (status_code, response_data)
    """
    headers = {
        'apikey': supabase_key,
        'Authorization': f"Bearer {supabase_key}",
        'Content-Type': 'application/json'
    }
    
    url = f"{supabase_url.rstrip('/')}{path}"
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        try:
            data = resp.json()
        except Exception:
            data = {'message': resp.text}
        return resp.status_code, data
    except requests.exceptions.Timeout:
        return 504, {'error': 'Request timeout'}
    except requests.exceptions.RequestException as e:
        return 500, {'error': str(e)}


def signup_handler(
    email: str,
    password: str,
    full_name: str,
    supabase_url: str,
    supabase_key: str
) -> Tuple[int, Dict[str, Any]]:
    """
    Handle user signup.
    
    Validates input, calls Supabase signup API, and returns user info.
    Does NOT create Flask session yet (user must verify email first).
    
    Args:
        email: User email
        password: User password
        full_name: User full name
        supabase_url: Supabase URL
        supabase_key: Supabase anon key
        
    Returns:
        Tuple of (http_status, response_dict)
    """
    # Validate inputs
    email = str(email).strip()
    password = str(password) if password else ""
    full_name = str(full_name).strip()
    
    is_valid, error = validate_email(email)
    if not is_valid:
        return 400, {'ok': False, 'error': error}
    
    is_valid, error = validate_password(password)
    if not is_valid:
        return 400, {'ok': False, 'error': error}
    
    is_valid, error = validate_full_name(full_name)
    if not is_valid:
        return 400, {'ok': False, 'error': error}
    
    # Call Supabase signup API
    status, data = supabase_auth_post(
        supabase_url,
        supabase_key,
        '/auth/v1/signup',
        {
            'email': email,
            'password': password,
            'data': {'full_name': full_name}
        }
    )
    
    # Handle errors
    if status >= 400:
        error_msg = data.get('msg') or \
                   data.get('error_description') or \
                   data.get('message') or \
                   data.get('error') or \
                   'Registrasi gagal.'
        return status, {
            'ok': False,
            'error': format_error_message(error_msg)
        }
    
    # Success - user created (email_verified_at will be NULL)
    user = data.get('user') or {}
    return 201, {
        'ok': True,
        'message': 'Registrasi berhasil. Cek email untuk verifikasi.',
        'user': {
            'id': user.get('id', ''),
            'email': user.get('email', email),
            'email_verified_at': user.get('email_verified_at'),
            'user_metadata': user.get('user_metadata', {})
        }
    }


def login_handler(
    email: str,
    password: str,
    supabase_url: str,
    supabase_key: str
) -> Tuple[int, Dict[str, Any]]:
    """
    Handle user login.
    
    Validates email & password, checks if email is verified, and creates Flask session.
    
    Args:
        email: User email
        password: User password
        supabase_url: Supabase URL
        supabase_key: Supabase anon key
        
    Returns:
        Tuple of (http_status, response_dict)
    """
    email = str(email).strip()
    password = str(password) if password else ""
    
    # Basic validation
    is_valid, error = validate_email(email)
    if not is_valid:
        return 400, {'ok': False, 'error': error}
    
    if not password:
        return 400, {'ok': False, 'error': 'Password wajib diisi.'}
    
    # Call Supabase token API
    status, data = supabase_auth_post(
        supabase_url,
        supabase_key,
        '/auth/v1/token?grant_type=password',
        {
            'email': email,
            'password': password
        }
    )
    
    # Handle auth errors
    if status >= 400:
        error_msg = data.get('msg') or \
                   data.get('error_description') or \
                   data.get('message') or \
                   data.get('error') or \
                   'Login gagal.'
        return status, {
            'ok': False,
            'error': format_error_message(error_msg)
        }
    
    # Check if email is verified
    user = data.get('user') or {}
    email_verified_at = user.get('email_verified_at')
    
    if not email_verified_at:
        # Email not verified - reject login
        return 401, {
            'ok': False,
            'error': 'Email belum diverifikasi. Silakan cek inbox Anda untuk link verifikasi.'
        }
    
    # Email verified - create session
    session['auth_user'] = {
        'id': user.get('id', ''),
        'email': user.get('email', email),
        'email_verified_at': email_verified_at,
        'full_name': (user.get('user_metadata') or {}).get('full_name', '')
    }
    session['auth_access_token'] = data.get('access_token', '')
    session.modified = True
    
    return 200, {
        'ok': True,
        'message': 'Login berhasil.',
        'user': session['auth_user']
    }


def verify_email_handler(
    token: str,
    supabase_url: str,
    supabase_key: str
) -> Tuple[int, Dict[str, Any]]:
    """
    Handle email verification via token from email link.
    
    Calls Supabase /auth/v1/verify endpoint to confirm email,
    then creates Flask session automatically.
    
    Args:
        token: Confirmation/verification token from email
        supabase_url: Supabase URL
        supabase_key: Supabase anon key
        
    Returns:
        Tuple of (http_status, response_dict)
    """
    token = str(token).strip()
    
    if not token:
        return 400, {
            'ok': False,
            'error': 'Token verifikasi tidak ditemukan.'
        }
    
    # Call Supabase verify endpoint
    status, data = supabase_auth_post(
        supabase_url,
        supabase_key,
        '/auth/v1/verify',
        {
            'type': 'email',
            'token': token
        }
    )
    
    # Handle errors
    if status >= 400:
        error_msg = data.get('message') or \
                   data.get('error') or \
                   data.get('error_description') or \
                   'Verifikasi email gagal.'
        return status, {
            'ok': False,
            'error': format_error_message(error_msg)
        }
    
    # Success - email verified, user authenticated
    # Response contains user with email_verified_at set
    user = data.get('user') or {}
    
    # Create session
    session['auth_user'] = {
        'id': user.get('id', ''),
        'email': user.get('email', ''),
        'email_verified_at': user.get('email_verified_at'),
        'full_name': (user.get('user_metadata') or {}).get('full_name', '')
    }
    session['auth_access_token'] = data.get('access_token', '')
    session.modified = True
    
    return 200, {
        'ok': True,
        'message': 'Email berhasil diverifikasi. Anda sudah bisa menggunakan converter!',
        'user': session['auth_user']
    }


def resend_verification_handler(
    email: str,
    supabase_url: str,
    supabase_key: str
) -> Tuple[int, Dict[str, Any]]:
    """
    Handle resending verification email to user.
    
    Includes rate limiting (max 3 per hour per email).
    
    Args:
        email: User email
        supabase_url: Supabase URL
        supabase_key: Supabase anon key
        
    Returns:
        Tuple of (http_status, response_dict)
    """
    email = str(email).strip()
    
    # Validate email format
    is_valid, error = validate_email(email)
    if not is_valid:
        return 400, {'ok': False, 'error': error}
    
    # Check rate limit
    is_allowed, limit_info = check_resend_rate_limit(email)
    
    if not is_allowed:
        return 429, {
            'ok': False,
            'error': f"Terlalu banyak percobaan. Coba lagi dalam {limit_info['retry_after_seconds']} detik.",
            'retry_after_seconds': limit_info['retry_after_seconds']
        }
    
    # Call Supabase resend API
    status, data = supabase_auth_post(
        supabase_url,
        supabase_key,
        '/auth/v1/resend',
        {
            'email': email,
            'type': 'signup'
        }
    )
    
    # Handle errors
    if status >= 400:
        # Even if Supabase fails, record the attempt
        record_resend_attempt(email)
        
        error_msg = data.get('message') or \
                   data.get('error') or \
                   data.get('error_description') or \
                   'Gagal mengirim email verifikasi.'
        
        # If user not found, still return somewhat helpful message
        if 'user not found' in str(error_msg).lower():
            return 404, {
                'ok': False,
                'error': 'User tidak ditemukan. Silakan signup terlebih dahulu.'
            }
        
        return status, {
            'ok': False,
            'error': format_error_message(error_msg)
        }
    
    # Success - record the attempt
    record_resend_attempt(email)
    
    return 200, {
        'ok': True,
        'message': 'Email verifikasi sudah dikirim. Cek inbox Anda.',
        'retry_after_seconds': 0
    }


def logout_handler() -> Tuple[int, Dict[str, Any]]:
    """
    Handle user logout.
    
    Clears Flask session.
    
    Returns:
        Tuple of (http_status, response_dict)
    """
    session.pop('auth_user', None)
    session.pop('auth_access_token', None)
    session.modified = True
    
    return 200, {
        'ok': True,
        'message': 'Logout berhasil.'
    }
