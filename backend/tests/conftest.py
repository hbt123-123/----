# -*- coding: utf-8 -*-
"""pytest 公共 fixture:临时数据目录、Flask app/client、登录会话、测试项目。

测试不依赖真实 agnes.env 与网络,AI 调用通过 monkeypatch mock。
存储重定向到临时目录,避免污染真实 data/。
"""
import os
import json
import pytest


@pytest.fixture
def tmp_data(tmp_path, monkeypatch):
    """临时数据目录,重定向 storage 与 routes.ai 的 DATA_DIR。"""
    import storage
    import routes.ai
    monkeypatch.setattr(storage, 'DATA_DIR', str(tmp_path))
    monkeypatch.setattr(routes.ai, 'DATA_DIR', str(tmp_path))
    return str(tmp_path)


@pytest.fixture
def app(tmp_data):
    from app import create_app
    a = create_app()
    a.config['TESTING'] = True
    return a


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_session(client):
    """以 admin(部长)身份登录(admin 由 ensure_admin 创建)。"""
    with client.session_transaction() as sess:
        sess['uid'] = 'admin'
    return client


@pytest.fixture
def make_user(tmp_data):
    """返回创建用户 helper,写入 users.json 并返回 uid。"""
    import auth

    def _create(role, name, uid=None):
        uid = uid or ('u_' + name)
        users = auth.load_users()
        if not any(u.get('id') == uid for u in users):
            users.append({
                'id': uid, 'name': name, 'role': role, 'student_id': '',
                'contact': '', 'is_admin': False, 'activated': True,
                'password_hash': '', 'created_at': '2026-01-01T00:00:00',
            })
            auth.save_users(users)
        return uid

    return _create


@pytest.fixture
def seed_project(tmp_data):
    """建测试项目:1 阶段/1 团队/2 任务(tk_1 无文件, tk_2 有 txt 文件)。返回 pid。"""
    pid = 'prj_test01'
    dir_ = '测试项目_2026'
    proj_dir = os.path.join(tmp_data, 'projects', dir_)
    os.makedirs(proj_dir, exist_ok=True)

    meta = {
        'id': pid, 'dir': dir_, 'name': '测试项目', 'template_name': '大创项目',
        'year': '2026', 'level': '校级', 'status': '进行中', 'owner_ids': [],
        'created_at': '2026-01-01T00:00:00', 'created_by': 'admin',
    }
    stages = [{
        'stage_id': 'stg_1', 'name': '申报阶段', 'order': 1, 'start_date': '',
        'due_date': '2026-10-31 23:59', 'need_defense': False, 'status': '进行中',
        'materials': ['项目申报书', '诚信承诺书'],
    }]
    teams = [{
        'team_id': 'tm_1', 'name': '绿源科技', 'leader': '张三', 'student_id': '2023001',
        'contact': '138', 'members': '张三、李四', 'advisor': '刘老师', 'remark': '',
    }]

    # tk_2 的上传文件(纯文本)
    upload_rel = 'projects/{}/uploads/申报阶段/绿源科技/诚信承诺书.txt'.format(dir_)
    upload_abs = os.path.join(tmp_data, *upload_rel.split('/'))
    os.makedirs(os.path.dirname(upload_abs), exist_ok=True)
    with open(upload_abs, 'w', encoding='utf-8') as f:
        f.write('本团队承诺所提交材料真实有效,无抄袭。')

    tasks = [
        {'task_id': 'tk_1', 'stage_id': 'stg_1', 'stage_name': '申报阶段', 'team_id': 'tm_1',
         'team_name': '绿源科技', 'material': '项目申报书', 'assignee_id': 'admin',
         'due_date': '2026-10-31 23:59', 'status': '未交', 'file_path': '', 'file_name': '',
         'file_versions': [], 'submitted_at': '', 'reviewed_at': '', 'review_comment': ''},
        {'task_id': 'tk_2', 'stage_id': 'stg_1', 'stage_name': '申报阶段', 'team_id': 'tm_1',
         'team_name': '绿源科技', 'material': '诚信承诺书', 'assignee_id': 'admin',
         'due_date': '2026-10-31 23:59', 'status': '已提交', 'file_path': upload_rel,
         'file_name': '诚信承诺书.txt', 'file_versions': [], 'submitted_at': '2026-01-02T00:00:00',
         'reviewed_at': '', 'review_comment': ''},
    ]
    for name, data in [('meta.json', meta), ('stages.json', stages),
                       ('teams.json', teams), ('tasks.json', tasks)]:
        with open(os.path.join(proj_dir, name), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    with open(os.path.join(tmp_data, 'projects.json'), 'w', encoding='utf-8') as f:
        json.dump([{'id': pid, 'dir': dir_, 'name': '测试项目',
                    'template_id': 'tpl_x', 'year': '2026'}], f, ensure_ascii=False)
    return pid
