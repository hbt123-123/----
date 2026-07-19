# -*- coding: utf-8 -*-
"""答辩评审路由:答辩安排、评委、出场顺序、成绩录入。

每项目一份 defenses.json:
{
  sessions: [
    {
      session_id, stage_id, stage_name, date, location,
      judges: [姓名,...],                   # 评委姓名列表(可外请,自由填写)
      arrangements: [                       # 出场安排 + 成绩
        { team_id, team_name, order, score, comment }
      ],
      status: '待开始'|'进行中'|'已完成'
    }
  ]
}

只有 stages.json 中 need_defense=True 的阶段可建答辩场。
成绩并入 export.py 汇总表(见 _build_summary)。
"""
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify

from guards import role_required
from storage import read_json, write_json
from config import PROJECTS_DIR
from routes.projects import load_project

bp = Blueprint('defenses', __name__, url_prefix='/api')


def _def_rel(dir_):
    return '{}/{}/defenses.json'.format(PROJECTS_DIR, dir_)


def _load_defenses(dir_):
    data = read_json(_def_rel(dir_), default=None)
    if not data or not isinstance(data, dict):
        return {'sessions': []}
    if 'sessions' not in data or not isinstance(data['sessions'], list):
        data['sessions'] = []
    return data


def _save_defenses(dir_, data):
    write_json(_def_rel(dir_), data)


def _defense_stages(dir_):
    """返回该项目中 need_defense=True 的阶段列表。"""
    stages = read_json('{}/{}/stages.json'.format(PROJECTS_DIR, dir_), default=[]) or []
    return [s for s in stages if s.get('need_defense')]


def _normalize_arrangement(a):
    return {
        'team_id': a.get('team_id', ''),
        'team_name': a.get('team_name', ''),
        'order': int(a.get('order') or 0),
        'score': float(a.get('score') or 0),
        'comment': (a.get('comment') or '').strip(),
    }


@bp.get('/projects/<pid>/defenses')
@role_required('部长', '副部长', '干事')
def list_defenses(pid):
    """答辩场次列表。干事只读。"""
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    data = _load_defenses(dir_)
    sessions = data.get('sessions', [])
    # 干事不返回评委敏感信息?保留只读视图(姓名非敏感)
    return jsonify(sessions=sessions)


@bp.post('/projects/<pid>/defenses')
@role_required('部长', '副部长')
def create_defense(pid):
    """创建答辩场次:选阶段(必须 need_defense=True),自动为该项目全部团队生成出场安排。"""
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    data = request.get_json(silent=True) or {}
    stage_id = (data.get('stage_id') or '').strip()
    date = (data.get('date') or '').strip()
    location = (data.get('location') or '').strip()
    judges = [j for j in (data.get('judges') or []) if str(j).strip()]
    if not stage_id:
        return jsonify(error='请选择答辩阶段'), 400

    stages = _defense_stages(dir_)
    stage = next((s for s in stages if s.get('stage_id') == stage_id), None)
    if not stage:
        return jsonify(error='该阶段未开启答辩,请在模板/项目设置中勾选「需要答辩」'), 400

    # 同一阶段仅允许一场答辩
    data_def = _load_defenses(dir_)
    if any(s.get('stage_id') == stage_id for s in data_def['sessions']):
        return jsonify(error='该阶段已存在答辩场次,请编辑现有场次'), 400

    # 自动为该项目全部团队生成出场安排(顺序默认按团队创建顺序)
    teams = read_json('{}/{}/teams.json'.format(PROJECTS_DIR, dir_), default=[]) or []
    arrangements = []
    for i, t in enumerate(teams, 1):
        arrangements.append({
            'team_id': t.get('team_id', ''),
            'team_name': t.get('name', ''),
            'order': i,
            'score': 0,
            'comment': '',
        })

    session = {
        'session_id': 'ds_' + uuid.uuid4().hex[:8],
        'stage_id': stage_id,
        'stage_name': stage.get('name', ''),
        'date': date,
        'location': location,
        'judges': judges,
        'arrangements': arrangements,
        'status': '待开始',
        'created_at': datetime.now().isoformat(),
    }
    data_def['sessions'].append(session)
    _save_defenses(dir_, data_def)
    return jsonify(session=session)


@bp.put('/projects/<pid>/defenses/<sid>')
@role_required('部长', '副部长')
def update_defense(pid, sid):
    """更新答辩场次:可改 date/location/judges/status/arrangements(顺序+成绩+评语)。

    body:
      date, location, judges[], status,
      arrangements: [{team_id, order, score, comment}]
    """
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    data = request.get_json(silent=True) or {}
    data_def = _load_defenses(dir_)
    session = next((s for s in data_def['sessions'] if s.get('session_id') == sid), None)
    if not session:
        return jsonify(error='答辩场次不存在'), 404

    if 'date' in data:
        session['date'] = (data.get('date') or '').strip()
    if 'location' in data:
        session['location'] = (data.get('location') or '').strip()
    if 'judges' in data:
        session['judges'] = [str(j).strip() for j in (data.get('judges') or []) if str(j).strip()]
    if 'status' in data:
        st = (data.get('status') or '').strip()
        if st in ('待开始', '进行中', '已完成'):
            session['status'] = st
    if 'arrangements' in data:
        # 接受前端整体替换出场安排(顺序+成绩+评语)
        arr_in = data.get('arrangements') or []
        # 按 team_id 合并,保留原 team_name
        old_map = {a.get('team_id'): a for a in session.get('arrangements', [])}
        new_arr = []
        for a in arr_in:
            tid = a.get('team_id', '')
            old = old_map.get(tid, {})
            merged = {
                'team_id': tid,
                'team_name': old.get('team_name') or a.get('team_name', ''),
                'order': int(a.get('order') or 0),
                'score': float(a.get('score') or 0),
                'comment': (a.get('comment') or '').strip(),
            }
            new_arr.append(merged)
        # 重新归一化 order(1..N),按传入顺序
        new_arr.sort(key=lambda x: x['order'])
        for i, a in enumerate(new_arr, 1):
            a['order'] = i
        session['arrangements'] = new_arr

    session['updated_at'] = datetime.now().isoformat()
    _save_defenses(dir_, data_def)
    return jsonify(session=session)


@bp.delete('/projects/<pid>/defenses/<sid>')
@role_required('部长', '副部长')
def delete_defense(pid, sid):
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    data_def = _load_defenses(dir_)
    before = len(data_def['sessions'])
    data_def['sessions'] = [s for s in data_def['sessions'] if s.get('session_id') != sid]
    if len(data_def['sessions']) == before:
        return jsonify(error='答辩场次不存在'), 404
    _save_defenses(dir_, data_def)
    return jsonify(ok=True)
