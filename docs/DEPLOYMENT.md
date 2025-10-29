# 部署指南

## 开发环境部署

### 1. 后端部署

#### 安装依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 配置数据库

创建PostgreSQL数据库：

```sql
CREATE DATABASE temu_omni;
CREATE USER temu_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE temu_omni TO temu_user;
```

#### 配置环境变量

复制 `env.template` 为 `.env` 并填写配置：

```bash
cp env.template .env
# 编辑 .env 文件
```

必需的配置项：
- `DATABASE_URL`: 数据库连接字符串
- `SECRET_KEY`: 应用密钥
- `TEMU_APP_KEY`: Temu API密钥
- `TEMU_APP_SECRET`: Temu API密钥

#### 初始化数据库

```bash
# 创建表
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

#### 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务将运行在 http://localhost:8000

访问 http://localhost:8000/docs 查看API文档

### 2. 前端部署

#### 安装依赖

```bash
cd frontend
npm install
```

#### 启动开发服务器

```bash
npm run dev
```

前端将运行在 http://localhost:5173

## 生产环境部署

### 1. 后端生产部署

#### 使用Gunicorn

```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 使用Supervisor

创建 `/etc/supervisor/conf.d/temu-omni.conf`：

```ini
[program:temu-omni-backend]
directory=/path/to/temu-Omni/backend
command=/path/to/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
user=your_user
autostart=true
autorestart=true
stderr_logfile=/var/log/temu-omni/backend.err.log
stdout_logfile=/var/log/temu-omni/backend.out.log
```

#### 使用Nginx反向代理

创建 `/etc/nginx/sites-available/temu-omni`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        root /path/to/temu-Omni/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

### 2. 前端生产部署

#### 构建

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist` 目录

#### 使用Nginx托管

配置已包含在上面的Nginx配置中。

## Docker部署

### 创建Dockerfile（后端）

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 创建Dockerfile（前端）

```dockerfile
FROM node:18 AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

### Docker Compose

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: temu_omni
      POSTGRES_USER: temu_user
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://temu_user:your_password@postgres:5432/temu_omni
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

启动：

```bash
docker-compose up -d
```

## 数据备份

### 备份数据库

```bash
pg_dump -U temu_user -h localhost temu_omni > backup_$(date +%Y%m%d).sql
```

### 恢复数据库

```bash
psql -U temu_user -h localhost temu_omni < backup_20240101.sql
```

## 监控和日志

### 查看应用日志

```bash
# Supervisor
tail -f /var/log/temu-omni/backend.out.log

# Docker
docker-compose logs -f backend
```

### 设置日志轮转

创建 `/etc/logrotate.d/temu-omni`：

```
/var/log/temu-omni/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 your_user your_user
    sharedscripts
    postrotate
        supervisorctl restart temu-omni-backend
    endscript
}
```

