# -*- coding: utf-8 -*-
"""临时验证脚本:阶段 2.1 模板接口。验证后删除。"""
import requests

BASE = 'http://127.0.0.1:5000'
ok = True


def check(name, cond, detail=''):
    global ok
    flag = 'PASS' if cond else 'FAIL'
    if not cond:
        ok = False
    print('[{}] {} {}'.format(flag, name, detail))


def main():
    admin = requests.Session()
    r = admin.post(f'{BASE}/api/auth/login',
                   json={'userId': 'admin', 'password': '12345678'})
    check('admin 登录', r.status_code == 200, r.json().get('user', {}).get('name', ''))

    # 1. 部长视角:模板列表
    r = admin.get(f'{BASE}/api/templates')
    tpls = r.json().get('templates', [])
    check('部长可读模板列表', r.status_code == 200 and len(tpls) == 3,
          f'返回 {len(tpls)} 个')
    for t in tpls:
        print('     · {} — {} 阶段'.format(t['name'], len(t['stages'])))

    # 2. 模板详情
    r = admin.get(f'{BASE}/api/templates/tpl_dachuang')
    check('模板详情', r.status_code == 200 and
          r.json().get('template', {}).get('id') == 'tpl_dachuang')

    # 3. 路径穿越防护(传 .. 应被正则挡掉)
    r = admin.get(f'{BASE}/api/templates/..')
    check('路径穿越被挡', r.status_code == 404, str(r.json()))

    # 4. 建临时干事,验证 403
    r = admin.post(f'{BASE}/api/users',
                   json={'name': '临时测试干事', 'role': '干事'})
    uid = r.json()['user']['id']
    officer = requests.Session()
    r = officer.post(f'{BASE}/api/auth/login',
                     json={'userId': uid, 'password': 'temp123456'})
    check('干事激活登录', r.status_code == 200)
    r = officer.get(f'{BASE}/api/templates')
    check('干事访问模板 403', r.status_code == 403, str(r.json()))

    # 5. 副部长视角:应 200
    r = admin.post(f'{BASE}/api/users',
                   json={'name': '临时副部', 'role': '副部长'})
    vid = r.json()['user']['id']
    vice = requests.Session()
    vice.post(f'{BASE}/api/auth/login',
              json={'userId': vid, 'password': 'temp123456'})
    r = vice.get(f'{BASE}/api/templates')
    check('副部长可读模板', r.status_code == 200, f'{len(r.json().get("templates", []))} 个')

    # 6. 未登录 401
    r = requests.get(f'{BASE}/api/templates')
    check('未登录 401', r.status_code == 401, str(r.json()))

    # 清理临时账号
    admin.delete(f'{BASE}/api/users/{uid}')
    admin.delete(f'{BASE}/api/users/{vid}')
    admin.post(f'{BASE}/api/auth/logout')

    print('\n结果: {}'.format('全部通过 ✅' if ok else '存在失败 ❌'))


if __name__ == '__main__':
    main()
