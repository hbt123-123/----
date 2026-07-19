# -*- coding: utf-8 -*-
"""游客只读视图:未登录可浏览公开项目(脱敏)。

脱敏规则:
- 隐藏:owner_ids / owner_names / dir / created_by 等内部字段
- 隐藏:团队明细(姓名/学号/联系方式)、任务指派人、文件路径、答辩评委姓名/团队成绩/评语
- 保留:项目基本信息、阶段清单(含进度统计)、整体任务统计、答辩场次公开信息
  (日期/地点/状态/评委人数/已答辩团队数)

可见性:meta 中 is_public 默认 True(不存在该字段视为公开)。
"""
from flask import Blueprint, jsonify

from storage import read_json
from config import PROJECTS_INDEX, PROJECTS_DIR

bp = Blueprint('public', __name__, url_prefix='/api/public')


def _is_public(meta):
    """meta 是否对游客公开。缺省视为公开。"""
    return bool(meta.get('is_public', True))


def _empty_task_stats():
    return {
        'total': 0, 'passed': 0, 'submitted': 0,
        'pending': 0, 'rejected': 0,
    }


def _aggregate_task_stats(tasks):
    """从任务列表统计整体进度(不含逾期/临期等敏感时间字段)。"""
    stats = _empty_task_stats()
    for t in tasks:
        status = t.get('status', '')
        stats['total'] += 1
        if status == '已通过':
            stats['passed'] += 1
        elif status == '已提交':
            stats['submitted'] += 1
        elif status == '已打回':
            stats['rejected'] += 1
        elif status == '未交':
            stats['pending'] += 1
    return stats


def _stage_progress(stages, tasks):
    """阶段进度:返回每个阶段的 done/total(不暴露任务本身)。"""
    stats = {s.get('stage_id'): {'done': 0, 'total': 0}
             for s in stages}
    for t in tasks:
        sid = t.get('stage_id')
        if sid in stats:
            stats[sid]['total'] += 1
            if t.get('status') == '已通过':
                stats[sid]['done'] += 1
    out = []
    for s in stages:
        sid = s.get('stage_id')
        st = stats.get(sid, {'done': 0, 'total': 0})
        out.append({
            'stage_id': sid,
            'name': s.get('name', ''),
            'order': s.get('order', 0),
            'start_date': s.get('start_date', ''),
            'due_date': s.get('due_date', ''),
            'need_defense': bool(s.get('need_defense')),
            'status': s.get('status', ''),
            'materials': list(s.get('materials') or []),
            'done': st['done'],
            'total': st['total'],
        })
    return out


def _public_defense_sessions(dir_):
    """答辩场次公开信息:仅保留日期/地点/状态/阶段名/评委数/已答辩团队数。

    不返回 judges 姓名列表、arrangements 团队明细与成绩。
    """
    data = read_json('{}/{}/defenses.json'.format(PROJECTS_DIR, dir_), default=None) or {}
    sessions = data.get('sessions', []) if isinstance(data, dict) else []
    out = []
    for s in sessions:
        arr = s.get('arrangements') or []
        finished = sum(1 for a in arr if a.get('score'))
        out.append({
            'session_id': s.get('session_id', ''),
            'stage_id': s.get('stage_id', ''),
            'stage_name': s.get('stage_name', ''),
            'date': s.get('date', ''),
            'location': s.get('location', ''),
            'status': s.get('status', ''),
            'judge_count': len(s.get('judges') or []),
            'team_count': len(arr),
            'finished_count': finished,
        })
    return out


def _public_project_meta(meta):
    """脱敏项目 meta:剥离内部字段。"""
    return {
        'id': meta.get('id', ''),
        'name': meta.get('name', ''),
        'template_name': meta.get('template_name', ''),
        'year': meta.get('year', ''),
        'level': meta.get('level', ''),
        'status': meta.get('status', ''),
        'created_at': meta.get('created_at', ''),
        'is_public': True,
    }


@bp.get('/projects')
def list_public_projects():
    """游客可见项目列表(脱敏)。"""
    idx = read_json(PROJECTS_INDEX, default=[]) or []
    items = []
    for entry in idx:
        meta = read_json('{}/{}/meta.json'.format(PROJECTS_DIR, entry.get('dir', '')), default=None)
        if not meta or not _is_public(meta):
            continue
        dir_ = entry.get('dir', '')
        tasks = read_json('{}/{}/tasks.json'.format(PROJECTS_DIR, dir_), default=[]) or []
        stages = read_json('{}/{}/stages.json'.format(PROJECTS_DIR, dir_), default=[]) or []
        teams = read_json('{}/{}/teams.json'.format(PROJECTS_DIR, dir_), default=[]) or []
        items.append({
            **_public_project_meta(meta),
            'stage_count': len(stages),
            'team_count': len(teams),
            'task_stats': _aggregate_task_stats(tasks),
        })
    items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify(projects=items)


@bp.get('/projects/<pid>')
def get_public_project(pid):
    """游客项目详情(脱敏):基本信息 + 阶段进度 + 答辩场次公开信息。"""
    idx = read_json(PROJECTS_INDEX, default=[]) or []
    entry = next((p for p in idx if p.get('id') == pid), None)
    if not entry:
        return jsonify(error='项目不存在'), 404
    meta = read_json('{}/{}/meta.json'.format(PROJECTS_DIR, entry['dir']), default=None)
    if not meta or not _is_public(meta):
        return jsonify(error='项目不存在'), 404
    dir_ = entry['dir']
    stages = read_json('{}/{}/stages.json'.format(PROJECTS_DIR, dir_), default=[]) or []
    tasks = read_json('{}/{}/tasks.json'.format(PROJECTS_DIR, dir_), default=[]) or []
    teams = read_json('{}/{}/teams.json'.format(PROJECTS_DIR, dir_), default=[]) or []
    return jsonify(
        project=_public_project_meta(meta),
        stages=_stage_progress(stages, tasks),
        task_stats=_aggregate_task_stats(tasks),
        team_count=len(teams),
        defense_sessions=_public_defense_sessions(dir_),
    )
