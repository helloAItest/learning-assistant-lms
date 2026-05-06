from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, abort)
from services.wrong_question_service import WrongQuestionService
from services.subject_service import SubjectService
from services.role_service import RoleService
from services.decorators import require_student
from services import ocr_service

wq_bp = Blueprint('wrong_questions', __name__, url_prefix='/wrong-questions')


# ── 列表 ───────────────────────────────────────────────────────────────────
@wq_bp.route('/')
def index():
    subject_id = request.args.get('subject_id', type=int)
    difficulty  = request.args.get('difficulty',  type=int)
    keyword     = request.args.get('q', '').strip() or None
    page        = request.args.get('page', 1, type=int)

    items, total = WrongQuestionService.list_all(
        subject_id=subject_id,
        difficulty=difficulty,
        keyword=keyword,
        page=page,
        per_page=20,
    )
    subjects    = SubjectService.get_all()
    total_pages = (total + 19) // 20

    return render_template(
        'wrong_questions/list.html',
        current_role=RoleService.get_current_role(),
        items=items,
        total=total,
        subjects=subjects,
        selected_subject=subject_id,
        selected_difficulty=difficulty,
        keyword=keyword or '',
        page=page,
        total_pages=total_pages,
    )


# ── 录入 ───────────────────────────────────────────────────────────────────
@wq_bp.route('/create', methods=['GET', 'POST'])
@require_student
def create():
    subjects = SubjectService.get_all()

    if request.method == 'POST':
        subject_id      = request.form.get('subject_id', type=int)
        question_content= request.form.get('question_content', '').strip()
        answer_content  = request.form.get('answer_content', '').strip()
        difficulty      = request.form.get('difficulty', 2, type=int)
        kp_id           = request.form.get('knowledge_point_id', type=int)
        new_kp_name     = request.form.get('new_kp_name', '').strip()
        image_file      = request.files.get('image')

        # 简单校验
        if not subject_id:
            flash('请选择科目', 'warning')
            return render_template('wrong_questions/create.html',
                                   subjects=subjects,
                                   current_role=RoleService.get_current_role())
        if not question_content or question_content == '<p><br></p>':
            flash('题目内容不能为空', 'warning')
            return render_template('wrong_questions/create.html',
                                   subjects=subjects,
                                   current_role=RoleService.get_current_role())

        # 处理新建知识点
        if new_kp_name:
            kp_id = SubjectService.create_knowledge_point(subject_id, new_kp_name)
        elif not kp_id:
            kp_id = None

        try:
            wq_id = WrongQuestionService.create(
                subject_id=subject_id,
                question_content=question_content,
                answer_content=answer_content,
                difficulty=difficulty,
                knowledge_point_id=kp_id,
                image_file=image_file if (image_file and image_file.filename) else None,
            )
            flash('✅ 错题录入成功！', 'success')
            return redirect(url_for('wrong_questions.detail', wq_id=wq_id))
        except Exception as e:
            flash(f'录入失败：{e}', 'danger')

    return render_template('wrong_questions/create.html',
                           subjects=subjects,
                           current_role=RoleService.get_current_role())


# ── 详情 ───────────────────────────────────────────────────────────────────
@wq_bp.route('/<int:wq_id>')
def detail(wq_id):
    wq = WrongQuestionService.get_by_id(wq_id)
    if not wq:
        abort(404)
    return render_template('wrong_questions/detail.html',
                           wq=wq,
                           current_role=RoleService.get_current_role())


# ── 编辑 ───────────────────────────────────────────────────────────────────
@wq_bp.route('/<int:wq_id>/edit', methods=['GET', 'POST'])
@require_student
def edit(wq_id):
    wq = WrongQuestionService.get_by_id(wq_id)
    if not wq:
        abort(404)
    subjects = SubjectService.get_all()
    kps      = SubjectService.get_knowledge_points(wq['subject_id'])

    if request.method == 'POST':
        subject_id       = request.form.get('subject_id', type=int)
        question_content = request.form.get('question_content', '').strip()
        answer_content   = request.form.get('answer_content', '').strip()
        difficulty       = request.form.get('difficulty', 2, type=int)
        kp_id            = request.form.get('knowledge_point_id', type=int)
        new_kp_name      = request.form.get('new_kp_name', '').strip()
        image_file       = request.files.get('image')

        if not question_content or question_content == '<p><br></p>':
            flash('题目内容不能为空', 'warning')
        else:
            if new_kp_name:
                kp_id = SubjectService.create_knowledge_point(subject_id, new_kp_name)
            elif not kp_id:
                kp_id = None

            WrongQuestionService.update(
                wq_id=wq_id,
                subject_id=subject_id,
                question_content=question_content,
                answer_content=answer_content,
                difficulty=difficulty,
                knowledge_point_id=kp_id,
                image_file=image_file if (image_file and image_file.filename) else None,
            )
            flash('✅ 修改已保存', 'success')
            return redirect(url_for('wrong_questions.detail', wq_id=wq_id))

    return render_template('wrong_questions/edit.html',
                           wq=wq,
                           subjects=subjects,
                           kps=kps,
                           current_role=RoleService.get_current_role())


# ── 删除 ───────────────────────────────────────────────────────────────────
@wq_bp.route('/<int:wq_id>/delete', methods=['POST'])
@require_student
def delete(wq_id):
    WrongQuestionService.delete(wq_id)
    flash('错题已删除', 'info')
    return redirect(url_for('wrong_questions.index'))


# ── 标记已掌握 / 取消 ──────────────────────────────────────────────────
@wq_bp.route('/<int:wq_id>/mastered', methods=['POST'])
@require_student
def toggle_mastered(wq_id):
    wq = WrongQuestionService.get_by_id(wq_id)
    if not wq:
        abort(404)
    new_val = not bool(wq['is_mastered'])
    WrongQuestionService.mark_mastered(wq_id, new_val)
    msg = '🎉 已标记为掌握！' if new_val else '已取消掌握标记'
    flash(msg, 'success')
    return redirect(url_for('wrong_questions.detail', wq_id=wq_id))


# ── 批量导入（入口页） ────────────────────────────────────
@wq_bp.route('/batch-import')
@require_student
def batch_import():
    subjects = SubjectService.get_all()
    ocr_available, ocr_msg = ocr_service.check_ocr_available()
    return render_template(
        'wrong_questions/batch_import.html',
        current_role=RoleService.get_current_role(),
        subjects=subjects,
        ocr_available=ocr_available,
        ocr_msg=ocr_msg,
    )
