# -*- coding: utf-8 -*-
"""权限装饰器:登录校验、角色校验。项目/任务归属校验在 routes/projects.py 的 load_project 中实现。"""
from functools import wraps
from flask import jsonify, request

from auth import current_user


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u:
            return jsonify(error='未登录或会话已过期'), 401
        request.current_user = u
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            u = current_user()
            if not u:
                return jsonify(error='未登录或会话已过期'), 401
            if u.get('role') not in roles:
                return jsonify(error='权限不足'), 403
            request.current_user = u
            return f(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(f):
    """部长权限。"""
    return role_required('部长')(f)
