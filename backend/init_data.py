# -*- coding: utf-8 -*-
"""数据初始化:建目录、创建固定 admin 账号、预置比赛模板。

部署后运行一次:  python init_data.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import ensure_dir, exists, write_json, list_json_files
from auth import ensure_admin
from config import (
    DATA_DIR, PROJECTS_INDEX, TEMPLATES_DIR, PROJECTS_DIR,
)


def _preset_templates():
    """预置 3 个常见比赛模板,便于开局即用。"""
    templates = [
        {
            'id': 'tpl_dachuang',
            'name': '大创项目',
            'stages': [
                {'order': 1, 'name': '申报阶段', 'due_date': '2026-10-31 23:59',
                 'materials': ['项目申报书', '诚信承诺书', '汇总表'], 'need_defense': False},
                {'order': 2, 'name': '中期检查', 'due_date': '2027-03-31 23:59',
                 'materials': ['中期检查报告', '阶段性成果'], 'need_defense': False},
                {'order': 3, 'name': '结题答辩', 'due_date': '2027-06-30 23:59',
                 'materials': ['结题报告', '结题答辩PPT', '成果附件'], 'need_defense': True},
            ],
        },
        {
            'id': 'tpl_tiaozhanbei',
            'name': '挑战杯',
            'stages': [
                {'order': 1, 'name': '院级申报', 'due_date': '2026-11-15 23:59',
                 'materials': ['作品申报书', '汇总表'], 'need_defense': False},
                {'order': 2, 'name': '校级答辩', 'due_date': '2026-12-20 23:59',
                 'materials': ['答辩PPT', '作品说明', '展示视频'], 'need_defense': True},
            ],
        },
        {
            'id': 'tpl_shehuishijian',
            'name': '寒暑期社会实践',
            'stages': [
                {'order': 1, 'name': '立项申报', 'due_date': '2026-07-15 23:59',
                 'materials': ['立项申报书', '安全责任书'], 'need_defense': False},
                {'order': 2, 'name': '实践开展', 'due_date': '2026-08-31 23:59',
                 'materials': ['实践日志', '新闻稿'], 'need_defense': False},
                {'order': 3, 'name': '总结评比', 'due_date': '2026-09-20 23:59',
                 'materials': ['总结报告', '调研报告', '答辩PPT'], 'need_defense': True},
            ],
        },
    ]
    for t in templates:
        path = '{}/{}.json'.format(TEMPLATES_DIR, t['id'])
        if not exists(path):
            write_json(path, t)
    return [t['name'] for t in templates]


def init():
    ensure_dir('')
    ensure_dir(TEMPLATES_DIR)
    ensure_dir(PROJECTS_DIR)
    if not exists(PROJECTS_INDEX):
        write_json(PROJECTS_INDEX, [])

    admin = ensure_admin()
    tpls = _preset_templates()

    print('=' * 50)
    print('数据目录      :', DATA_DIR)
    print('管理员账号    :', admin['id'], '(初始密码: 12345678)')
    print('预置模板      :', '、'.join(tpls))
    print('已有模板文件  :', len(list_json_files(TEMPLATES_DIR)))
    print('初始化完成。')
    print('=' * 50)


if __name__ == '__main__':
    init()
