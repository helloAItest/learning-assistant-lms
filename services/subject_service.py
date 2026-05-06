"""科目与知识点查询服务"""
from db import get_db


class SubjectService:

    @staticmethod
    def get_all():
        """获取所有科目"""
        return get_db().execute(
            "SELECT * FROM subjects ORDER BY id"
        ).fetchall()

    @staticmethod
    def get_by_id(subject_id: int):
        return get_db().execute(
            "SELECT * FROM subjects WHERE id=?", (subject_id,)
        ).fetchone()

    @staticmethod
    def get_knowledge_points(subject_id: int):
        """获取某科目下的知识点列表"""
        return get_db().execute(
            """SELECT * FROM knowledge_points
               WHERE subject_id=? ORDER BY chapter, name""",
            (subject_id,)
        ).fetchall()

    @staticmethod
    def create_knowledge_point(subject_id: int, name: str, chapter: str = '未分类') -> int:
        """创建知识点，返回 id（已存在则返回现有 id）"""
        db = get_db()
        existing = db.execute(
            "SELECT id FROM knowledge_points WHERE subject_id=? AND name=?",
            (subject_id, name)
        ).fetchone()
        if existing:
            return existing['id']
        cur = db.execute(
            "INSERT INTO knowledge_points(subject_id, name, chapter) VALUES(?,?,?)",
            (subject_id, name, chapter)
        )
        db.commit()
        return cur.lastrowid
