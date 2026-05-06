from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from services.wrong_question_service import WrongQuestionService
from services.subject_service import SubjectService
from services.role_service import RoleService
from services.decorators import require_student
from services import ocr_service

wq_bp = Blueprint('wrong_questions', __name__, url_prefix='/wrong-questions')

@wq_bp.route('/')
def index():
    sid = request.args.get('subject_id', type=int)
    dif = request.args.get('difficulty',  type=int)
    kw  = request.args.get('q','').strip() or None
    pg  = request.args.get('page',1,type=int)
    items, total = WrongQuestionService.list_all(subject_id=sid,difficulty=dif,keyword=kw,page=pg,per_page=20)
    subjects = SubjectService.get_all()
    return render_template('wrong_questions/list.html', current_role=RoleService.get_current_role(),
        items=items, total=total, subjects=subjects, selected_subject=sid,
        selected_difficulty=dif, keyword=kw or '', page=pg, total_pages=(total+19)//20)

@wq_bp.route('/create', methods=['GET','POST'])
@require_student
def create():
    subjects = SubjectService.get_all()
    if request.method == 'POST':
        sid = request.form.get('subject_id', type=int)
        qc  = request.form.get('question_content','').strip()
        ac  = request.form.get('answer_content','').strip()
        dif = request.form.get('difficulty',2,type=int)
        kp  = request.form.get('knowledge_point_id',type=int)
        nkp = request.form.get('new_kp_name','').strip()
        img = request.files.get('image')
        if not sid: flash('请选择科目','warning'); return render_template('wrong_questions/create.html',subjects=subjects,current_role=RoleService.get_current_role())
        if not qc or qc=='<p><br></p>': flash('题目内容不能为空','warning'); return render_template('wrong_questions/create.html',subjects=subjects,current_role=RoleService.get_current_role())
        if nkp: kp = SubjectService.create_knowledge_point(sid, nkp)
        elif not kp: kp = None
        try:
            wqid = WrongQuestionService.create(subject_id=sid,question_content=qc,answer_content=ac,difficulty=dif,knowledge_point_id=kp,image_file=img if (img and img.filename) else None)
            flash('✅ 错题录入成功！','success'); return redirect(url_for('wrong_questions.detail',wq_id=wqid))
        except Exception as e: flash(f'录入失败：{e}','danger')
    return render_template('wrong_questions/create.html',subjects=subjects,current_role=RoleService.get_current_role())

@wq_bp.route('/<int:wq_id>')
def detail(wq_id):
    wq = WrongQuestionService.get_by_id(wq_id)
    if not wq: abort(404)
    return render_template('wrong_questions/detail.html',wq=wq,current_role=RoleService.get_current_role())

@wq_bp.route('/<int:wq_id>/edit', methods=['GET','POST'])
@require_student
def edit(wq_id):
    wq = WrongQuestionService.get_by_id(wq_id)
    if not wq: abort(404)
    subjects = SubjectService.get_all()
    kps = SubjectService.get_knowledge_points(wq['subject_id'])
    if request.method == 'POST':
        sid = request.form.get('subject_id',type=int)
        qc  = request.form.get('question_content','').strip()
        ac  = request.form.get('answer_content','').strip()
        dif = request.form.get('difficulty',2,type=int)
        kp  = request.form.get('knowledge_point_id',type=int)
        nkp = request.form.get('new_kp_name','').strip()
        img = request.files.get('image')
        if not qc or qc=='<p><br></p>': flash('题目内容不能为空','warning')
        else:
            if nkp: kp = SubjectService.create_knowledge_point(sid, nkp)
            elif not kp: kp = None
            WrongQuestionService.update(wq_id=wq_id,subject_id=sid,question_content=qc,answer_content=ac,difficulty=dif,knowledge_point_id=kp,image_file=img if (img and img.filename) else None)
            flash('✅ 修改已保存','success'); return redirect(url_for('wrong_questions.detail',wq_id=wq_id))
    return render_template('wrong_questions/edit.html',wq=wq,subjects=subjects,kps=kps,current_role=RoleService.get_current_role())

@wq_bp.route('/<int:wq_id>/delete', methods=['POST'])
@require_student
def delete(wq_id):
    WrongQuestionService.delete(wq_id); flash('错题已删除','info')
    return redirect(url_for('wrong_questions.index'))

@wq_bp.route('/<int:wq_id>/mastered', methods=['POST'])
@require_student
def toggle_mastered(wq_id):
    wq = WrongQuestionService.get_by_id(wq_id)
    if not wq: abort(404)
    nv = not bool(wq['is_mastered'])
    WrongQuestionService.mark_mastered(wq_id, nv)
    flash('🎉 已标记为掌握！' if nv else '已取消掌握标记','success')
    return redirect(url_for('wrong_questions.detail',wq_id=wq_id))

@wq_bp.route('/batch-import')
@require_student
def batch_import():
    subjects = SubjectService.get_all()
    ok, msg = ocr_service.check_ocr_available()
    return render_template('wrong_questions/batch_import.html',
        current_role=RoleService.get_current_role(), subjects=subjects, ocr_available=ok, ocr_msg=msg)
