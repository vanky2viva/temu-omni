"""统一的环境变量加载工具"""
from pathlib import Path
from dotenv import load_dotenv
import os


def load_env_file():
    """
    加载环境变量文件
    
    按优先级查找并加载 .env 文件：
    1. 项目根目录/.env（优先）
    2. 项目根目录/.env.production
    3. backend/.env（向后兼容）
    
    Returns:
        str: 加载的 .env 文件路径，如果未找到则返回 None
    """
    # 获取项目根目录
    # __file__ 是 backend/app/core/env_loader.py
    # 所以 backend_dir 是 backend 目录
    # root_dir 是项目根目录（backend 的父目录）
    current_file = Path(__file__)
    backend_dir = current_file.parent.parent.parent  # backend/
    root_dir = backend_dir.parent  # 项目根目录
    
    # 按优先级查找 .env 文件
    env_files = [
        root_dir / ".env",           # 项目根目录（优先）
        root_dir / ".env.production", # 生产环境配置
        backend_dir / ".env",        # backend 目录（向后兼容）
    ]
    
    # 找到第一个存在的 .env 文件并加载
    for env_path in env_files:
        if env_path.exists():
            load_dotenv(env_path, override=False)  # override=False 表示不覆盖已存在的环境变量
            return str(env_path)
    
    return None


# 自动加载（在模块导入时执行）
_loaded_env_file = load_env_file()

