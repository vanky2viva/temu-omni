"""飞书在线表格服务"""
import re
import httpx
import pandas as pd
from typing import Dict, Any, Optional, List
from loguru import logger


class FeishuSheetsService:
    """飞书在线表格服务类"""
    
    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        """
        初始化飞书API客户端
        
        Args:
            app_id: 飞书应用ID（可选，使用环境变量）
            app_secret: 飞书应用密钥（可选，使用环境变量）
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://open.feishu.cn/open-apis"
        self.access_token = None
    
    async def get_access_token(self) -> str:
        """
        获取飞书访问令牌
        
        Returns:
            访问令牌
        """
        if not self.app_id or not self.app_secret:
            # 如果没有配置飞书凭证，返回空token（将在后续使用公开分享链接）
            logger.warning("飞书App ID和Secret未配置，将尝试使用公开分享链接")
            return ""
        
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            result = response.json()
            
            if result.get("code") == 0:
                self.access_token = result.get("tenant_access_token")
                return self.access_token
            else:
                raise Exception(f"获取飞书访问令牌失败: {result.get('msg')}")
    
    def parse_feishu_url(self, url: str) -> Dict[str, str]:
        """
        解析飞书表格URL，提取spreadsheet_token和sheet_id
        
        Args:
            url: 飞书表格URL
            
        Returns:
            包含spreadsheet_token和sheet_id的字典
            
        Example:
            https://mcnkufobiqbi.feishu.cn/sheets/Xd3SsrVlEhNoBXtawvlcryWVnJc?sheet=HPLHTM
            -> {
                'spreadsheet_token': 'Xd3SsrVlEhNoBXtawvlcryWVnJc',
                'sheet_id': 'HPLHTM'
            }
        """
        # 提取 host
        host_match = re.search(r'https?://([^/]+)', url)
        host = host_match.group(1) if host_match else 'bytedance.feishu.cn'

        # 提取 spreadsheet_token
        spreadsheet_pattern = r'/sheets/([A-Za-z0-9_-]+)'
        spreadsheet_match = re.search(spreadsheet_pattern, url)
        
        if not spreadsheet_match:
            raise ValueError("无法从URL中提取表格ID，请确保URL格式正确")
        
        spreadsheet_token = spreadsheet_match.group(1)
        
        # 提取 sheet_id (可选)
        sheet_id = None
        sheet_pattern = r'[?&]sheet=([A-Za-z0-9_-]+)'
        sheet_match = re.search(sheet_pattern, url)
        
        if sheet_match:
            sheet_id = sheet_match.group(1)
        
        return {
            'host': host,
            'spreadsheet_token': spreadsheet_token,
            'sheet_id': sheet_id
        }
    
    async def read_sheet_data(
        self, 
        spreadsheet_token: str, 
        sheet_id: Optional[str] = None,
        range_notation: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None
    ) -> pd.DataFrame:
        """
        读取飞书表格数据
        
        Args:
            spreadsheet_token: 表格token
            sheet_id: 工作表ID（可选）
            range_notation: 范围标记，如"A1:Z1000"（可选）
            password: 表格访问密码（可选）
            
        Returns:
            pandas DataFrame
        """
        # 方法1: 尝试通过API读取（需要授权）
        try:
            if self.app_id and self.app_secret:
                return await self._read_via_api(spreadsheet_token, sheet_id, range_notation)
        except Exception as e:
            logger.warning(f"通过API读取失败: {e}，尝试使用导出方式")
        
        # 方法2: 尝试通过导出链接读取（公开表格或密码保护表格）
        return await self._read_via_export(spreadsheet_token, sheet_id, password, host)
    
    async def _read_via_api(
        self, 
        spreadsheet_token: str, 
        sheet_id: Optional[str] = None,
        range_notation: Optional[str] = None
    ) -> pd.DataFrame:
        """通过飞书API读取表格数据"""
        if not self.access_token:
            await self.get_access_token()
        
        # 获取工作表元数据
        if not sheet_id:
            sheet_id = await self._get_first_sheet_id(spreadsheet_token)
        
        # 读取数据
        url = f"{self.base_url}/sheets/v2/spreadsheets/{spreadsheet_token}/values/{sheet_id}"
        if range_notation:
            url += f"!{range_notation}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            result = response.json()
            
            if result.get("code") == 0:
                data = result.get("data", {})
                values = data.get("values", [])
                
                if not values:
                    raise ValueError("表格数据为空")
                
                # 第一行作为列名
                columns = values[0]
                rows = values[1:]
                
                # 创建DataFrame
                df = pd.DataFrame(rows, columns=columns)
                return df
            else:
                raise Exception(f"读取表格数据失败: {result.get('msg')}")
    
    async def _read_via_export(
        self, 
        spreadsheet_token: str, 
        sheet_id: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None
    ) -> pd.DataFrame:
        """
        通过导出链接读取表格数据（适用于公开分享或密码保护的表格）
        
        Args:
            spreadsheet_token: 表格token
            sheet_id: 工作表ID
            password: 访问密码（用于密码保护的表格）
        """
        # 构建导出URL（同域）
        domain = host or 'bytedance.feishu.cn'
        export_url = f"https://{domain}/sheets/{spreadsheet_token}"
        if sheet_id:
            export_url += f"?sheet={sheet_id}"
        
        # 准备请求头和cookies
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/csv,application/vnd.ms-excel,application/octet-stream,*/*;q=0.8',
            # 一些公开分享需要带上来源页
            'Referer': export_url,
            'X-Requested-With': 'XMLHttpRequest',
        }
        
        # 如果有密码，添加到请求参数中
        params = {}
        if password:
            params['pwd'] = password
        
        # 尝试通过HTML解析获取数据
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            try:
                # 若未指定 sheet_id，先抓取HTML尝试解析第一个工作表ID
                parsed_sheet_id = sheet_id
                if not parsed_sheet_id:
                    html_resp = await client.get(export_url, headers=headers)
                    if html_resp.status_code == 200:
                        html_text = html_resp.text
                        # 常见两种形式：sheet=XXXXX 或 "sheetId":"XXXXX"
                        m = re.search(r"[?&]sheet=([A-Za-z0-9_-]{4,})", html_text)
                        if not m:
                            m = re.search(r'"sheetId"\s*:\s*"([A-Za-z0-9_-]{4,})"', html_text)
                        if m:
                            parsed_sheet_id = m.group(1)
                            export_url = f"https://{domain}/sheets/{spreadsheet_token}?sheet={parsed_sheet_id}"
                            logger.info(f"解析到sheet_id={parsed_sheet_id}，使用首个工作表导出")
                # 尝试获取CSV导出
                sep = '&' if '?' in export_url else '?'
                csv_url = f"{export_url}{sep}export=csv"
                if password:
                    csv_url += f"&pwd={password}"
                
                response = await client.get(csv_url, headers=headers)
                
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '').lower()
                    raw = response.content

                    # 如果明显是HTML提示页
                    head = raw[:200].lower()
                    if b'<html' in head:
                        txt = head.decode(errors='ignore')
                        if ('password' in txt) or ('no permission' in txt) or ('forbidden' in txt) or ('\xe5\xaf\x86\xe7\xa0\x81' in txt):
                            raise Exception("访问被拒绝或需要密码，请检查分享权限或提供密码")

                    # text/plain / octet-stream 也按CSV处理，尝试多种编码
                    # 读取CSV，自动检测分隔符与编码
                    from io import BytesIO
                    for enc in ['utf-8', 'utf-8-sig', 'gb18030', 'gbk']:
                        try:
                            df = pd.read_csv(BytesIO(raw), encoding=enc, engine='python', sep=None)
                            return df
                        except Exception:
                            continue
                        raise Exception("收到CSV文本但解析失败（已尝试utf-8/utf-8-sig/gb18030/gbk）")
                    raise Exception(f"未获得CSV数据，请检查分享链接是否允许导出（url={csv_url}）")
                elif response.status_code == 403:
                    raise Exception("访问被拒绝，请检查表格权限或密码是否正确")
            except pd.errors.EmptyDataError:
                raise Exception("表格数据为空")
            except Exception as e:
                if "密码" in str(e) or "password" in str(e).lower():
                    raise
                logger.warning(f"CSV导出失败: {e}")
        
        # 如果所有方法都失败，给出详细的错误提示
        error_msg = "无法读取表格数据。请确保：\n"
        if password:
            error_msg += "1. 密码正确\n"
            error_msg += "2. 表格链接有效且未过期\n"
        else:
            error_msg += "1. 表格设置为「公开可访问」或「知道链接的人可以查看」\n"
            error_msg += "2. 如果表格需要密码，请提供密码\n"
        error_msg += "3. 或者在系统中配置飞书应用凭证（App ID和Secret）"
        
        raise Exception(error_msg)
    
    async def _get_first_sheet_id(self, spreadsheet_token: str) -> str:
        """获取表格的第一个工作表ID"""
        url = f"{self.base_url}/sheets/v2/spreadsheets/{spreadsheet_token}/metainfo"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            result = response.json()
            
            if result.get("code") == 0:
                data = result.get("data", {})
                sheets = data.get("sheets", [])
                
                if sheets:
                    return sheets[0].get("sheetId")
                else:
                    raise ValueError("表格中没有工作表")
            else:
                raise Exception(f"获取工作表信息失败: {result.get('msg')}")
    
    async def read_sheet_from_url(self, url: str, password: Optional[str] = None) -> pd.DataFrame:
        """
        从飞书表格URL直接读取数据
        
        Args:
            url: 飞书表格完整URL
            password: 表格访问密码（可选，用于密码保护的表格）
            
        Returns:
            pandas DataFrame
        """
        # 解析URL
        parsed = self.parse_feishu_url(url)
        spreadsheet_token = parsed['spreadsheet_token']
        sheet_id = parsed.get('sheet_id')
        host = parsed.get('host')
        
        logger.info(f"准备读取飞书表格: token={spreadsheet_token}, sheet={sheet_id}, 密码保护={'是' if password else '否'}")
        
        # 读取数据
        df = await self.read_sheet_data(spreadsheet_token, sheet_id, password=password, host=host)
        
        logger.info(f"成功读取飞书表格数据: {len(df)} 行 x {len(df.columns)} 列")
        
        return df
    
    @staticmethod
    def validate_feishu_url(url: str) -> bool:
        """
        验证是否为有效的飞书表格URL
        
        Args:
            url: URL字符串
            
        Returns:
            是否有效
        """
        pattern = r'https?://[^/]+\.feishu\.cn/sheets/[A-Za-z0-9_-]+'
        return bool(re.match(pattern, url))

