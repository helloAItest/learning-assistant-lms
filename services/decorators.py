from functools import wraps
from flask import abort
from services.role_service import RoleService, STUDENT, PARENT

def require_student(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not RoleService.is_student(): abort(403)
        return f(*args, **kwargs)
    return decorated

def require_parent(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not RoleService.is_parent(): abort(403)
        return f(*args, **kwargs)
    return decorated
