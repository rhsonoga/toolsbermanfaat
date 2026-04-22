"""Premium access helpers."""


def get_auth_status(auth_user=None):
    """
    Determine authentication status for premium overlay.

    Returns:
        'verified': User is logged in and email is verified
        'need_verify': User is logged in but email is not verified
        'not_login': User is not logged in
    """
    if not auth_user:
        return 'not_login'

    email_verified_at = auth_user.get('email_verified_at')
    if email_verified_at:
        return 'verified'
    return 'need_verify'
