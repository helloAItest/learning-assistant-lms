import sqlite3
from flask import g, current_app


def get_db():
    """获取当前请求的数据库连接（每次请求共享同一连接）"""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE_PATH'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        # 启用 WAL 模式提升并发读性能
        g.db.execute('PRAGMA journal_mode=WAL')
        # 启用外键约束
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db


def close_db(e=None):
    """请求结束时关闭数据库连接"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_app(app):
    """将数据库生命周期绑定到 Flask app"""
    app.teardown_appcontext(close_db)
