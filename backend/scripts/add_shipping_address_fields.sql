-- 添加收货地址字段到 orders 表
-- 如果字段已存在，脚本会报错但不会影响其他字段的创建

-- 添加城市字段
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='orders' AND column_name='shipping_city') THEN
        ALTER TABLE orders ADD COLUMN shipping_city VARCHAR(100);
    END IF;
END $$;

-- 添加省份字段
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='orders' AND column_name='shipping_province') THEN
        ALTER TABLE orders ADD COLUMN shipping_province VARCHAR(50);
    END IF;
END $$;

-- 添加邮编字段
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='orders' AND column_name='shipping_postal_code') THEN
        ALTER TABLE orders ADD COLUMN shipping_postal_code VARCHAR(20);
    END IF;
END $$;

-- 为省份字段添加索引（便于查询和统计）
CREATE INDEX IF NOT EXISTS idx_orders_shipping_province ON orders(shipping_province);

