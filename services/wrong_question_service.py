"""
ANC-05: WrongQuestionService — 错题管理（MOD-03）
负责：CRUD、图片上传、Pillow 缩略图生成（限宽 800px）
"""
import os
import uuid
from datetime import date
from flask import current_app
from PIL import Image
from db import get_db

# 允许的图片扩展名
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}


def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_image(file_obj) -> tuple[str, str]:
    """
    保存上传图片并生成缩略图
    返回 (original_relative_path, thumb_relative_path)
    原图落盘：static/uploads/<uuid>.<ext>
    缩略图：  static/uploads/thumbs/<uuid>_thumb.<ext>
    """
    ext = file_obj.filename.rsplit('.', 1)[1].lower()
    uid = uuid.uuid4().hex
    filename      = f"{uid}.{ext}"
    thumb_filename = f"{uid}_thumb.{ext}"

    upload_folder    = current_app.config['UPLOAD_FOLDER']
    thumbnail_folder = current_app.config['THUMBNAIL_FOLDER']
    max_width        = current_app.config['THUMBNAIL_MAX_WIDTH']

    orig_path  = os.path.join(upload_folder,    filename)
    thumb_path = os.path.join(thumbnail_folder, thumb_filename)

    # 保存原图
    file_obj.save(orig_path)

    # 生成缩略图（限宽 800px，保持比例）
    with Image.open(orig_path) as img:
        img = img.convert('RGB') if img.mode in ('RGBA', 'P') else img
        w, h = img.size
        if w > max_width:
            ratio     = max_width / w
            new_size  = (max_width, int(h * ratio))
            img       = img.resize(new_size, Image.LANCZOS)
        img.save(thumb_path, optimize=True, quality=85)

    # 返回相对路径（以 static 为根，用于 url_for）
    rel_orig  = f"uploads/{filename}"
    rel_thumb = f"uploads/thumbs/{thumb_filename}"
    return rel_orig, rel_thumb


class WrongQuestionService:

    # ── 创建 ─────────────────────────────────────────────────────────────
    @staticmethod
    def create(subject_id: int,
               question_content: str,
               answer_content: str = '',
               difficulty: int = 2,
               knowledge_point_id: int = None,
               image_file=None) -> int:
        """
        ANC-05: 录入错题（含图片上传）
        返回新建的错题 id
        """
        db = get_db()
        image_path = thumb_path = None

        if image_file and image_file.filename and _allowed_file(image_file.filename):
            image_path, thumb_path = _save_image(image_file)

        cur = db.execute(
            """INSERT INTO wrong_questions
               (student_id, subject_id, knowledge_point_id,
                question_content, image_path, thumb_path,
                answer_content, difficulty, last_error_date)
               VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (subject_id, knowledge_point_id,
             question_content, image_path, thumb_path,
             answer_content, difficulty, date.today().isoformat())
        )
        db.commit()
        return cur.lastrowid

    # ── 列表查询 ──────────────────────────────────────────────────────────
    @staticmethod
    def list_all(subject_id: int = None,
                 difficulty: int = None,
                 keyword: str = None,
                 page: int = 1,
                 per_page: int = 20):
        """
        分页查询错题列表，支持科目/难度/关键字筛选
        返回 (items, total_count)
        """
        db = get_db()
        where_clauses = ['wq.student_id = 1']
        params: list = []

        if subject_id:
            where_clauses.append('wq.subject_id = ?')
            params.append(subject_id)
        if difficulty:
            where_clauses.append('wq.difficulty = ?')
            params.append(difficulty)
        if keyword:
            where_clauses.append('wq.question_content LIKE ?')
            params.append(f'%{keyword}%')

        where_sql = ' AND '.join(where_clauses)
        count = db.execute(
            f"SELECT COUNT(*) AS cnt FROM wrong_questions wq WHERE {where_sql}",
            params
        ).fetchone()['cnt']

        offset = (page - 1) * per_page
        items = db.execute(
            f"""SELECT wq.*, s.name AS subject_name, s.color AS subject_color,
                       s.icon AS subject_icon,
                       kp.name AS kp_name
                FROM wrong_questions wq
                JOIN subjects s ON s.id = wq.subject_id
                LEFT JOIN knowledge_points kp ON kp.id = wq.knowledge_point_id
                WHERE {where_sql}
                ORDER BY wq.created_at DESC
                LIMIT ? OFFSET ?""",
            params + [per_page, offset]
        ).fetchall()

        return items, count

    # ── 单条查询 ──────────────────────────────────────────────────────────
    @staticmethod
    def get_by_id(wq_id: int):
        db = get_db()
        row = db.execute(
            """SELECT wq.*, s.name AS subject_name, s.color AS subject_color,
                      s.icon AS subject_icon,
                      kp.name AS kp_name, kp.chapter AS kp_chapter
               FROM wrong_questions wq
               JOIN subjects s ON s.id = wq.subject_id
               LEFT JOIN knowledge_points kp ON kp.id = wq.knowledge_point_id
               WHERE wq.id = ? AND wq.student_id = 1""",
            (wq_id,)
        ).fetchone()
        return row

    # ── 更新 ─────────────────────────────────────────────────────────────
    @staticmethod
    def update(wq_id: int,
               subject_id: int,
               question_content: str,
               answer_content: str = '',
               difficulty: int = 2,
               knowledge_point_id: int = None,
               image_file=None):
        db = get_db()
        existing = WrongQuestionService.get_by_id(wq_id)
        if not existing:
            return False

        image_path = existing['image_path']
        thumb_path = existing['thumb_path']

        if image_file and image_file.filename and _allowed_file(image_file.filename):
            image_path, thumb_path = _save_image(image_file)

        db.execute(
            """UPDATE wrong_questions
               SET subject_id=?, knowledge_point_id=?,
                   question_content=?, answer_content=?,
                   difficulty=?, image_path=?, thumb_path=?,
                   updated_at=datetime('now','localtime')
               WHERE id=? AND student_id=1""",
            (subject_id, knowledge_point_id,
             question_content, answer_content,
             difficulty, image_path, thumb_path, wq_id)
        )
        db.commit()
        return True

    # ── 标记已掌握 ────────────────────────────────────────────────────
    @staticmethod
    def mark_mastered(wq_id: int, mastered: bool = True):
        db = get_db()
        db.execute(
            "UPDATE wrong_questions SET is_mastered=? WHERE id=? AND student_id=1",
            (1 if mastered else 0, wq_id)
        )
        db.commit()

    # ── 删除 ─────────────────────────────────────────────────────────────
    @staticmethod
    def delete(wq_id: int):
        db = get_db()
        db.execute(
            "DELETE FROM wrong_questions WHERE id=? AND student_id=1",
            (wq_id,)
        )
        db.commit()

    # ── 增加错误次数 ───────────────────────────────────────────────────
    @staticmethod
    def increment_error(wq_id: int):
        db = get_db()
        db.execute(
            """UPDATE wrong_questions
               SET error_count = error_count + 1,
                   last_error_date = date('now','localtime')
               WHERE id=? AND student_id=1""",
            (wq_id,)
        )
        db.commit()
