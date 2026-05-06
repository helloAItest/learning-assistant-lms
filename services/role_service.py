from flask import session

# ─── 艾宾浩斯复习间隔天数 ────────────────────────────────────────────
# Stage: 1    2    3    4    5    6(已掌握，不再提醒)
REVIEW_INTERVALS = {1: 1, 2: 3, 3: 7, 4: 14, 5: 30, 6: None}

STUDENT = 'student'
PARENT  = 'parent'
DEFAULT_ROLE = STUDENT


class RoleService:
    """ANC-01: 角色切换服务（MOD-01）"""

    @staticmethod
    def get_current_role() -> str:
        """获取当前 Session 中的角色，默认为学生"""
        return session.get('role', DEFAULT_ROLE)

    @staticmethod
    def switch_role(role: str) -> bool:
        """
        ANC-01: RoleService.switch_role(role)
        将指定角色写入 Session，返回是否切换成功
        """
        if role in (STUDENT, PARENT):
            session['role'] = role
            return True
        return False

    @staticmethod
    def is_student() -> bool:
        return RoleService.get_current_role() == STUDENT

    @staticmethod
    def is_parent() -> bool:
        return RoleService.get_current_role() == PARENT

    @staticmethod
    def get_display_name() -> str:
        role = RoleService.get_current_role()
        return '学生模式' if role == STUDENT else '家长模式'
