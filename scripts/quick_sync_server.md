# 服务器同步更新 - 快速解决方案

## 问题
服务器执行 `git pull origin main` 时遇到本地更改冲突：
```
error: Your local changes to the following files would be overwritten by merge:
        frontend/src/services/orderCostApi.ts
Please commit your changes or stash them before you merge.
```

## 解决方案

### 方案1：快速同步（丢弃本地更改） ⚡

如果服务器上的本地更改不重要，直接丢弃并使用远程版本：

```bash
# 1. 丢弃本地更改
git checkout -- frontend/src/services/orderCostApi.ts

# 2. 拉取远程更新
git pull origin main

# 3. 完成！
```

### 方案2：安全同步（保留本地更改） 🔒

如果服务器上的本地更改可能重要，先暂存再合并：

```bash
# 1. 暂存本地更改
git stash push -m "服务器本地更改备份"

# 2. 拉取远程更新
git pull origin main

# 3. 尝试应用本地更改
git stash pop

# 4. 如果有冲突，手动解决：
#    - 查看冲突：git status
#    - 编辑冲突文件：vim frontend/src/services/orderCostApi.ts
#    - 解决冲突后：git add frontend/src/services/orderCostApi.ts
#    - 提交：git commit -m "解决合并冲突"
```

### 方案3：查看差异后决定 🔍

```bash
# 1. 查看本地更改内容
git diff frontend/src/services/orderCostApi.ts

# 2. 根据内容决定使用方案1还是方案2
```

## 推荐操作

**如果是生产服务器，建议使用方案1（快速同步）**，因为：
- 生产环境应该使用版本控制的代码
- 本地临时修改应该通过正常流程提交
- 避免合并冲突的风险

## 完整操作流程

```bash
# 在服务器上执行
cd ~/temu-omni  # 或你的项目目录

# 查看当前状态
git status

# 快速同步（丢弃本地更改）
git checkout -- frontend/src/services/orderCostApi.ts
git pull origin main

# 验证
git status
```





