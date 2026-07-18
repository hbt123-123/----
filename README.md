# 创实部信息化管理平台

> 中南民族大学资源与环境学院团委学生会创新实践部 · 科创竞赛与社会实践项目管理平台

一个轻量级的竞赛/实践项目材料管理平台,用于管理比赛项目全流程(申报-中期-结题)的材料收集、审核与汇总。**无数据库**,采用 JSON 文件存储,一项目一目录沙箱,部署简单、内存占用低。

## 功能概览

### ✅ 已完成

| 模块 | 说明 |
|------|------|
| **认证与账号** | 姓名模糊下拉登录、首次登录设密码激活、部长重置密码、修改密码 |
| **成员管理** | 增删改、Excel 批量导入、角色分配(部长/副部长/干事) |
| **比赛模板** | 增删改、复制;阶段清单(名称/截止时间/答辩/材料清单) |
| **项目管理** | 三步创建向导(选模板->填信息->设阶段时间)、列表、详情 |
| **参赛团队** | 增删改、Excel 批量导入 |
| **材料文件上传** | 拖拽文件夹批量上传,两种模式(选团队拖 / 整包按子文件夹识别),同名归档历史版本 |
| **材料任务矩阵** | 批量生成任务、上传、副部审核(通过/打回)、下载 |
| **汇总表(自动)** | 系统自动生成团队×材料状态矩阵,一键下载 Excel |
| **汇总工作表(可编辑)** | 导入 Excel->网页编辑->加自定义列(含自动判断列)->搜索筛选->下载 |
| **权限边界** | 干事只看自己任务、副部长管负责项目、部长全权 |

### 🔜 待开发

- 部长驾驶舱(项目进度/逾期预警/人员负荷总览)
- 站内消息通知与提醒
- 答辩评审
- 游客只读视图
- 响应式与动画打磨
- AI 辅助(材料完整性检查/汇报书草稿,预留接口)

## 技术栈

- **后端**:Python 3 + Flask 3 + openpyxl + filelock(JSON 原子写、文件锁)
- **前端**:Vue 3 + Vite 5 + Element Plus + Pinia + Vue Router + axios
- **存储**:文件系统 JSON(无数据库),一项目一目录沙箱
- **认证**:Flask session(签名 cookie)+ werkzeug 密码哈希

## 本地开发

### 环境要求

- Python 3.10+
- Node.js 18+

### 启动

```bash
# 1. 安装后端依赖
cd backend
pip install -r requirements.txt

# 2. 初始化数据(建 admin 账号 + 预置模板)
python init_data.py

# 3. 启动后端(默认 127.0.0.1:5000,debug 模式自动重载)
python app.py

# 4. 另开终端,启动前端(默认 127.0.0.1:5173,热更新)
cd frontend
npm install
npm run dev
```

打开 http://127.0.0.1:5173 ,姓名下拉选「管理员」,密码 `12345678`。

> 后端 `debug=True` 改代码自动重载;前端 Vite HMR 即时更新。
> **注意**:若新增/修改后端蓝图或路由后请求返回 405,可能是 reloader 没生效,重启后端进程即可。

## 目录结构

```
资环创实/
  科创竞赛与社会实践项目管理平台说明书.md   # 需求文档(只读)
  DEVELOPMENT.md                            # 开发进度与架构现状
  README.md                                 # 本文件
  backend/
    app.py                  # Flask 入口,注册蓝图,SPA 托管
    config.py               # 配置(路径/密钥/限制)
    storage.py              # JSON 原子读写 + 文件锁
    auth.py                 # 哈希/session/激活/admin
    guards.py               # 权限装饰器
    init_data.py            # 初始化数据(admin + 模板)
    requirements.txt
    routes/                 # 各业务路由
      auth users templates projects teams tasks files export worksheets
    utils/
      paths.py              # 目录名清洗、防路径穿越
      upload.py             # 文件保存 + 历史版本归档
  frontend/
    src/
      api/                  # axios 封装的接口模块
      components/           # 团队/文件/任务/汇总/工作表面板
      views/                # 登录/工作台/成员/模板/项目/详情/个人中心
      layouts/ stores/ router/
    vite.config.js          # 构建到 ../backend/static,代理 /api
  data/                     # 运行数据(不入库,init_data 生成)
    users.json              # 账号
    projects.json           # 项目索引
    templates/              # 比赛模板
    projects/{项目目录}/    # 一项目一目录(meta/stages/teams/tasks/worksheet + uploads/ + exports/)
  deploy/                   # 部署脚本(可选,本地开发不需要)
```

## 数据存储

一项目一目录沙箱,自包含、可直接打包归档:

```
data/projects/{项目名}_{年份}/
  meta.json          项目基本信息
  stages.json        阶段(含截止时间、材料清单)
  teams.json         参赛团队
  tasks.json         材料任务(含审核状态)
  worksheet.json     可编辑汇总工作表
  uploads/{团队名}/{文件名}            拖拽上传的文件
                     /.versions/        历史版本(同名再次上传时归档)
  uploads/{阶段名}/{团队名}/{文件名}   任务上传的文件
  exports/汇总表.xlsx、工作表.xlsx     导出的 Excel
```

## 部署(可选)

本地开发无需部署。如需上线,见 [`deploy/README.md`](deploy/README.md)(Flask + systemd + Cloudflare Tunnel,无数据库)。
