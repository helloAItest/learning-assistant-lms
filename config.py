import os
import secrets


class Config:
    # Flask Session 加密密钥，生产环境建议通过环境变量设置
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    # SQLite 数据库路径
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'lms.db')

    # 图片上传目录
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')

    # 缩略图存储目录
    THUMBNAIL_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'thumbs')

    # 缩略图最大宽度（px）
    THUMBNAIL_MAX_WIDTH = 800

    # 最大上传文件大小：5MB
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
