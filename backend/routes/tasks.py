# -*- coding: utf-8 -*-
"""材料任务路由:批量生成、列表、上传、审核、下载。

任务 = 某团队在某阶段的某项材料。状态:未交 / 已提交 / 已通过 / 已打回。
文件存 projects/{dir}/uploads/{阶段}/{团队}/{文件名},同名归档历史版本。
"""
import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

from guards import role_required
from storage import read_json, write_json
from config import PROJECTS_DIR, DATA_DIR
from routes.projects import load_project
from utils.upload import save_upload
from utils.paths import safe_join

bp = Blueprint('tasks', __name__, url_prefix='/api')


def _tasks_rel(dir_):
    return '{}/{}/tasks.json'.format(PROJECTS_DIR, dir_)


def _load_tasks(dir_):
    return read_json(_tasks_rel(dir_), default=[]) or []


@bp.get('/projects/<pid>/tasks')
@role_required('部长', '副部长', '干事')
def list_tasks(pid):
    """任务列表。干事只看指派给自己的;部长/副部长看全部。可按 stage/team 过滤。"""
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    tasks = _load_tasks(dir_)
    u = request.current_user
    if u.get('role') == '干事':
        tasks = [t for t in tasks if t.get('assignee_id') == u['id']]
    stage_id = request.args.get('stage_id')
    team_id = request.args.get('team_id')
    if stage_id:
        tasks = [t for t in tasks if t.get('stage_id') == stage_id]
    if team_id:
        tasks = [t for t in tasks if t.get('team_id') == team_id]
    return jsonify(tasks=tasks)


@bp.post('/projects/<pid>/tasks/generate')
@role_required('部长', '副部长')
def generate_tasks(pid):
    """批量生成任务:选阶段 + 团队范围 + 材料清单 → 每队每材料一个任务。"""
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    data = request.get_json(silent=True) or {}
    stage_id = data.get('stage_id')
    team_ids = data.get('team_ids') or []
    materials = data.get('materials') or []
    assignee_id = data.get('assignee_id') or ''
    if not stage_id or not team_ids or not materials:
        return jsonify(error='阶段、团队、材料清单均必填'), 400

    stages = read_json('{}/{}/stages.json'.format(PROJECTS_DIR, dir_), default=[]) or []
    stage = next((s for s in stages if s.get('stage_id') == stage_id), None)
    if not stage:
        return jsonify(error='阶段不存在'), 404
    teams = read_json('{}/{}/teams.json'.format(PROJECTS_DIR, dir_), default=[]) or []
    team_map = {t.get('team_id'): t for t in teams}

    tasks = _load_tasks(dir_)
    existing = {(t.get('stage_id'), t.get('team_id'), t.get('material')) for t in tasks}
    created = 0
    for tid in team_ids:
        team = team_map.get(tid)
        if not team:
            continue
        for mat in materials:
            mat = (mat or '').strip()
            if not mat:
                continue
            key = (stage_id, tid, mat)
            if key in existing:
                continue
            tasks.append({
                'task_id': 'tk_' + uuid.uuid4().hex[:8],
                'stage_id': stage_id,
                'stage_name': stage.get('name', ''),
                'team_id': tid,
                'team_name': team.get('name', ''),
                'material': mat,
                'assignee_id': assignee_id,
                'due_date': stage.get('due_date', ''),
                'status': '未交',
                'file_path': '',
                'file_name': '',
                'file_versions': [],
                'submitted_at': '',
                'reviewed_at': '',
                'review_comment': '',
            })
            existing.add(key)
            created += 1
    write_json(_tasks_rel(dir_), tasks)
    return jsonify(created=created, total=len(tasks))


@bp.post('/projects/<pid>/tasks/<tid>/upload')
@role_required('部长', '副部长', '干事')
def upload_task(pid, tid):
    """上传材料文件,同名归档历史版本,状态→已提交。干事只能上传指派给自己的任务。"""
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    f = request.files.get('file')
    if not f:
        return jsonify(error='未上传文件'), 400
    tasks = _load_tasks(dir_)
    task = next((t for t in tasks if t.get('task_id') == tid), None)
    if not task:
        return jsonify(error='任务不存在'), 404
    u = request.current_user
    if u.get('role') == '干事' and task.get('assignee_id') != u['id']:
        return jsonify(error='只能上传指派给自己的任务'), 403

    rel, info = save_upload(dir_, task.get('stage_name', ''), task.get('team_name', ''), f.filename, f)
    if rel is None:
        return jsonify(error=info), 400

    task['file_versions'] = (task.get('file_versions') or []) + info
    task['file_path'] = rel
    task['file_name'] = f.filename
    task['status'] = '已提交'
    task['submitted_at'] = datetime.now().isoformat()
    write_json(_tasks_rel(dir_), tasks)
    return jsonify(task=task)


@bp.post('/projects/<pid>/tasks/<tid>/review')
@role_required('部长', '副部长')
def review_task(pid, tid):
    """审核:pass→已通过,reject→已打回(可重新提交)。"""
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    data = request.get_json(silent=True) or {}
    action = data.get('action')
    comment = (data.get('comment') or '').strip()
    if action not in ('pass', 'reject'):
        return jsonify(error='action 必须为 pass 或 reject'), 400
    tasks = _load_tasks(dir_)
    task = next((t for t in tasks if t.get('task_id') == tid), None)
    if not task:
        return jsonify(error='任务不存在'), 404
    task['status'] = '已通过' if action == 'pass' else '已打回'
    task['reviewed_at'] = datetime.now().isoformat()
    task['review_comment'] = comment
    write_json(_tasks_rel(dir_), tasks)
    return jsonify(task=task)


@bp.delete('/projects/<pid>/tasks/<tid>')
@role_required('部长', '副部长')
def delete_task(pid, tid):
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    tasks = _load_tasks(dir_)
    tasks = [t for t in tasks if t.get('task_id') != tid]
    write_json(_tasks_rel(dir_), tasks)
    return jsonify(ok=True)


@bp.get('/projects/<pid>/tasks/<tid>/file')
@role_required('部长', '副部长', '干事')
def download_task_file(pid, tid):
    """下载任务当前文件。干事只能下载指派给自己的任务。"""
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    tasks = _load_tasks(dir_)
    task = next((t for t in tasks if t.get('task_id') == tid), None)
    if not task or not task.get('file_path'):
        return jsonify(error='文件不存在'), 404
    u = request.current_user
    if u.get('role') == '干事' and task.get('assignee_id') != u['id']:
        return jsonify(error='无权下载该文件'), 403
    abs_path = safe_join(DATA_DIR, task['file_path'])
    if not os.path.isfile(abs_path):
        return jsonify(error='文件不存在'), 404
    return send_file(abs_path, as_attachment=True,
                     download_name=task.get('file_name') or os.path.basename(abs_path))
