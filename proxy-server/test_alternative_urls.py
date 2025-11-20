#!/usr/bin/env python3
"""测试不同的 API URL"""
import requests
import json
import hashlib
import time

def generate_sign(app_secret, params):
    temp = []
    sorted_params = sorted(params.items())
    for key, value in sorted_params:
        if value is not None:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            temp.append(str(key) + str(value).strip("\""))
    un_sign = "".join(temp)
    un_sign = str(app_secret) + un_sign + str(app_secret)
    sign = hashlib.md5(un_sign.encode("utf-8")).hexdigest().upper()
    return sign

app_key = "798478197604e93f6f2ce4c2e833041u"
app_secret = "776a96163c56c53e237f5456d4e14765301aa8aa"
access_token = "upsfmfl9g5bbxpn8rvhols3c959kghjc0cvcripjfsmfzihkykxsaobrb3k"

# 测试不同的 API URL
api_urls = [
    "https://agentpartner.temu.com/api",
    "https://openapi-b-us.temu.com/openapi/router",
    "https://openapi.temu.com/openapi/router"
]

api_type = "bg.open.accesstoken.info.get"
timestamp = int(time.time())
common_params = {
    "app_key": app_key,
    "data_type": "JSON",
    "timestamp": timestamp,
    "type": api_type,
    "version": "V1",
    "access_token": access_token
}
sign = generate_sign(app_secret, common_params)
request_payload = {**common_params, "sign": sign}

print("="*80)
print("测试不同的 API URL")
print("="*80)

for api_url in api_urls:
    print(f"\n{'='*80}")
    print(f"测试 API URL: {api_url}")
    print(f"{'='*80}")
    try:
        response = requests.post(
            api_url, 
            json=request_payload, 
            headers={"Content-Type": "application/json"}, 
            timeout=10
        )
        print(f"HTTP 状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        if response.status_code == 200 and result.get("success"):
            print(f"\n✅ 成功! 正确的 API URL 是: {api_url}")
            break
        elif response.status_code == 403:
            error_code = result.get("error_code", "未知")
            error_msg = result.get("error_msg", "")
            print(f"❌ 403 错误: error_code={error_code}, error_msg={error_msg}")
    except Exception as e:
        print(f"❌ 错误: {e}")


