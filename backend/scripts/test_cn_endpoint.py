"""测试 CN 端点获取商品列表"""
import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.temu.client import TemuAPIClient


async def test_cn_endpoint():
    """测试 CN 端点获取商品列表"""
    
    # CN 端点配置
    cn_base_url = "https://openapi.kuajingmaihuo.com/openapi/router"
    app_key = "af5bcf5d4bd5a492fa09c2ee302d75b9"
    app_secret = "e4f229bb9c4db21daa999e73c8683d42ba0a7094"
    access_token = "fqcc2cjys63s1hmctczonulmsbj84vkoogwpe1gwpvvhiav7x2vfovt0"
    
    print("=" * 60)
    print("测试 CN 端点获取商品列表")
    print("=" * 60)
    print(f"接口地址: {cn_base_url}")
    print(f"App Key: {app_key}")
    print(f"Access Token: {access_token[:20]}...")
    print("=" * 60)
    print()
    
    # 创建 API 客户端
    client = TemuAPIClient(
        app_key=app_key,
        app_secret=app_secret,
        proxy_url=None  # 不使用代理，直接请求
    )
    
    # 覆盖 base_url 为 CN 端点
    client.base_url = cn_base_url
    
    try:
        # 先测试 Token 验证
        print("步骤 1: 验证 Token...")
        print(f"API 类型: bg.open.accesstoken.info.get")
        print()
        
        try:
            token_info = await client.get_token_info(access_token)
            print("✅ Token 验证成功！")
            print(f"Token 信息: {json.dumps(token_info, indent=2, ensure_ascii=False)}")
            print()
            
            # 检查 API 权限范围
            api_scope_list = token_info.get("apiScopeList", [])
            if api_scope_list:
                print(f"已授权的 API 列表 ({len(api_scope_list)} 个):")
                for api in api_scope_list[:20]:  # 只显示前 20 个
                    print(f"  - {api}")
                if len(api_scope_list) > 20:
                    print(f"  ... 还有 {len(api_scope_list) - 20} 个")
                print()
        except Exception as e:
            print(f"⚠️ Token 验证失败: {e}")
            print()
        
        # 尝试不同的商品列表 API 类型和参数格式
        test_cases = [
            {
                "api_type": "bg.local.goods.list.query",
                "request_data": {"pageNumber": 1, "pageSize": 10}
            },
            {
                "api_type": "bg.local.goods.list.query",
                "request_data": {"pageNo": 1, "pageSize": 10}
            },
            {
                "api_type": "bg.goods.list.get",
                "request_data": {"pageNumber": 1, "pageSize": 10}
            },
            {
                "api_type": "bg.goods.list.get",
                "request_data": {"pageNo": 1, "pageSize": 10}
            },
            {
                "api_type": "bg.goods.list.query",
                "request_data": {"pageNumber": 1, "pageSize": 10}
            },
            {
                "api_type": "bg.local.goods.list.get",
                "request_data": {"pageNumber": 1, "pageSize": 10}
            },
        ]
        
        print("步骤 2: 尝试获取商品列表...")
        print()
        
        success = False
        for i, test_case in enumerate(test_cases, 1):
            api_type = test_case["api_type"]
            request_data = test_case["request_data"]
            
            print(f"测试 {i}/{len(test_cases)}: {api_type}")
            print(f"  参数: {request_data}")
            try:
                # 直接调用 _request 方法
                result = await client._request(
                    api_type=api_type,
                    request_data=request_data,
                    access_token=access_token
                )
                
                print(f"✅ 成功！API 类型: {api_type}")
                print()
                print("响应结果:")
                print("-" * 60)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                print("-" * 60)
                print()
                
                # 解析并显示关键信息
                if isinstance(result, dict):
                    # CN 端点使用 data 字段和 totalCount
                    total = result.get("totalCount", result.get("totalItemNum", result.get("total", result.get("totalNum", 0))))
                    goods_list = result.get("data", result.get("goodsList", result.get("list", [])))
                    
                    print(f"商品总数: {total}")
                    print(f"当前页商品数: {len(goods_list) if isinstance(goods_list, list) else 0}")
                    print()
                    
                    if isinstance(goods_list, list) and len(goods_list) > 0:
                        print("商品列表预览（前 3 条）:")
                        for i, goods in enumerate(goods_list[:3], 1):
                            print(f"\n商品 {i}:")
                            # CN 端点使用 productId 和 productName
                            product_id = goods.get('productId', goods.get('goodsId', goods.get('id', 'N/A')))
                            product_name = goods.get('productName', goods.get('goodsName', goods.get('name', 'N/A')))
                            product_status = goods.get('skcSiteStatus', goods.get('goodsStatus', goods.get('status', 'N/A')))
                            print(f"  - 商品ID: {product_id}")
                            print(f"  - 商品名称: {product_name[:80]}..." if len(str(product_name)) > 80 else f"  - 商品名称: {product_name}")
                            print(f"  - 商品状态: {product_status}")
                            if goods.get('mainImageUrl'):
                                print(f"  - 主图: {goods.get('mainImageUrl')[:60]}...")
                
                success = True
                break
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ 失败: {error_msg}")
                print()
                continue
        
        if not success:
            print("所有 API 类型都失败了。")
            return False
        
    except Exception as e:
        print("❌ 请求失败！")
        print()
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print()
        
        # 如果是 HTTP 错误，显示更多信息
        if hasattr(e, 'response'):
            print("HTTP 响应详情:")
            try:
                error_detail = e.response.json() if hasattr(e.response, 'json') else str(e.response.text)
                print(json.dumps(error_detail, indent=2, ensure_ascii=False))
            except:
                print(f"状态码: {e.response.status_code}")
                print(f"响应内容: {e.response.text}")
        
        return False
    
    finally:
        await client.close()
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_cn_endpoint())
    sys.exit(0 if success else 1)

