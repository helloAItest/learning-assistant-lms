import os
import secrets


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'lms.db')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    THUMBNAIL_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'thumbs')
    THUMBNAIL_MAX_WIDTH = 800
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
