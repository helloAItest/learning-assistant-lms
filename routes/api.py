"""API Blueprint"""
import os
from flask import Blueprint, jsonify, request, current_app
from services.subject_service import SubjectService
from services.wrong_question_service import _allowed_file, _save_image
from services import ocr_service
from db import get_db

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/knowledge-points/<int:subject_id>')
def knowledge_points(subject_id):
    kps = SubjectService.get_knowledge_points(subject_id)
    return jsonify([{'id':kp['id'],'name':kp['name'],'chapter':kp['chapter']} for kp in kps])

@api_bp.route('/ocr-status')
def ocr_status():
    available, msg = ocr_service.check_ocr_available()
    return jsonify({'available': available, 'message': msg})

@api_bp.route('/batch-ocr', methods=['POST'])
def batch_ocr():
    files = request.files.getlist('images')
    if not files: return jsonify({'error': '未上传任何图片'}), 400
    files = files[:10]
    subjects = {s['name']:s['id'] for s in SubjectService.get_all()}
    results = []
    for f in files:
        if not f.filename or not _allowed_file(f.filename):
            results.append({'error': f'不支持的文件类型', 'filename': f.filename})
            continue
        try:
            ip, tp = _save_image(f)
        except Exception as e:
            results.append({'error': str(e), 'filename': f.filename})
            continue
        full = os.path.join(current_app.static_folder, ip)
        parsed = ocr_service.parse_image(full)
        results.append({
            'filename': f.filename, 'image_path': ip, 'thumb_path': tp,
            'question_content': parsed['question_content'], 'answer_content': parsed['answer_content'],
            'detected_subject': parsed['detected_subject'], 'subject_id': subjects.get(parsed['detected_subject']),
            'difficulty': parsed['difficulty'], 'ocr_available': parsed['ocr_available'],
            'raw_text': parsed['raw_text'],
        })
    return jsonify({'results': results, 'count': len(results)})

@api_bp.route('/batch-save', methods=['POST'])
def batch_save():
    data = request.get_json(force=True)
    if not data or 'questions' not in data: return jsonify({'error': '请求格式错误'}), 400
    db = get_db()
    ids = []
    for q in data['questions']:
        sid = q.get('subject_id')
        qc  = q.get('question_content','').strip()
        if not sid or not qc: continue
        cur = db.execute(
            """INSERT INTO wrong_questions(student_id,subject_id,knowledge_point_id,
               question_content,image_path,thumb_path,answer_content,difficulty,last_error_date)
               VALUES(1,?,NULL,?,?,?,?,?,date('now','localtime'))""",
            (sid,qc,q.get('image_path') or None,q.get('thumb_path') or None,
             q.get('answer_content',''),int(q.get('difficulty',2))))
        ids.append(cur.lastrowid)
    db.commit()
    return jsonify({'saved': len(ids), 'ids': ids})
