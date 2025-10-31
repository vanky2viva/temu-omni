-- 添加缺失的商品表字段
-- 如果使用PostgreSQL
ALTER TABLE products ADD COLUMN IF NOT EXISTS skc_id VARCHAR(100);
ALTER TABLE products ADD COLUMN IF NOT EXISTS price_status VARCHAR(50);

-- 如果使用SQLite（需要先检查字段是否存在）
-- SQLite不支持IF NOT EXISTS，需要手动检查
-- 或者直接运行（如果字段已存在会报错，可以忽略）
-- ALTER TABLE products ADD COLUMN skc_id VARCHAR(100);
-- ALTER TABLE products ADD COLUMN price_status VARCHAR(50);

