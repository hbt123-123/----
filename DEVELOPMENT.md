# 开发进度与架构说明

> 本文档记录平台当前的开发进度、架构现状与关键技术决策。需求见《科创竞赛与社会实践项目管理平台说明书.md》。

## 一、整体进度

### ✅ 已完成阶段

**阶段 0-1:骨架与认证**
- Flask 最小应用 + JSON 原子读写(`storage.py`)+ 健康检查
- Vue3 + Vite + Element Plus 脚手架,登录页,axios 拦截器
- `users.json` 初始化:admin 固定账号(不可删/不可重置)
- 登录页姓名模糊下拉、首次登录设密码激活
- 部长成员管理:增删改、Excel 批量导入、密码重置
- session + 权限装饰器(`login_required`/`role_required`/`admin_required`)
- 权限边界:干事越权访问成员管理 -> 403(已验证)

**阶段 2:模板与项目**
- 比赛模板 CRUD:模板名、阶段清单(名称/截止时间/材料清单/是否答辩)、复制
- 预置 3 个模板:大创项目、挑战杯、寒暑期社会实践
- 项目创建向导:选模板->深拷贝阶段->填基本信息->指派副部长->设各阶段截止时间
- 项目列表、项目详情(meta + 阶段时间线)
- 副部长归属权限:副部长只看/管自己负责的项目,建项目自动成为负责人

**阶段 4(核心):团队与材料任务**
- 团队 CRUD + Excel 批量导入
- 材料任务批量生成(选阶段+团队范围+材料清单->每队每材料一个任务)
- 任务上传:文件存 `uploads/{阶段}/{团队}/{文件名}`,同名归档历史版本
- 审核:通过/打回(填原因),状态流转 未交->已提交->已通过/已打回
- 干事工作台:干事只看指派给自己的任务
- 文件下载(含权限校验)

**材料汇总(用户核心需求)**
- 拖拽文件夹上传(两种模式):选团队拖 / 整包按子文件夹名自动识别团队
- 团队级文件管理:列表、下载、删除
- 自动汇总表:系统按团队×材料生成状态矩阵,预览 + 下载 Excel
- 可编辑汇总工作表:导入 Excel->网页编辑->加自定义列(手动/自动判断)->搜索筛选->保存->下载
  - 自动判断列:按团队名在后台是否有文件,自动填「是/否」(如「是否完成提交」)

**部长驾驶舱(阶段 5)**
- 工作台重构为角色分层驾驶舱,替代原静态欢迎页
- 后端新增 `/api/dashboard` 聚合端点:一次请求返回全部驾驶舱数据,按角色裁剪
- 部长/副部长视图:4 张统计卡(进行中项目/待审核/逾期/临期)+ 项目进度卡片网格(含阶段进度条)+ 人员负荷横条 + 逾期/临期/待审核三列预警
- 干事视图:个人统计卡 + 我的待办任务表(按截止时间排序,逾期高亮)
- 逾期/临期判定在后端用 `datetime.now()` 完成(临期 = 3 天内到期),避免前端时区差异
- 副部长仅看 owner_ids 含自己的项目;干事仅看 assignee_id 含自己的任务
- 不引入图表库,用 el-progress + 纯 CSS 横条完成可视化

**通知提醒(阶段 6)**
- 站内消息: `notifications.json` 持久化,按 user_id 隔离;支持列表/未读数/已读/删除
- 自动提醒: `backend/cli.py remind` 独立入口(零常驻,不在 Flask 进程开线程),由 systemd timer / cron 每 2h 调用一次,扫描全部进行中项目的逾期/临期/待审核任务,向 assignee(owner_ids ∪ 部长)推送
- 手动催办: 驾驶舱三个预警卡片各加「全部催办」按钮(部长/副部长可见),1h 内不可对同一任务重复催办
- 去重: auto 24h / manual 1h 双窗口,dedup key 含 user_id(pending_review 一条任务发多人不漏)
- 复用 `routes/dashboard._classify_task` 判定逾期/临期,不引入新依赖
- 前端:顶栏铃铛 + el-popover 预览(60s 轮询 unread-count,标签后台暂停)+ `/notifications` 通知中心页(全部/未读 tab、点击跳转、删除)
- 文案区分 auto/manual:manual 标题前缀 `[催办]` 并署催办人姓名

**答辩评审(阶段 7)**
- 答辩场次:每项目 `defenses.json`,仅对 `stages.json` 中 `need_defense=True` 的阶段可建场;同阶段仅一场
- 创建场次时自动为项目全部团队生成出场安排(默认按团队顺序),无需手动逐个添加
- 评委:自由填写姓名(可外请非平台用户),el-tag 可增删;不强行绑定 user_id
- 出场顺序:↑/↓ 手动调整 + 「随机抽签」(Fisher-Yates 洗牌)+「按团队名排序」三种方式
- 成绩录入:0-100 分(支持 0.5 步长、1 位小数)+ 评语;干事只读
- 状态流转:待开始 -> 进行中 -> 已完成(部长/副部长手动切换)
- 并入汇总表: `export.py._build_summary` 增加答辩成绩列(列名 `答辩成绩-<阶段名>`),预览表与下载 Excel 均包含
- 前端: `DefensePanel.vue` 嵌入项目详情页(TaskPanel 与 ExportPanel 之间),ExportPanel 预览表新增答辩成绩列展示

**游客只读视图 + 响应式动画打磨(阶段 8)**
- 后端 `routes/public.py` 蓝图(`/api/public`),无需登录:
  - `GET /api/public/projects` — 公开项目列表(脱敏)
  - `GET /api/public/projects/<pid>` — 项目详情(脱敏:meta + 阶段进度 + 答辩场次公开信息)
- 脱敏规则:隐藏 `owner_ids`/`owner_names`/`dir`/`created_by`/团队明细/任务指派人/文件路径/答辩评委姓名与团队成绩;保留项目基本信息、阶段进度统计(done/total)、整体任务统计、答辩场次公开信息(日期/地点/状态/评委数/已答辩团队数)
- 可见性:meta 中 `is_public` 字段缺省视为 `True`(默认公开);后续可在项目编辑中关闭
- 前端:独立 `PublicLayout.vue`(简化顶栏 + 登录入口),`PublicProjects.vue`(项目卡片网格 + 搜索筛选 + Hero 统计),`PublicProjectDetail.vue`(基本信息 + 4 张统计卡 + 阶段时间线 + 答辩公开表 + 登录提示卡)
- 路由:`/public/projects`、`/public/projects/:id`,均标记 `meta.public=true` 绕过登录守卫;登录页底部加「游客浏览 →」入口
- 响应式补强(`styles/main.css`):
  - 平板 768-1023px:主区 padding 16px、表格字号 12px
  - 手机 <768px:表单 label 顶部对齐、时间线左缩、el-tabs 横向滚动、el-card body padding 14px、el-row gutter 收窄、表单控件全宽
  - 超小屏 <420px:表格 11px、el-tag 紧凑、el-card body padding 10px
  - 横屏手机:对话框 96vw
- 动画打磨:
  - el-button hover/active 微位移、el-card transition、el-progress 进度条 0.5s 缓动、el-dialog 弹出动画(dialog-pop keyframes)、el-drawer 0.28s 缓动
  - 路由切换 fade-up(MainLayout 与 PublicLayout 的 `<transition name="fade">` 升级)
  - `.stagger-item` 工具类供列表项 stagger 入场;`el-skeleton__item` 闪动加载
  - 无障碍:`@media (prefers-reduced-motion: reduce)` 一键禁用全部动画

### 🔜 待开发(按优先级)

1. **AI 辅助**(预留):接免费 API(智谱/通义/DeepSeek)做材料完整性检查、汇报书草稿生成

## 二、架构现状

```
浏览器(部长/副部/干事)
    │
    ▼
Vite Dev Server(5173,HMR)──代理──> Flask(127.0.0.1:5000,debug)
                                        ├─ /api/*       REST API
                                        └─ /data/       JSON 文件存储
```

本地开发:前端 Vite(5173)+ 后端 Flask(5000),Vite 代理 `/api`。
生产部署(可选):前端构建到 `backend/static`,Flask 同时托管静态文件与 API,cloudflared tunnel 暴露。

## 三、后端路由清单

| 蓝图 | 前缀 | 主要端点 | 权限 |
|------|------|---------|------|
| auth | /api/auth | candidates/login/logout/me/change-password | 登录相关 |
| users | /api/users | CRUD/import/reset-password | 部长 |
| templates | /api/templates | CRUD/clone | 读:部长+副部;写:部长 |
| projects | /api/projects | list/create/get | 部长+副部(归属过滤) |
| teams | /api/projects/<pid>/teams | CRUD/import | 部长+副部 |
| tasks | /api/projects/<pid>/tasks | generate/list/upload/review/download | 部长+副部+干事(归属) |
| files | /api/projects/<pid>/teams/<tid>/files | 批量上传/list/download/delete | 部长+副部+干事 |
| export | /api/projects/<pid>/export | preview/download | 部长+副部 |
| worksheets | /api/projects/<pid>/worksheet | get/import/save/download | 部长+副部(干事只读) |
| dashboard | /api/dashboard | get(聚合统计) | 部长+副部+干事(按角色裁剪) |
| notifications | /api/notifications | list/unread-count/read/read-all/delete/remind | list 类:登录;remind:部长+副部(归属过滤) |
| defenses | /api/projects/<pid>/defenses | list/create/update/delete | list:部长+副部+干事(干事只读);写:部长+副部(归属过滤) |
| public | /api/public | projects/projects/<pid>(脱敏) | 无需登录(游客只读) |

## 四、关键技术决策

| 决策 | 说明 |
|------|------|
| **无数据库** | JSON 文件存储,一项目一目录沙箱,自包含可 tar 打包归档 |
| **原子写** | `storage.py`:临时文件 + `os.replace` + filelock 软锁,防并发写坏 |
| **版本管理不用 git** | 比赛材料多为二进制,git 管不好且门槛高;改用「同名上传归档历史版本」(`.versions/` 目录 + 时间戳) |
| **路径防穿越** | `utils/paths.py`:目录名清洗非法字符、`safe_join` 校验路径仍在项目目录内、模板 ID 正则白名单 |
| **姓名重名** | users 姓名可重,内部一律用 userId;下拉显示姓名区分 |
| **admin 特殊** | 固定 id='admin',不可删/不可改角色/不可被重置密码 |
| **副部长归属** | 副部长只能访问 owner_ids 含自己的项目;建项目自动加入 owner_ids |
| **干事最小权限** | 只看/上传指派给自己的任务,不能审核、不能生成任务 |
| **AI 暂不接** | 架构预留,核心闭环优先;避免引入网络/密钥依赖 |

## 五、测试验证记录

开发过程中用临时脚本验证后,脚本已删除。已验证的关键链路:

- ✅ 认证全流程:登录/激活/改密/重置/越权 403
- ✅ 模板 CRUD + 副部只读 403 + 路径穿越防护
- ✅ 项目创建 + 文件落地 + 副部归属过滤(403)
- ✅ 团队 CRUD + 导入(重名跳过)
- ✅ 任务生成/上传(版本快照)/审核/下载/干事归属
- ✅ 拖拽批量上传 + 同名归档
- ✅ 工作表导入/自动判断列/导出

> 后续如需正式测试,可建 `backend/tests/` 放 pytest 用例(storage 原子写、权限边界、路径清洗、excel 生成)。

## 六、已知限制

- 前端 Element Plus 全量引入(未按需),bundle 偏大;后续可优化
- 后端 debug=True 仅用于本地开发,生产需用 gunicorn
- 通知仅站内消息,未接邮件/钉钉/微信推送(架构预留)
- 通知无自动清理,长期累积会增大 notifications.json(可后续加 `cli.py cleanup --before 90d`)
- 无自动备份,生产部署时需配 crontab(见 deploy/backup.sh)

## 七、定时任务部署(通知提醒)

通知提醒的自动扫描由独立 CLI 触发,不在 Flask 进程内开线程(零常驻)。生产部署用 systemd timer:

```ini
# /etc/systemd/system/zhansai-remind.timer
[Unit]
Description=Zhansai auto-remind (every 2h)

[Timer]
OnBootSec=5min
OnUnitActiveSec=2h
Unit=zhansai-remind.service

[Install]
WantedBy=timers.target

# /etc/systemd/system/zhansai-remind.service
[Service]
Type=oneshot
User=root
WorkingDirectory=/var/www/zhansai/backend
Environment=ZHANSAI_DATA_DIR=/var/www/zhansai/data
ExecStart=/usr/bin/python3 /var/www/zhansai/backend/cli.py remind
```

启用:`systemctl daemon-reload && systemctl enable --now zhansai-remind.timer`

本地开发手动触发:`cd backend && python cli.py remind`(可加 `--type overdue` / `--dry-run` 调试)。

cron 等价写法(无 systemd 环境):
```
0 */2 * * * cd /var/www/zhansai/backend && ZHANSAI_DATA_DIR=/var/www/zhansai/data /usr/bin/python3 cli.py remind >> /var/log/zhansai-remind.log 2>&1
```
