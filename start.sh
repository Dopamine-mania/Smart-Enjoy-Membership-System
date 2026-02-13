#!/bin/bash
# 智享会员系统 - 一键启动脚本

echo "════════════════════════════════════════════════════════════"
echo "           智享会员系统 - 一键启动"
echo "════════════════════════════════════════════════════════════"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

echo "✓ Docker 已安装"

echo ""
echo "正在启动服务..."
echo "  - PostgreSQL 14"
echo "  - Redis 7"
echo "  - FastAPI 应用"
echo ""

# 启动服务
docker compose up -d --build

# 等待服务启动
echo "等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "════════════════════════════════════════════════════════════"
echo "           服务状态"
echo "════════════════════════════════════════════════════════════"
docker compose ps

echo ""
echo "════════════════════════════════════════════════════════════"
echo "           访问信息"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  🌐 API 文档:    http://localhost:8000/docs"
echo "  🏥 健康检查:    http://localhost:8000/health"
echo "  📊 数据库:      localhost:5432"
echo "  🔴 Redis:       localhost:6379"
echo ""
echo "  👤 管理员账户:  admin / admin123"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "           常用命令"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  查看日志:      docker compose logs -f app"
echo "  停止服务:      docker compose down"
echo "  重启服务:      docker compose restart app"
echo "  验证 API:      bash verify_api.sh"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo "✅ 服务启动完成！"
echo ""
