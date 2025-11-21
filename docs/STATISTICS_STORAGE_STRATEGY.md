# 统计数据存储和计算策略

## 一、现状分析

### 1.1 订单级别数据（已存储）
- ✅ **订单表（orders）**：已存储基础数据
  - `unit_price`: 单价（从商品供货价计算）
  - `total_price`: 总价（单价 × 数量）
  - `unit_cost`: 单位成本
  - `total_cost`: 总成本
  - `profit`: 利润（总价 - 总成本）

### 1.2 聚合统计数据（部分存储）
- ✅ **报表快照表（report_snapshots）**：存储每日/每周报表
  - 已实现日报生成定时任务（每日00:15）
  - 存储指标：GMV、订单数、成本、利润、利润率等
- ⚠️ **实时统计API**：前端刷新时实时计算
  - `StatisticsService`: 实时计算统计数据
  - `analytics.py`: GMV表格等实时查询

## 二、推荐策略

### 2.1 订单级别数据 ✅ **已实现，保持不变**

**存储位置**：`orders` 表
- 订单创建/更新时自动计算并存储
- 价格从商品表的供货价计算
- 利润 = 总价 - 总成本

**优点**：
- 数据准确，可追溯
- 查询性能好
- 支持历史数据分析

### 2.2 聚合统计数据 - **混合策略**

#### 策略A：历史数据（日报/周报/月报）- **存储到表**

**存储位置**：`report_snapshots` 表（已存在）

**计算时机**：后台定时任务
- ✅ 日报：每日00:15自动生成（已实现）
- ⚠️ 周报：建议每周一00:30生成
- ⚠️ 月报：建议每月1日01:00生成

**存储内容**：
```json
{
  "date": "2025-11-21",
  "total_orders": 150,
  "gmv": 45000.00,
  "total_cost": 30000.00,
  "total_profit": 15000.00,
  "profit_rate": 0.3333,  // 利润率 = 利润 / GMV
  "refund_count": 5,
  "refund_rate": 0.0333,
  "status_counts": {...},
  "top_products": [...]
}
```

**优点**：
- 历史数据查询快
- 支持数据对比分析
- 减少数据库压力

#### 策略B：实时查询（当前日期/自定义范围）- **实时计算 + 缓存**

**计算时机**：前端刷新时实时计算

**优化方案**：
1. **Redis缓存**（推荐）
   - 缓存键：`stats:shop:{shop_id}:date:{date}`
   - 缓存时间：5-10分钟
   - 当订单数据更新时，清除相关缓存

2. **数据库查询优化**
   - 使用聚合函数（SUM、COUNT）
   - 添加适当的索引
   - 限制查询时间范围

**优点**：
- 数据实时性好
- 灵活支持自定义查询
- 缓存提升性能

### 2.3 GMV表格等复杂统计 - **实时计算 + 可选缓存**

**场景**：按日/周/月分组的GMV表格

**策略**：
- 对于**历史数据**（>1天前）：从 `report_snapshots` 表读取
- 对于**当前日期**：实时计算 + Redis缓存（5分钟）
- 对于**自定义范围**：实时计算（如果范围大，考虑后台任务）

## 三、实施建议

### 3.1 立即实施（高优先级）

1. **完善报表快照生成**
   - ✅ 日报：已实现
   - ⚠️ 周报：添加周报生成任务
   - ⚠️ 月报：添加月报生成任务

2. **添加Redis缓存**
   - 缓存实时统计数据
   - 订单更新时清除缓存

3. **优化实时查询**
   - 添加数据库索引
   - 限制查询范围

### 3.2 中期优化（中优先级）

1. **统计数据表优化**
   - 考虑添加 `statistics_summary` 表存储常用统计
   - 支持按店铺、日期、类型聚合

2. **后台任务优化**
   - 支持手动触发统计计算
   - 支持重新计算历史数据

### 3.3 长期优化（低优先级）

1. **数据仓库**
   - 考虑ETL到数据仓库
   - 支持更复杂的分析

2. **实时流处理**
   - 使用Kafka等消息队列
   - 实时更新统计数据

## 四、具体实现方案

### 4.1 添加周报和月报生成

```python
# backend/app/core/scheduler.py

def generate_weekly_reports_job():
    """生成周报（每周一00:30执行）"""
    logger.info("开始执行定时任务：生成周报...")
    db = SessionLocal()
    try:
        report_service = ReportService(db)
        shops = db.query(Shop).filter(Shop.is_active == True).all()
        
        # 计算上周的日期范围
        today = date.today()
        last_monday = today - timedelta(days=today.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)
        
        for shop in shops:
            # 生成上周的周报
            weekly_metrics = report_service.generate_weekly_metrics(
                shop.id, last_monday, last_sunday
            )
            report_service.save_weekly_report(shop.id, last_monday, weekly_metrics)
    finally:
        db.close()

def generate_monthly_reports_job():
    """生成月报（每月1日01:00执行）"""
    logger.info("开始执行定时任务：生成月报...")
    db = SessionLocal()
    try:
        report_service = ReportService(db)
        shops = db.query(Shop).filter(Shop.is_active == True).all()
        
        # 计算上月的日期范围
        today = date.today()
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        
        for shop in shops:
            # 生成上月的月报
            monthly_metrics = report_service.generate_monthly_metrics(
                shop.id, first_day_last_month, last_day_last_month
            )
            report_service.save_monthly_report(shop.id, first_day_last_month, monthly_metrics)
    finally:
        db.close()
```

### 4.2 添加Redis缓存

```python
# backend/app/services/statistics.py

from app.core.redis_client import redis_client

class StatisticsService:
    @staticmethod
    def get_order_statistics_cached(
        db: Session,
        shop_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[OrderStatus] = None,
        cache_ttl: int = 300  # 5分钟
    ) -> Dict[str, Any]:
        """带缓存的统计数据查询"""
        # 生成缓存键
        cache_key = f"stats:shops:{','.join(map(str, shop_ids or []))}:"
        cache_key += f"start:{start_date}:end:{end_date}:status:{status}"
        
        # 尝试从缓存获取
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # 计算统计数据
        stats = StatisticsService.get_order_statistics(
            db, shop_ids, start_date, end_date, status
        )
        
        # 存入缓存
        redis_client.setex(cache_key, cache_ttl, json.dumps(stats))
        
        return stats
```

### 4.3 订单更新时清除缓存

```python
# backend/app/services/sync_service.py

def _invalidate_statistics_cache(self, shop_id: int, order_date: date):
    """订单更新时清除相关统计缓存"""
    from app.core.redis_client import redis_client
    
    # 清除该日期相关的所有统计缓存
    pattern = f"stats:*shop*{shop_id}*date*{order_date}*"
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)
```

## 五、总结

### 推荐方案

1. **订单级别数据**：✅ 已存储，保持不变
2. **历史统计数据**：✅ 存储到 `report_snapshots` 表，后台定时计算
3. **实时统计数据**：实时计算 + Redis缓存（5-10分钟）
4. **GMV表格等**：历史数据从表读取，当前数据实时计算+缓存

### 优势

- ✅ **性能**：历史数据查询快，实时数据有缓存
- ✅ **准确性**：订单数据准确存储，统计数据可追溯
- ✅ **灵活性**：支持实时查询和自定义范围
- ✅ **可扩展**：支持未来添加更多统计维度

### 注意事项

1. **数据一致性**：订单更新时需要清除相关缓存
2. **计算资源**：大数据量时考虑后台任务
3. **存储空间**：定期清理过期的缓存和统计数据

