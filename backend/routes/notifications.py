# -*- coding: utf-8 -*-
"""通知路由:站内消息列表/未读数/已读/删除,以及部长/副部长批量催办。

权限:
- 列表类端点: login_required(用户只看自己的通知)
- POST /remind: role_required('部长','副部长') —— 副部长仅对自己负责的项目生效
"""
from datetime import datetime
from flask import Blueprint, request, jsonify

from guards import login_required, role_required
from storage import read_json, write_json
from config import NOTIFY_FILE, PROJECTS_INDEX, PROJECTS_DIR
from notify import manual_remind

bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


def _load_all():
    return read_json(NOTIFY_FILE, default=[]) or []


def _save_all(items):
    return write_json(NOTIFY_FILE, items)


# ---------- 列表 ----------
@bp.get('')
@login_required
def list_notifications():
    """当前用户的通知列表。

    Query:
      ?unread=1          仅未读
      ?limit=N           限制条数(默认 50,最大 200)
      ?offset=M          分页偏移(默认 0)
    返回 {notifications:[...], total:N}(total 为筛选后总数)。
    """
    u = request.current_user
    items = [n for n in _load_all() if n.get('user_id') == u['id']]

    if request.args.get('unread') == '1':
        items = [n for n in items if not n.get('read_at')]

    items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    total = len(items)

    try:
        limit = int(request.args.get('limit', 50))
    except (ValueError, TypeError):
        limit = 50
    limit = max(1, min(limit, 200))
    try:
        offset = int(request.args.get('offset', 0))
    except (ValueError, TypeError):
        offset = 0
    offset = max(0, offset)
    paged = items[offset: offset + limit]

    return jsonify(notifications=paged, total=total, limit=limit, offset=offset)


@bp.get('/unread-count')
@login_required
def unread_count():
    """轻量端点,60s 轮询用。"""
    u = request.current_user
    n = sum(1 for x in _load_all()
            if x.get('user_id') == u['id'] and not x.get('read_at'))
    return jsonify(count=n)


# ---------- 标记已读 ----------
@bp.post('/<nid>/read')
@login_required
def mark_read(nid):
    u = request.current_user
    items = _load_all()
    found = False
    for n in items:
        if n.get('id') == nid:
            if n.get('user_id') != u['id']:
                return jsonify(error='无权操作此通知'), 403
            if not n.get('read_at'):
                n['read_at'] = datetime.now().isoformat()
            found = True
            break
    if not found:
        return jsonify(error='通知不存在'), 404
    _save_all(items)
    return jsonify(ok=True)


@bp.post('/read-all')
@login_required
def mark_all_read():
    u = request.current_user
    items = _load_all()
    now_iso = datetime.now().isoformat()
    updated = 0
    for n in items:
        if n.get('user_id') == u['id'] and not n.get('read_at'):
            n['read_at'] = now_iso
            updated += 1
    if updated:
        _save_all(items)
    return jsonify(ok=True, updated=updated)


# ---------- 删除 ----------
@bp.delete('/<nid>')
@login_required
def delete_notification(nid):
    u = request.current_user
    items = _load_all()
    new_items = []
    found = False
    for n in items:
        if n.get('id') == nid:
            if n.get('user_id') != u['id']:
                return jsonify(error='无权操作此通知'), 403
            found = True
            continue
        new_items.append(n)
    if not found:
        return jsonify(error='通知不存在'), 404
    _save_all(new_items)
    return jsonify(ok=True)


# ---------- 批量催办 ----------
@bp.post('/remind')
@role_required('部长', '副部长')
def remind():
    """部长/副部长对某类预警批量发送手动催办(1h 去重窗口)。

    Body:
      { "category": "overdue|due_soon|pending_review",
        "project_id": "可选,限定单项目",
        "task_ids": ["可选,任务子集"] }

    副部长:仅对 owner_ids 含自己的项目生效;若 project_id 指向不可见项目 → 403。
    """
    u = request.current_user
    data = request.get_json(silent=True) or {}
    category = data.get('category')
    project_id = data.get('project_id') or None
    task_ids = data.get('task_ids') or None

    if category not in ('overdue', 'due_soon', 'pending_review'):
        return jsonify(error='category 必须为 overdue / due_soon / pending_review'), 400

    # 计算可见项目 dir 列表
    idx = read_json(PROJECTS_INDEX, default=[]) or []
    visible_dirs = None  # None=全部可见(部长)
    if u.get('role') == '副部长':
        visible_dirs = set()
        for entry in idx:
            dir_ = entry.get('dir', '')
            if not dir_:
                continue
            meta = read_json('{}/{}/meta.json'.format(PROJECTS_DIR, dir_), default=None)
            if not meta:
                continue
            if u['id'] in (meta.get('owner_ids') or []):
                visible_dirs.add(dir_)
        # 若指定 project_id 但不在可见范围 → 403
        if project_id:
            pid_dir = next((e.get('dir', '') for e in idx if e.get('id') == project_id), '')
            if pid_dir not in visible_dirs:
                return jsonify(error='无权对该项目催办'), 403

    stats = manual_remind(
        actor_user_id=u['id'],
        category=category,
        project_id=project_id,
        task_ids=task_ids,
        visible_project_dirs=visible_dirs,
    )
    return jsonify(
        sent=stats.get('sent', 0),
        deduped=stats.get('deduped', 0),
        skipped=stats.get('skipped', {}),
    )