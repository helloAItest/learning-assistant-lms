from flask import Blueprint, redirect, request, url_for, flash
from services.role_service import RoleService

role_bp = Blueprint('role', __name__)


@role_bp.route('/switch-role/<role>')
def switch_role(role):
    """ANC-01: 切换当前角色写入 Session，然后跳回来源页"""
    if RoleService.switch_role(role):
        name = RoleService.get_display_name()
        flash(f'已切换到{name} 👋', 'success')
    else:
        flash('无效的角色', 'danger')

    # 跳回来源页，若无来源则回首页
    referrer = request.referrer
    return redirect(referrer if referrer else url_for('main.dashboard'))
