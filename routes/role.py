from flask import Blueprint, redirect, request, url_for, flash
from services.role_service import RoleService

role_bp = Blueprint('role', __name__)

@role_bp.route('/switch-role/<role>')
def switch_role(role):
    """ANC-01"""
    if RoleService.switch_role(role):
        flash(f'已切换到{RoleService.get_display_name()} 👋', 'success')
    else:
        flash('无效的角色', 'danger')
    referrer = request.referrer
    return redirect(referrer if referrer else url_for('main.dashboard'))
