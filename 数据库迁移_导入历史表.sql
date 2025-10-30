-- 创建导入类型枚举
CREATE TYPE importtype AS ENUM ('orders', 'products', 'activities');

-- 创建导入状态枚举
CREATE TYPE importstatus AS ENUM ('processing', 'success', 'failed', 'partial');

-- 创建导入历史记录表
CREATE TABLE import_history (
    id SERIAL PRIMARY KEY,
    shop_id INTEGER NOT NULL REFERENCES shops(id),
    import_type importtype NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER,
    total_rows INTEGER DEFAULT 0,
    success_rows INTEGER DEFAULT 0,
    failed_rows INTEGER DEFAULT 0,
    skipped_rows INTEGER DEFAULT 0,
    status importstatus DEFAULT 'processing',
    error_log TEXT,
    success_log TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX ix_import_history_id ON import_history(id);
CREATE INDEX ix_import_history_shop_id ON import_history(shop_id);

-- 添加注释
COMMENT ON TABLE import_history IS '导入历史记录表';
COMMENT ON COLUMN import_history.shop_id IS '店铺ID';
COMMENT ON COLUMN import_history.import_type IS '导入类型';
COMMENT ON COLUMN import_history.file_name IS '文件名';
COMMENT ON COLUMN import_history.file_size IS '文件大小(字节)';
COMMENT ON COLUMN import_history.total_rows IS '总行数';
COMMENT ON COLUMN import_history.success_rows IS '成功行数';
COMMENT ON COLUMN import_history.failed_rows IS '失败行数';
COMMENT ON COLUMN import_history.skipped_rows IS '跳过行数';
COMMENT ON COLUMN import_history.status IS '导入状态';
COMMENT ON COLUMN import_history.error_log IS '错误日志(JSON格式)';
COMMENT ON COLUMN import_history.success_log IS '成功日志(JSON格式)';
COMMENT ON COLUMN import_history.started_at IS '开始时间';
COMMENT ON COLUMN import_history.completed_at IS '完成时间';
COMMENT ON COLUMN import_history.created_at IS '创建时间';

