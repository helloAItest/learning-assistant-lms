from flask import Blueprint, render_template
from services.role_service import RoleService
from db import get_db
from datetime import date

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    db = get_db()
    role = RoleService.get_current_role()
    today = date.today().isoformat()
    today_review_count = db.execute(
        "SELECT COUNT(*) AS cnt FROM review_plans WHERE student_id=1 AND next_review_date<=? AND review_stage<6",
        (today,)
    ).fetchone()['cnt']
    total_wrong = db.execute(
        "SELECT COUNT(*) AS cnt FROM wrong_questions WHERE student_id=1 AND is_mastered=0"
    ).fetchone()['cnt']
    week_wrong = db.execute(
        "SELECT COUNT(*) AS cnt FROM wrong_questions WHERE student_id=1 AND created_at>=date('now','localtime','-7 days')"
    ).fetchone()['cnt']
    subjects_stats = db.execute(
        """SELECT s.name,s.icon,s.color,COUNT(wq.id) AS wrong_count
           FROM subjects s LEFT JOIN wrong_questions wq
             ON wq.subject_id=s.id AND wq.student_id=1 AND wq.is_mastered=0
           GROUP BY s.id ORDER BY wrong_count DESC"""
    ).fetchall()
    recent_wrongs = db.execute(
        """SELECT wq.id,wq.question_content,wq.difficulty,wq.created_at,
                  s.name AS subject_name,s.color AS subject_color,s.icon AS subject_icon
           FROM wrong_questions wq JOIN subjects s ON s.id=wq.subject_id
           WHERE wq.student_id=1 ORDER BY wq.created_at DESC LIMIT 5"""
    ).fetchall()
    return render_template('dashboard.html', current_role=role,
        today_review_count=today_review_count, total_wrong=total_wrong,
        week_wrong=week_wrong, subjects_stats=subjects_stats, recent_wrongs=recent_wrongs)
