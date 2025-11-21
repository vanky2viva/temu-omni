# 502错误快速修复指南

## 🚀 快速修复步骤

### 方法1: 重启所有服务（推荐）

在服务器上执行：

```bash
cd /path/to/temu-Omni

# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 等待30秒让服务启动
sleep 30

# 检查状态
docker-compose -f docker-compose.prod.yml ps
```

### 方法2: 运行诊断脚本

```bash
cd /path/to/temu-Omni
./scripts/diagnose_502.sh
```

脚本会自动检查所有问题并给出修复建议。

### 方法3: 完全重启

```bash
cd /path/to/temu-Omni

# 停止所有服务
docker-compose -f docker-compose.prod.yml down

# 重新启动
docker-compose -f docker-compose.prod.yml up -d

# 等待启动完成
sleep 60

# 检查状态
docker-compose -f docker-compose.prod.yml ps
```

---

## 🔍 常见原因和解决方法

### 原因1: 后端服务未启动

**检查**:
```bash
docker-compose -f docker-compose.prod.yml ps backend
```

**修复**:
```bash
# 查看后端日志
docker-compose -f docker-compose.prod.yml logs backend

# 重启后端
docker-compose -f docker-compose.prod.yml restart backend
```

### 原因2: 前端服务未启动

**检查**:
```bash
docker-compose -f docker-compose.prod.yml ps frontend
```

**修复**:
```bash
# 查看前端日志
docker-compose -f docker-compose.prod.yml logs frontend

# 重启前端
docker-compose -f docker-compose.prod.yml restart frontend
```

### 原因3: 数据库连接失败

**检查**:
```bash
docker-compose -f docker-compose.prod.yml logs backend | grep -i "database\|connection"
```

**修复**:
```bash
# 检查数据库容器
docker-compose -f docker-compose.prod.yml ps postgres

# 检查环境变量
docker-compose -f docker-compose.prod.yml exec backend env | grep DATABASE_URL
```

### 原因4: 容器网络问题

**修复**:
```bash
# 重新创建网络
docker-compose -f docker-compose.prod.yml down
docker network prune -f
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📞 需要帮助？

如果问题仍未解决，请提供以下信息：

1. 运行诊断脚本的输出:
   ```bash
   ./scripts/diagnose_502.sh > diagnose_output.txt
   ```

2. 容器状态:
   ```bash
   docker-compose -f docker-compose.prod.yml ps > container_status.txt
   ```

3. 错误日志:
   ```bash
   docker-compose -f docker-compose.prod.yml logs > all_logs.txt
   ```

---

*详细排查步骤请查看 [FIX_502_ERROR.md](FIX_502_ERROR.md)*


