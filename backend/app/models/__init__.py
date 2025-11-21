"""数据模型"""
from app.models.shop import Shop
from app.models.order import Order
from app.models.product import Product, ProductCost
from app.models.activity import Activity
from app.models.import_history import ImportHistory
from app.models.system_config import SystemConfig
from app.models.user import User

# 暂时注释掉新模型的导入，等数据库迁移完成后再启用
# from app.models.temu_orders_raw import TemuOrdersRaw
# from app.models.temu_products_raw import TemuProductsRaw
# from app.models.order_item import OrderItem
# from app.models.payout import Payout
# from app.models.report_snapshot import ReportSnapshot

__all__ = [
    "Shop", "Order", "Product", "ProductCost", "Activity", "ImportHistory", "User",
    # "TemuOrdersRaw", "TemuProductsRaw", "OrderItem", "Payout", "ReportSnapshot"
]

