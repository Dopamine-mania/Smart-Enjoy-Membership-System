# Contributing to Smart Enjoy Membership System

感谢你对智享会员系统的关注！我们欢迎任何形式的贡献。

## 如何贡献

### 报告 Bug

如果你发现了 bug，请创建一个 issue 并包含以下信息：

- Bug 的详细描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息（操作系统、Python 版本、Docker 版本等）
- 相关日志或截图

### 提出新功能

如果你有新功能的想法：

1. 先创建一个 issue 讨论这个功能
2. 说明为什么需要这个功能
3. 描述预期的实现方式
4. 等待维护者反馈

### 提交代码

1. **Fork 仓库**
   ```bash
   # 在 GitHub 上 fork 仓库
   git clone https://github.com/YOUR_USERNAME/Smart-Enjoy-Membership-System.git
   cd Smart-Enjoy-Membership-System
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **开发和测试**
   - 遵循现有的代码风格
   - 添加必要的测试
   - 确保所有测试通过
   - 更新相关文档

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   # 或
   git commit -m "fix: fix your bug description"
   ```

   提交信息格式：
   - `feat:` 新功能
   - `fix:` Bug 修复
   - `docs:` 文档更新
   - `style:` 代码格式调整
   - `refactor:` 代码重构
   - `test:` 测试相关
   - `chore:` 构建或辅助工具变动

5. **推送到 GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **创建 Pull Request**
   - 在 GitHub 上创建 PR
   - 描述你的更改
   - 关联相关的 issue
   - 等待代码审查

## 代码规范

### Python 代码风格

- 遵循 PEP 8 规范
- 使用类型注解
- 添加文档字符串
- 保持函数简洁（单一职责）

### 目录结构

```
app/
├── api/v1/          # API 端点
├── core/            # 核心功能
├── middleware/      # 中间件
├── models/          # 数据库模型
├── schemas/         # Pydantic 模型
├── services/        # 业务逻辑
├── repositories/    # 数据访问
└── utils/           # 工具函数
```

### 测试

- 为新功能添加单元测试
- 确保测试覆盖率不降低
- 运行 `pytest` 确保所有测试通过

### 文档

- 更新 README.md（如果需要）
- 添加 API 文档注释
- 更新 CHANGELOG.md

## 开发环境设置

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **启动服务**
   ```bash
   cd docker
   docker compose up -d
   ```

3. **运行测试**
   ```bash
   pytest tests/
   ```

4. **代码检查**
   ```bash
   python3 check_syntax.py
   ```

## 问题和讨论

- 使用 GitHub Issues 报告问题
- 使用 GitHub Discussions 进行讨论
- 加入我们的社区（如果有）

## 行为准则

- 尊重所有贡献者
- 保持友好和专业
- 接受建设性批评
- 关注项目的最佳利益

## 许可证

通过贡献代码，你同意你的贡献将在 MIT 许可证下发布。

---

再次感谢你的贡献！🎉
