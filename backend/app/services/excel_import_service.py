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
                    # 更新价格信息
                    if price > 0:
                        existing.current_price = price
                        import_record.success_rows += 1
                        success_items.append({
                            'row': index + 1,
                            'name': product_name,
                            'action': 'updated'
                        })
                    else:
                        import_record.skipped_rows += 1
                else:
                    # 创建新商品
                    product = Product(
                        shop_id=self.shop.id,
                        product_id=sku_id,
                        product_name=product_name,
                        current_price=price if price > 0 else 0,
                        category=str(row.get('类目', '')),
                        is_active=(row.get('状态') == '价格申报中'),
                        description=f"SPU: {spu_id}\nSKU货号: {row.get('SKU货号', '')}",
                        manager=getattr(self.shop, 'default_manager', None),
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
                
                # 检查重复
                existing = self.db.query(Order).filter(
                    Order.shop_id == self.shop.id,
                    Order.order_sn == order_sn
                ).first()
                
                if existing:
                    import_record.skipped_rows += 1
                    continue
                
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
                
                # 创建订单
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
                    customer_id=str(row.get('客户ID', row.get('买家ID', ''))),
                    shipping_country=str(row.get('收货国家', row.get('国家', ''))),
                    created_at=datetime.utcnow()
                )
                
                self.db.add(order)
                import_record.success_rows += 1
                success_items.append({'row': index + 1, 'order_sn': order_sn, 'amount': float(total_price)})
                
            except Exception as e:
                import_record.failed_rows += 1
                errors.append({'row': index + 1, 'error': str(e)})
                logger.error(f"导入订单失败 - 行{index + 1}: {e}")
        
        self.db.commit()
        
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

