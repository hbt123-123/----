# -*- coding: utf-8 -*-
"""比赛模板路由:列表、详情、新建、编辑、复制、删除。

读:部长/副部长;写:仅部长。
"""
import re
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify

from guards import role_required, admin_required
from storage import list_json_files, read_json, write_json, delete_file
from config import TEMPLATES_DIR

bp = Blueprint('templates', __name__, url_prefix='/api/templates')

# 模板 ID 仅允许字母数字下划线横线,杜绝 `../` 路径穿越
_TID_RE = re.compile(r'^[A-Za-z0-9_-]+$')


def _new_template_id():
    return 'tpl_' + uuid.uuid4().hex[:10]


def _load_template(tid):
    """按 ID 安全读取模板。tid 非法则返回 None。"""
    if not tid or not _TID_RE.match(tid):
        return None
    return read_json('{}/{}.json'.format(TEMPLATES_DIR, tid), default=None)


def _normalize_stage(s, i):
    return {
        'order': s.get('order', i + 1),
        'name': s.get('name', '') or '',
        'due_date': s.get('due_date') or '',
        'materials': s.get('materials') or [],
        'need_defense': bool(s.get('need_defense')),
    }


def _normalize_stages_input(stages):
    """规范化前端传入的阶段:补 order、默认值、跳过无名称阶段。"""
    result = []
    for i, s in enumerate(stages or []):
        name = (s.get('name') or '').strip() if isinstance(s, dict) else ''
        if not name:
            continue
        result.append({
            'order': i + 1,
            'name': name,
            'due_date': (s.get('due_date') or '').strip(),
            'materials': [str(m).strip() for m in (s.get('materials') or []) if str(m).strip()],
            'need_defense': bool(s.get('need_defense')),
        })
    return result


@bp.get('')
@role_required('部长', '副部长')
def list_templates():
    """模板列表(含阶段与材料清单,供前端直接展示)。"""
    items = []
    for fn in list_json_files(TEMPLATES_DIR):
        t = read_json('{}/{}'.format(TEMPLATES_DIR, fn), default=None)
        if not t or not t.get('id'):
            continue
        stages = [_normalize_stage(s, i) for i, s in enumerate(t.get('stages') or [])]
        items.append({
            'id': t['id'],
            'name': t.get('name') or '未命名模板',
            'stages': stages,
        })
    items.sort(key=lambda x: x['name'])
    return jsonify(templates=items)


@bp.get('/<tid>')
@role_required('部长', '副部长')
def get_template(tid):
    """模板详情。"""
    t = _load_template(tid)
    if not t:
        return jsonify(error='模板不存在'), 404
    t = dict(t)
    t['stages'] = [_normalize_stage(s, i) for i, s in enumerate(t.get('stages') or [])]
    return jsonify(template=t)


@bp.post('')
@admin_required
def create_template():
    """新建模板(仅部长)。"""
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify(error='模板名称必填'), 400
    stages = _normalize_stages_input(data.get('stages'))
    if not stages:
        return jsonify(error='至少需要一个阶段'), 400
    tpl = {
        'id': _new_template_id(),
        'name': name,
        'stages': stages,
        'created_at': datetime.now().isoformat(),
    }
    write_json('{}/{}.json'.format(TEMPLATES_DIR, tpl['id']), tpl)
    return jsonify(template=tpl)


@bp.put('/<tid>')
@admin_required
def update_template(tid):
    """更新模板(仅部长)。"""
    t = _load_template(tid)
    if not t:
        return jsonify(error='模板不存在'), 404
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify(error='模板名称必填'), 400
    stages = _normalize_stages_input(data.get('stages'))
    if not stages:
        return jsonify(error='至少需要一个阶段'), 400
    t['name'] = name
    t['stages'] = stages
    t['updated_at'] = datetime.now().isoformat()
    write_json('{}/{}.json'.format(TEMPLATES_DIR, tid), t)
    return jsonify(template=t)


@bp.post('/<tid>/clone')
@admin_required
def clone_template(tid):
    """复制模板(仅部长):基于现有模板生成副本。"""
    src = _load_template(tid)
    if not src:
        return jsonify(error='模板不存在'), 404
    new = {
        'id': _new_template_id(),
        'name': (src.get('name') or '') + ' 副本',
        'stages': [_normalize_stage(s, i) for i, s in enumerate(src.get('stages') or [])],
        'created_at': datetime.now().isoformat(),
        'cloned_from': tid,
    }
    write_json('{}/{}.json'.format(TEMPLATES_DIR, new['id']), new)
    return jsonify(template=new)


@bp.delete('/<tid>')
@admin_required
def delete_template(tid):
    """删除模板(仅部长)。"""
    if not tid or not _TID_RE.match(tid):
        return jsonify(error='模板不存在'), 404
    rel = '{}/{}.json'.format(TEMPLATES_DIR, tid)
    if not read_json(rel, default=None):
        return jsonify(error='模板不存在'), 404
    delete_file(rel)
    return jsonify(ok=True)
