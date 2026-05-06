from db import get_db

class SubjectService:
    @staticmethod
    def get_all(): return get_db().execute("SELECT * FROM subjects ORDER BY id").fetchall()
    @staticmethod
    def get_by_id(sid): return get_db().execute("SELECT * FROM subjects WHERE id=?", (sid,)).fetchone()
    @staticmethod
    def get_knowledge_points(sid):
        return get_db().execute("SELECT * FROM knowledge_points WHERE subject_id=? ORDER BY chapter,name", (sid,)).fetchall()
    @staticmethod
    def create_knowledge_point(sid, name, chapter='未分类'):
        db = get_db()
        ex = db.execute("SELECT id FROM knowledge_points WHERE subject_id=? AND name=?", (sid,name)).fetchone()
        if ex: return ex['id']
        cur = db.execute("INSERT INTO knowledge_points(subject_id,name,chapter) VALUES(?,?,?)", (sid,name,chapter))
        db.commit()
        return cur.lastrowid
