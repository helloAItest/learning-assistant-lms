"""
init_db.py  ——  数据库初始化脚本
运行方式：python init_db.py
"""
import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'lms.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    role         TEXT NOT NULL CHECK(role IN ('student', 'parent')),
    display_name TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS subjects (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT NOT NULL UNIQUE,
    icon   TEXT NOT NULL DEFAULT '📚',
    color  TEXT NOT NULL DEFAULT '#667eea'
);

CREATE TABLE IF NOT EXISTS knowledge_points (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    chapter    TEXT NOT NULL DEFAULT '未分类',
    name       TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS wrong_questions (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id         INTEGER NOT NULL REFERENCES users(id),
    subject_id         INTEGER NOT NULL REFERENCES subjects(id),
    knowledge_point_id INTEGER REFERENCES knowledge_points(id),
    question_content   TEXT NOT NULL,
    image_path         TEXT,
    thumb_path         TEXT,
    answer_content     TEXT,
    difficulty         INTEGER NOT NULL DEFAULT 2 CHECK(difficulty IN (1,2,3)),
    error_count        INTEGER NOT NULL DEFAULT 1,
    last_error_date    TEXT NOT NULL DEFAULT (date('now', 'localtime')),
    is_mastered        INTEGER NOT NULL DEFAULT 0,
    created_at         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at         TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS review_plans (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id         INTEGER NOT NULL REFERENCES users(id),
    knowledge_point_id INTEGER NOT NULL REFERENCES knowledge_points(id),
    review_stage       INTEGER NOT NULL DEFAULT 1 CHECK(review_stage BETWEEN 1 AND 6),
    next_review_date   TEXT NOT NULL,
    created_at         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(student_id, knowledge_point_id)
);

CREATE TABLE IF NOT EXISTS review_records (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id         INTEGER NOT NULL REFERENCES users(id),
    knowledge_point_id INTEGER NOT NULL REFERENCES knowledge_points(id),
    review_date        TEXT NOT NULL,
    result             TEXT NOT NULL CHECK(result IN ('pass', 'fail')),
    stage_before       INTEGER NOT NULL,
    stage_after        INTEGER NOT NULL,
    created_at         TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS mastery_scores (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id         INTEGER NOT NULL REFERENCES users(id),
    knowledge_point_id INTEGER NOT NULL REFERENCES knowledge_points(id),
    score              REAL NOT NULL DEFAULT 0.0 CHECK(score BETWEEN 0.0 AND 1.0),
    last_updated       TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(student_id, knowledge_point_id)
);
"""

INITIAL_USERS = [(1, 'student', '同学'), (2, 'parent', '家长')]

INITIAL_SUBJECTS = [
    ('语文', '📖', '#FF6B6B'), ('数学', '📐', '#4ECDC4'),
    ('英语', '🔤', '#45B7D1'), ('物理', '⚡', '#96CEB4'),
    ('化学', '🧪', '#F9CA24'), ('生物', '🌱', '#6C5CE7'),
    ('历史', '📜', '#A29BFE'), ('地理', '🌍', '#00B894'),
    ('道德与法治', '⚖️', '#FD79A8'),
]

def init_db():
    print(f"📂 数据库路径：{DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA journal_mode = WAL')
    conn.executescript(SCHEMA)
    conn.executemany("INSERT OR IGNORE INTO users(id, role, display_name) VALUES (?, ?, ?)", INITIAL_USERS)
    conn.executemany("INSERT OR IGNORE INTO subjects(name, icon, color) VALUES (?, ?, ?)", INITIAL_SUBJECTS)
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成！")

if __name__ == '__main__':
    init_db()
