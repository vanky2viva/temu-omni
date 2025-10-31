"""Excel导入服务"""
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import json
from loguru import logger

from app.models.shop import Shop
from app.models.import_history import ImportHistory, ImportType, ImportStatus
from app.models.activity import Activity, ActivityType
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.services.feishu_sheets_service import FeishuSheetsService


class ExcelImportService:
    """Excel导入服务类"""
    
    def __init__(self, db: Session, shop: Shop):
        self.db = db
        self.shop = shop
        self.feishu_service = FeishuSheetsService()
    
    async def import_activities_from_url(
        self,
        feishu_url: str,
        password: Optional[str] = None
    ) -> ImportHistory:
        """
        从飞书在线表格导入活动数据
        
        Args:
            feishu_url: 飞书表格URL
            password: 表格访问密码（可选）
            
        Returns:
            导入历史记录
        """
        # 创建导入记录
        import_record = ImportHistory(
            shop_id=self.shop.id,
            import_type=ImportType.ACTIVITIES,
            file_name=f"飞书表格: {feishu_url[:50]}...",
            file_size=0,
            status=ImportStatus.PROCESSING
        )
        self.db.add(import_record)
        self.db.commit()
        self.db.refresh(import_record)
        
        try:
            # 从飞书表格读取数据
            df = await self.feishu_service.read_sheet_from_url(feishu_url, password)
            
            # 使用通用导入逻辑
            return await self._process_activities_dataframe(df, import_record)
            
        except Exception as e:
            self.db.rollback()
            import_record.status = ImportStatus.FAILED
            import_record.completed_at = datetime.utcnow()
            import_record.error_log = json.dumps({'error': str(e)}, ensure_ascii=False)
            self.db.commit()
            logger.error(f"从飞书表格导入活动失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    async def import_activities(
        self, 
        file_path: str, 
        file_name: str,
        file_size: int
    ) -> ImportHistory:
        """
        导入活动数据
        
        Args:
            file_path: 文件路径
            file_name: 文件名
            file_size: 文件大小
            
        Returns:
            导入历史记录
        """
        # 创建导入记录
        import_record = ImportHistory(
            shop_id=self.shop.id,
            import_type=ImportType.ACTIVITIES,
            file_name=file_name,
            file_size=file_size,
            status=ImportStatus.PROCESSING
        )
        self.db.add(import_record)
        self.db.commit()
        self.db.refresh(import_record)
        
        errors = []
        success_items = []
        
        try:
            # 读取Excel
            df = pd.read_excel(file_path)
            
            # 使用通用导入逻辑
            return await self._process_activities_dataframe(df, import_record)
            
        except Exception as e:
            self.db.rollback()
            import_record.status = ImportStatus.FAILED
            import_record.completed_at = datetime.utcnow()
            import_record.error_log = json.dumps({'error': str(e)}, ensure_ascii=False)
            self.db.commit()
            logger.error(f"活动导入失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    async def import_products(
        self, 
        file_path: str, 
        file_name: str,
        file_size: int
    ) -> ImportHistory:
        """
        导入商品数据
        
        Args:
            file_path: 文件路径
            file_name: 文件名
            file_size: 文件大小
            
        Returns:
            导入历史记录
        """
        # 创建导入记录
        import_record = ImportHistory(
            shop_id=self.shop.id,
            import_type=ImportType.PRODUCTS,
            file_name=file_name,
            file_size=file_size,
            status=ImportStatus.PROCESSING
        )
        self.db.add(import_record)
        self.db.commit()
        self.db.refresh(import_record)
        
        try:
            # 读取Excel
            df = pd.read_excel(file_path)
            
            # 使用通用导入逻辑
            return await self._process_products_dataframe(df, import_record)
            
        except Exception as e:
            self.db.rollback()
            import_record.status = ImportStatus.FAILED
            import_record.completed_at = datetime.utcnow()
            import_record.error_log = json.dumps({'error': str(e)}, ensure_ascii=False)
            self.db.commit()
            logger.error(f"商品导入失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    async def _process_activities_dataframe(
        self,
        df: pd.DataFrame,
        import_record: ImportHistory
    ) -> ImportHistory:
        """
        处理活动数据DataFrame（通用逻辑，支持Excel和在线表格）
        
        Args:
            df: pandas DataFrame
            import_record: 导入记录
            
        Returns:
            更新后的导入记录
        """
        errors = []
        success_items = []
        
        import_record.total_rows = len(df)
        self.db.commit()
        
        logger.info(f"开始导入活动数据 - 店铺: {self.shop.shop_name}, 总行数: {len(df)}")
        
        # 处理每一行
        for index, row in df.iterrows():
            try:
                # 提取数据
                product_name = str(row.get('商品信息', ''))
                spu_id = str(row.get('SPU ID', ''))
                
                # 生成活动名称
                activity_name = f"活动推广 - {product_name[:50]}"
                
                # 检查是否已存在
                existing = self.db.query(Activity).filter(
                    Activity.shop_id == self.shop.id,
                    Activity.activity_name == activity_name
                ).first()
                
                if existing:
                    import_record.skipped_rows += 1
                    continue
                
                # 解析GMV和转化率
                gmv = float(row.get('活动 GMV', 0))
                click_rate = self._parse_percentage(row.get('活动商品点击转化率', '0%'))
                pay_rate = self._parse_percentage(row.get('活动商品支付转化率', '0%'))
                
                # 创建活动记录
                activity = Activity(
                    shop_id=self.shop.id,
                    activity_name=activity_name,
                    activity_type=ActivityType.PROMOTION,
                    start_time=datetime.now(),
                    end_time=None,
                    description=f"SPU: {spu_id}\n销量: {row.get('活动销量', 0)}\n曝光: {row.get('活动商品曝光用户数', 0)}\n点击: {row.get('活动商品点击用户数', 0)}",
                    budget=gmv,
                    actual_cost=gmv,
                    is_active=True
                )
                
                self.db.add(activity)
                import_record.success_rows += 1
                success_items.append({
                    'row': index + 1,
                    'name': activity_name,
                    'gmv': gmv
                })
                
            except Exception as e:
                import_record.failed_rows += 1
                errors.append({
                    'row': index + 1,
                    'error': str(e),
                    'data': row.to_dict() if hasattr(row, 'to_dict') else str(row)
                })
                logger.error(f"导入活动失败 - 行{index + 1}: {e}")
        
        # 提交所有更改
        self.db.commit()
        
        # 更新导入记录状态
        import_record.completed_at = datetime.utcnow()
        if import_record.failed_rows == 0:
            import_record.status = ImportStatus.SUCCESS
        elif import_record.success_rows > 0:
            import_record.status = ImportStatus.PARTIAL
        else:
            import_record.status = ImportStatus.FAILED
        
        import_record.error_log = json.dumps(errors, ensure_ascii=False) if errors else None
        import_record.success_log = json.dumps(success_items[:10], ensure_ascii=False)
        
        self.db.commit()
        
        logger.info(
            f"活动导入完成 - 店铺: {self.shop.shop_name}, "
            f"成功: {import_record.success_rows}, "
            f"失败: {import_record.failed_rows}, "
            f"跳过: {import_record.skipped_rows}"
        )
        
        return import_record
    
    async def import_products_from_url(
        self,
        feishu_url: str,
        password: Optional[str] = None
    ) -> ImportHistory:
        """
        从飞书在线表格导入商品数据
        
        Args:
            feishu_url: 飞书表格URL
            password: 表格访问密码（可选）
            
        Returns:
            导入历史记录
        """
        # 创建导入记录
        import_record = ImportHistory(
            shop_id=self.shop.id,
            import_type=ImportType.PRODUCTS,
            file_name=f"飞书表格: {feishu_url[:50]}...",
            file_size=0,
            status=ImportStatus.PROCESSING
        )
        self.db.add(import_record)
        self.db.commit()
        self.db.refresh(import_record)
        
        try:
            # 从飞书表格读取数据
            df = await self.feishu_service.read_sheet_from_url(feishu_url, password)
            
            # 使用通用导入逻辑
            return await self._process_products_dataframe(df, import_record)
            
        except Exception as e:
            self.db.rollback()
            import_record.status = ImportStatus.FAILED
            import_record.completed_at = datetime.utcnow()
            import_record.error_log = json.dumps({'error': str(e)}, ensure_ascii=False)
            self.db.commit()
            logger.error(f"从飞书表格导入商品失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    def _parse_percentage(self, value: str) -> float:
        """解析百分比字符串 "1.15%" -> 0.0115"""
        try:
            if isinstance(value, str):
                return float(value.replace('%', '')) / 100
            return float(value)
        except:
            return 0.0
    
    def _parse_price(self, value: str) -> float:
        """解析价格字符串 "999.00元" -> 999.00"""
        try:
            if isinstance(value, str):
                # 移除"元"和其他非数字字符（保留小数点）
                value = value.replace('元', '').replace('¥', '').replace(',', '').strip()
            return float(value)
        except:
            return 0.0
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """解析日期时间"""
        if pd.isna(value) or value is None or value == '':
            return None
        
        try:
            if isinstance(value, str):
                # 尝试多种日期格式
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y/%m/%d %H:%M:%S',
                    '%Y-%m-%d',
                    '%Y/%m/%d',
                ]
                for fmt in formats:
                    try:
                        return datetime.strptime(value, fmt)
                    except:
                        continue
            # 如果是pandas的Timestamp对象
            if hasattr(value, 'to_pydatetime'):
                return value.to_pydatetime()
            return None
        except:
            return None
    
    async def _process_products_dataframe(
        self,
        df: pd.DataFrame,
        import_record: ImportHistory
    ) -> ImportHistory:
        """
        处理商品数据DataFrame（通用逻辑）
        """
        errors = []
        success_items = []
        
        import_record.total_rows = len(df)
        self.db.commit()
        
        logger.info(f"开始导入商品数据 - 店铺: {self.shop.shop_name}, 总行数: {len(df)}")
        
        # 打印所有列名以便调试
        logger.info(f"Excel列名: {list(df.columns)}")
        
        # 辅助函数：尝试多个可能的列名获取值
        def get_column_value(row, possible_names, default=''):
            """尝试多个可能的列名获取值"""
            for name in possible_names:
                if name in row and pd.notna(row.get(name)) and str(row.get(name)).strip():
                    return str(row.get(name)).strip()
            return default
        
        # 检查必要的字段是否存在（提前检测，避免事务失败）
        try:
            # 尝试查询一个产品来检测表结构
            test_query = self.db.query(Product).limit(1).first()
            # 如果查询成功但表结构缺少字段，尝试访问字段来触发错误
            if test_query:
                _ = getattr(test_query, 'skc_id', None)
                _ = getattr(test_query, 'price_status', None)
        except Exception as struct_error:
            error_msg = str(struct_error)
            if 'skc_id' in error_msg or 'price_status' in error_msg or 'no such column' in error_msg.lower():
                self.db.rollback()
                logger.error("数据库表缺少必要的字段，请先运行迁移或修复脚本")
                logger.error("运行: python3 backend/scripts/fix_missing_product_fields.py")
                logger.error("或运行: alembic upgrade head")
                raise Exception(
                    "数据库表缺少字段 skc_id 或 price_status。"
                    "请先运行数据库迁移：alembic upgrade head"
                    "或运行修复脚本：python3 backend/scripts/fix_missing_product_fields.py"
                ) from struct_error
            raise
        
        # 处理每一行
        for index, row in df.iterrows():
            try:
                product_name = str(row.get('商品名称', ''))
                sku_id = str(row.get('SKU ID', ''))
                spu_id = str(row.get('SPU ID', ''))
                
                # 解析价格
                price_str = str(row.get('申报价格', '0'))
                price = self._parse_price(price_str)
                
                # 检查商品是否已存在
                existing = self.db.query(Product).filter(
                    Product.shop_id == self.shop.id,
                    Product.product_id == sku_id
                ).first()
                
                if existing:
                    # 更新商品信息
                    sku_number = str(row.get('SKU货号', '')).strip()
                    category = str(row.get('类目', '')).strip()
                    # 负责人：Excel中没有该列或为空时，使用店铺默认负责人
                    manager = str(row.get('负责人', '')).strip()
                    if not manager or manager.lower() in ['nan', 'none', '']:
                        manager = self.shop.default_manager or ''
                    skc_id = str(row.get('SKC ID', '')).strip()
                    # 尝试多个可能的列名来获取申报价格状态
                    price_status_candidates = [
                        '申报价格状态', '申报价格状态 ', ' 申报价格状态', 
                        '价格状态', '申报状态', '价格状态 ', '申报状态 ',
                        '申报价格 状态', '申报 价格状态'
                    ]
                    price_status = get_column_value(row, price_status_candidates, '')
                    
                    # 如果为空，尝试从所有包含"状态"的列获取
                    if not price_status:
                        status_cols = [col for col in df.columns if '状态' in str(col) and '申报' in str(col)]
                        for status_col in status_cols:
                            if status_col in row and pd.notna(row[status_col]):
                                val = str(row[status_col]).strip()
                                if val and val.lower() not in ['nan', 'none', '']:
                                    price_status = val
                                    logger.debug(f"行 {index + 1}: 从列 '{status_col}' 获取申报价格状态 = {price_status}")
                                    break
                    
                    # 处理空值和'nan'字符串
                    if sku_number and sku_number.lower() not in ['nan', 'none', '']:
                        existing.sku = sku_number
                    if category and category.lower() not in ['nan', 'none', '']:
                        existing.category = category
                    if manager and manager.lower() not in ['nan', 'none', '']:
                        existing.manager = manager
                    elif not existing.manager:
                        # 如果没有负责人且店铺有默认负责人，使用默认负责人
                        default_manager = getattr(self.shop, 'default_manager', None)
                        if default_manager:
                            existing.manager = default_manager
                    
                    # 更新SKC ID
                    if skc_id and skc_id.lower() not in ['nan', 'none', '']:
                        existing.skc_id = skc_id
                    
                    # 更新申报价格状态（直接从表格导入，不自动设置）
                    if price_status and price_status.lower() not in ['nan', 'none', '']:
                        existing.price_status = price_status
                    
                    # 更新状态（支持多种状态值）
                    status_str = str(row.get('状态', '')).strip()
                    is_published = (
                        status_str == '已发布' or 
                        status_str == '已发布到站点' or
                        '已发布' in status_str
                    )
                    existing.is_active = is_published
                    
                    # 更新价格和货币单位（申报价格单位是人民币）
                    if price > 0:
                        existing.current_price = price
                    existing.currency = 'CNY'  # 申报价格单位是人民币，无论价格是否大于0
                    
                    # 更新SPU ID（如果存在）
                    if spu_id and spu_id.lower() not in ['nan', 'none', '']:
                        # 更新description中的SPU信息
                        if spu_id:
                            existing.description = f"SPU: {spu_id}"
                    
                    import_record.success_rows += 1
                    success_items.append({
                        'row': index + 1,
                        'name': product_name,
                        'action': 'updated'
                    })
                else:
                    # 创建新商品
                    sku_number = str(row.get('SKU货号', '')).strip()
                    category = str(row.get('类目', '')).strip()
                    # 负责人：Excel中没有该列或为空时，使用店铺默认负责人
                    manager = str(row.get('负责人', '')).strip()
                    if not manager or manager.lower() in ['nan', 'none', '']:
                        manager = self.shop.default_manager or ''
                    skc_id = str(row.get('SKC ID', '')).strip()
                    # 尝试多个可能的列名来获取申报价格状态
                    price_status_candidates = [
                        '申报价格状态', '申报价格状态 ', ' 申报价格状态', 
                        '价格状态', '申报状态', '价格状态 ', '申报状态 ',
                        '申报价格 状态', '申报 价格状态'
                    ]
                    price_status = get_column_value(row, price_status_candidates, '')
                    
                    # 如果为空，尝试从所有包含"状态"的列获取
                    if not price_status:
                        status_cols = [col for col in df.columns if '状态' in str(col) and '申报' in str(col)]
                        for status_col in status_cols:
                            if status_col in row and pd.notna(row[status_col]):
                                val = str(row[status_col]).strip()
                                if val and val.lower() not in ['nan', 'none', '']:
                                    price_status = val
                                    logger.debug(f"行 {index + 1}: 从列 '{status_col}' 获取申报价格状态 = {price_status}")
                                    break
                    
                    # 处理空值和'nan'字符串
                    if sku_number.lower() in ['nan', 'none', '']:
                        sku_number = None
                    if category.lower() in ['nan', 'none', '']:
                        category = None
                    if manager.lower() in ['nan', 'none', '']:
                        manager = getattr(self.shop, 'default_manager', None)
                    if skc_id.lower() in ['nan', 'none', '']:
                        skc_id = None
                    if price_status.lower() in ['nan', 'none', '']:
                        price_status = None
                    
                    # 处理SPU ID
                    description = None
                    if spu_id and spu_id.lower() not in ['nan', 'none', '']:
                        description = f"SPU: {spu_id}"
                    
                    # 判断状态（支持多种状态值）
                    status_str = str(row.get('状态', '')).strip()
                    # 已发布的状态值包括：已发布、已发布到站点
                    # 未发布的状态值包括：未发布、价格申报中、已下架
                    is_published = (
                        status_str == '已发布' or 
                        status_str == '已发布到站点' or
                        '已发布' in status_str
                    )
                    
                    product = Product(
                        shop_id=self.shop.id,
                        product_id=sku_id,
                        product_name=product_name,
                        sku=sku_number,  # 设置SKU货号
                        current_price=price if price > 0 else 0,
                        currency='CNY',  # 申报价格单位是人民币
                        category=category,
                        is_active=is_published,
                        description=description,
                        manager=manager,
                        skc_id=skc_id,
                        price_status=price_status,  # 直接使用从表格导入的值
                        created_at=datetime.utcnow()
                    )
                    self.db.add(product)
                    import_record.success_rows += 1
                    success_items.append({
                        'row': index + 1,
                        'name': product_name,
                        'action': 'created'
                    })
                
            except Exception as e:
                import_record.failed_rows += 1
                errors.append({
                    'row': index + 1,
                    'error': str(e),
                    'data': row.to_dict() if hasattr(row, 'to_dict') else str(row)
                })
                logger.error(f"导入商品失败 - 行{index + 1}: {e}")
                # 如果事务失败，回滚并尝试继续
                try:
                    self.db.rollback()
                except:
                    pass
        
        # 提交所有更改
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"提交商品数据失败: {e}")
            raise
        
        # 更新导入记录状态
        import_record.completed_at = datetime.utcnow()
        if import_record.failed_rows == 0:
            import_record.status = ImportStatus.SUCCESS
        elif import_record.success_rows > 0:
            import_record.status = ImportStatus.PARTIAL
        else:
            import_record.status = ImportStatus.FAILED
        
        import_record.error_log = json.dumps(errors, ensure_ascii=False) if errors else None
        import_record.success_log = json.dumps(success_items[:10], ensure_ascii=False)
        
        self.db.commit()
        
        logger.info(
            f"商品导入完成 - 店铺: {self.shop.shop_name}, "
            f"成功: {import_record.success_rows}, "
            f"失败: {import_record.failed_rows}, "
            f"跳过: {import_record.skipped_rows}"
        )
        
        return import_record
    
    async def import_orders_from_url(
        self,
        feishu_url: str,
        password: Optional[str] = None
    ) -> ImportHistory:
        """从飞书在线表格导入订单数据"""
        import_record = ImportHistory(
            shop_id=self.shop.id,
            import_type=ImportType.ORDERS,
            file_name=f"飞书表格: {feishu_url[:50]}...",
            file_size=0,
            status=ImportStatus.PROCESSING
        )
        self.db.add(import_record)
        self.db.commit()
        self.db.refresh(import_record)
        
        try:
            df = await self.feishu_service.read_sheet_from_url(feishu_url, password)
            return await self._process_orders_dataframe(df, import_record)
        except Exception as e:
            self.db.rollback()
            import_record.status = ImportStatus.FAILED
            import_record.completed_at = datetime.utcnow()
            import_record.error_log = json.dumps({'error': str(e)}, ensure_ascii=False)
            self.db.commit()
            logger.error(f"从飞书表格导入订单失败: {e}")
            raise
    
    async def import_orders(self, file_path: str, file_name: str, file_size: int) -> ImportHistory:
        """导入订单数据（Excel文件）"""
        import_record = ImportHistory(
            shop_id=self.shop.id,
            import_type=ImportType.ORDERS,
            file_name=file_name,
            file_size=file_size,
            status=ImportStatus.PROCESSING
        )
        self.db.add(import_record)
        self.db.commit()
        self.db.refresh(import_record)
        
        try:
            df = pd.read_excel(file_path)
            return await self._process_orders_dataframe(df, import_record)
        except Exception as e:
            self.db.rollback()
            import_record.status = ImportStatus.FAILED
            import_record.completed_at = datetime.utcnow()
            import_record.error_log = json.dumps({'error': str(e)}, ensure_ascii=False)
            self.db.commit()
            logger.error(f"订单导入失败: {e}")
            raise
    
    async def _process_orders_dataframe(self, df: pd.DataFrame, import_record: ImportHistory) -> ImportHistory:
        """处理订单数据DataFrame"""
        errors = []
        success_items = []
        
        import_record.total_rows = len(df)
        self.db.commit()
        
        logger.info(f"开始导入订单 - 店铺: {self.shop.shop_name}, 总行数: {len(df)}")
        
        for index, row in df.iterrows():
            try:
                # 订单编号（必需）
                order_sn = str(row.get('订单编号', row.get('订单号', '')))
                if not order_sn or order_sn == 'nan':
                    import_record.failed_rows += 1
                    errors.append({'row': index + 1, 'error': '缺少订单编号'})
                    continue
                
                # 检查是否已存在，存在则更新
                existing = self.db.query(Order).filter(
                    Order.shop_id == self.shop.id,
                    Order.order_sn == order_sn
                ).first()
                
                # 解析数据
                product_name = str(row.get('商品名称', row.get('商品', '')))
                quantity = int(row.get('数量', row.get('购买数量', 1)))
                unit_price = self._parse_price(str(row.get('单价', row.get('商品单价', '0'))))
                total_price = self._parse_price(str(row.get('订单金额', row.get('总金额', '0'))))
                
                order_time = self._parse_datetime(row.get('下单时间', row.get('订单时间')))
                if not order_time:
                    order_time = datetime.utcnow()
                
                payment_time = self._parse_datetime(row.get('支付时间'))
                status_str = str(row.get('订单状态', row.get('状态', 'PENDING')))
                status = self._parse_order_status(status_str)
                
                if existing:
                    # 更新现有订单
                    existing.product_name = product_name
                    existing.product_sku = str(row.get('SKU', row.get('商品SKU', '')))
                    existing.quantity = quantity
                    existing.unit_price = unit_price
                    existing.total_price = total_price if total_price > 0 else unit_price * quantity
                    existing.currency = str(row.get('币种', row.get('货币', 'USD')))
                    existing.status = status
                    existing.order_time = order_time
                    existing.payment_time = payment_time
                    existing.shipping_time = self._parse_datetime(row.get('发货时间'))
                    existing.delivery_time = self._parse_datetime(row.get('送达时间'))
                    existing.customer_id = str(row.get('客户ID', row.get('买家ID', '')))
                    existing.shipping_country = str(row.get('收货国家', row.get('国家', '')))
                    existing.updated_at = datetime.utcnow()
                    
                    # 保存原始数据
                    existing.raw_data = json.dumps(row.to_dict(), ensure_ascii=False, default=str)
                    
                    import_record.success_rows += 1
                    success_items.append({'row': index + 1, 'order_sn': order_sn, 'action': 'updated'})
                else:
                    # 创建新订单
                    order = Order(
                        shop_id=self.shop.id,
                        order_sn=order_sn,
                        product_name=product_name,
                        product_sku=str(row.get('SKU', row.get('商品SKU', ''))),
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price if total_price > 0 else unit_price * quantity,
                        currency=str(row.get('币种', row.get('货币', 'USD'))),
                        status=status,
                        order_time=order_time,
                        payment_time=payment_time,
                        shipping_time=self._parse_datetime(row.get('发货时间')),
                        delivery_time=self._parse_datetime(row.get('送达时间')),
                        customer_id=str(row.get('客户ID', row.get('买家ID', ''))),
                        shipping_country=str(row.get('收货国家', row.get('国家', ''))),
                        raw_data=json.dumps(row.to_dict(), ensure_ascii=False, default=str),
                        created_at=datetime.utcnow()
                    )
                    
                    self.db.add(order)
                    import_record.success_rows += 1
                    success_items.append({'row': index + 1, 'order_sn': order_sn, 'action': 'created'})
                
                # 每处理一行就提交，避免批量提交时的冲突
                try:
                    self.db.commit()
                except Exception as commit_error:
                    logger.error(f"提交订单失败 - 行{index + 1}, 订单号{order_sn}: {commit_error}")
                    self.db.rollback()
                    import_record.failed_rows += 1
                    import_record.success_rows -= 1  # 回退成功计数
                    errors.append({'row': index + 1, 'order_sn': order_sn, 'error': str(commit_error)})
                
            except Exception as e:
                import_record.failed_rows += 1
                errors.append({'row': index + 1, 'error': str(e)})
                logger.error(f"导入订单失败 - 行{index + 1}: {e}")
                self.db.rollback()  # 确保回滚
        
        # 不需要再次批量提交，因为每行都已经单独提交
        
        import_record.completed_at = datetime.utcnow()
        if import_record.failed_rows == 0:
            import_record.status = ImportStatus.SUCCESS
        elif import_record.success_rows > 0:
            import_record.status = ImportStatus.PARTIAL
        else:
            import_record.status = ImportStatus.FAILED
        
        import_record.error_log = json.dumps(errors, ensure_ascii=False) if errors else None
        import_record.success_log = json.dumps(success_items[:10], ensure_ascii=False)
        self.db.commit()
        
        logger.info(
            f"订单导入完成 - 成功: {import_record.success_rows}, "
            f"失败: {import_record.failed_rows}, 跳过: {import_record.skipped_rows}"
        )
        
        return import_record
    
    def _parse_order_status(self, status_str: str) -> OrderStatus:
        """解析订单状态"""
        status_str = status_str.upper().strip()
        status_mapping = {
            'PENDING': OrderStatus.PENDING, '待支付': OrderStatus.PENDING,
            'PAID': OrderStatus.PAID, '已支付': OrderStatus.PAID,
            'SHIPPED': OrderStatus.SHIPPED, '已发货': OrderStatus.SHIPPED,
            'DELIVERED': OrderStatus.DELIVERED, '已完成': OrderStatus.DELIVERED,
            'CANCELLED': OrderStatus.CANCELLED, '已取消': OrderStatus.CANCELLED,
            'REFUNDED': OrderStatus.REFUNDED, '已退款': OrderStatus.REFUNDED,
        }
        return status_mapping.get(status_str, OrderStatus.PENDING)

