"""Utility functions for authentication module."""

import re
import time
from datetime import datetime, timedelta
from typing import Tuple

def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    email = str(email).strip() if email else ""
    if not email:
        return False, "Email tidak boleh kosong."
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Format email tidak valid."
    
    if len(email) > 255:
        return False, "Email terlalu panjang."
    
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    pwd = str(password) if password else ""
    
    if not pwd:
        return False, "Password tidak boleh kosong."
    
    if len(pwd) < 8:
        return False, "Password minimal 8 karakter."
    
    if len(pwd) > 128:
        return False, "Password terlalu panjang."
    
    # Optional: add complexity check (at least one number, one letter)
    has_letter = any(c.isalpha() for c in pwd)
    has_digit = any(c.isdigit() for c in pwd)
    
    if not (has_letter and has_digit):
        return False, "Password harus memiliki huruf dan angka."
    
    return True, ""


def validate_full_name(full_name: str) -> Tuple[bool, str]:
    """
    Validate full name.
    
    Args:
        full_name: Full name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    name = str(full_name).strip() if full_name else ""
    
    if not name:
        return False, "Nama lengkap tidak boleh kosong."
    
    if len(name) < 2:
        return False, "Nama terlalu pendek (minimal 2 karakter)."
    
    if len(name) > 255:
        return False, "Nama terlalu panjang."
    
    # Allow letters, spaces, hyphens, apostrophes
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        return False, "Nama hanya boleh berisi huruf, spasi, dan tanda hubung."
    
    return True, ""


# In-memory rate limiting (for development)
# In production, use Redis or database
RESEND_ATTEMPTS = {}  # {email: [(timestamp, attempt_count), ...]}
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
MAX_RESENDS_PER_WINDOW = 3


def check_resend_rate_limit(email: str) -> Tuple[bool, dict]:
    """
    Check if user has exceeded resend rate limit (3 per hour).
    
    Args:
        email: User email address
        
    Returns:
        Tuple of (is_allowed, info_dict)
        info_dict contains: 'allowed', 'remaining', 'retry_after_seconds'
    """
    email = str(email).lower().strip()
    current_time = time.time()
    
    # Clean up old entries
    if email in RESEND_ATTEMPTS:
        RESEND_ATTEMPTS[email] = [
            (ts, count) for ts, count in RESEND_ATTEMPTS[email]
            if current_time - ts < RATE_LIMIT_WINDOW
        ]
    
    # Check current count
    if email not in RESEND_ATTEMPTS or not RESEND_ATTEMPTS[email]:
        # First attempt in this window
        return True, {
            'allowed': True,
            'remaining': MAX_RESENDS_PER_WINDOW - 1,
            'retry_after_seconds': 0,
        }
    
    attempts = RESEND_ATTEMPTS[email]
    latest_ts, attempt_count = attempts[-1] if attempts else (0, 0)
    
    if attempt_count >= MAX_RESENDS_PER_WINDOW:
        # Rate limit exceeded
        oldest_ts = attempts[0][0]
        retry_after = int(RATE_LIMIT_WINDOW - (current_time - oldest_ts)) + 1
        return False, {
            'allowed': False,
            'remaining': 0,
            'retry_after_seconds': max(1, retry_after),
        }
    
    # Allow and increment
    return True, {
        'allowed': True,
        'remaining': MAX_RESENDS_PER_WINDOW - attempt_count - 1,
        'retry_after_seconds': 0,
    }


def record_resend_attempt(email: str):
    """
    Record a resend verification email attempt.
    
    In production, store in database instead.
    
    Args:
        email: User email address
    """
    email = str(email).lower().strip()
    current_time = time.time()
    
    if email not in RESEND_ATTEMPTS:
        RESEND_ATTEMPTS[email] = []
    
    # Clean old entries
    RESEND_ATTEMPTS[email] = [
        (ts, count) for ts, count in RESEND_ATTEMPTS[email]
        if current_time - ts < RATE_LIMIT_WINDOW
    ]
    
    if not RESEND_ATTEMPTS[email]:
        # First attempt in new window
        RESEND_ATTEMPTS[email] = [(current_time, 1)]
    else:
        # Increment count in current window
        ts, count = RESEND_ATTEMPTS[email][-1]
        RESEND_ATTEMPTS[email][-1] = (ts, count + 1)


def format_error_message(error_str: str) -> str:
    """
    Format Supabase error messages to user-friendly Indonesian messages.
    
    Args:
        error_str: Raw error string from Supabase
        
    Returns:
        Formatted user-friendly message
    """
    error = str(error_str).lower()
    
    if 'already registered' in error or 'user already exists' in error:
        return "Email sudah terdaftar. Silakan login atau gunakan email lain."
    
    if 'invalid email' in error:
        return "Email tidak valid."
    
    if 'password' in error and 'weak' in error:
        return "Password terlalu lemah. Gunakan kombinasi huruf, angka, dan simbol."
    
    if 'email not confirmed' in error:
        return "Email belum dikonfirmasi. Silakan cek inbox Anda."
    
    if 'invalid credentials' in error or 'wrong password' in error:
        return "Email atau password salah."
    
    if 'user not found' in error:
        return "User tidak ditemukan."
    
    if 'token' in error and 'expired' in error:
        return "Link verifikasi sudah kadaluarsa. Minta email verifikasi baru."
    
    if 'invalid token' in error:
        return "Token tidak valid. Minta email verifikasi baru."
    
    # Default message
    return "Terjadi kesalahan. Silakan coba lagi nanti."
