# -*- coding: utf-8 -*-
"""部长驾驶舱路由:工作台聚合统计。

一次性返回驾驶舱所需数据,按角色裁剪:
- 部长:全部项目的进度、人员负荷、逾期/临期/待审核预警
- 副部长:仅自己负责项目的同类数据
- 干事:仅个人任务统计与待办列表

逾期/临期判定在后端用 datetime.now() 完成,避免前端时区差异。
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from guards import role_required
from storage import read_json
from config import PROJECTS_INDEX, PROJECTS_DIR
from auth import load_users

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


# ---------- 工具 ----------
def _parse_due(s):
    """解析截止时间字符串 'YYYY-MM-DD HH:mm';失败返回 None。"""
    if not s or not isinstance(s, str):
        return None
    try:
        return datetime.strptime(s.strip(), '%Y-%m-%d %H:%M')
    except (ValueError, TypeError):
        return None


def _classify_task(task, now, soon_threshold):
    """判定任务的逾期/临期标志。

    返回 (is_overdue, is_due_soon):
      - 逾期:due_date < now 且 status != '已通过'
      - 临期:now <= due_date <= now + soon_threshold 且 status not in ('已通过','已打回')
    """
    due = _parse_due(task.get('due_date', ''))
    status = task.get('status', '')
    if due is None:
        return False, False
    if due < now and status != '已通过':
        return True, False
    if now <= due <= now + soon_threshold and status not in ('已通过', '已打回'):
        return False, True
    return False, False


def _empty_task_stats():
    return {
        'total': 0, 'passed': 0, 'submitted': 0,
        'pending': 0, 'rejected': 0,
        'overdue': 0, 'due_soon': 0,
    }


# ---------- 主端点 ----------
@bp.get('')
@role_required('部长', '副部长', '干事')
def get_dashboard():
    """驾驶舱聚合数据。"""
    u = request.current_user
    role = u.get('role', '')
    now = datetime.now()
    soon = timedelta(days=3)

    idx = read_json(PROJECTS_INDEX, default=[]) or []
    users = load_users()
    user_map = {x.get('id'): x for x in users}

    # 按角色筛选可见项目
    visible_projects = []
    for entry in idx:
        meta = read_json('{}/{}/meta.json'.format(PROJECTS_DIR, entry.get('dir', '')), default=None)
        if not meta:
            continue
        if role == '副部长' and u['id'] not in (meta.get('owner_ids') or []):
            continue
        visible_projects.append((meta, entry.get('dir', '')))

    # 干事走简化分支
    if role == '干事':
        return jsonify(_dashboard_for_staff(u, visible_projects, now, soon))

    # 部长 / 副部长:聚合项目级数据
    projects_out = []
    workload_map = {}  # user_id -> {total, pending_review, overdue}
    alerts = {'overdue': [], 'due_soon': [], 'pending_review': []}
    overview = {
        'projects_active': 0,
        'tasks_pending_review': 0,
        'tasks_overdue': 0,
        'tasks_due_soon': 0,
    }

    for meta, dir_ in visible_projects:
        if meta.get('status') == '进行中':
            overview['projects_active'] += 1

        stages = read_json('{}/{}/stages.json'.format(PROJECTS_DIR, dir_), default=[]) or []
        tasks = read_json('{}/{}/tasks.json'.format(PROJECTS_DIR, dir_), default=[]) or []

        # 阶段级进度
        stage_map = {s.get('stage_id'): s for s in stages}
        stage_stats = {s.get('stage_id'): {'done': 0, 'total': 0, 'overdue': 0}
                       for s in stages}
        task_stats = _empty_task_stats()

        for t in tasks:
            status = t.get('status', '')
            task_stats['total'] += 1
            if status == '已通过':
                task_stats['passed'] += 1
            elif status == '已提交':
                task_stats['submitted'] += 1  # 已提交待审
            elif status == '已打回':
                task_stats['rejected'] += 1
            elif status == '未交':
                task_stats['pending'] += 1  # 未交(待办)

            # 阶段聚合
            sid = t.get('stage_id')
            if sid in stage_stats:
                stage_stats[sid]['total'] += 1
                if status == '已通过':
                    stage_stats[sid]['done'] += 1

            # 逾期/临期
            is_overdue, is_due_soon = _classify_task(t, now, soon)
            if is_overdue:
                task_stats['overdue'] += 1
            if is_due_soon:
                task_stats['due_soon'] += 1

            # 阶段逾期计数(基于任务)
            if is_overdue and sid in stage_stats:
                stage_stats[sid]['overdue'] += 1

            # 人员负荷(仅统计 assignee_id 非空且属于本系统用户)
            aid = t.get('assignee_id', '')
            if aid:
                w = workload_map.setdefault(aid, {'total': 0, 'pending_review': 0, 'overdue': 0})
                w['total'] += 1
                if status == '已提交':
                    w['pending_review'] += 1
                if is_overdue:
                    w['overdue'] += 1

            # 预警列表
            alert_item = {
                'project_id': meta.get('id', ''),
                'project_name': meta.get('name', ''),
                'task_id': t.get('task_id', ''),
                'stage_name': t.get('stage_name', ''),
                'team_name': t.get('team_name', ''),
                'material': t.get('material', ''),
                'due_date': t.get('due_date', ''),
                'status': status,
            }
            if is_overdue:
                alerts['overdue'].append(alert_item)
            elif is_due_soon:
                alerts['due_soon'].append(alert_item)
            if status == '已提交':
                alerts['pending_review'].append({
                    **alert_item,
                    'submitted_at': t.get('submitted_at', ''),
                })

        # 概览累计:待审核 = 已提交待审(submitted);逾期/临期基于判定
        overview['tasks_pending_review'] += task_stats['submitted']
        overview['tasks_overdue'] += task_stats['overdue']
        overview['tasks_due_soon'] += task_stats['due_soon']

        # 组装阶段进度
        stage_progress = []
        for s in stages:
            sid = s.get('stage_id')
            st = stage_stats.get(sid, {'done': 0, 'total': 0, 'overdue': 0})
            stage_progress.append({
                'stage_id': sid,
                'name': s.get('name', ''),
                'due_date': s.get('due_date', ''),
                'need_defense': bool(s.get('need_defense')),
                'done': st['done'],
                'total': st['total'],
                'overdue': st['overdue'],
            })

        owner_ids = meta.get('owner_ids') or []
        projects_out.append({
            'id': meta.get('id', ''),
            'name': meta.get('name', ''),
            'year': meta.get('year', ''),
            'level': meta.get('level', ''),
            'status': meta.get('status', ''),
            'template_name': meta.get('template_name', ''),
            'owner_ids': owner_ids,
            'owner_names': [user_map.get(oid, {}).get('name', '') for oid in owner_ids],
            'stage_progress': stage_progress,
            'task_stats': task_stats,
        })

    # 人员负荷列表(只保留出现在 workload_map 中的用户,按总任务数倒序)
    workload = []
    for aid, w in workload_map.items():
        usr = user_map.get(aid)
        if not usr:
            continue
        workload.append({
            'user_id': aid,
            'name': usr.get('name', ''),
            'role': usr.get('role', ''),
            'total': w['total'],
            'pending_review': w['pending_review'],
            'overdue': w['overdue'],
        })
    workload.sort(key=lambda x: x['total'], reverse=True)

    return jsonify(
        role=role,
        overview=overview,
        projects=projects_out,
        workload=workload,
        alerts=alerts,
    )


def _dashboard_for_staff(u, visible_projects, now, soon):
    """干事视图:个人任务统计 + 待办列表。

    干事可见项目集合与副部长逻辑不同——干事对项目的可见性由任务指派决定,
    因此这里遍历所有项目但只取 assignee_id == 自己 的任务。
    为简化,visible_projects 由调用方按副部长规则过滤(干事不在 owner_ids,
    通常会拿到全部项目),这里再按任务归属过滤。
    """
    # 干事没有归属项目过滤,需要看全部项目找自己任务
    idx = read_json(PROJECTS_INDEX, default=[]) or []
    my_tasks = []
    for entry in idx:
        meta = read_json('{}/{}/meta.json'.format(PROJECTS_DIR, entry.get('dir', '')), default=None)
        if not meta:
            continue
        tasks = read_json('{}/{}/tasks.json'.format(PROJECTS_DIR, entry.get('dir', '')), default=[]) or []
        for t in tasks:
            if t.get('assignee_id') != u['id']:
                continue
            my_tasks.append({
                'task_id': t.get('task_id', ''),
                'project_id': meta.get('id', ''),
                'project_name': meta.get('name', ''),
                'stage_name': t.get('stage_name', ''),
                'team_name': t.get('team_name', ''),
                'material': t.get('material', ''),
                'due_date': t.get('due_date', ''),
                'status': t.get('status', ''),
            })

    # 统计
    overview = {
        'my_total': len(my_tasks),
        'my_submitted': 0,
        'my_passed': 0,
        'my_rejected': 0,
        'my_overdue': 0,
        'my_due_soon': 0,
    }
    for t in my_tasks:
        status = t['status']
        if status == '已提交':
            overview['my_submitted'] += 1
        elif status == '已通过':
            overview['my_passed'] += 1
        elif status == '已打回':
            overview['my_rejected'] += 1
        is_overdue, is_due_soon = _classify_task(t, now, soon)
        if is_overdue:
            overview['my_overdue'] += 1
        if is_due_soon:
            overview['my_due_soon'] += 1

    # 待办排序:有 due_date 的按升序在前,无 due_date 在后
    def _sort_key(t):
        due = _parse_due(t.get('due_date', ''))
        return (0, due) if due else (1, datetime.max)

    my_tasks.sort(key=_sort_key)

    return {
        'role': '干事',
        'overview': overview,
        'my_tasks': my_tasks,
    }
