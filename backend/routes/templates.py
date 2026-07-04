# -*- coding: utf-8 -*-
"""比赛模板路由:列表、详情(部长/副部长可读)。增删改在 2.2 补充。"""
import re
from flask import Blueprint, jsonify

from guards import role_required
from storage import list_json_files, read_json
from config import TEMPLATES_DIR

bp = Blueprint('templates', __name__, url_prefix='/api/templates')

# 模板 ID 仅允许字母数字下划线横线,杜绝 `../` 路径穿越
_TID_RE = re.compile(r'^[A-Za-z0-9_-]+$')


def _load_template(tid):
    """按 ID 安全读取模板。tid 非法则返回 None。"""
    if not tid or not _TID_RE.match(tid):
        return None
    return read_json('{}/{}.json'.format(TEMPLATES_DIR, tid), default=None)


def _normalize_stage(s, i):
    return {
        'order': s.get('order', i + 1),
        'name': s.get('name', '') or '',
        'duration_days': s.get('duration_days', 0) or 0,
        'materials': s.get('materials') or [],
        'need_defense': bool(s.get('need_defense')),
    }


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
