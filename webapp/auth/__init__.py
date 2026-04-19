"""Authentication module for email verification and access control."""

from .decorators import require_verified_email
from .handlers import (
    signup_handler,
    login_handler,
    verify_email_handler,
    resend_verification_handler,
    logout_handler,
)
from .utils import (
    validate_email,
    validate_password,
    check_resend_rate_limit,
    record_resend_attempt,
)

__all__ = [
    'require_verified_email',
    'signup_handler',
    'login_handler',
    'verify_email_handler',
    'resend_verification_handler',
    'logout_handler',
    'validate_email',
    'validate_password',
    'check_resend_rate_limit',
    'record_resend_attempt',
]
