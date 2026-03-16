#!/bin/bash
# 阿里云服务器一键初始化脚本
# 适用系统: Ubuntu 22.04
# 使用方法: bash setup.sh

set -e

echo "=== 1. 更新系统 ==="
apt update && apt upgrade -y

echo "=== 2. 安装 Docker ==="
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

echo "=== 3. 安装 Docker Compose ==="
apt install -y docker-compose-plugin

echo "=== 4. 安装 git ==="
apt install -y git

echo "=== 5. 克隆项目 ==="
cd /opt
git clone https://github.com/wuhar14-bot/hotel-inspection.git
cd hotel-inspection

echo "=== 6. 创建 .env 文件 ==="
cat > .env <<'EOF'
DB_PASSWORD=Hotel@2026Secure
QWEN_API_KEY=sk-a8e9de55030f40ea9e8c3cc6ac427b76
EOF

echo "=== 7. 启动服务 ==="
docker compose up -d --build

echo "=== 8. 配置防火墙 (放行 8000 端口) ==="
ufw allow 8000/tcp || true

echo ""
echo "✅ 部署完成！"
echo "访问地址: http://$(curl -s ifconfig.me):8000"
echo "管理看板: http://$(curl -s ifconfig.me):8000/manager"
