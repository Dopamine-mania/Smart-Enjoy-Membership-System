# 审核前自测操作指南

## 📋 完整测试清单

按照以下步骤逐一执行，每完成一项打勾 ✅

---

## 第一步：红线指标自测（一票否决项）

### ✅ 测试 1.1: 检查 Session 轨迹文件

**操作**：
```bash
ls -lh session_trace.json
```

**检查点**：
- [ ] 文件存在
- [ ] 文件大小 > 10KB
- [ ] 文件格式为 JSON

**预期结果**：
```
-rw-r--r-- 1 user user 13K Feb 12 10:00 session_trace.json
```

**如果失败**：这是一票否决项！必须有此文件才能提交。

---

### ✅ 测试 1.2: 检查硬编码路径

**操作**：
```bash
# 搜索 /home/jovyan/ 路径
grep -r "/home/jovyan/" app/ 2>/dev/null | grep -v ".pyc"

# 搜索 Windows 路径
grep -r "C:\\\\" app/ 2>/dev/null | grep -v ".pyc"
```

**检查点**：
- [ ] 无 `/home/jovyan/` 路径
- [ ] 无 `C:\` 路径
- [ ] 所有路径都是相对路径或容器内路径

**预期结果**：
```
(无输出，表示没有找到硬编码路径)
```

**如果失败**：这是一票否决项！必须移除所有硬编码路径。

---

### ✅ 测试 1.3: Docker 配置完整性

**操作**：
```bash
ls -lh docker/docker-compose.yml docker/Dockerfile docker/init-db.sql
```

**检查点**：
- [ ] docker-compose.yml 存在
- [ ] Dockerfile 存在
- [ ] init-db.sql 存在

**预期结果**：
```
-rw-r--r-- 1 user user 1.2K docker/docker-compose.yml
-rw-r--r-- 1 user user  500 docker/Dockerfile
-rw-r--r-- 1 user user  8.5K docker/init-db.sql
```

---

## 第二步：Docker 一键启动测试

### ✅ 测试 2.1: 清理旧环境

**操作**：
```bash
cd docker
docker compose down -v
```

**检查点**：
- [ ] 命令执行成功
- [ ] 旧容器已停止
- [ ] 旧数据卷已删除

**预期结果**：
```
[+] Running 4/4
 ✔ Container app       Removed
 ✔ Container postgres  Removed
 ✔ Container redis     Removed
 ✔ Network removed
```

---

### ✅ 测试 2.2: 启动所有服务

**操作**：
```bash
docker compose up -d
```

**检查点**：
- [ ] 所有3个服务启动成功
- [ ] 无错误信息

**预期结果**：
```
[+] Running 3/3
 ✔ Container postgres  Started
 ✔ Container redis     Started
 ✔ Container app       Started
```

**📸 截图 1**：保存此输出截图

---

### ✅ 测试 2.3: 检查服务状态

**操作**：
```bash
docker compose ps
```

**检查点**：
- [ ] postgres 状态为 `Up (healthy)`
- [ ] redis 状态为 `Up (healthy)`
- [ ] app 状态为 `Up (healthy)`

**预期结果**：
```
NAME       IMAGE              STATUS
postgres   postgres:14        Up (healthy)
redis      redis:7            Up (healthy)
app        membership-app     Up (healthy)
```

**📸 截图 2**：保存此输出截图

---

### ✅ 测试 2.4: 查看应用日志

**操作**：
```bash
docker compose logs app | tail -20
```

**检查点**：
- [ ] 看到 "Application startup complete"
- [ ] 看到 "Uvicorn running on http://0.0.0.0:8000"
- [ ] 无错误信息

**预期结果**：
```
app  | INFO:     Application startup complete.
app  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### ✅ 测试 2.5: 等待服务完全启动

**操作**：
```bash
sleep 10  # 等待10秒
```

**检查点**：
- [ ] 等待完成

---

## 第三步：API 功能测试

### ✅ 测试 3.1: 健康检查

**操作**：
```bash
curl http://localhost:8000/health
```

**检查点**：
- [ ] 返回 200 状态码
- [ ] 返回 `{"status": "healthy"}`

**预期结果**：
```json
{"status":"healthy"}
```

---

### ✅ 测试 3.2: Swagger 文档

**操作**：
在浏览器中访问：`http://localhost:8000/docs`

**检查点**：
- [ ] 页面正常加载
- [ ] 看到 "FastAPI" 标题
- [ ] 看到所有 API 端点列表

**📸 截图 3**：保存 Swagger 页面截图

---

### ✅ 测试 3.3: 验证码限流（1/分钟）

**第一次请求（应成功）**：
```bash
curl -X POST http://localhost:8000/api/v1/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "purpose": "register"}'
```

**检查点**：
- [ ] 返回成功响应
- [ ] 包含 `"code": "SUCCESS"`

**预期结果**：
```json
{
  "code": "SUCCESS",
  "message": "验证码已发送",
  "data": {...}
}
```

**立即第二次请求（应失败）**：
```bash
curl -X POST http://localhost:8000/api/v1/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "purpose": "register"}'
```

**检查点**：
- [ ] 返回错误响应
- [ ] 包含 `"code": "VERIFICATION_CODE_RATE_LIMIT"`
- [ ] 包含 `"trace_id"`

**预期结果**：
```json
{
  "code": "VERIFICATION_CODE_RATE_LIMIT",
  "message": "验证码发送过于频繁，请稍后再试",
  "trace_id": "uuid-format"
}
```

**📸 截图 4**：保存第二次请求的错误响应截图

---

### ✅ 测试 3.4: 登录锁定（5次失败锁定15分钟）

**注册测试用户**：
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "locktest@example.com", "code": "123456", "nickname": "LockTest"}'
```

**连续5次错误登录**：
```bash
for i in {1..5}; do
  echo "尝试 $i:"
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "locktest@example.com", "code": "wrong"}'
  echo ""
done
```

**检查点**：
- [ ] 前5次返回 `"code": "INVALID_VERIFICATION_CODE"`

**第6次尝试（应显示锁定）**：
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "locktest@example.com", "code": "123456"}'
```

**检查点**：
- [ ] 返回 `"code": "ACCOUNT_LOCKED"`
- [ ] 消息包含 "15分钟"

**预期结果**：
```json
{
  "code": "ACCOUNT_LOCKED",
  "message": "账户已锁定，请15分钟后再试",
  "trace_id": "uuid-format"
}
```

**📸 截图 5**：保存账户锁定的响应截图

---

### ✅ 测试 3.5: 数据脱敏

**注册并登录**：
```bash
# 注册
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "mask@example.com", "code": "123456", "nickname": "MaskTest"}')

# 提取 token
TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "Token: $TOKEN"
```

**查询个人资料**：
```bash
curl http://localhost:8000/api/v1/members/me \
  -H "Authorization: Bearer $TOKEN"
```

**检查点**：
- [ ] 邮箱显示为 `mas***@example.com` 格式
- [ ] 不是明文 `mask@example.com`

**预期结果**：
```json
{
  "code": "SUCCESS",
  "data": {
    "id": 1,
    "email": "mas***@example.com",  // 已脱敏
    "nickname": "MaskTest",
    ...
  }
}
```

**📸 截图 6**：保存脱敏数据的响应截图

---

### ✅ 测试 3.6: 错误格式统一

**发送错误请求**：
```bash
curl -X POST http://localhost:8000/api/v1/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email": "invalid-email"}'
```

**检查点**：
- [ ] 包含 `"code"` 字段
- [ ] 包含 `"message"` 字段
- [ ] 包含 `"trace_id"` 字段

**预期结果**：
```json
{
  "code": "VALIDATION_ERROR",
  "message": "参数验证失败",
  "trace_id": "uuid-format",
  "details": {...}
}
```

---

### ✅ 测试 3.7: 管理员登录

**管理员登录**：
```bash
ADMIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

ADMIN_TOKEN=$(echo $ADMIN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "Admin Token: $ADMIN_TOKEN"
```

**检查点**：
- [ ] 登录成功
- [ ] 获得 access_token

---

### ✅ 测试 3.8: 审计日志

**查询审计日志**：
```bash
curl http://localhost:8000/api/v1/admin/audit-logs \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**检查点**：
- [ ] 返回审计日志列表
- [ ] 包含 `admin_user_id` 字段
- [ ] 包含 `action` 字段
- [ ] 包含 `resource` 字段
- [ ] 包含 `trace_id` 字段

**预期结果**：
```json
{
  "code": "SUCCESS",
  "data": {
    "items": [
      {
        "id": 1,
        "admin_user_id": 1,
        "action": "admin.login",
        "resource": "admin_users",
        "trace_id": "uuid-format",
        ...
      }
    ],
    ...
  }
}
```

---

## 第四步：文档完整性检查

### ✅ 测试 4.1: 必需文档文件

**操作**：
```bash
ls -lh README.md QUICK_REFERENCE.md PROJECT_SUMMARY.md LICENSE CONTRIBUTING.md session_trace.json
```

**检查点**：
- [ ] README.md 存在（> 10KB）
- [ ] QUICK_REFERENCE.md 存在
- [ ] PROJECT_SUMMARY.md 存在
- [ ] LICENSE 存在
- [ ] CONTRIBUTING.md 存在
- [ ] session_trace.json 存在（> 10KB）

---

### ✅ 测试 4.2: README 关键内容

**操作**：
```bash
# 检查启动命令
grep "docker compose up" README.md

# 检查测试账号
grep "admin123" README.md

# 检查服务地址
grep "8000" README.md
```

**检查点**：
- [ ] 包含 Docker 启动命令
- [ ] 包含测试账号信息
- [ ] 包含服务地址

---

## 第五步：GitHub 仓库检查

### ✅ 测试 5.1: 检查远程仓库

**操作**：
在浏览器中访问：`https://github.com/Dopamine-mania/Smart-Enjoy-Membership-System`

**检查点**：
- [ ] 仓库可以访问
- [ ] 所有文件已上传
- [ ] session_trace.json 在根目录
- [ ] README.md 正常显示

**📸 截图 7**：保存 GitHub 仓库首页截图

---

### ✅ 测试 5.2: 检查提交历史

**操作**：
点击 "commits" 查看提交历史

**检查点**：
- [ ] 至少有 3 次提交
- [ ] 提交信息清晰

---

## 📊 测试结果汇总

### 红线指标（一票否决项）
- [ ] Session 轨迹文件存在
- [ ] 无硬编码路径
- [ ] Docker 一键启动成功

### 业务逻辑核心指标
- [ ] 验证码限流（1/分钟，10/天）
- [ ] 登录锁定（5次失败锁定15分钟）
- [ ] 数据脱敏（邮箱）
- [ ] 错误格式统一

### 工程质量指标
- [ ] 审计日志完整
- [ ] 文档齐全
- [ ] GitHub 仓库完整

---

## 📸 需要准备的截图清单

1. ✅ Docker 启动成功（docker compose up -d）
2. ✅ 服务状态健康（docker compose ps）
3. ✅ Swagger 文档页面
4. ✅ 验证码限流错误响应
5. ✅ 账户锁定错误响应
6. ✅ 数据脱敏响应
7. ✅ GitHub 仓库首页

---

## ✅ 最终确认

所有测试通过后，确认以下信息：

**提交审核所需信息**：
- GitHub 仓库地址：`https://github.com/Dopamine-mania/Smart-Enjoy-Membership-System`
- Session 轨迹文件：`session_trace.json`（项目根目录）
- 测试账号：`admin / admin123`
- 启动命令：`cd docker && docker compose up -d`
- 服务地址：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

**预期得分**：150/150 分（满分）

---

## 🎯 如果测试失败怎么办？

### 问题 1: Docker 启动失败
**解决方案**：
```bash
# 查看详细日志
docker compose logs

# 检查端口占用
lsof -i :8000
lsof -i :5432
lsof -i :6379

# 重新构建
docker compose build --no-cache
docker compose up -d
```

### 问题 2: API 返回 500 错误
**解决方案**：
```bash
# 查看应用日志
docker compose logs app

# 检查数据库连接
docker compose exec postgres psql -U postgres -d membership_db -c "\dt"

# 检查 Redis 连接
docker compose exec redis redis-cli ping
```

### 问题 3: 验证码限流不生效
**解决方案**：
- 检查 Redis 是否正常运行
- 查看应用日志中的 Redis 连接信息
- 确认 `.env` 文件中的 Redis 配置正确

### 问题 4: 数据脱敏不生效
**解决方案**：
- 检查 `app/utils/data_masking.py` 文件
- 确认 API 响应中调用了 `mask_email()` 函数
- 查看应用日志

---

## 📝 测试完成后的操作

1. **整理截图**：将 7 张截图保存到一个文件夹
2. **录制视频**（可选）：1-2 分钟演示完整流程
3. **填写提交表格**：准备好所有信息
4. **提交审核**：上传材料并提交

---

**祝你审核顺利通过！预期获得满分 150/150 分！** 🎉
