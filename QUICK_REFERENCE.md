# 智享会员系统 - 快速参考卡

## 🚀 快速启动

```bash
# 方式1: 使用一键启动脚本
bash start.sh

# 方式2: 手动启动
docker compose up -d --build
```

## 📋 默认账户

| 类型 | 用户名/邮箱 | 密码 |
|------|------------|------|
| 管理员 | admin | admin123 |
| 测试用户 | test@example.com | (验证码登录) |

## 🔗 访问地址

| 服务 | 地址 |
|------|------|
| API 文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

## 📡 核心 API 端点

### 认证
- `POST /api/v1/auth/send-code` - 发送验证码
- `POST /api/v1/auth/register` - 注册
- `POST /api/v1/auth/login` - 登录
- `POST /api/v1/auth/logout` - 登出

### 会员
- `GET /api/v1/members/me` - 获取资料
- `PATCH /api/v1/members/me` - 更新资料

### 积分
- `GET /api/v1/points/balance` - 查询余额
- `GET /api/v1/points/transactions` - 交易历史

### 权益
- `GET /api/v1/benefits` - 可用权益
- `GET /api/v1/benefits/my-benefits` - 我的权益

### 订单
- `GET /api/v1/orders` - 订单列表

### 管理员
- `POST /api/v1/admin/auth/login` - 管理员登录
- `GET /api/v1/admin/users` - 用户列表
- `POST /api/v1/admin/points/adjust` - 调整积分
- `POST /api/v1/admin/benefits/distribute` - 发放权益

## 🛠️ 常用命令

### 服务管理
```bash
# 启动
docker compose up -d --build

# 停止
docker compose down

# 重启
docker compose restart app

# 查看日志
docker compose logs -f app

# 查看状态
docker compose ps

# 清理数据（重新开始）
docker compose down -v
```

### 数据库操作
```bash
# 连接 PostgreSQL
docker compose exec postgres psql -U membership -d membership_db

# 查看用户
SELECT id, email, nickname, member_level, available_points FROM users;

# 查看积分交易
SELECT * FROM point_transactions ORDER BY created_at DESC LIMIT 10;
```

### Redis 操作
```bash
# 连接 Redis
docker compose exec redis redis-cli

# 查看所有 key
KEYS *

# 查看验证码
GET verification_code:test@example.com:register
```

### API 测试
```bash
# 健康检查
curl http://localhost:8000/health

# 完整 API 测试
bash verify_api.sh

# 发送验证码
curl -X POST http://localhost:8000/api/v1/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "purpose": "register"}'
```

## 🔧 故障排查

### 服务无法启动
```bash
# 查看日志
docker compose logs app

# 检查端口占用
lsof -i :8000
lsof -i :5432
lsof -i :6379
```

### 数据库连接失败
```bash
# 检查 PostgreSQL
docker compose exec postgres pg_isready -U membership

# 重启数据库
docker compose restart postgres
```

### Redis 连接失败
```bash
# 检查 Redis
docker compose exec redis redis-cli ping

# 重启 Redis
docker compose restart redis
```

## 📊 项目统计

- **Python 文件**: 50 个
- **代码行数**: ~2100 行
- **API 端点**: 25+ 个
- **数据库表**: 13 张
- **Docker 服务**: 3 个

## 🔒 安全提醒

⚠️ **生产环境必须修改：**
1. JWT 密钥 (JWT_SECRET_KEY)
2. 管理员密码 (admin/admin123)
3. 数据库密码
4. 启用 HTTPS

## 📚 文档

- 完整文档: `cat README.md`
- 项目总结: `cat PROJECT_SUMMARY.md`
- 环境检查: `python3 quickstart.py`

## 🎯 下一步

1. ✅ 启动服务: `bash start.sh`
2. ✅ 验证 API: `bash verify_api.sh`
3. ✅ 访问文档: http://localhost:8000/docs
4. 📝 编写测试
5. 🚀 生产部署

---

**项目位置**: `./` (项目根目录)

**技术栈**: FastAPI + PostgreSQL + Redis + Docker
