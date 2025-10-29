# Temu-Omni Makefile
# 快速命令集合

.PHONY: help dev dev-up dev-down dev-logs dev-restart prod-build prod-up prod-down clean db-init db-backup

# 默认目标
help:
	@echo "Temu-Omni 开发命令："
	@echo ""
	@echo "开发环境："
	@echo "  make dev          - 启动开发环境（后台运行）"
	@echo "  make dev-up       - 启动开发环境"
	@echo "  make dev-down     - 停止开发环境"
	@echo "  make dev-logs     - 查看开发环境日志"
	@echo "  make dev-restart  - 重启开发环境"
	@echo ""
	@echo "生产环境："
	@echo "  make prod-build   - 构建生产环境镜像"
	@echo "  make prod-up      - 启动生产环境"
	@echo "  make prod-down    - 停止生产环境"
	@echo ""
	@echo "数据库："
	@echo "  make db-init      - 初始化数据库"
	@echo "  make db-backup    - 备份数据库"
	@echo ""
	@echo "其他："
	@echo "  make clean        - 清理所有容器和数据卷"

# 开发环境
dev:
	docker-compose up -d

dev-up:
	docker-compose up

dev-down:
	docker-compose down

dev-logs:
	docker-compose logs -f

dev-restart:
	docker-compose restart

# 生产环境
prod-build:
	docker-compose -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.prod.yml down

# 数据库操作
db-init:
	docker-compose exec backend python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
	@echo "数据库初始化完成！"

db-backup:
	docker-compose exec postgres pg_dump -U temu_user temu_omni > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "数据库备份完成！"

# 清理
clean:
	docker-compose down -v
	@echo "所有容器和数据卷已清理！"

