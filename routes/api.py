"""API 蓝图：为前端 JS 提供 JSON 数据接口"""
import os
import uuid
from flask import Blueprint, jsonify, request, current_app
from services.subject_service import SubjectService
from services.wrong_question_service import WrongQuestionService, _allowed_file, _save_image
from services import ocr_service
from db import get_db
from PIL import Image

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/knowledge-points/<int:subject_id>')
def knowledge_points(subject_id):
    """获取某科目下的知识点列表（供录入表单异步加载）"""
    kps = SubjectService.get_knowledge_points(subject_id)
    return jsonify([
        {'id': kp['id'], 'name': kp['name'], 'chapter': kp['chapter']}
        for kp in kps
    ])


@api_bp.route('/ocr-status')
def ocr_status():
    """返回 OCR 是否就绪"""
    available, msg = ocr_service.check_ocr_available()
    return jsonify({'available': available, 'message': msg})


@api_bp.route('/batch-ocr', methods=['POST'])
def batch_ocr():
    """
    批量 OCR 接口：接收最多 10 张图片，每张执行：
      1. 保存原图 + 生成缩略图
      2. OCR 提取文字
      3. 规则引擎推断科目/难度
    返回 JSON 数组
    """
    files = request.files.getlist('images')  # input name="images"
    if not files:
        return jsonify({'error': '未上传任何图片'}), 400

    files = files[:10]  # 限制最多 10 张
    subjects = {s['name']: s['id'] for s in SubjectService.get_all()}
    results  = []

    for f in files:
        if not f.filename or not _allowed_file(f.filename):
            results.append({
                'error': f'不支持的文件类型: {f.filename}',
                'filename': f.filename
            })
            continue

        # 保存图片 + 生成缩略图
        try:
            image_path, thumb_path = _save_image(f)
        except Exception as e:
            results.append({'error': f'图片保存失败: {e}', 'filename': f.filename})
            continue

        # OCR 分析
        full_path = os.path.join(
            current_app.static_folder, image_path
        )
        parsed = ocr_service.parse_image(full_path)

        # 将科目名映射到 subject_id
        detected_subject_id = subjects.get(parsed['detected_subject'])

        results.append({
            'filename':         f.filename,
            'image_path':       image_path,
            'thumb_path':       thumb_path,
            'question_content': parsed['question_content'],
            'answer_content':   parsed['answer_content'],
            'detected_subject': parsed['detected_subject'],
            'subject_id':       detected_subject_id,
            'difficulty':       parsed['difficulty'],
            'ocr_available':    parsed['ocr_available'],
            'raw_text':         parsed['raw_text'],
        })

    return jsonify({'results': results, 'count': len(results)})


@api_bp.route('/batch-save', methods=['POST'])
def batch_save():
    """
    批量保存已确认的错题
    请求体 JSON:
    {
      "questions": [
        {
          "subject_id": int,
          "question_content": str,
          "answer_content": str,
          "difficulty": int,
          "image_path": str,
          "thumb_path": str
        }, ...
      ]
    }
    """
    data = request.get_json(force=True)
    if not data or 'questions' not in data:
        return jsonify({'error': '请求格式错误'}), 400

    questions = data['questions']
    if not questions:
        return jsonify({'error': '没有错题数据可保存'}), 400

    db = get_db()
    saved_ids = []

    for q in questions:
        subject_id = q.get('subject_id')
        question_content = q.get('question_content', '').strip()
        if not subject_id or not question_content:
            continue  # 跳过不完整的项

        cur = db.execute(
            """INSERT INTO wrong_questions
               (student_id, subject_id, knowledge_point_id,
                question_content, image_path, thumb_path,
                answer_content, difficulty, last_error_date)
               VALUES (1, ?, NULL, ?, ?, ?, ?, ?, date('now','localtime'))""",
            (subject_id,
             question_content,
             q.get('image_path') or None,
             q.get('thumb_path') or None,
             q.get('answer_content', ''),
             int(q.get('difficulty', 2)))
        )
        saved_ids.append(cur.lastrowid)

    db.commit()
    return jsonify({
        'saved': len(saved_ids),
        'ids':   saved_ids
    })
