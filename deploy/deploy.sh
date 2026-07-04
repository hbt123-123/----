#!/usr/bin/env bash
# 一键部署:本地构建前端 → 打包上传 → 服务器 venv 装依赖 → 初始化 → 启动 systemd
# 用法:在项目根目录执行  bash deploy/deploy.sh
set -euo pipefail

REMOTE=root@8.130.23.56
REMOTE_DIR=/var/www/zhansai
PROJ_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "[1/6] 构建前端(产物输出到 backend/static)..."
cd "$PROJ_ROOT/frontend"
npm install
npm run build
cd "$PROJ_ROOT"

echo "[2/6] 打包后端与部署文件(排除 data/venv/__pycache__)..."
tar -czf /tmp/zhansai_backend.tar.gz \
  --exclude='backend/data' \
  --exclude='backend/venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  -C "$PROJ_ROOT" backend deploy

echo "[3/6] 上传到服务器..."
ssh "$REMOTE" "mkdir -p $REMOTE_DIR"
scp /tmp/zhansai_backend.tar.gz "$REMOTE:/tmp/"

echo "[4/6] 服务器:解压 + 创建 venv + 安装 Python 依赖..."
ssh "$REMOTE" bash -s <<'REMOTE_EOF'
set -euo pipefail
cd /var/www/zhansai
tar -xzf /tmp/zhansai_backend.tar.gz
# 确保 venv 可用(Ubuntu 24.04 需 python3.12-venv 提供 ensurepip)
if [ ! -x venv/bin/pip ]; then
  rm -rf venv
  if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
    apt-get update
    apt-get install -y python3.12-venv python3-full
  fi
  python3 -m venv venv
fi
# 生成 .env(仅首次),包含随机 SECRET_KEY 与数据目录
if [ ! -f backend/.env ]; then
  KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
  {
    echo "ZHANSAI_SECRET_KEY=$KEY"
    echo "ZHANSAI_DATA_DIR=/var/www/zhansai/data"
  } > backend/.env
  echo "已生成 backend/.env(含随机密钥)"
fi
venv/bin/pip install --upgrade pip -q
venv/bin/pip install -r backend/requirements.txt
REMOTE_EOF

echo "[5/6] 服务器:初始化数据(幂等,不覆盖已有 admin 密码)..."
ssh "$REMOTE" "cd $REMOTE_DIR/backend && ZHANSAI_DATA_DIR=$REMOTE_DIR/data /var/www/zhansai/venv/bin/python init_data.py"

echo "[6/6] 服务器:安装 systemd 服务并启动..."
ssh "$REMOTE" bash -s <<'REMOTE_EOF'
set -euo pipefail
cp /var/www/zhansai/deploy/zhansai.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable zhansai
systemctl restart zhansai
sleep 2
systemctl status zhansai --no-pager | head -15
echo "--- health check ---"
curl -s http://127.0.0.1:5000/api/health
echo
REMOTE_EOF

echo ""
echo "部署完成。"
echo "下一步:在 Cloudflare Zero Trust 控制台为现有 tunnel 添加 public hostname"
echo "  Service: HTTP → localhost:5000,详见 deploy/README.md"
