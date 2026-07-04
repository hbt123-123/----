# -*- coding: utf-8 -*-
"""Flask 应用入口:注册蓝图、SPA 静态托管、健康检查。

运行(cwd=backend):
    开发:  python app.py
    生产:  gunicorn -w 1 --threads 4 -b 127.0.0.1:5000 app:app
"""
import os
from flask import Flask, send_from_directory, jsonify, request

from config import (
    DATA_DIR, STATIC_DIR, SECRET_KEY, MAX_CONTENT_LENGTH, PERMANENT_SESSION_LIFETIME,
)
from storage import ensure_dir
from auth import ensure_admin
from routes.auth import bp as auth_bp
from routes.users import bp as users_bp
from routes.templates import bp as templates_bp


def create_app():
    ensure_dir('')
    static_folder = STATIC_DIR if os.path.isdir(STATIC_DIR) else None

    app = Flask(__name__, static_folder=static_folder, static_url_path='')
    app.config.update(
        SECRET_KEY=SECRET_KEY,
        MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH,
        PERMANENT_SESSION_LIFETIME=PERMANENT_SESSION_LIFETIME,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(templates_bp)

    @app.get('/api/health')
    def health():
        return jsonify(ok=True, data_dir=DATA_DIR, has_static=static_folder is not None)

    @app.errorhandler(400)
    def bad_request(e):
        msg = e.description if hasattr(e, 'description') else '请求参数错误'
        return jsonify(error=str(msg)), 400

    # SPA:history 模式 fallback,非 /api 路径回退到 index.html
    if static_folder:
        @app.route('/')
        def index():
            return send_from_directory(static_folder, 'index.html')

        @app.errorhandler(404)
        def fallback(e):
            if request.path.startswith('/api'):
                return jsonify(error='接口不存在'), 404
            rel = request.path.lstrip('/')
            if rel and os.path.isfile(os.path.join(static_folder, rel)):
                return send_from_directory(static_folder, rel)
            return send_from_directory(static_folder, 'index.html')

    ensure_admin()
    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
