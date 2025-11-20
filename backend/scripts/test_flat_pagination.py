#!/usr/bin/env python3
"""Test Pagination with Flat Params"""
import asyncio
import sys
import json
import time
import hashlib
import httpx
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.core.config import settings

class DebugClient:
    def __init__(self, app_key, app_secret, base_url):
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    def _generate_sign(self, params: Dict[str, Any]) -> str:
        temp = []
        sorted_params = sorted(params.items())
        for key, value in sorted_params:
            if value is not None:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
                temp.append(str(key) + str(value).strip('\"'))
        
        un_sign = ''.join(temp)
        un_sign = str(self.app_secret) + un_sign + str(self.app_secret)
        return hashlib.md5(un_sign.encode('utf-8')).hexdigest().upper()

    async def request_flat(self, api_type, params, access_token):
        """参数平铺测试"""
        timestamp = int(time.time())
        common_params = {
            "app_key": self.app_key,
            "data_type": "JSON",
            "timestamp": timestamp,
            "type": api_type,
            "version": "V1",
            "access_token": access_token
        }
        all_params = {**common_params, **params}
        sign = self._generate_sign(all_params)
        request_payload = {**all_params, "sign": sign}
        
        resp = await self.client.post(self.base_url, json=request_payload)
        return resp.json()

async def test_pagination():
    db = SessionLocal()
    try:
        shop = db.query(Shop).filter(Shop.shop_name == "festival finds").first()
        if not shop: return

        cn_app_key = shop.cn_app_key or settings.TEMU_CN_APP_KEY
        cn_app_secret = shop.cn_app_secret or settings.TEMU_CN_APP_SECRET
        base_url = shop.cn_api_base_url or 'https://openapi.kuajingmaihuo.com/openapi/router'
        
        client = DebugClient(cn_app_key, cn_app_secret, base_url)
        
        print("🔍 测试 bg.goods.list.get 分页 (Flat)...")
        
        # Page 1
        res1 = await client.request_flat("bg.goods.list.get", {"page": 1, "pageSize": 5}, shop.cn_access_token)
        ids1 = [i.get('productId') for i in res1.get('result', {}).get('data', [])]
        print(f"Page 1: {ids1}")
        
        # Page 2
        res2 = await client.request_flat("bg.goods.list.get", {"page": 2, "pageSize": 5}, shop.cn_access_token)
        ids2 = [i.get('productId') for i in res2.get('result', {}).get('data', [])]
        print(f"Page 2: {ids2}")
        
        if ids1 and ids2 and ids1[0] != ids2[0]:
            print("✅ 分页正常工作")
        else:
            print("⚠️ 分页依然重复")
            
        await client.client.aclose()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_pagination())

