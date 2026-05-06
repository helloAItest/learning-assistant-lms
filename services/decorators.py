from functools import wraps
from flask import session, abort
from services.role_service import RoleService, STUDENT, PARENT


def require_student(f):
    """装饰器：仅学生模式可访问，家长模式返回 403"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not RoleService.is_student():
            abort(403)
        return f(*args, **kwargs)
    return decorated


def require_parent(f):
    """装饰器：仅家长模式可访问"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not RoleService.is_parent():
            abort(403)
        return f(*args, **kwargs)
    return decorated
