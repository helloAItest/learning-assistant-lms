"""
ANC-05: WrongQuestionService — 错题管理（MOD-03）
"""
import os, uuid
from datetime import date
from flask import current_app
from PIL import Image
from db import get_db

ALLOWED_EXTENSIONS = {'jpg','jpeg','png','gif','webp'}

def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def _save_image(file_obj):
    ext = file_obj.filename.rsplit('.',1)[1].lower()
    uid = uuid.uuid4().hex
    fname, tname = f"{uid}.{ext}", f"{uid}_thumb.{ext}"
    uf = current_app.config['UPLOAD_FOLDER']
    tf = current_app.config['THUMBNAIL_FOLDER']
    mw = current_app.config['THUMBNAIL_MAX_WIDTH']
    orig = os.path.join(uf, fname)
    thumb = os.path.join(tf, tname)
    file_obj.save(orig)
    with Image.open(orig) as img:
        img = img.convert('RGB') if img.mode in ('RGBA','P') else img
        w, h = img.size
        if w > mw:
            img = img.resize((mw, int(h*mw/w)), Image.LANCZOS)
        img.save(thumb, optimize=True, quality=85)
    return f"uploads/{fname}", f"uploads/thumbs/{tname}"

class WrongQuestionService:
    @staticmethod
    def create(subject_id, question_content, answer_content='', difficulty=2,
               knowledge_point_id=None, image_file=None):
        db = get_db()
        ip = tp = None
        if image_file and image_file.filename and _allowed_file(image_file.filename):
            ip, tp = _save_image(image_file)
        cur = db.execute(
            """INSERT INTO wrong_questions(student_id,subject_id,knowledge_point_id,
               question_content,image_path,thumb_path,answer_content,difficulty,last_error_date)
               VALUES(1,?,?,?,?,?,?,?,?)""",
            (subject_id,knowledge_point_id,question_content,ip,tp,answer_content,difficulty,date.today().isoformat()))
        db.commit()
        return cur.lastrowid

    @staticmethod
    def list_all(subject_id=None, difficulty=None, keyword=None, page=1, per_page=20):
        db = get_db()
        w, p = ['wq.student_id=1'], []
        if subject_id: w.append('wq.subject_id=?'); p.append(subject_id)
        if difficulty:  w.append('wq.difficulty=?'); p.append(difficulty)
        if keyword:     w.append('wq.question_content LIKE ?'); p.append(f'%{keyword}%')
        ws = ' AND '.join(w)
        cnt = db.execute(f"SELECT COUNT(*) AS cnt FROM wrong_questions wq WHERE {ws}", p).fetchone()['cnt']
        items = db.execute(
            f"""SELECT wq.*,s.name AS subject_name,s.color AS subject_color,s.icon AS subject_icon,
                       kp.name AS kp_name
                FROM wrong_questions wq JOIN subjects s ON s.id=wq.subject_id
                LEFT JOIN knowledge_points kp ON kp.id=wq.knowledge_point_id
                WHERE {ws} ORDER BY wq.created_at DESC LIMIT ? OFFSET ?""",
            p+[per_page,(page-1)*per_page]).fetchall()
        return items, cnt

    @staticmethod
    def get_by_id(wq_id):
        return get_db().execute(
            """SELECT wq.*,s.name AS subject_name,s.color AS subject_color,s.icon AS subject_icon,
                      kp.name AS kp_name,kp.chapter AS kp_chapter
               FROM wrong_questions wq JOIN subjects s ON s.id=wq.subject_id
               LEFT JOIN knowledge_points kp ON kp.id=wq.knowledge_point_id
               WHERE wq.id=? AND wq.student_id=1""", (wq_id,)).fetchone()

    @staticmethod
    def update(wq_id, subject_id, question_content, answer_content='', difficulty=2,
               knowledge_point_id=None, image_file=None):
        db = get_db()
        ex = WrongQuestionService.get_by_id(wq_id)
        if not ex: return False
        ip, tp = ex['image_path'], ex['thumb_path']
        if image_file and image_file.filename and _allowed_file(image_file.filename):
            ip, tp = _save_image(image_file)
        db.execute(
            """UPDATE wrong_questions SET subject_id=?,knowledge_point_id=?,
               question_content=?,answer_content=?,difficulty=?,image_path=?,thumb_path=?,
               updated_at=datetime('now','localtime') WHERE id=? AND student_id=1""",
            (subject_id,knowledge_point_id,question_content,answer_content,difficulty,ip,tp,wq_id))
        db.commit()
        return True

    @staticmethod
    def mark_mastered(wq_id, mastered=True):
        db = get_db()
        db.execute("UPDATE wrong_questions SET is_mastered=? WHERE id=? AND student_id=1", (1 if mastered else 0, wq_id))
        db.commit()

    @staticmethod
    def delete(wq_id):
        db = get_db()
        db.execute("DELETE FROM wrong_questions WHERE id=? AND student_id=1", (wq_id,))
        db.commit()

    @staticmethod
    def increment_error(wq_id):
        db = get_db()
        db.execute("UPDATE wrong_questions SET error_count=error_count+1,last_error_date=date('now','localtime') WHERE id=? AND student_id=1", (wq_id,))
        db.commit()
