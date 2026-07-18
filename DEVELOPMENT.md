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

### 🔜 待开发(按优先级)

1. **部长驾驶舱**:项目进度卡片、逾期预警高亮、人员负荷视图、批量催办
2. **通知提醒**:站内消息、逾期/临期提醒(systemd timer + flask CLI,零常驻)
3. **答辩评审**:答辩安排、评委、顺序、成绩录入,并入汇总表
4. **游客只读视图**:未登录可浏览公开项目(脱敏)
5. **响应式与动画打磨**:平板/手机适配、过渡动画
6. **AI 辅助**(预留):接免费 API(智谱/通义/DeepSeek)做材料完整性检查、汇报书草稿生成

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
- 暂无定时任务(逾期提醒),待阶段 6 用 systemd timer 实现
- 无自动备份,生产部署时需配 crontab(见 deploy/backup.sh)
