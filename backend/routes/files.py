# -*- coding: utf-8 -*-
"""项目文件管理:团队级批量上传、列表、下载、删除。

拖拽文件夹批量上传存 projects/{dir}/uploads/{团队名}/{文件名},同名归档历史版本。
"""
import os
from flask import Blueprint, request, jsonify, send_file

from guards import role_required
from storage import read_json
from config import PROJECTS_DIR, DATA_DIR
from routes.projects import load_project
from utils.upload import save_upload
from utils.paths import safe_join, sanitize_name

bp = Blueprint('files', __name__, url_prefix='/api')


def _teams_rel(dir_):
    return '{}/{}/teams.json'.format(PROJECTS_DIR, dir_)


def _find_team(dir_, tid):
    teams = read_json(_teams_rel(dir_), default=[]) or []
    return next((t for t in teams if t.get('team_id') == tid), None)


def _team_files_rel(dir_, team_name):
    return 'projects/{}/uploads/{}'.format(dir_, sanitize_name(team_name) or '未分团队')


@bp.post('/projects/<pid>/teams/<tid>/files')
@role_required('部长', '副部长', '干事')
def upload_team_files(pid, tid):
    """批量上传文件到指定团队(拖拽文件夹)。"""
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    team = _find_team(dir_, tid)
    if not team:
        return jsonify(error='团队不存在'), 404
    files = request.files.getlist('files')
    if not files:
        return jsonify(error='未上传文件'), 400
    uploaded = []
    archived = 0
    for f in files:
        if not f or not f.filename:
            continue
        rel, info = save_upload(dir_, '', team.get('name', ''), f.filename, f)
        if rel is None:
            continue
        archived += len(info)
        uploaded.append({'filename': f.filename, 'path': rel})
    return jsonify(uploaded=uploaded, archived=archived, total=len(uploaded))


@bp.get('/projects/<pid>/teams/<tid>/files')
@role_required('部长', '副部长', '干事')
def list_team_files(pid, tid):
    """列出团队当前文件(不含 .versions 历史版本)。"""
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    team = _find_team(dir_, tid)
    if not team:
        return jsonify(error='团队不存在'), 404
    abs_dir = safe_join(DATA_DIR, _team_files_rel(dir_, team.get('name', '')))
    items = []
    if os.path.isdir(abs_dir):
        for fn in os.listdir(abs_dir):
            full = os.path.join(abs_dir, fn)
            if os.path.isfile(full) and not fn.startswith('.'):
                st = os.stat(full)
                items.append({
                    'filename': fn,
                    'size': st.st_size,
                    'mtime': int(st.st_mtime),
                })
    items.sort(key=lambda x: x['filename'])
    return jsonify(files=items)


@bp.get('/projects/<pid>/teams/<tid>/files/<filename>')
@role_required('部长', '副部长', '干事')
def download_team_file(pid, tid, filename):
    """下载团队文件。"""
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    team = _find_team(dir_, tid)
    if not team:
        return jsonify(error='团队不存在'), 404
    abs_dir = safe_join(DATA_DIR, _team_files_rel(dir_, team.get('name', '')))
    target = safe_join(abs_dir, sanitize_name(filename))
    if not os.path.isfile(target):
        return jsonify(error='文件不存在'), 404
    return send_file(target, as_attachment=True, download_name=filename)


@bp.delete('/projects/<pid>/teams/<tid>/files/<filename>')
@role_required('部长', '副部长')
def delete_team_file(pid, tid, filename):
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    team = _find_team(dir_, tid)
    if not team:
        return jsonify(error='团队不存在'), 404
    abs_dir = safe_join(DATA_DIR, _team_files_rel(dir_, team.get('name', '')))
    target = safe_join(abs_dir, sanitize_name(filename))
    if os.path.isfile(target):
        os.remove(target)
    return jsonify(ok=True)
