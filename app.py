"""
app.py  ——  Flask 应用入口
开发模式：flask run --debug --port 5000
生产模式：waitress-serve --host=127.0.0.1 --port=5000 app:app
"""
import os
from flask import Flask
from config import Config
import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config['UPLOAD_FOLDER'],    exist_ok=True)
    os.makedirs(app.config['THUMBNAIL_FOLDER'], exist_ok=True)

    db.init_app(app)

    from routes.main import main_bp
    from routes.role import role_bp
    from routes.wrong_questions import wq_bp
    from routes.api import api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(role_bp)
    app.register_blueprint(wq_bp)
    app.register_blueprint(api_bp)

    from flask import render_template

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
