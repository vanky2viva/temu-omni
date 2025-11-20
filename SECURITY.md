# 安全指南

## 敏感信息处理

本项目包含敏感信息，请遵循以下安全准则：

### 1. 环境变量

所有敏感信息必须通过环境变量配置，**不要**硬编码在代码中。

敏感信息包括：
- API密钥（App Key / App Secret）
- 访问令牌（Access Token）
- 数据库连接字符串
- 代理服务器地址
- 其他认证凭据

### 2. 配置文件

- `.env` 文件包含敏感信息，**永远不要**提交到Git仓库
- 使用 `.env.template` 或 `env.template` 作为配置模板
- 在部署时，从安全存储（如密钥管理服务）获取环境变量

### 3. Git提交前检查

在提交代码前，请确保：
- ✅ 没有硬编码的API密钥、令牌或密码
- ✅ `.env` 文件在 `.gitignore` 中
- ✅ 没有提交包含敏感信息的测试脚本
- ✅ 使用 `git-secrets` 或类似工具检查敏感信息

### 4. 如果敏感信息已提交

如果敏感信息已经被提交到Git仓库：

1. **立即轮换所有泄露的凭据**
2. 从Git历史中移除敏感信息：
   ```bash
   # 使用 git-filter-repo 或 BFG Repo-Cleaner
   git filter-repo --invert-paths --path sensitive-file.txt
   ```
3. 强制推送（注意：这会重写历史）
   ```bash
   git push origin --force --all
   ```

### 5. 代码审查

在代码审查时，特别注意：
- 检查是否有硬编码的敏感信息
- 确认所有敏感配置都从环境变量读取
- 验证 `.gitignore` 正确配置

## 环境变量清单

请确保以下环境变量已正确配置：

### 必需的环境变量

```bash
# 标准端点配置
TEMU_APP_KEY=your_app_key
TEMU_APP_SECRET=your_app_secret

# CN端点配置
TEMU_CN_APP_KEY=your_cn_app_key
TEMU_CN_APP_SECRET=your_cn_app_secret

# 代理配置
TEMU_API_PROXY_URL=http://your-proxy-server:8001

# 数据库配置
DATABASE_URL=postgresql://user:password@host:port/database

# 应用密钥
SECRET_KEY=your-secret-key
```

参考 `backend/env.template` 获取完整的环境变量列表。

