#!/usr/bin/env python3
"""重启后端服务并清除连接池的脚本"""
import os
import sys

def restart_backend_service():
    """重启后端服务的辅助脚本"""
    print("=" * 60)
    print("后端服务重启指南")
    print("=" * 60)
    print("\n字段已成功添加到数据库，但后端服务需要重启才能使用新字段。")
    print("\n请选择重启方式：\n")
    
    print("方式1: 如果使用Docker Compose")
    print("  docker-compose restart backend")
    print("  或")
    print("  docker-compose down && docker-compose up -d\n")
    
    print("方式2: 如果使用Docker直接运行")
    print("  docker restart temu-omni-backend\n")
    
    print("方式3: 如果是直接运行Python进程")
    print("  1. 找到运行后端服务的进程并停止")
    print("  2. 重新启动后端服务:")
    print("     cd backend && python3 -m uvicorn app.main:app --reload\n")
    
    print("方式4: 如果是使用systemd或supervisor")
    print("  sudo systemctl restart temu-omni-backend")
    print("  或")
    print("  sudo supervisorctl restart temu-omni-backend\n")
    
    print("=" * 60)
    print("重启后，请重新尝试导入商品数据")
    print("=" * 60)


if __name__ == "__main__":
    restart_backend_service()

