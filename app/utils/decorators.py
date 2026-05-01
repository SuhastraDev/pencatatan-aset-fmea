from functools import wraps
from flask import abort, redirect, url_for, request
from flask_login import current_user


def role_required(*roles):
    """Batasi akses route hanya untuk role tertentu."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                # Redirect ke login dengan next parameter, bukan abort(401)
                return redirect(url_for('auth.login', next=request.url))
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_room_ownership(f):
    """Pastikan admin_ruangan hanya mengakses aset milik ruangannya sendiri."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role == 'admin_ruangan':
            asset_id = kwargs.get('asset_id') or kwargs.get('id')
            if asset_id:
                from app.models.asset import Asset
                asset = Asset.query.get_or_404(asset_id)
                if asset.room_id != current_user.room_id:
                    abort(403)
        return f(*args, **kwargs)
    return decorated_function
