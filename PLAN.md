# 科创竞赛与社会实践项目管理平台 — 实现计划

## 一、架构总览

```
浏览器(部长/副部/干事/游客)
        │ HTTPS
        ▼
Cloudflare 域名(用户已有,如 zhansai.xxx.com)
        │ cloudflared tunnel(已运行,token 模式)
        ▼
Flask 应用(127.0.0.1:5000,gunicorn 托管)
  ├─ /            → 托管 Vue 构建产物 dist/(静态文件)
  ├─ /api/*       → REST API(认证/业务/文件/导出)
  └─ /data/       → JSON 文件存储(一项目一目录沙箱)
```

**单进程、单端口**:Flask 同时托管前端静态文件与后端 API,部署最简,无需 Nginx。cloudflared 把域名映射到 `localhost:5000`,自带 HTTPS,无需开放额外端口。

## 二、技术栈(已确认)

| 层 | 选型 | 说明 |
|----|------|------|
| 后端 | Python 3.12 + Flask 3 + gunicorn | 常驻约 40-60MB |
| xlsx | openpyxl | 汇总表生成与批量导入解析 |
| 认证 | Flask session(签名 cookie)+ werkzeug 密码哈希 | 无需 Redis |
| 前端 | Vue 3 + Vite 5 + Element Plus + Pinia + Vue Router + axios | 中后台组件齐全 |
| 动画 | @vueuse/motion + Element Plus 内置过渡 | 满足"动画过渡自然" |
| 进程管理 | systemd(主)+ pm2 备选 | 与现有 gamehub 一致 |
| 暴露 | 现有 cloudflared tunnel | 自带 HTTPS |
| 存储 | 文件系统 JSON(无数据库) | 按需求第五部分 |

## 三、本地项目结构

```
E:\project\资环创实\
  科创竞赛与社会实践项目管理平台说明书.md
  backend/
    app.py                  # Flask 入口、注册蓝图、托管 dist/
    config.py               # 路径常量、密钥、超时
    requirements.txt        # flask, gunicorn, openpyxl, werkzeug
    storage.py              # JSON 原子读写(临时文件+os.replace)、文件锁
    auth.py                 # 哈希、session、激活令牌
    guards.py               # 权限装饰器(login/role/项目归属/任务归属)
    utils/excel.py          # openpyxl 生成与解析
    utils/importers.py      # 人员/团队批量导入
    utils/paths.py          # 目录名清洗、防路径穿越
    routes/
      auth.py  users.py  templates.py  projects.py  stages.py
      teams.py  tasks.py  review.py  export.py  notify.py  defense.py
    tests/                  # pytest 核心逻辑测试
  frontend/
    package.json  vite.config.js  index.html
    src/
      main.js  App.vue  router/index.js  stores/auth.js  api/index.js
      views/   # Login, Activate, Dashboard, Projects, ProjectDetail,
               # Templates, Members, Teams, Tasks(MyTasks), Review,
               # Export, Defense, Profile...
      components/
    dist/                   # 构建产物(部署时拷到 backend/static)
  deploy/
    zhansai.service         # systemd unit
    deploy.sh               # 一键部署脚本
    init_data.py            # 初始化 data 目录与 admin 账号
    backup.sh               # crontab 备份脚本
```

## 四、数据存储设计(沿用需求第五部分)

根目录 `/var/www/zhansai/data`,结构与需求文档完全一致:

```
/data
  /templates/{模板ID}.json
  /users.json
  /projects.json
  /projects/{项目目录名}/
     meta.json  stages.json  teams.json  tasks.json
     /uploads/{阶段名}/{团队名}/{文件名}
     /exports/{汇总表}.xlsx
  /notifications.json       # 站内消息(全局,按 userId 索引)
```

**关键字段补充**(`tasks.json` 增 `submitted_at/Reviewed_at/review_comment`;`users.json` 增 `activated/password_hash/is_admin`)。目录名按需求规则清洗非法字符、重名追加序号。

## 五、分阶段实现步骤

### 阶段 0:骨架与部署底座(先跑通空壳)
- 后端:Flask 最小应用 + `storage.py` 原子读写 + 健康检查 `/api/health`
- 前端:Vite + Vue + Element Plus 脚手架,登录页空壳,axios 拦截器
- 部署:gunicorn + systemd + cloudflared tunnel 路由(指导用户在 Zero Trust 控制台加 public hostname → `http://localhost:5000`)
- 产出:浏览器能打开域名,看到登录页,`/api/health` 通

### 阶段 1:认证与账号体系(需求 4.1.3)
- `users.json` 初始化:admin 固定账号(`is_admin=true`,姓名"管理员",初始密码 `12345678` 哈希存储,不可删/不可被他人重置)
- 登录页:姓名模糊匹配下拉(拉取已激活成员 + admin),选中后输密码;**未激活**成员选中后显示"设置密码"框,激活后登录
- 激活流程:部长预设姓名(无密码,`activated=false`)→ 成员首次登录从名单选自己 → 设密码 → `activated=true`
- 部长后台:创建/编辑成员、批量导入、密码重置(格式化)、角色分配
- session + 权限装饰器:`@login_required` / `@role_required` / `@project_owner_required` / `@task_owner_required`
- 前端:登录、激活、个人中心(改密)、成员管理页

### 阶段 2:基础数据(需求 4.1.1、4.2.1 模板与项目创建)
- 比赛模板 CRUD:模板名、阶段清单(顺序/建议时长/材料清单/是否答辩);复制、停用
- 预置 2-3 个内置模板(大创、挑战杯、社会实践)便于开局
- 项目创建:选模板 → 继承阶段与材料清单 → 填基本信息(名称/级别/年份/通知附件)→ 指派 1-2 名副部长 → 设各阶段起止时间(可覆盖默认)
- 前端:模板管理页、项目创建向导

### 阶段 3:项目总览与详情(需求 4.2.2、4.2.3)
- 部长驾驶舱:项目卡片(名称/当前阶段/进度=已完成任务/总任务/负责人)、逾期预警高亮、人员负荷视图(副部项目数、干事任务数)
- 项目详情:阶段/团队/任务矩阵总览,按阶段/团队/干事筛选
- 手动催办入口(生成站内消息)
- 前端:Dashboard、ProjectDetail(含筛选、Tab 切换)

### 阶段 4:团队与阶段任务(需求 4.3、4.4 — 核心)
- 团队 CRUD + Excel 批量导入 + 阶段间名单同步(可增删)
- 阶段控制:状态(未开始/进行中/已完成)、手动切换(校验任务完成度)、"启动下一阶段"(可选自动生成任务草案、复用名单)
- 材料任务批量生成:选阶段+团队范围+材料清单 → 每队每项生成一个任务
- 任务指派:单条指派 + 批量指派(如所有"申报书"→ 干事A)
- 干事工作台:"我的任务"按截止时间排序,逾期红色标注;上传文件后"待提交→已提交"+备注;任务历史
- 文件上传:`multipart` → 存 `uploads/{阶段名}/{团队名}/{原文件名}`,路径校验防穿越
- 前端:Teams、Stages、TaskAssign、MyTasks(干事首页)、文件上传组件

### 阶段 5:审核与汇总(需求 4.5)
- 副部审核视图:按阶段/干事/状态筛选,预览下载文件,通过→"已审核",打回→"待提交"+原因;批量审核
- 一键汇总表:openpyxl 按学校格式生成(序号/团队/队长/成员/联系方式/各材料状态/审核备注),预览+下载 .xlsx,存 `exports/`
- 报送管理:标记阶段"已报送"+上传盖章扫描件;项目整体进度自动更新
- 前端:Review、Export(预览表格)、报送标记

### 阶段 6:通知提醒与扩展(需求 4.6、4.7)
- 站内消息:`notifications.json`,干事提交→副部收到通知;逾期/临期→干事收到提醒
- 自动提醒:systemd timer 每日跑 `flask check-overdue` 命令扫描临期/逾期任务生成消息(零常驻内存,优于 APScheduler)
- 部长批量催办:对某项目/阶段所有逾期任务一键催办
- 答辩评审(扩展):创建答辩安排(时间/地点/评委)、分配顺序、录入成绩/等级/是否通过,可并入汇总表或单独导出
- (可选)飞书/钉钉 webhook 推送:配置后转发站内消息

### 阶段 7:游客只读视图(需求 二·游客)
- 未登录可浏览公开项目/阶段/材料提交状态(不含敏感字段如学号、联系方式)
- 全站只读,无新增/改/删/上传入口;API 层 `@readonly_public` 守卫

### 阶段 8:打磨与上线
- 响应式适配(桌面/平板/手机),Element Plus 栅格 + 断点
- 动画:路由切换、列表增删、状态变更过渡
- 数据备份:crontab 每日 `tar -czf /backup/data-$(date).tar.gz /var/www/zhansai/data`,保留 14 天
- 一键导出项目:`tar` 打包整个项目目录
- 初始化脚本:建 admin、预置模板、建 data 目录
- pytest 核心测试:storage 原子写、权限边界、excel 生成、路径清洗

## 六、关键技术难点与对策

| 难点 | 对策 |
|------|------|
| JSON 并发写坏数据 | `storage.py`:写临时文件 → `os.replace` 原子重命名;按项目文件加 `fcntl` 文件锁;全局写串行 |
| 路径穿越攻击 | `utils/paths.py`:清洗阶段名/团队名非法字符,校验解析后路径仍在项目 uploads 目录内 |
| 姓名重名登录混淆 | users 姓名可重,但下拉显示"姓名(学号后4位)"区分;内部一律用 userId |
| admin 既是用户名又是姓名的矛盾 | users.json 中 admin 记录 `name="管理员"`、`username="admin"`、`is_admin=true`;登录下拉含此条,显示"管理员(admin)" |
| 定时提醒零额外内存 | 用 systemd timer + flask CLI 命令,不引入 APScheduler 常驻线程 |
| 前端构建产物与 API 同源 | Vite `build.outDir = ../backend/static`,`base='./'`;Flask 用 `static_folder` 托管,`/api` 之外路由 fallback 到 `index.html`(SPA history 模式) |
| 13-15 人低并发 | gunicorn 2 worker + 4 thread 足够,内存 < 80MB |

## 七、部署清单

1. 本地:`cd frontend && npm run build` → 产物落 `backend/static/`
2. 上传 `backend/` 到 `/var/www/zhansai/backend/`(scp/rsync)
3. 服务器:`pip3 install -r requirements.txt`(建议 venv)
4. `python3 init_data.py` 初始化 data 目录、admin 账号、预置模板
5. 装 gunicorn,写 `/etc/systemd/system/zhansai.service`,`systemctl enable --now zhansai`
6. cloudflared tunnel:用户在 Cloudflare Zero Trust → Tunnels → 现有 tunnel → Public Hostname → 新增 `子域名.你的域名 → http://localhost:5000`(我会给截图级步骤)
7. crontab 加每日备份
8. 验证:访问域名 → 登录页 → admin/12345678 登录 → 创建模板 → 建项目

## 八、测试与验收
- pytest:storage 原子写、权限装饰器边界、excel 生成、路径清洗、批量导入解析
- 手测脚本:admin 登录→建成员→成员激活→建模板→建项目→指派任务→干事上传→副部审核→导出汇总表→报送,全链路走通
- 响应式:Chrome DevTools 三档断点回归
- 权限边界:干事越权访问他人任务/副部越权访问非负责项目 → 403

## 九、不在本期范围(后续扩展)
- 费用收集、人员统计独立模块(需求 1.3 提及,可复用任务模型扩展)
- 对象存储备份(先本地 tar,后续可接 OSS)
- 参赛学生直传表单(需求 4.4.3 注,本期以干事代收为主)
