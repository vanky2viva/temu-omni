#!/usr/bin/env python3
"""
检查同步状态脚本 - 诊断卡住的同步进程
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import redis
import json

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.core.config import settings

def check_sync_status():
    """检查同步状态"""
    db: Session = SessionLocal()
    
    try:
        # 检查 Redis 中的同步进度
        try:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://redis:6379/0')
            if redis_url.startswith('redis://'):
                import urllib.parse
                parsed = urllib.parse.urlparse(redis_url)
                redis_password = parsed.password if parsed.password else None
                redis_host = parsed.hostname or 'redis'
                redis_port = parsed.port or 6379
                redis_db = int(parsed.path.lstrip('/')) if parsed.path else 0
                
                redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                redis_client.ping()
                
                print("✅ Redis 连接成功\n")
                
                # 检查所有店铺的同步状态
                shops = db.query(Shop).all()
                print(f"📊 检查 {len(shops)} 个店铺的同步状态:\n")
                
                for shop in shops:
                    progress_key = f"sync_progress:{shop.id}"
                    logs_key = f"sync_logs:{shop.id}"
                    
                    # 获取同步进度
                    progress_data = redis_client.get(progress_key)
                    if progress_data:
                        progress = json.loads(progress_data)
                        status = progress.get('status', 'unknown')
                        progress_percent = progress.get('progress', 0)
                        
                        if status == 'in_progress':
                            print(f"⚠️  店铺 {shop.shop_name} (ID: {shop.id}):")
                            print(f"   状态: {status}")
                            print(f"   进度: {progress_percent}%")
                            print(f"   最后更新: {progress.get('last_update', 'N/A')}")
                            
                            # 检查是否卡住（超过10分钟没有更新）
                            last_update_str = progress.get('last_update')
                            if last_update_str:
                                try:
                                    last_update = datetime.fromisoformat(last_update_str)
                                    now = datetime.now()
                                    elapsed = (now - last_update).total_seconds()
                                    
                                    if elapsed > 600:  # 10分钟
                                        print(f"   ⚠️  可能卡住: 已超过 {int(elapsed/60)} 分钟没有更新")
                                        print(f"   💡 建议: 清除同步状态并重新同步")
                                        
                                        # 提供清除命令
                                        print(f"   🔧 清除命令: redis-cli DEL {progress_key}")
                                    else:
                                        print(f"   ✅ 正常: {int(elapsed)} 秒前更新")
                                except Exception as e:
                                    print(f"   ⚠️  无法解析最后更新时间: {e}")
                            
                            # 获取最近的日志
                            logs = redis_client.lrange(logs_key, 0, 4)
                            if logs:
                                print(f"   最近日志:")
                                for log_str in logs:
                                    try:
                                        log = json.loads(log_str)
                                        print(f"     [{log.get('timestamp', 'N/A')}] {log.get('message', 'N/A')}")
                                    except:
                                        pass
                            print()
                    else:
                        print(f"✅ 店铺 {shop.shop_name} (ID: {shop.id}): 无同步任务\n")
                
            else:
                print("❌ Redis URL 格式不正确")
        except Exception as e:
            print(f"❌ Redis 连接失败: {e}")
            print("   同步状态可能存储在内存中（多 worker 环境下可能丢失）")
        
        # 检查数据库连接
        print("\n📊 数据库连接状态:")
        try:
            from sqlalchemy import text
            result = db.execute(text("SELECT 1"))
            print("✅ 数据库连接正常")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    check_sync_status()

