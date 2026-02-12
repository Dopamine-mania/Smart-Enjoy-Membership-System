#!/bin/bash

# API Verification Script for Membership System
# This script tests all major API endpoints

set -e

BASE_URL="http://localhost:8000"
EMAIL="test@example.com"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"

echo "=========================================="
echo "智享会员系统 API 验证脚本"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print success
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# Function to print info
info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Test 1: Health Check
info "测试 1: 健康检查"
HEALTH=$(curl -s "$BASE_URL/health")
if echo "$HEALTH" | grep -q "healthy"; then
    success "健康检查通过"
else
    error "健康检查失败"
fi
echo ""

# Test 2: Send Verification Code
info "测试 2: 发送注册验证码"
SEND_CODE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/send-code" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$EMAIL\", \"purpose\": \"register\"}")

if echo "$SEND_CODE_RESPONSE" | grep -q "验证码已发送"; then
    CODE=$(echo "$SEND_CODE_RESPONSE" | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
    success "验证码发送成功: $CODE"
else
    error "验证码发送失败"
fi
echo ""

# Test 3: Register User
info "测试 3: 用户注册"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$EMAIL\", \"code\": \"$CODE\", \"nickname\": \"测试用户\"}")

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    USER_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    success "用户注册成功"
else
    # User might already exist, try login
    info "用户可能已存在，尝试登录..."

    # Send login code
    SEND_LOGIN_CODE=$(curl -s -X POST "$BASE_URL/api/v1/auth/send-code" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$EMAIL\", \"purpose\": \"login\"}")

    LOGIN_CODE=$(echo "$SEND_LOGIN_CODE" | grep -o '"code":"[^"]*"' | cut -d'"' -f4)

    # Login
    LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$EMAIL\", \"code\": \"$LOGIN_CODE\"}")

    if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
        USER_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        success "用户登录成功"
    else
        error "用户注册/登录失败"
    fi
fi
echo ""

# Test 4: Get User Profile
info "测试 4: 获取用户资料"
PROFILE_RESPONSE=$(curl -s "$BASE_URL/api/v1/members/me" \
    -H "Authorization: Bearer $USER_TOKEN")

if echo "$PROFILE_RESPONSE" | grep -q "email"; then
    success "获取用户资料成功"
    echo "   用户信息: $(echo $PROFILE_RESPONSE | grep -o '"nickname":"[^"]*"' | cut -d'"' -f4)"
else
    error "获取用户资料失败"
fi
echo ""

# Test 5: Update Profile
info "测试 5: 更新用户资料"
UPDATE_RESPONSE=$(curl -s -X PATCH "$BASE_URL/api/v1/members/me" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"nickname": "更新后的昵称", "gender": "male"}')

if echo "$UPDATE_RESPONSE" | grep -q "更新后的昵称"; then
    success "更新用户资料成功"
else
    error "更新用户资料失败"
fi
echo ""

# Test 6: Get Points Balance
info "测试 6: 查询积分余额"
POINTS_RESPONSE=$(curl -s "$BASE_URL/api/v1/points/balance" \
    -H "Authorization: Bearer $USER_TOKEN")

if echo "$POINTS_RESPONSE" | grep -q "available_points"; then
    POINTS=$(echo "$POINTS_RESPONSE" | grep -o '"available_points":[0-9]*' | cut -d':' -f2)
    success "查询积分余额成功: $POINTS 积分"
else
    error "查询积分余额失败"
fi
echo ""

# Test 7: Get Point Transactions
info "测试 7: 查询积分交易历史"
TRANSACTIONS_RESPONSE=$(curl -s "$BASE_URL/api/v1/points/transactions?page=1&page_size=10" \
    -H "Authorization: Bearer $USER_TOKEN")

if echo "$TRANSACTIONS_RESPONSE" | grep -q "items"; then
    success "查询积分交易历史成功"
else
    error "查询积分交易历史失败"
fi
echo ""

# Test 8: Get Benefits
info "测试 8: 查询可用权益"
BENEFITS_RESPONSE=$(curl -s "$BASE_URL/api/v1/benefits" \
    -H "Authorization: Bearer $USER_TOKEN")

if echo "$BENEFITS_RESPONSE" | grep -q "Bronze Monthly Points"; then
    success "查询可用权益成功"
else
    error "查询可用权益失败"
fi
echo ""

# Test 9: Get My Benefits
info "测试 9: 查询我的权益"
MY_BENEFITS_RESPONSE=$(curl -s "$BASE_URL/api/v1/benefits/my-benefits?page=1&page_size=10" \
    -H "Authorization: Bearer $USER_TOKEN")

if echo "$MY_BENEFITS_RESPONSE" | grep -q "items"; then
    success "查询我的权益成功"
else
    error "查询我的权益失败"
fi
echo ""

# Test 10: Get Orders
info "测试 10: 查询订单列表"
ORDERS_RESPONSE=$(curl -s "$BASE_URL/api/v1/orders?page=1&page_size=10" \
    -H "Authorization: Bearer $USER_TOKEN")

if echo "$ORDERS_RESPONSE" | grep -q "items"; then
    success "查询订单列表成功"
else
    error "查询订单列表失败"
fi
echo ""

# Test 11: Admin Login
info "测试 11: 管理员登录"
ADMIN_LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/admin/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$ADMIN_USERNAME\", \"password\": \"$ADMIN_PASSWORD\"}")

if echo "$ADMIN_LOGIN_RESPONSE" | grep -q "access_token"; then
    ADMIN_TOKEN=$(echo "$ADMIN_LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    success "管理员登录成功"
else
    error "管理员登录失败"
fi
echo ""

# Test 12: Admin List Users
info "测试 12: 管理员查询用户列表"
ADMIN_USERS_RESPONSE=$(curl -s "$BASE_URL/api/v1/admin/users?page=1&page_size=10" \
    -H "Authorization: Bearer $ADMIN_TOKEN")

if echo "$ADMIN_USERS_RESPONSE" | grep -q "items"; then
    success "管理员查询用户列表成功"
else
    error "管理员查询用户列表失败"
fi
echo ""

# Test 13: Admin Adjust Points
info "测试 13: 管理员调整积分"
ADJUST_POINTS_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/admin/points/adjust" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"user_id": 1, "points": 100, "reason": "测试奖励"}')

if echo "$ADJUST_POINTS_RESPONSE" | grep -q "积分调整成功"; then
    success "管理员调整积分成功"
else
    error "管理员调整积分失败"
fi
echo ""

# Test 14: Verify Points Updated
info "测试 14: 验证积分已更新"
UPDATED_POINTS_RESPONSE=$(curl -s "$BASE_URL/api/v1/points/balance" \
    -H "Authorization: Bearer $USER_TOKEN")

UPDATED_POINTS=$(echo "$UPDATED_POINTS_RESPONSE" | grep -o '"available_points":[0-9]*' | cut -d':' -f2)
if [ "$UPDATED_POINTS" -ge 100 ]; then
    success "积分已更新: $UPDATED_POINTS 积分"
else
    error "积分更新验证失败"
fi
echo ""

# Test 15: Rate Limiting Test
info "测试 15: 验证码限流测试"
FIRST_CODE=$(curl -s -X POST "$BASE_URL/api/v1/auth/send-code" \
    -H "Content-Type: application/json" \
    -d '{"email": "ratelimit@test.com", "purpose": "register"}')

SECOND_CODE=$(curl -s -X POST "$BASE_URL/api/v1/auth/send-code" \
    -H "Content-Type: application/json" \
    -d '{"email": "ratelimit@test.com", "purpose": "register"}')

if echo "$SECOND_CODE" | grep -q "VERIFICATION_CODE_RATE_LIMIT"; then
    success "限流功能正常工作"
else
    error "限流功能未生效"
fi
echo ""

# Test 16: Logout
info "测试 16: 用户登出"
LOGOUT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/logout" \
    -H "Authorization: Bearer $USER_TOKEN")

if echo "$LOGOUT_RESPONSE" | grep -q "登出成功"; then
    success "用户登出成功"
else
    error "用户登出失败"
fi
echo ""

# Final Summary
echo "=========================================="
echo -e "${GREEN}所有测试通过！系统运行正常。${NC}"
echo "=========================================="
echo ""
echo "提示："
echo "  - API 文档: $BASE_URL/docs"
echo "  - 健康检查: $BASE_URL/health"
echo "  - 管理员账户: admin / admin123"
echo ""
