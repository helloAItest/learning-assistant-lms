"""
OCR 识别服务 + 规则引擎
依赖：pytesseract + Tesseract OCR 可执行文件
一次性安装：https://github.com/UB-Mannheim/tesseract/wiki
           下载 tesseract-ocr-w64-setup-*.exe，安装时勾选 Additional language data → chi_sim
"""
import os
import re
from typing import Optional

# Tesseract 可执行文件路径（Windows 默认安装路径）
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ── 科目关键词映射表 ─────────────────────────────────────────────────────────
SUBJECT_KEYWORDS: dict[str, list[str]] = {
    '语文':  ['诗', '词', '文言', '阅读', '写作', '修辞', '字词', '古文', '散文',
              '文章', '拼音', '成语', '句子', '段落', '汉字'],
    '数学':  ['方程', '函数', '几何', '三角', '代数', '证明', '计算', '面积',
              '体积', '概率', '集合', '数列', '不等式', '向量', '矩阵', '积分'],
    '英语':  ['grammar', 'tense', 'vocabulary', 'reading', 'writing',
              '时态', '词汇', '语法', '单词', '翻译', '完形', '语境'],
    '物理':  ['速度', '质量', '电流', '电压', '电阔', '功率', '能量',
              '运动', '牛顿', '力学', '电学', '光学', '波动', '热学'],
    '化学':  ['化学式', '元素', '原子', '分子', '反应', '氧化', '酸碱',
              '化合物', '溶液', '嫁化剂', '化学键', '化学方程'],
    '生物':  ['细胞', '遗传', '基因', '光合', '呼吸', '生态', '蛋白质',
              'DNA', '染色体', '进化', '酶', '神经', '激素'],
    '历史':  ['朝代', '战争', '革命', '改革', '皇帝', '历史', '事件',
              '古代', '近代', '现代', '条约', '运动', '政策'],
    '地理':  ['地形', '气候', '经度', '纬度', '大陆', '河流', '山脉',
              '省份', '人口', '地图', '海洋', '大气', '地壳'],
    '道德与法治': ['法律', '公民', '权利', '义务', '道德', '国家',
                   '规则', '社会', '责任', '宪法', '法规'],
}

# 难度关键词（命中越多越难）
HARD_KEYWORDS = ['证明', '推导', '分析', '综合', '计算过程', '综合题', '探究']
EASY_KEYWORDS = ['填空', '判断', '选择', '单选', '写出']


def _get_ocr_engine():
    """检查 pytesseract + Tesseract 是否可用，返回状态"""
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        version = pytesseract.get_tesseract_version()
        return pytesseract, str(version)
    except Exception:
        return None, None


def check_ocr_available() -> tuple[bool, str]:
    """返回 (可用, 提示信息)"""
    engine, version = _get_ocr_engine()
    if engine:
        return True, f'Tesseract {version} 已就绪'
    return False, (
        'OCR 未就绪。请安装 Tesseract：\n'
        '  1. 下载：https://github.com/UB-Mannheim/tesseract/wiki\n'
        '  2. 安装时勾选 chi_sim（简体中文）语言包\n'
        '  3. 重启应用后重试'
    )


def extract_text(image_path: str) -> str:
    """
    OCR 提取图片中的文字
    返回识别到的原始文字，失败时返回空字符串
    """
    engine, _ = _get_ocr_engine()
    if not engine:
        return ''

    try:
        from PIL import Image
        img = Image.open(image_path)
        # 使用简体中文+英文混合识别
        text = engine.image_to_string(img, lang='chi_sim+eng')
        return text.strip()
    except Exception as e:
        return f'[OCR 失败: {e}]'


# ── 规则引擎：科目推断 ──────────────────────────────────────────────────────────
def detect_subject_name(text: str) -> Optional[str]:
    """
    根据文字内容推断最可能的科目名称
    返回科目名（字符串），无法判断时返回 None
    """
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for subject, keywords in SUBJECT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            scores[subject] = score
    if not scores:
        return None
    return max(scores, key=lambda s: scores[s])


def detect_difficulty(text: str) -> int:
    """
    根据文字内容推断难度（1=简单, 2=中等, 3=困难）
    启发式规则：
      - 命中困难关键词 >= 1  →  困难
      - 命中简单关键词 >= 1  →  简单
      - 否则按文字长度估算
    """
    hard_hits = sum(1 for kw in HARD_KEYWORDS if kw in text)
    easy_hits  = sum(1 for kw in EASY_KEYWORDS if kw in text)

    if hard_hits >= 1:
        return 3
    if easy_hits >= 1:
        return 1

    length = len(text)
    if length < 80:
        return 1
    if length < 250:
        return 2
    return 3


def split_question_answer(text: str) -> tuple[str, str]:
    """
    尝试将 OCR 原文拆分为题目内容 + 解析/答案
    匹配常见分隔标记：解析、答案、参考答案、解题过程等
    """
    pattern = r'(?:解析|答案|参考答案|解题过程|解题思路|分析)[：:：\s]'
    match = re.search(pattern, text)
    if match:
        question = text[:match.start()].strip()
        answer   = text[match.end():].strip()
        return question, answer
    return text.strip(), ''


def parse_image(image_path: str) -> dict:
    """
    对一张图片完整执行 OCR + 规则引擎分析
    返回结构化结果字典
    """
    raw_text = extract_text(image_path)
    question_text, answer_text = split_question_answer(raw_text)
    subject_name = detect_subject_name(raw_text)
    difficulty   = detect_difficulty(raw_text)

    return {
        'raw_text':         raw_text,
        'question_content': question_text,
        'answer_content':   answer_text,
        'detected_subject': subject_name,
        'difficulty':       difficulty,
        'ocr_available':    bool(raw_text and not raw_text.startswith('[OCR')),
    }
