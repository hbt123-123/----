# -*- coding: utf-8 -*-
"""项目路由:创建、列表。

创建项目:选模板 → 深拷贝阶段与材料清单 → 填基本信息 → 指派副部长 → 设各阶段截止时间。
一项目一目录沙箱:projects/{目录名}/meta.json + stages.json + teams.json + tasks.json。
"""
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify

from guards import role_required
from storage import read_json, write_json, ensure_dir
from config import PROJECTS_INDEX, PROJECTS_DIR
from utils.paths import sanitize_name, unique_dirname
from routes.templates import _load_template

bp = Blueprint('projects', __name__, url_prefix='/api/projects')


def load_project(pid, user=None):
    """加载项目 meta 与目录名,带归属校验。返回 (meta, dir) 或 (None, None)。"""
    idx = read_json(PROJECTS_INDEX, default=[]) or []
    entry = next((p for p in idx if p.get('id') == pid), None)
    if not entry:
        return None, None
    meta = read_json('{}/{}/meta.json'.format(PROJECTS_DIR, entry['dir']), default=None)
    if not meta:
        return None, None
    if user and user.get('role') == '副部长' and user['id'] not in (meta.get('owner_ids') or []):
        return None, None
    return meta, entry['dir']


@bp.get('')
@role_required('部长', '副部长')
def list_projects():
    """项目列表(读取各项目 meta)。"""
    idx = read_json(PROJECTS_INDEX, default=[]) or []
    u = request.current_user
    items = []
    for p in idx:
        meta = read_json('{}/{}/meta.json'.format(PROJECTS_DIR, p['dir']), default=None) or p
        if u.get('role') == '副部长' and u['id'] not in (meta.get('owner_ids') or []):
            continue
        items.append(meta)
    items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify(projects=items)


@bp.get('/<pid>')
@role_required('部长', '副部长')
def get_project(pid):
    """项目详情:meta + stages。副部长仅可访问自己负责的项目。"""
    idx = read_json(PROJECTS_INDEX, default=[]) or []
    entry = next((p for p in idx if p.get('id') == pid), None)
    if not entry:
        return jsonify(error='项目不存在'), 404
    meta = read_json('{}/{}/meta.json'.format(PROJECTS_DIR, entry['dir']), default=None)
    if not meta:
        return jsonify(error='项目不存在'), 404
    u = request.current_user
    if u.get('role') == '副部长' and u['id'] not in (meta.get('owner_ids') or []):
        return jsonify(error='无权访问该项目'), 403
    stages = read_json('{}/{}/stages.json'.format(PROJECTS_DIR, entry['dir']), default=[])
    return jsonify(project=meta, stages=stages)


@bp.post('')
@role_required('部长', '副部长')
def create_project():
    """创建项目(部长/副部长)。"""
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    year = str(data.get('year') or '').strip()
    template_id = data.get('template_id') or ''
    owner_ids = [oid for oid in (data.get('owner_ids') or []) if oid]
    u = request.current_user
    if u.get('role') == '副部长' and u['id'] not in owner_ids:
        owner_ids.append(u['id'])
    level = (data.get('level') or '').strip()
    stages_input = data.get('stages') or []

    if not name:
        return jsonify(error='项目名称必填'), 400
    if not year:
        return jsonify(error='年份必填'), 400
    tpl = _load_template(template_id)
    if not tpl:
        return jsonify(error='请选择有效模板'), 400

    pid = 'prj_' + uuid.uuid4().hex[:10]
    idx = read_json(PROJECTS_INDEX, default=[]) or []
    existing_dirs = {p['dir'] for p in idx}
    base = sanitize_name(name) + '_' + sanitize_name(year)
    dirname = unique_dirname(base, existing_dirs)

    # 阶段:从模板深拷贝,用前端传入的 start/due 覆盖模板默认
    tpl_stages = tpl.get('stages') or []
    stages = []
    for i, s in enumerate(tpl_stages):
        si = stages_input[i] if i < len(stages_input) else {}
        stages.append({
            'stage_id': 'stg_' + uuid.uuid4().hex[:8],
            'name': s.get('name', '') or '',
            'order': s.get('order', i + 1) or i + 1,
            'start_date': (si.get('start_date') or '').strip(),
            'due_date': (si.get('due_date') or s.get('due_date') or '').strip(),
            'need_defense': bool(s.get('need_defense')),
            'status': '未开始',
            'materials': list(s.get('materials') or []),
        })

    meta = {
        'id': pid,
        'dir': dirname,
        'name': name,
        'template_id': template_id,
        'template_name': tpl.get('name', ''),
        'year': year,
        'level': level,
        'status': '进行中',
        'owner_ids': owner_ids,
        'created_at': datetime.now().isoformat(),
        'created_by': request.current_user['id'],
    }

    # 一项目一目录:写入 meta/stages/teams/tasks
    ensure_dir('{}/{}'.format(PROJECTS_DIR, dirname))
    write_json('{}/{}/meta.json'.format(PROJECTS_DIR, dirname), meta)
    write_json('{}/{}/stages.json'.format(PROJECTS_DIR, dirname), stages)
    write_json('{}/{}/teams.json'.format(PROJECTS_DIR, dirname), [])
    write_json('{}/{}/tasks.json'.format(PROJECTS_DIR, dirname), [])

    idx.append({
        'id': pid,
        'dir': dirname,
        'name': name,
        'template_id': template_id,
        'year': year,
    })
    write_json(PROJECTS_INDEX, idx)

    return jsonify(project=meta, stages=stages)
