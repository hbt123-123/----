# -*- coding: utf-8 -*-
"""AI 辅助路由:材料完整性检查、汇报书草稿生成、材料内容摘要。

AI 为只读辅助,不写入任何业务数据。配置缺失返回 503,调用失败返回 502/504。
权限:check/draft 限部长+副部长;summarize 限部长+副部长+干事(干事仅自己任务)。
"""
import json
from flask import Blueprint, request, jsonify

from guards import role_required
from storage import read_json
from config import PROJECTS_DIR, DATA_DIR
from routes.projects import load_project
from utils.paths import safe_join
from utils.extract import extract_text
from ai_config import is_ai_ready
from ai_client import chat, AIClientError

bp = Blueprint('ai', __name__, url_prefix='/api')


def _ai_unavailable():
    return jsonify(error='AI 未配置,请检查 agnes.env'), 503


def _ai_error(e):
    code = e.status_code if e.status_code in (502, 503, 504) else 502
    return jsonify(error='AI 调用失败: {}'.format(e.message)), code


def _load_stages_teams_tasks(dir_):
    stages = read_json('{}/{}/stages.json'.format(PROJECTS_DIR, dir_), default=[]) or []
    teams = read_json('{}/{}/teams.json'.format(PROJECTS_DIR, dir_), default=[]) or []
    tasks = read_json('{}/{}/tasks.json'.format(PROJECTS_DIR, dir_), default=[]) or []
    return stages, teams, tasks


@bp.post('/projects/<pid>/ai/check')
@role_required('部长', '副部长')
def check_completeness(pid):
    """材料完整性检查:对照阶段材料清单 + 任务状态,AI 给出缺失项/规范性/建议。"""
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    if not is_ai_ready():
        return _ai_unavailable()

    data = request.get_json(silent=True) or {}
    stage_id = (data.get('stage_id') or '').strip()
    team_id = (data.get('team_id') or '').strip()

    stages, teams, tasks = _load_stages_teams_tasks(dir_)
    if stage_id:
        stages = [s for s in stages if s.get('stage_id') == stage_id]
    if team_id:
        teams = [t for t in teams if t.get('team_id') == team_id]
    if not stages:
        return jsonify(error='所选范围无阶段数据'), 400
    if not teams:
        return jsonify(error='所选范围无团队数据'), 400

    # 构造上下文:每阶段每团队每材料的提交状态 + 文件名
    lines = []
    for s in stages:
        materials = s.get('materials') or []
        lines.append('## 阶段:{}(应交材料:{})'.format(
            s.get('name', ''), '、'.join(materials) or '无'))
        for tm in teams:
            lines.append('- 团队:{}(team_id:{})'.format(tm.get('name', ''), tm.get('team_id', '')))
            for mat in materials:
                task = next((t for t in tasks
                             if t.get('stage_id') == s.get('stage_id')
                             and t.get('team_id') == tm.get('team_id')
                             and t.get('material') == mat), None)
                if task:
                    lines.append('  · {} | 状态:{} | 文件名:{}'.format(
                        mat, task.get('status', '未交'), task.get('file_name') or '无'))
                else:
                    lines.append('  · {} | 状态:未交(未生成任务) | 文件名:无'.format(mat))
    context = '\n'.join(lines)

    messages = [
        {'role': 'system', 'content':
         '你是材料完整性检查助手。严格对照各阶段应交材料清单,检查每个团队的提交情况,'
         '指出缺失材料、文件名不规范之处,并给出补交建议。'
         '必须只返回 JSON,格式:'
         '{"teams":[{"team_id":"","team_name":"","missing":[],"irregular":[],"suggestions":""}],"overall":""}'},
        {'role': 'user', 'content':
         '项目:{}\n\n{}\n\n请检查并返回 JSON。'.format(meta.get('name', ''), context)},
    ]

    try:
        raw = chat(messages, temperature=0.2, max_tokens=2000)
    except AIClientError as e:
        return _ai_error(e)

    # 容错解析 JSON:剥离可能的 ```json 包裹
    result = None
    cleaned = raw.strip()
    if cleaned.startswith('```'):
        parts = cleaned.split('```')
        if len(parts) >= 3:
            cleaned = parts[1].strip()
            if cleaned.startswith('json'):
                cleaned = cleaned[4:].strip()
    try:
        result = json.loads(cleaned)
    except (ValueError, json.JSONDecodeError):
        result = None

    return jsonify(result=result if result is not None else raw, raw=raw)


@bp.post('/projects/<pid>/ai/draft')
@role_required('部长', '副部长')
def generate_draft(pid):
    """汇报书草稿生成:根据项目/阶段/团队信息生成 Markdown 草稿。"""
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    if not is_ai_ready():
        return _ai_unavailable()

    data = request.get_json(silent=True) or {}
    stage_id = (data.get('stage_id') or '').strip()
    team_id = (data.get('team_id') or '').strip()
    draft_type = (data.get('type') or '').strip()

    stages, teams, tasks = _load_stages_teams_tasks(dir_)
    stage = next((s for s in stages if s.get('stage_id') == stage_id), None) if stage_id else None
    if stage_id and not stage:
        return jsonify(error='阶段不存在'), 404

    # 按阶段名推断类型
    if not draft_type:
        sname = (stage or {}).get('name', '')
        if '申报' in sname:
            draft_type = '申报'
        elif '中期' in sname:
            draft_type = '中期'
        elif '结题' in sname:
            draft_type = '结题'
        elif sname:
            draft_type = '阶段'
        else:
            draft_type = '项目'

    team = next((t for t in teams if t.get('team_id') == team_id), None) if team_id else None

    # 构造上下文
    base_info = '\n'.join([
        '项目名称:{}'.format(meta.get('name', '')),
        '比赛级别:{}'.format(meta.get('level', '')),
        '年份:{}'.format(meta.get('year', '')),
        '使用模板:{}'.format(meta.get('template_name', '')),
    ])
    context_parts = [base_info]
    if stage:
        context_parts.append('阶段:{}(应交材料:{}, 截止:{})'.format(
            stage.get('name', ''),
            '、'.join(stage.get('materials') or []) or '无',
            stage.get('due_date', '') or '未设'))
    if team:
        context_parts.append('团队:{} | 队长:{} | 学号:{} | 成员:{} | 指导老师:{}'.format(
            team.get('name', ''), team.get('leader', ''), team.get('student_id', ''),
            team.get('members', ''), team.get('advisor', '')))
    else:
        context_parts.append('团队数:{}'.format(len(teams)))
    context = '\n'.join(context_parts)

    messages = [
        {'role': 'system', 'content':
         '你是高校科创竞赛汇报书撰写助手。根据提供的项目/阶段/团队信息,撰写一份结构清晰、'
         '内容务实的{}汇报书草稿,使用 Markdown 格式,含标题、项目概况、进展/计划、成果、'
         '问题与对策、下一步等小节。不要编造具体数据,需要补充处用【】标注。'.format(draft_type)},
        {'role': 'user', 'content': context + '\n\n请生成{}汇报书草稿。'.format(draft_type)},
    ]

    try:
        draft = chat(messages, temperature=0.5, max_tokens=2000)
    except AIClientError as e:
        return _ai_error(e)

    return jsonify(draft=draft,
                   stage_name=(stage or {}).get('name', ''),
                   team_name=(team or {}).get('name', ''))


@bp.post('/projects/<pid>/ai/summarize')
@role_required('部长', '副部长', '干事')
def summarize_material(pid):
    """材料内容摘要:读取任务文件文本,AI 生成摘要供审核参考。"""
    meta, dir_ = load_project(pid, request.current_user)
    if not dir_:
        return jsonify(error='项目不存在或无权访问'), 404
    if not is_ai_ready():
        return _ai_unavailable()

    data = request.get_json(silent=True) or {}
    task_id = (data.get('task_id') or '').strip()
    if not task_id:
        return jsonify(error='task_id 必填'), 400

    tasks = read_json('{}/{}/tasks.json'.format(PROJECTS_DIR, dir_), default=[]) or []
    task = next((t for t in tasks if t.get('task_id') == task_id), None)
    if not task:
        return jsonify(error='任务不存在'), 404

    u = request.current_user
    if u.get('role') == '干事' and task.get('assignee_id') != u['id']:
        return jsonify(error='只能查看指派给自己的任务'), 403

    if not task.get('file_path'):
        return jsonify(error='该任务尚未上传文件'), 400

    abs_path = safe_join(DATA_DIR, task['file_path'])
    text, note = extract_text(abs_path)

    teams = read_json('{}/{}/teams.json'.format(PROJECTS_DIR, dir_), default=[]) or []
    team = next((t for t in teams if t.get('team_id') == task.get('team_id')), None)

    if text:
        content_section = text
    else:
        content_section = '(无法提取文件文本内容。{}。请基于文件名与材料类型给出一般性摘要与规范性提示)'.format(
            note or '文件为非文本类型')

    messages = [
        {'role': 'system', 'content':
         '你是材料审核摘要助手。根据提交的材料内容,生成 200 字以内的摘要,'
         '并附带简短的规范性提示(如文件命名、内容完整性)。直接输出摘要与提示,不要寒暄。'},
        {'role': 'user', 'content':
         '材料名称:{}\n所属团队:{}\n文件名:{}\n\n材料内容:\n{}'.format(
             task.get('material', ''), (team or {}).get('name', ''),
             task.get('file_name', ''), content_section)},
    ]

    try:
        summary = chat(messages, temperature=0.2, max_tokens=800)
    except AIClientError as e:
        return _ai_error(e)

    return jsonify(summary=summary, note=note, file_name=task.get('file_name', ''))
