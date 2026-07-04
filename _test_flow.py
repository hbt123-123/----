# -*- coding: utf-8 -*-
"""临时集成测试:走通 admin 登录→建成员→成员激活→改密→部长重置→重新激活。运行后可删除。"""
import json
import urllib.request as u
import http.cookiejar as ck

BASE = 'http://127.0.0.1:5000/api'


def make_opener():
    return u.build_opener(u.HTTPCookieProcessor(ck.CookieJar()))


def req(opener, path, data=None, method=None):
    url = BASE + path
    if data is None and method is None:
        r = opener.open(url)
    else:
        headers = {}
        body = b''
        if data is not None:
            body = json.dumps(data).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        req_obj = u.Request(url, data=body, headers=headers, method=method or ('POST' if data is not None else 'GET'))
        r = opener.open(req_obj)
    return json.loads(r.read())


admin = make_opener()
# 1. admin 登录
r = req(admin, '/auth/login', {'userId': 'admin', 'password': '12345678'})
print('1) admin 登录:', r['user']['name'], r['user']['role'])

# 2. 创建干事张三
new = req(admin, '/users', {'name': '张三', 'role': '干事', 'student_id': '2021001', 'contact': '13800000000'})
uid = new['user']['id']
print('2) 创建张三: id=%s activated=%s' % (uid, new['user']['activated']))

# 3. 候选列表确认张三未激活
cands = req(admin, '/auth/candidates')['candidates']
zs = next(c for c in cands if c['id'] == uid)
print('3) 候选张三 activated=%s' % zs['activated'])

# 4. 张三首次登录设密码(激活)
zs_opener = make_opener()
r = req(zs_opener, '/auth/login', {'userId': uid, 'password': 'abc123'})
print('4) 激活登录: activated_now=%s activated=%s' % (r.get('activated_now'), r['user']['activated']))

# 5. 张三 me
me = req(zs_opener, '/auth/me')['user']
print('5) 张三 me:', me['name'], me['role'])

# 6. 张三改密
r = req(zs_opener, '/auth/change-password', {'oldPassword': 'abc123', 'newPassword': 'xyz789'})
print('6) 张三改密:', r)

# 7. 张三用新密码重登
zs_opener2 = make_opener()
r = req(zs_opener2, '/auth/login', {'userId': uid, 'password': 'xyz789'})
print('7) 新密码登录:', r['user']['name'], 'activated=', r['user']['activated'])

# 8. 部长重置张三密码(POST,空 body)
r = req(admin, '/users/%s/reset-password' % uid, {})
cands2 = req(admin, '/auth/candidates')['candidates']
zs2 = next(c for c in cands2 if c['id'] == uid)
print('8) 部长重置后 activated=', zs2['activated'])

# 9. 重置后,张三走激活分支重新设密码
zs_opener3 = make_opener()
r = req(zs_opener3, '/auth/login', {'userId': uid, 'password': 'newpass1'})
print('9) 重置后重新激活: activated_now=%s activated=%s' % (r.get('activated_now'), r['user']['activated']))

# 10. 干事张三不能访问成员管理(403)
try:
    r = req(zs_opener3, '/users')
    print('10) 干事访问 /users: 异常,应被拒绝')
except u.HTTPError as e:
    print('10) 干事访问 /users: HTTP %d 符合预期(403)' % e.code)

# 11. 删除张三
r = req(admin, '/users/%s' % uid, method='DELETE')
print('11) 删除张三:', r)

print('\n=== ALL OK ===')
