# 智享会员系统 (Membership System)

一个功能完整的会员管理系统后端，提供统一的会员注册/登录、权益发放、订单管理和风控能力。

## 功能特性

### 核心功能
- ✅ **邮箱验证码认证** - 基于邮箱的注册/登录，带验证码验证
- ✅ **JWT 令牌管理** - 2小时过期，支持刷新和黑名单
- ✅ **积分系统** - 订单完成自动赚取积分，支持幂等性
- ✅ **会员等级** - Bronze/Silver/Gold/Platinum 四个等级
- ✅ **权益发放** - 按月自动发放权益，分布式锁防重复
- ✅ **订单管理** - 订单查询、状态跟踪
- ✅ **管理后台** - RBAC 权限控制、审计日志

### 技术特性
- ✅ **限流保护** - 验证码发送限流（1次/分钟，10次/天）
- ✅ **账户锁定** - 登录失败5次自动锁定15分钟
- ✅ **数据脱敏** - 邮箱、身份证号自动脱敏
- ✅ **北京时区** - 所有时间自动转换为北京时间
- ✅ **统一错误处理** - 带 trace_id 的错误响应
- ✅ **幂等性保证** - 积分发放、权益分发支持幂等

## 技术栈

- **FastAPI** - Python Web 框架
- **PostgreSQL 14** - 主数据库
- **Redis 7** - 缓存、限流、JWT 黑名单
- **Docker Compose** - 容器化部署
- **SQLAlchemy** - ORM
- **Alembic** - 数据库迁移
- **JWT** - 身份认证

## 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+

### 启动服务

1. **克隆项目**
```bash
cd Smart-Enjoy-Membership-System
```

2. **启动所有服务**
```bash
docker compose up -d --build
```

3. **查看日志**
```bash
docker compose logs -f app
```

4. **检查服务状态**
```bash
docker compose ps
```

所有服务启动后：
- API 服务: http://localhost:8000
- API 文档: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### 停止服务

```bash
docker compose down
```

### 清理数据（重新开始）

```bash
docker compose down -v
```

## 模型轨迹文件（审核要求）

本仓库包含开发过程的模型轨迹文件（OpenAI messages 格式 + 原始 session）：

- 转换后（OpenAI messages JSON）：`session_trace.json`（根目录）或 `session_trace/openai_messages.json`
- 转换前（Codex session JSONL）：`session_trace/codex_session.jsonl`
- 说明文档：`session_trace/README.md`

## API 验证步骤

### 1. 健康检查

```bash
curl http://localhost:8000/health
```

预期响应：
```json
{"status": "healthy"}
```

### 2. 用户注册流程

#### 2.1 发送验证码

```bash
curl -X POST http://localhost:8000/api/v1/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "purpose": "register"
  }'
```

预期响应：
```json
{
  "message": "验证码已发送",
  "data": {
    "code": "037891"
  }
}
```

**注意**: `code` 为 6 位数字验证码；该项目为便于测试会在响应中返回，并在控制台日志中打印（模拟邮件发送）。

#### 2.2 注册用户

```bash
CODE=$(curl -s -X POST http://localhost:8000/api/v1/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "purpose": "register"}' | sed -n 's/.*"code":"\\([0-9]\\{6\\}\\)".*/\\1/p')

curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"test@example.com\",
    \"code\": \"${CODE}\",
    \"nickname\": \"测试用户\"
  }"
```

预期响应：
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 7200
}
```

保存 `access_token` 用于后续请求。

### 3. 用户登录流程

#### 3.1 发送登录验证码

```bash
curl -X POST http://localhost:8000/api/v1/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "purpose": "login"
  }'
```

#### 3.2 登录

```bash
CODE=$(curl -s -X POST http://localhost:8000/api/v1/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "purpose": "login"}' | sed -n 's/.*"code":"\\([0-9]\\{6\\}\\)".*/\\1/p')

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"test@example.com\",
    \"code\": \"${CODE}\"
  }"
```

### 4. 获取用户资料

```bash
curl http://localhost:8000/api/v1/members/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

预期响应（注意邮箱已脱敏）：
```json
{
  "id": 1,
  "email": "tes***@example.com",
  "nickname": "测试用户",
  "member_level": "bronze",
  "available_points": 0,
  "total_earned_points": 0,
  "created_at": "2024-02-12 14:30:00"
}
```

### 5. 更新用户资料

```bash
curl -X PATCH http://localhost:8000/api/v1/members/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "新昵称",
    "gender": "male"
  }'
```

### 6. 查看积分余额

```bash
curl http://localhost:8000/api/v1/points/balance \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 7. 查看积分交易历史

```bash
curl "http://localhost:8000/api/v1/points/transactions?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 8. 查看可用权益

```bash
curl http://localhost:8000/api/v1/benefits \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 9. 查看我的权益

```bash
curl "http://localhost:8000/api/v1/benefits/my-benefits?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 10. 查询订单

```bash
curl "http://localhost:8000/api/v1/orders?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

可选参数：
- `status`: pending/paid/completed/cancelled/refunded
- `start_date`: 开始日期
- `end_date`: 结束日期

### 11. 管理员登录

```bash
curl -X POST http://localhost:8000/api/v1/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

预期响应：
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 7200,
  "admin": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com"
  }
}
```

### 12. 管理员查看用户列表

```bash
curl "http://localhost:8000/api/v1/admin/users?page=1&page_size=20" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

### 13. 管理员调整积分

```bash
curl -X POST http://localhost:8000/api/v1/admin/points/adjust \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "points": 100,
    "reason": "新用户奖励"
  }'
```

### 14. 管理员锁定用户

```bash
curl -X POST "http://localhost:8000/api/v1/admin/users/1/lock?reason=违规操作" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

### 15. 管理员查看审计日志

```bash
curl "http://localhost:8000/api/v1/admin/audit-logs?page=1&page_size=50" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

## 限流测试

### 测试验证码限流（1次/分钟）

```bash
# 第一次请求 - 成功
curl -X POST http://localhost:8000/api/v1/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "purpose": "register"}'

# 立即第二次请求 - 失败（限流）
curl -X POST http://localhost:8000/api/v1/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "purpose": "register"}'
```

预期第二次请求返回：
```json
{
  "code": "VERIFICATION_CODE_RATE_LIMIT",
  "message": "验证码发送过于频繁，请稍后再试",
  "trace_id": "..."
}
```

### 测试登录失败锁定（5次失败）

连续5次使用错误验证码登录，账户将被锁定15分钟。

## 数据库访问

### 连接 PostgreSQL

```bash
docker compose exec postgres psql -U membership -d membership_db
```

### 常用查询

```sql
-- 查看所有用户
SELECT id, email, nickname, member_level, available_points FROM users;

-- 查看积分交易
SELECT * FROM point_transactions ORDER BY created_at DESC LIMIT 10;

-- 查看权益发放记录
SELECT * FROM benefit_distributions ORDER BY distributed_at DESC LIMIT 10;

-- 查看审计日志
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;
```

### 连接 Redis

```bash
docker compose exec redis redis-cli
```

### 常用 Redis 命令

```bash
# 查看所有 key
KEYS *

# 查看验证码
GET verification_code:test@example.com:register

# 查看限流计数
GET rate_limit:verification:test@example.com:minute

# 查看登录失败次数
GET login_failures:test@example.com

# 查看 JWT 黑名单
KEYS jwt_blacklist:*
```

## 项目结构

```
.
├── app/                         # FastAPI 后端代码
│   ├── main.py                  # FastAPI 应用入口
│   ├── config.py                # 配置管理
│   ├── dependencies.py          # 依赖注入
│   ├── api/v1/                  # API 端点
│   ├── core/                    # JWT/限流/错误码
│   ├── middleware/              # 认证/错误处理/trace_id
│   ├── models/                  # 数据库模型
│   ├── schemas/                 # Pydantic 模型
│   ├── services/                # 业务逻辑
│   ├── repositories/            # 数据访问
│   ├── db/                      # 数据库会话
│   └── utils/                   # 工具函数（脱敏/时间等）
├── docker/                      # Docker 镜像与初始化 SQL
│   ├── Dockerfile
│   └── init-db.sql
├── docker-compose.yml           # 一键启动（从项目根目录执行）
├── requirements.txt
├── .env.example                 # 可选（生产/自定义覆盖）
└── README.md
```

## 环境变量

无需创建 `.env` 也可直接启动（`docker-compose.yml` 已包含本地测试默认配置）。

如需自定义配置，可通过系统环境变量覆盖，或创建 `.env`（可选）并在其中设置变量。

主要配置项：
- `DATABASE_URL`: PostgreSQL 连接字符串
- `REDIS_URL`: Redis 连接字符串
- `JWT_SECRET_KEY`: JWT 密钥（生产环境必须修改）
- `JWT_EXPIRY_HOURS`: JWT 过期时间（小时）
- `VERIFICATION_CODE_RATE_LIMIT_MINUTE`: 验证码分钟限流
- `VERIFICATION_CODE_RATE_LIMIT_DAY`: 验证码每日限流
- `LOGIN_FAILURE_LIMIT`: 登录失败锁定阈值
- `LOGIN_LOCK_MINUTES`: 账户锁定时长（分钟）

## 默认账户

### 管理员账户
- 用户名: `admin`
- 密码: `admin123`
- 角色: 系统管理员（完整权限）

**⚠️ 生产环境请立即修改默认密码！**

## 安全建议

1. **修改 JWT 密钥**: 在生产环境中使用强随机密钥
2. **修改默认密码**: 修改管理员默认密码
3. **启用 HTTPS**: 使用反向代理（Nginx）配置 SSL
4. **配置防火墙**: 限制数据库和 Redis 端口访问
5. **启用真实邮件**: 配置 SMTP 发送真实验证码邮件
6. **日志监控**: 配置日志收集和监控告警
7. **备份策略**: 定期备份 PostgreSQL 数据

## 故障排查

### 服务无法启动

```bash
# 查看日志
docker compose logs app

# 检查数据库连接
docker compose logs postgres

# 检查 Redis 连接
docker compose logs redis
```

### 数据库连接失败

```bash
# 检查 PostgreSQL 是否就绪
docker compose exec postgres pg_isready -U membership

# 重启数据库
docker compose restart postgres
```

### Redis 连接失败

```bash
# 检查 Redis 是否运行
docker compose exec redis redis-cli ping

# 重启 Redis
docker compose restart redis
```

### 重置所有数据

```bash
# 停止并删除所有容器和数据卷
docker compose down -v

# 重新启动
docker compose up -d --build
```

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发指南（可选）

本项目默认以 Docker Compose 作为唯一运行方式（验收亦基于此），不要求本机安装 PostgreSQL/Redis。

常用开发命令：

```bash
# 语法检查
python3 check_syntax.py

# 启动/重启服务
docker compose up -d --build
docker compose restart app

# 端到端验证
bash verify_api.sh
bash pre_review_test.sh
```

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue。
