-- 为 PostgreSQL 数据库添加 CN 相关字段
-- 使用方法：psql -U username -d database_name -f add_cn_fields.sql
-- 或者在 Python 中执行这些 SQL 语句

-- 添加 CN 相关字段（如果不存在）
DO $$
BEGIN
    -- 添加 cn_access_token 字段
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'shops' AND column_name = 'cn_access_token'
    ) THEN
        ALTER TABLE shops ADD COLUMN cn_access_token TEXT;
        RAISE NOTICE '已添加字段: cn_access_token';
    END IF;
    
    -- 添加 cn_app_key 字段
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'shops' AND column_name = 'cn_app_key'
    ) THEN
        ALTER TABLE shops ADD COLUMN cn_app_key VARCHAR(200);
        RAISE NOTICE '已添加字段: cn_app_key';
    END IF;
    
    -- 添加 cn_app_secret 字段
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'shops' AND column_name = 'cn_app_secret'
    ) THEN
        ALTER TABLE shops ADD COLUMN cn_app_secret TEXT;
        RAISE NOTICE '已添加字段: cn_app_secret';
    END IF;
    
    -- 添加 cn_api_base_url 字段
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'shops' AND column_name = 'cn_api_base_url'
    ) THEN
        ALTER TABLE shops ADD COLUMN cn_api_base_url VARCHAR(200);
        RAISE NOTICE '已添加字段: cn_api_base_url';
    END IF;
END $$;

-- 设置默认值
UPDATE shops 
SET 
    cn_api_base_url = COALESCE(cn_api_base_url, 'https://openapi.kuajingmaihuo.com/openapi/router'),
    cn_app_key = COALESCE(cn_app_key, 'af5bcf5d4bd5a492fa09c2ee302d75b9'),
    cn_app_secret = COALESCE(cn_app_secret, 'e4f229bb9c4db21daa999e73c8683d42ba0a7094')
WHERE 
    cn_api_base_url IS NULL 
    OR cn_app_key IS NULL 
    OR cn_app_secret IS NULL;

-- 验证字段是否添加成功
SELECT 
    column_name, 
    data_type, 
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'shops' 
    AND column_name LIKE 'cn_%'
ORDER BY column_name;

