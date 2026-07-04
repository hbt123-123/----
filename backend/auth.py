# -*- coding: utf-8 -*-
"""认证核心:用户加载、密码哈希、session、激活、admin 保障。"""
import uuid
from datetime import datetime

from flask import session
from werkzeug.security import generate_password_hash, check_password_hash

from storage import read_json, write_json
from config import USERS_FILE, ADMIN_USERNAME, ADMIN_INIT_PASSWORD


# ---------- 用户读写 ----------
def load_users():
    return read_json(USERS_FILE, default=[])


def save_users(users):
    return write_json(USERS_FILE, users)


def find_user(uid):
    for u in load_users():
        if u.get('id') == uid:
            return u
    return None


def find_user_in(users, uid):
    return next((u for u in users if u.get('id') == uid), None)


# ---------- 公共视图(脱敏) ----------
def to_public(u):
    if not u:
        return None
    return {
        'id': u.get('id'),
        'name': u.get('name', ''),
        'role': u.get('role', ''),
        'student_id': u.get('student_id', ''),
        'contact': u.get('contact', ''),
        'activated': u.get('activated', False),
        'is_admin': u.get('is_admin', False),
        'created_at': u.get('created_at', ''),
    }


def public_candidates():
    """登录页下拉候选:所有成员,不含密码字段。"""
    return [to_public(u) for u in load_users()]


# ---------- 密码 ----------
def set_password(u, pwd):
    u['password_hash'] = generate_password_hash(pwd)
    u['activated'] = True
    u['password_set_at'] = datetime.now().isoformat()


def check_pwd(u, pwd):
    h = u.get('password_hash')
    if not h:
        return False
    return check_password_hash(h, pwd)


# ---------- session ----------
def login_session(u):
    session['uid'] = u.get('id')
    session.permanent = True


def logout_session():
    session.clear()


def current_user():
    uid = session.get('uid')
    if not uid:
        return None
    return find_user(uid)


# ---------- ID 与 admin 保障 ----------
def new_user_id():
    return uuid.uuid4().hex[:12]


def ensure_admin():
    """启动时确保固定 admin 账号存在(若缺则创建,不覆盖已有密码)。"""
    users = load_users()
    admin = next((u for u in users if u.get('is_admin')), None)
    if admin:
        return admin
    admin = {
        'id': ADMIN_USERNAME,
        'name': '管理员',
        'role': '部长',
        'student_id': '',
        'contact': '',
        'is_admin': True,
        'activated': True,
        'password_hash': generate_password_hash(ADMIN_INIT_PASSWORD),
        'created_at': datetime.now().isoformat(),
    }
    users.append(admin)
    save_users(users)
    return admin
