#!/bin/bash
# 审核前自测脚本 - 完整版
# 执行此脚本可自动完成所有关键测试

set -e

echo "════════════════════════════════════════════════════════════"
echo "           智享会员系统 - 审核前自测脚本"
echo "════════════════════════════════════════════════════════════"
echo ""

# Prefer `docker compose` (v2). Fall back to legacy `docker-compose` if needed.
COMPOSE=(docker compose)
if ! docker compose version >/dev/null 2>&1; then
    if command -v docker-compose >/dev/null 2>&1; then
        COMPOSE=(docker-compose)
    else
        echo "❌ 未检测到 Docker Compose（需要 docker compose 或 docker-compose）"
        exit 1
    fi
fi

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试结果统计
PASSED=0
FAILED=0

# 测试函数
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ 通过${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ 失败${NC}"
        FAILED=$((FAILED + 1))
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "第一步：红线指标自测（一票否决项）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 测试 1: 检查 Session 轨迹文件
echo "测试 1: 检查 Session 轨迹文件"
echo -n "  检查 session_trace.json 是否存在... "
if [ -f "session_trace.json" ]; then
    SIZE=$(stat -f%z session_trace.json 2>/dev/null || stat -c%s session_trace.json 2>/dev/null)
    if [ $SIZE -gt 1000 ]; then
        test_result 0
        echo "    文件大小: $SIZE 字节"
    else
        test_result 1
        echo "    文件太小，可能内容不完整"
    fi
else
    test_result 1
    echo "    ❌ 文件不存在！这是一票否决项！"
fi
echo ""

# 测试 2: 检查硬编码路径
echo "测试 2: 检查代码中是否有硬编码路径"
echo -n "  搜索 /home/jovyan/ 路径... "
if grep -r "/home/jovyan/" app/ 2>/dev/null | grep -v ".pyc" | grep -q .; then
    test_result 1
    echo "    发现硬编码路径："
    grep -r "/home/jovyan/" app/ 2>/dev/null | grep -v ".pyc" | head -3
else
    test_result 0
fi

echo -n "  搜索 C:\\ 路径... "
if grep -r "C:\\\\" app/ 2>/dev/null | grep -v ".pyc" | grep -q .; then
    test_result 1
else
    test_result 0
fi
echo ""

# 测试 3: Docker 配置检查
echo "测试 3: Docker 配置完整性"
echo -n "  检查 docker-compose.yml... "
if [ -f "docker-compose.yml" ]; then
    test_result 0
else
    test_result 1
fi

echo -n "  检查 Dockerfile... "
if [ -f "docker/Dockerfile" ]; then
    test_result 0
else
    test_result 1
fi

echo -n "  检查 init-db.sql... "
if [ -f "docker/init-db.sql" ]; then
    test_result 0
else
    test_result 1
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "第二步：Docker 启动测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "准备启动 Docker 服务..."
echo "命令: docker compose up -d --build（在项目根目录执行）"
echo ""
echo "执行：清理旧环境（docker compose down -v）..."
"${COMPOSE[@]}" down -v >/dev/null 2>&1 || true

echo "执行：启动服务（docker compose up -d --build）..."
set +e
UP_OUT=$("${COMPOSE[@]}" up -d --build 2>&1)
UP_STATUS=$?
set -e

if [ $UP_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ docker compose up 执行成功${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ docker compose up 执行失败（这是红线项）${NC}"
    echo "$UP_OUT"
    FAILED=$((FAILED + 1))
fi

wait_healthy() {
    local service="$1"
    local timeout="${2:-90}"
    local start_ts
    start_ts=$(date +%s)

    while true; do
        local cid status now
        cid=$("${COMPOSE[@]}" ps -q "$service" 2>/dev/null || true)
        if [ -n "$cid" ]; then
            status=$(docker inspect -f '{{.State.Health.Status}}' "$cid" 2>/dev/null || true)
            if [ "$status" = "healthy" ]; then
                return 0
            fi
        fi

        now=$(date +%s)
        if [ $((now - start_ts)) -ge "$timeout" ]; then
            return 1
        fi
        sleep 2
    done
}

echo "等待 postgres/redis 变为 healthy..."
echo -n "  postgres... "
if wait_healthy postgres 90; then
    test_result 0
else
    test_result 1
fi

echo -n "  redis... "
if wait_healthy redis 90; then
    test_result 0
else
    test_result 1
fi

echo -n "  app 运行中... "
APP_CID=$("${COMPOSE[@]}" ps -q app 2>/dev/null || true)
if [ -n "$APP_CID" ] && [ "$(docker inspect -f '{{.State.Running}}' "$APP_CID" 2>/dev/null || echo false)" = "true" ]; then
    test_result 0
else
    test_result 1
fi

echo ""
echo "服务状态："
"${COMPOSE[@]}" ps || true
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "第三步：API 功能测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 等待服务就绪
echo "等待服务就绪（/health 200）..."
READY=0
for i in {1..60}; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/health" 2>/dev/null || echo "000")
    if [ "$CODE" = "200" ]; then
        READY=1
        break
    fi
    sleep 1
done
if [ "$READY" = "1" ]; then
    echo -e "${GREEN}✅ /health 已就绪${NC}"
else
    echo -e "${RED}❌ /health 未就绪（60秒超时）${NC}"
    FAILED=$((FAILED + 1))
fi

BASE_URL="http://localhost:8000"

# 测试 4: 健康检查
echo "测试 4: 健康检查"
echo -n "  GET /health... "
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/health" 2>/dev/null || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
if [ "$HTTP_CODE" = "200" ]; then
    test_result 0
else
    test_result 1
    echo "    HTTP 状态码: $HTTP_CODE"
fi
echo ""

# 测试 5: 验证码限流（1/分钟）
echo "测试 5: 验证码限流（1/分钟，10/天）"
TEST_EMAIL="ratelimit_$(date +%s)@test.com"

echo "  第一次请求（应成功）..."
RESPONSE1=$(curl -s -X POST "$BASE_URL/api/v1/auth/send-code" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$TEST_EMAIL\", \"purpose\": \"register\"}" 2>/dev/null)

echo "  立即第二次请求（应失败）..."
RESPONSE2=$(curl -s -X POST "$BASE_URL/api/v1/auth/send-code" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$TEST_EMAIL\", \"purpose\": \"register\"}" 2>/dev/null)

echo -n "  检查限流是否生效... "
if echo "$RESPONSE2" | grep -q "VERIFICATION_CODE_RATE_LIMIT\|rate.*limit\|频繁"; then
    test_result 0
    echo "    第二次请求被正确拒绝"
else
    test_result 1
    echo "    响应: $RESPONSE2"
fi
echo ""

# 测试 6: 数据脱敏
echo "测试 6: 数据脱敏"
TEST_EMAIL2="mask$(date +%s)@example.com"

echo "  获取注册验证码..."
CODE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/send-code" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$TEST_EMAIL2\", \"purpose\": \"register\"}" 2>/dev/null)

CODE=$(echo "$CODE_RESPONSE" | grep -o '"code":"[^"]*"' | cut -d'"' -f4)

echo "  注册用户..."
REG_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$TEST_EMAIL2\", \"code\": \"${CODE:-123456}\", \"nickname\": \"MaskTest\"}" 2>/dev/null)

TOKEN=$(echo "$REG_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo "  查询个人资料..."
    PROFILE=$(curl -s "$BASE_URL/api/v1/members/me" \
      -H "Authorization: Bearer $TOKEN" 2>/dev/null)

    echo -n "  检查邮箱是否脱敏... "
    if echo "$PROFILE" | grep -q "\*\*\*"; then
        test_result 0
        echo "    邮箱已正确脱敏"
    else
        test_result 1
        echo "    响应: $PROFILE"
    fi
else
    echo -e "${YELLOW}  ⚠️  注册失败，跳过脱敏测试${NC}"
fi
echo ""

# 测试 7: 错误格式统一
echo "测试 7: 错误格式统一"
echo "  发送错误请求..."
ERROR_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/send-code" \
  -H "Content-Type: application/json" \
  -d '{"email": "invalid-email"}' 2>/dev/null)

echo -n "  检查错误格式... "
if echo "$ERROR_RESPONSE" | grep -q '"code"' && \
   echo "$ERROR_RESPONSE" | grep -q '"message"' && \
   echo "$ERROR_RESPONSE" | grep -q '"trace_id"'; then
    test_result 0
    echo "    错误格式正确: {code, message, trace_id}"
else
    test_result 1
    echo "    响应: $ERROR_RESPONSE"
fi
echo ""

# 测试 8: 管理员登录和审计日志
echo "测试 8: 管理员功能和审计日志"
echo "  管理员登录..."
ADMIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/admin/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' 2>/dev/null)

ADMIN_TOKEN=$(echo "$ADMIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$ADMIN_TOKEN" ]; then
    echo -e "${GREEN}  ✅ 管理员登录成功${NC}"
    PASSED=$((PASSED + 1))

    echo "  触发一条审计日志（查询用户列表）..."
    curl -s "$BASE_URL/api/v1/admin/users?page=1&page_size=1" \
      -H "Authorization: Bearer $ADMIN_TOKEN" >/dev/null 2>&1 || true

    echo "  查询审计日志..."
    AUDIT_LOGS=$(curl -s "$BASE_URL/api/v1/admin/audit-logs" \
      -H "Authorization: Bearer $ADMIN_TOKEN" 2>/dev/null)

    echo -n "  检查审计日志格式... "
    if echo "$AUDIT_LOGS" | grep -q '"admin_user_id"\|"action"\|"resource"'; then
        test_result 0
    else
        test_result 1
    fi
else
    echo -e "${RED}  ❌ 管理员登录失败${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "第四步：文档完整性检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 测试 9: 文档文件
echo "测试 9: 必需文档文件"
DOCS=("README.md" "QUICK_REFERENCE.md" "PROJECT_SUMMARY.md" "LICENSE" "CONTRIBUTING.md")

for doc in "${DOCS[@]}"; do
    echo -n "  检查 $doc... "
    if [ -f "$doc" ]; then
        test_result 0
    else
        test_result 1
    fi
done
echo ""

# 测试 10: README 内容
echo "测试 10: README 关键内容"
echo -n "  检查启动命令... "
if grep -q "docker compose up" README.md; then
    test_result 0
else
    test_result 1
fi

echo -n "  检查测试账号... "
if grep -q "admin" README.md && grep -q "admin123" README.md; then
    test_result 0
else
    test_result 1
fi

echo -n "  检查服务地址... "
if grep -q "localhost:8000\|8000" README.md; then
    test_result 0
else
    test_result 1
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "测试结果汇总"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "通过: ${GREEN}$PASSED${NC}"
echo -e "失败: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ 所有测试通过！项目已准备好提交审核！${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}❌ 有 $FAILED 项测试失败，请修复后再提交${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
    exit 1
fi
