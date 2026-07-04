# -*- coding: utf-8 -*-
"""认证路由:登录(含首次激活)、登出、当前用户、改密。"""
from flask import Blueprint, request, jsonify

from auth import (
    load_users, save_users, find_user_in, public_candidates, to_public,
    set_password, check_pwd, login_session, logout_session, current_user,
)
from guards import login_required

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.get('/candidates')
def candidates():
    """登录页姓名下拉候选(无需登录):返回全部成员,不含密码字段。"""
    return jsonify(candidates=public_candidates())


@bp.post('/login')
def login():
    data = request.get_json(silent=True) or {}
    uid = (data.get('userId') or '').strip()
    pwd = data.get('password') or ''
    if not uid:
        return jsonify(error='请选择用户'), 400

    users = load_users()
    user = find_user_in(users, uid)
    if not user:
        return jsonify(error='用户不存在'), 404

    # 未激活:首次登录,设置初始密码完成激活
    if not user.get('activated'):
        if len(pwd) < 6:
            return jsonify(error='首次登录,请设置不少于 6 位的密码'), 400
        set_password(user, pwd)
        save_users(users)
        login_session(user)
        return jsonify(user=to_public(user), activated_now=True)

    if not check_pwd(user, pwd):
        return jsonify(error='密码错误'), 401
    login_session(user)
    return jsonify(user=to_public(user))


@bp.post('/logout')
def logout():
    logout_session()
    return jsonify(ok=True)


@bp.get('/me')
@login_required
def me():
    return jsonify(user=to_public(current_user()))


@bp.post('/change-password')
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    old = data.get('oldPassword') or ''
    new = data.get('newPassword') or ''
    if len(new) < 6:
        return jsonify(error='新密码不少于 6 位'), 400
    users = load_users()
    u = find_user_in(users, current_user()['id'])
    if not u:
        return jsonify(error='用户不存在'), 404
    if not check_pwd(u, old):
        return jsonify(error='原密码错误'), 401
    set_password(u, new)
    save_users(users)
    return jsonify(ok=True)
