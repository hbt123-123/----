# -*- coding: utf-8 -*-
"""全局配置。本地开发用项目内 data/ 目录,生产用环境变量覆盖。"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# 数据目录:本地开发默认 <项目根>/data;生产用 ZHANSAI_DATA_DIR 指向 /var/www/zhansai/data
DATA_DIR = os.environ.get('ZHANSAI_DATA_DIR', os.path.join(PROJECT_ROOT, 'data'))

# 前端构建产物目录:Vite 构建后拷贝/输出到此
STATIC_DIR = os.environ.get('ZHANSAI_STATIC_DIR', os.path.join(BASE_DIR, 'static'))

SECRET_KEY = os.environ.get('ZHANSAI_SECRET_KEY', 'dev-secret-please-change-in-prod')

MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7  # 7 天

# 文件系统非法字符(用于目录名/文件名清洗)
ILLEGAL_FILENAME_CHARS = '/\\:*?"<>|'

# 固定管理员账号
ADMIN_USERNAME = 'admin'
ADMIN_INIT_PASSWORD = '12345678'

# 允许上传的材料扩展名
ALLOWED_UPLOAD_EXT = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.rar', '.7z', '.jpg', '.jpeg', '.png', '.txt', '.csv',
}

# 存储相对路径
USERS_FILE = 'users.json'
PROJECTS_INDEX = 'projects.json'
TEMPLATES_DIR = 'templates'
PROJECTS_DIR = 'projects'
NOTIFY_FILE = 'notifications.json'
