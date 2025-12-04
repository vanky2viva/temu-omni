#!/usr/bin/env python3
"""
清理卡住的同步状态脚本
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import redis
import json
from app.core.config import settings

def clear_stuck_sync(shop_id: int = None):
    """清理卡住的同步状态"""
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
            
            if shop_id:
                # 清理指定店铺的同步状态
                progress_key = f"sync_progress:{shop_id}"
                logs_key = f"sync_logs:{shop_id}"
                
                redis_client.delete(progress_key)
                redis_client.delete(logs_key)
                print(f"✅ 已清理店铺 ID {shop_id} 的同步状态")
            else:
                # 清理所有店铺的同步状态
                print("⚠️  清理所有店铺的同步状态...")
                
                # 查找所有同步进度键
                progress_keys = redis_client.keys("sync_progress:*")
                logs_keys = redis_client.keys("sync_logs:*")
                
                if progress_keys:
                    for key in progress_keys:
                        redis_client.delete(key)
                        print(f"   已删除: {key}")
                
                if logs_keys:
                    for key in logs_keys:
                        redis_client.delete(key)
                        print(f"   已删除: {key}")
                
                if not progress_keys and not logs_keys:
                    print("   ✅ 没有找到需要清理的同步状态")
                else:
                    print(f"\n✅ 已清理 {len(progress_keys)} 个进度键和 {len(logs_keys)} 个日志键")
            
        else:
            print("❌ Redis URL 格式不正确")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import sys
    shop_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    clear_stuck_sync(shop_id)


