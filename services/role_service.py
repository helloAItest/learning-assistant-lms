from flask import session

REVIEW_INTERVALS = {1:1, 2:3, 3:7, 4:14, 5:30, 6:None}
STUDENT = 'student'
PARENT  = 'parent'
DEFAULT_ROLE = STUDENT

class RoleService:
    @staticmethod
    def get_current_role(): return session.get('role', DEFAULT_ROLE)
    @staticmethod
    def switch_role(role):
        if role in (STUDENT, PARENT):
            session['role'] = role
            return True
        return False
    @staticmethod
    def is_student(): return RoleService.get_current_role() == STUDENT
    @staticmethod
    def is_parent(): return RoleService.get_current_role() == PARENT
    @staticmethod
    def get_display_name():
        return '学生模式' if RoleService.get_current_role()==STUDENT else '家长模式'
