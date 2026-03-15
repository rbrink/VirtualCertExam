from flask import redirect, url_for, abort
from flask_login import current_user
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth_bp.login"))
        if getattr(current_user, "role", None) != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated