"""
OCR 识别服务 + 规则引擎
依赖：pytesseract + Tesseract OCR
安装：https://github.com/UB-Mannheim/tesseract/wiki
"""
import os, re
from typing import Optional

TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SUBJECT_KEYWORDS = {
    '语文': ['诗','词','文言','阅读','写作','修辞','字词','古文','散文','文章','拼音','成语','句子','段落','汉字'],
    '数学': ['方程','函数','几何','三角','代数','证明','计算','面积','体积','概率','集合','数列','不等式','向量','矩阵','积分'],
    '英语': ['grammar','tense','vocabulary','reading','writing','时态','词汇','语法','单词','翻译','完形','语境'],
    '物理': ['速度','质量','电流','电压','电阻','功率','能量','运动','牛顿','力学','电学','光学','波动','热学'],
    '化学': ['化学式','元素','原子','分子','反应','氧化','酸碱','化合物','溶液','催化剂','化学键','化学方程'],
    '生物': ['细胞','遗传','基因','光合','呼吸','生态','蛋白质','DNA','染色体','进化','酶','神经','激素'],
    '历史': ['朝代','战争','革命','改革','皇帝','历史','事件','古代','近代','现代','条约','运动','政策'],
    '地理': ['地形','气候','经度','纬度','大陆','河流','山脉','省份','人口','地图','海洋','大气','地壳'],
    '道德与法治': ['法律','公民','权利','义务','道德','国家','规则','社会','责任','宪法','法规'],
}

HARD_KEYWORDS = ['证明','推导','分析','综合','计算过程','综合题','探究']
EASY_KEYWORDS = ['填空','判断','选择','单选','写出']

def _get_ocr_engine():
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        return pytesseract, str(pytesseract.get_tesseract_version())
    except Exception:
        return None, None

def check_ocr_available():
    engine, v = _get_ocr_engine()
    if engine: return True, f'Tesseract {v} 已就绪'
    return False, 'OCR 未就绪。请安装 Tesseract + chi_sim 语言包'

def extract_text(image_path):
    engine, _ = _get_ocr_engine()
    if not engine: return ''
    try:
        from PIL import Image
        return engine.image_to_string(Image.open(image_path), lang='chi_sim+eng').strip()
    except Exception as e:
        return f'[OCR 失败: {e}]'

def detect_subject_name(text):
    tl = text.lower()
    scores = {s: sum(1 for kw in kws if kw.lower() in tl) for s, kws in SUBJECT_KEYWORDS.items()}
    scores = {s:v for s,v in scores.items() if v>0}
    return max(scores, key=scores.get) if scores else None

def detect_difficulty(text):
    if sum(1 for kw in HARD_KEYWORDS if kw in text): return 3
    if sum(1 for kw in EASY_KEYWORDS if kw in text): return 1
    return 1 if len(text)<80 else (2 if len(text)<250 else 3)

def split_question_answer(text):
    m = re.search(r'(?:解析|答案|参考答案|解题过程|解题思路|分析)[：:\s]', text)
    return (text[:m.start()].strip(), text[m.end():].strip()) if m else (text.strip(), '')

def parse_image(image_path):
    raw = extract_text(image_path)
    q, a = split_question_answer(raw)
    return {
        'raw_text': raw, 'question_content': q, 'answer_content': a,
        'detected_subject': detect_subject_name(raw), 'difficulty': detect_difficulty(raw),
        'ocr_available': bool(raw and not raw.startswith('[OCR')),
    }
