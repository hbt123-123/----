# 部署指南

本平台采用 **Flask(后端 + 静态托管)+ Cloudflare Tunnel** 架构,无数据库,内存占用 < 80MB。

## 服务器目标

| 项 | 值 |
|----|----|
| 公网 IP | 8.130.23.56 |
| 系统 | Ubuntu 24.04.2 LTS |
| Python | 3.12.3 |
| 部署目录 | `/var/www/zhansai` |
| 监听 | `127.0.0.1:5000`(仅本地,由 tunnel 暴露) |
| 进程管理 | systemd(`zhansai.service`) |
| 暴露 | 现有 cloudflared tunnel(token 模式) |

## 一、一键部署(在本地项目根目录执行)

```bash
bash deploy/deploy.sh
```

脚本会自动完成:构建前端 → 打包上传 → 安装依赖 → 初始化数据 → 启动 systemd。

> 部署脚本首次会在服务器生成 `backend/.env`(含随机 `SECRET_KEY`),后续部署不会覆盖。

## 二、配置 Cloudflare Tunnel(暴露服务)

服务器上 cloudflared 已以 **token 模式**运行,tunnel 路由在 Cloudflare 控制台配置(非本地文件)。

1. 登录 [Cloudflare Zero Trust](https://one.dash.cloudflare.com)
2. 左侧 **Networks → Tunnels**
3. 找到现有 tunnel(2026-07-03 创建),点击 **Configure(配置)**
4. 进入 **Public Hostname** 标签 → **Add a public hostname**
5. 填写:
   - **Subdomain**: `zhansai`(或任意你喜欢的子域名)
   - **Domain**: 选择你的域名
   - **Path**: 留空
   - **Service**: Type = `HTTP`,URL = `localhost:5000`
6. **Save**

配置后约 10-30 秒生效,访问 `https://zhansai.你的域名` 即可看到登录页(自带 HTTPS)。

## 三、首次登录

- 在登录页姓名下拉选择 **管理员(admin)**,初始密码 `12345678`
- 登录后到「个人中心」修改密码
- 到「成员管理」创建副部长、干事账号(或批量导入)
- 新成员首次登录时,从下拉选择自己姓名并设置密码完成激活

## 四、批量导入成员格式

Excel(xlsx)表头:`姓名 | 学号 | 角色 | 联系方式`,从第二行起填写。角色可选 `部长/副部长/干事`,留空默认 `干事`。

## 五、备份

已内置每日备份脚本,加入 crontab 即可:

```bash
ssh root@8.130.23.56 'crontab -l 2>/dev/null; echo "0 3 * * * /var/www/zhansai/deploy/backup.sh >> /var/log/zhansai-backup.log 2>&1"' | ssh root@8.130.23.56 'crontab -'
```

备份包存放 `/backup/zhansai/data-YYYYMMDD_HHMMSS.tar.gz`,保留 14 天。

## 六、项目整目录导出(归档/移交)

任一项目目录自包含,可直接打包:

```bash
ssh root@8.130.23.56 'tar -czf /tmp/大创项目_2026.tar.gz -C /var/www/zhansai/data/projects 大创项目_2026'
```

## 七、常用运维命令

```bash
ssh root@8.130.23.56 'systemctl status zhansai'          # 查看状态
ssh root@8.130.23.56 'systemctl restart zhansai'         # 重启
ssh root@8.130.23.56 'journalctl -u zhansai -f'          # 实时日志
ssh root@8.130.23.56 'curl -s http://127.0.0.1:5000/api/health'  # 健康检查
```

## 八、目录结构(服务器)

```
/var/www/zhansai/
  backend/            应用代码 + static/(前端构建产物)+ .env
  deploy/             zhansai.service / deploy.sh / backup.sh
  data/               JSON 数据(一项目一目录沙箱)+ users.json + projects.json + templates/
```
