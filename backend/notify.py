# -*- coding: utf-8 -*-
"""通知提醒核心模块:消息推送、去重、系统级自动扫描与手动催办。

两类调用方:
- backend/cli.py            auto 扫描,24h 去重窗口
- backend/routes/notifications.py  manual 催办,1h 去重窗口

不依赖 Flask app/request 上下文,可独立运行(Blueprint 实例化不需要 app)。
"""
import uuid
from datetime import datetime, timedelta

from storage import read_json, write_json
from config import NOTIFY_FILE, PROJECTS_INDEX, PROJECTS_DIR
from auth import load_users, find_user
from routes.dashboard import _classify_task


# ---------- 常量 ----------
SOON_THRESHOLD = timedelta(days=3)
AUTO_DEDUPE_MINUTES = 24 * 60      # auto-remind 24h 去重
MANUAL_DEDUPE_MINUTES = 60         # manual 催办 1h 去重

VALID_TYPES = ('overdue', 'due_soon', 'pending_review', 'system')


# ---------- 基础读写 ----------
def _load_notifications():
    return read_json(NOTIFY_FILE, default=[]) or []


def _save_notifications(items):
    return write_json(NOTIFY_FILE, items)


def _parse_iso(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


# ---------- 推送 ----------
def push_notification(user_id, type_, title, content, link='',
                      project_id='', task_id='',
                      from_user='system', from_kind='auto', now=None):
    """追加一条通知,返回新通知 dict;不查重(查重由调用方决定)。"""
    if not user_id or type_ not in VALID_TYPES:
        return None
    now = now or datetime.now()
    item = {
        'id': 'n_' + uuid.uuid4().hex[:8],
        'user_id': user_id,
        'type': type_,
        'title': title,
        'content': content,
        'link': link or '',
        'project_id': project_id or '',
        'task_id': task_id or '',
        'created_at': now.isoformat(),
        'read_at': '',
        'from_user': from_user or 'system',
        'from_kind': from_kind or 'auto',
    }
    items = _load_notifications()
    items.append(item)
    _save_notifications(items)
    return item


# ---------- 去重 ----------
def should_dedupe(user_id, task_id, type_, window_minutes, now=None):
    """同一 (user_id, task_id, type_) 在 window_minutes 内是否已存在。

    task_id 为空时(系统公告)直接返回 False。
    """
    if not task_id:
        return False
    now = now or datetime.now()
    threshold = now - timedelta(minutes=window_minutes)
    for it in _load_notifications():
        if (it.get('user_id') == user_id
                and it.get('task_id') == task_id
                and it.get('type') == type_):
            created = _parse_iso(it.get('created_at', ''))
            if created and created >= threshold:
                return True
    return False


# ---------- 文案 ----------
def _build_content(type_, project_name, stage_name, team_name, material,
                   due_date, from_user_name='', is_manual=False):
    """根据 type 与触发方式构造 (title, content)。"""
    parts = [p for p in [project_name, stage_name, team_name, material] if p]
    subject = '「' + '/'.join(parts) + '」'
    if is_manual:
        who = (from_user_name or '系统') + ' '
        if type_ == 'overdue':
            return ('[催办] 任务逾期',
                    f'{who}催办你:{subject}已逾期(截止 {due_date}),请尽快提交。')
        if type_ == 'due_soon':
            return ('[催办] 任务临期',
                    f'{who}催办你:{subject}将于 {due_date} 到期,请及时提交。')
        if type_ == 'pending_review':
            return ('[催办] 待审核任务',
                    f'{who}提醒你:{subject}已提交待审核,请尽快处理。')
    else:
        if type_ == 'overdue':
            return ('任务逾期提醒',
                    f'{subject}已逾期(截止 {due_date}),请尽快提交。')
        if type_ == 'due_soon':
            return ('任务临期提醒',
                    f'{subject}将于 {due_date} 到期,请及时提交。')
        if type_ == 'pending_review':
            return ('待审核任务提醒',
                    f'{subject}已提交待审核,请尽快处理。')
    return ('系统通知', subject)


# ---------- 收件人解析 ----------
def _resolve_recipients(type_, task_assignee_id, meta, users):
    """根据 type 决定收件人 user_id 列表(去重,剔除不存在用户)。

    - overdue/due_soon -> [assignee_id]  (空或不存在则空列表)
    - pending_review   -> set(meta.owner_ids) ∪ {u.id | u.role=='部长'}
    """
    valid_ids = {u.get('id') for u in users}
    if type_ in ('overdue', 'due_soon'):
        if task_assignee_id and task_assignee_id in valid_ids:
            return [task_assignee_id]
        return []
    if type_ == 'pending_review':
        recipients = set(meta.get('owner_ids') or [])
        recipients |= {u.get('id') for u in users if u.get('role') == '部长'}
        return [r for r in recipients if r in valid_ids]
    return []


# ---------- 系统级扫描(auto) ----------
def scan_and_remind(now=None, only_type=None, dry_run=False):
    """遍历所有进行中项目,向收件人推送 auto 提醒。

    返回 {scanned_projects, scanned_tasks, sent, deduped, skipped:{...}}。
    """
    now = now or datetime.now()
    users = load_users()
    idx = read_json(PROJECTS_INDEX, default=[]) or []

    stats = {
        'scanned_projects': 0,
        'scanned_tasks': 0,
        'sent': 0,
        'deduped': 0,
        'skipped': {
            'no_assignee': 0,
            'no_owner': 0,
            'user_missing': 0,
            'project_closed': 0,
        },
    }

    for entry in idx:
        dir_ = entry.get('dir', '')
        if not dir_:
            continue
        meta = read_json('{}/{}/meta.json'.format(PROJECTS_DIR, dir_), default=None)
        if not meta:
            continue
        if meta.get('status') != '进行中':
            stats['skipped']['project_closed'] += 1
            continue
        stats['scanned_projects'] += 1

        tasks = read_json('{}/{}/tasks.json'.format(PROJECTS_DIR, dir_), default=[]) or []
        for t in tasks:
            stats['scanned_tasks'] += 1
            status = t.get('status', '')
            assignee = t.get('assignee_id', '')
            due = t.get('due_date', '')
            is_overdue, is_due_soon = _classify_task(t, now, SOON_THRESHOLD)
            is_pending_review = (status == '已提交')
            # 给 assignee 的提醒(overdue/due_soon)只在 assignee 还需行动时触发:
            # 已提交待审 → assignee 已完成本分,不再催;已通过 → 已结束。
            assignee_needs_action = status in ('未交', '已打回')

            types_to_send = []
            if not only_type or only_type == 'overdue':
                if is_overdue and assignee_needs_action:
                    types_to_send.append('overdue')
            if not only_type or only_type == 'due_soon':
                if is_due_soon and assignee_needs_action:
                    types_to_send.append('due_soon')
            if not only_type or only_type == 'pending_review':
                if is_pending_review:
                    types_to_send.append('pending_review')

            for type_ in types_to_send:
                _send_one(type_, t, meta, users, now, stats,
                          actor_id='system', is_manual=False, dry_run=dry_run)
    return stats


# ---------- 手动催办(manual) ----------
def manual_remind(actor_user_id, category, project_id=None, task_ids=None,
                  visible_project_dirs=None):
    """部长/副部长手动批量催办。

    参数:
      actor_user_id: 催办人 user_id(用于 from_user 与文案署名)
      category: 'overdue' | 'due_soon' | 'pending_review'
      project_id: 可选,限定单项目
      task_ids: 可选,限定任务子集
      visible_project_dirs: 可见项目 dir 列表(副部长归属过滤后),None=全部可见(部长)

    返回 {sent, deduped, skipped:{...}}
    """
    if category not in ('overdue', 'due_soon', 'pending_review'):
        return {'sent': 0, 'deduped': 0, 'skipped': {}, 'error': 'category 非法'}

    now = datetime.now()
    users = load_users()
    actor = find_user(actor_user_id)
    actor_name = (actor or {}).get('name', '') or '系统'

    idx = read_json(PROJECTS_INDEX, default=[]) or []
    task_id_set = set(task_ids) if task_ids else None

    stats = {
        'sent': 0, 'deduped': 0,
        'skipped': {'no_assignee': 0, 'no_owner': 0, 'user_missing': 0, 'forbidden': 0},
    }

    for entry in idx:
        dir_ = entry.get('dir', '')
        if not dir_:
            continue
        if visible_project_dirs is not None and dir_ not in visible_project_dirs:
            stats['skipped']['forbidden'] += 1
            continue
        meta = read_json('{}/{}/meta.json'.format(PROJECTS_DIR, dir_), default=None)
        if not meta:
            continue
        if project_id and meta.get('id') != project_id:
            continue
        if meta.get('status') != '进行中':
            continue

        tasks = read_json('{}/{}/tasks.json'.format(PROJECTS_DIR, dir_), default=[]) or []
        for t in tasks:
            if task_id_set and t.get('task_id') not in task_id_set:
                continue
            status = t.get('status', '')
            assignee = t.get('assignee_id', '')
            due = t.get('due_date', '')
            is_overdue, is_due_soon = _classify_task(t, now, SOON_THRESHOLD)
            is_pending_review = (status == '已提交')
            assignee_needs_action = status in ('未交', '已打回')

            if category == 'overdue' and not (is_overdue and assignee_needs_action):
                continue
            if category == 'due_soon' and not (is_due_soon and assignee_needs_action):
                continue
            if category == 'pending_review' and not is_pending_review:
                continue

            _send_one(category, t, meta, users, now, stats,
                      actor_id=actor_user_id, actor_name=actor_name,
                      is_manual=True, dry_run=False,
                      dedupe_minutes=MANUAL_DEDUPE_MINUTES)
    return stats


# ---------- 内部:发一条任务提醒 ----------
def _send_one(type_, task, meta, users, now, stats,
              actor_id='system', actor_name='', is_manual=False,
              dry_run=False, dedupe_minutes=None):
    """对单个任务+单个类型,解析收件人并发送(含去重)。"""
    if dedupe_minutes is None:
        dedupe_minutes = AUTO_DEDUPE_MINUTES
    assignee = task.get('assignee_id', '')
    due = task.get('due_date', '')
    recipients = _resolve_recipients(type_, assignee, meta, users)

    if not recipients:
        if type_ in ('overdue', 'due_soon'):
            if not assignee:
                stats['skipped']['no_assignee'] = stats['skipped'].get('no_assignee', 0) + 1
            else:
                stats['skipped']['user_missing'] = stats['skipped'].get('user_missing', 0) + 1
        else:
            stats['skipped']['no_owner'] = stats['skipped'].get('no_owner', 0) + 1
        return

    title, content = _build_content(
        type_,
        meta.get('name', ''),
        task.get('stage_name', ''),
        task.get('team_name', ''),
        task.get('material', ''),
        due,
        from_user_name=actor_name,
        is_manual=is_manual,
    )
    for uid in recipients:
        if should_dedupe(uid, task.get('task_id', ''), type_, dedupe_minutes, now):
            stats['deduped'] += 1
            continue
        if dry_run:
            stats['sent'] += 1
            continue
        pushed = push_notification(
            uid, type_, title, content,
            link='/projects/' + meta.get('id', ''),
            project_id=meta.get('id', ''),
            task_id=task.get('task_id', ''),
            from_user=actor_id, from_kind='manual' if is_manual else 'auto', now=now,
        )
        if pushed:
            stats['sent'] += 1
