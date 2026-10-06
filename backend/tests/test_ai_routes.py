# -*- coding: utf-8 -*-
"""AI 路由集成测试:权限边界、配置缺失、正常返回、错误处理。

所有 AI 调用均 mock,不触达真实 Agnes API,不消耗额度。
"""
import pytest
from ai_client import AIClientError

PID = 'prj_test01'


def _chat_json(messages, **kw):
    return ('{"teams":[{"team_id":"tm_1","team_name":"绿源科技",'
            '"missing":["诚信承诺书"],"irregular":[],"suggestions":"请尽快补交"}],'
            '"overall":"整体良好"}')


def _chat_text(messages, **kw):
    return '检查结果:绿源科技缺失诚信承诺书,请补交。'


def _chat_draft(messages, **kw):
    return '# 申报书草稿\n## 项目概况\n本项目由绿源科技团队开展。'


def _chat_summary(messages, **kw):
    return '摘要:本团队承诺材料真实有效,无抄袭行为。'


# ---------- 权限:未登录 → 401 ----------
def test_check_requires_login(client, seed_project):
    r = client.post('/api/projects/{}/ai/check'.format(PID), json={})
    assert r.status_code == 401


def test_draft_requires_login(client, seed_project):
    r = client.post('/api/projects/{}/ai/draft'.format(PID), json={})
    assert r.status_code == 401


def test_summarize_requires_login(client, seed_project):
    r = client.post('/api/projects/{}/ai/summarize'.format(PID), json={})
    assert r.status_code == 401


# ---------- 副部长非归属 → 404 ----------
def test_check_non_owner_404(client, seed_project, make_user):
    uid = make_user('副部长', '副甲')  # owner_ids=[] 不含副甲
    with client.session_transaction() as sess:
        sess['uid'] = uid
    r = client.post('/api/projects/{}/ai/check'.format(PID), json={})
    assert r.status_code == 404


# ---------- AI 未配置 → 503 ----------
def test_check_ai_unconfigured(admin_session, seed_project, monkeypatch):
    monkeypatch.setattr('routes.ai.is_ai_ready', lambda: False)
    r = admin_session.post('/api/projects/{}/ai/check'.format(PID), json={})
    assert r.status_code == 503


# ---------- 正常:check(AI 返回 JSON) ----------
def test_check_ok_json(admin_session, seed_project, monkeypatch):
    monkeypatch.setattr('routes.ai.is_ai_ready', lambda: True)
    monkeypatch.setattr('routes.ai.chat', _chat_json)
    r = admin_session.post('/api/projects/{}/ai/check'.format(PID), json={})
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data['result'], dict)
    assert data['result']['teams'][0]['team_name'] == '绿源科技'
    assert '诚信承诺书' in data['result']['teams'][0]['missing']


# ---------- 正常:check(AI 返回非 JSON → result=None, 原样 raw) ----------
def test_check_ok_text(admin_session, seed_project, monkeypatch):
    monkeypatch.setattr('routes.ai.is_ai_ready', lambda: True)
    monkeypatch.setattr('routes.ai.chat', _chat_text)
    r = admin_session.post('/api/projects/{}/ai/check'.format(PID), json={})
    assert r.status_code == 200
    data = r.get_json()
    # 非 JSON 时 result 原样返回文本(等于 raw)
    assert data['result'] == data['raw']
    assert '绿源科技' in data['result']


# ---------- 正常:draft ----------
def test_draft_ok(admin_session, seed_project, monkeypatch):
    monkeypatch.setattr('routes.ai.is_ai_ready', lambda: True)
    monkeypatch.setattr('routes.ai.chat', _chat_draft)
    r = admin_session.post('/api/projects/{}/ai/draft'.format(PID),
                           json={'stage_id': 'stg_1'})
    assert r.status_code == 200
    data = r.get_json()
    assert '草稿' in data['draft']
    assert data['stage_name'] == '申报阶段'


# ---------- summarize:任务无文件 → 400 ----------
def test_summarize_no_file(admin_session, seed_project, monkeypatch):
    monkeypatch.setattr('routes.ai.is_ai_ready', lambda: True)
    r = admin_session.post('/api/projects/{}/ai/summarize'.format(PID),
                           json={'task_id': 'tk_1'})
    assert r.status_code == 400


# ---------- 正常:summarize ----------
def test_summarize_ok(admin_session, seed_project, monkeypatch):
    monkeypatch.setattr('routes.ai.is_ai_ready', lambda: True)
    monkeypatch.setattr('routes.ai.chat', _chat_summary)
    r = admin_session.post('/api/projects/{}/ai/summarize'.format(PID),
                           json={'task_id': 'tk_2'})
    assert r.status_code == 200
    data = r.get_json()
    assert '承诺' in data['summary']
    assert data['file_name'] == '诚信承诺书.txt'


# ---------- summarize:干事访问他人任务 → 403 ----------
def test_summarize_officer_other_task(client, seed_project, make_user, monkeypatch):
    uid = make_user('干事', '干甲')
    with client.session_transaction() as sess:
        sess['uid'] = uid
    monkeypatch.setattr('routes.ai.is_ai_ready', lambda: True)
    # tk_2 的 assignee_id='admin',干甲无权
    r = client.post('/api/projects/{}/ai/summarize'.format(PID),
                    json={'task_id': 'tk_2'})
    assert r.status_code == 403


# ---------- summarize:任务不存在 → 404 ----------
def test_summarize_task_not_found(admin_session, seed_project, monkeypatch):
    monkeypatch.setattr('routes.ai.is_ai_ready', lambda: True)
    r = admin_session.post('/api/projects/{}/ai/summarize'.format(PID),
                           json={'task_id': 'tk_nope'})
    assert r.status_code == 404


# ---------- AI 调用失败 → 502 ----------
def test_check_ai_failure(admin_session, seed_project, monkeypatch):
    monkeypatch.setattr('routes.ai.is_ai_ready', lambda: True)

    def boom(messages, **kw):
        raise AIClientError('AI 服务异常', status_code=502)

    monkeypatch.setattr('routes.ai.chat', boom)
    r = admin_session.post('/api/projects/{}/ai/check'.format(PID), json={})
    assert r.status_code == 502


# ---------- check:范围无团队 → 400 ----------
def test_check_no_team(admin_session, seed_project, monkeypatch):
    monkeypatch.setattr('routes.ai.is_ai_ready', lambda: True)
    r = admin_session.post('/api/projects/{}/ai/check'.format(PID),
                           json={'team_id': 'tm_nope'})
    assert r.status_code == 400
