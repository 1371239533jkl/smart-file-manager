-- =====================================================
-- 数据库迁移脚本 - 修复分类重复问题
-- 执行时间：2026-06-12
-- 说明：添加唯一索引防止分类重复，并清理已有重复数据
-- =====================================================

USE smart_file_manager;

-- 1. 清理重复的分类数据（保留最新的记录）
DELETE t1 FROM file_classifications t1
INNER JOIN file_classifications t2 
WHERE 
    t1.id < t2.id 
    AND t1.file_id = t2.file_id 
    AND t1.classification_type = t2.classification_type 
    AND t1.classification_value = t2.classification_value;

-- 2. 添加唯一索引（防止未来再次出现重复）
-- 使用 ALTER TABLE IGNORE 自动忽略重复键
ALTER IGNORE TABLE file_classifications 
ADD UNIQUE INDEX idx_file_cls_unique (file_id, classification_type, classification_value);

-- 3. 验证结果
SELECT 
    file_id, 
    classification_type, 
    classification_value, 
    COUNT(*) as count
FROM file_classifications
GROUP BY file_id, classification_type, classification_value
HAVING count > 1;

-- 如果上面的查询返回空结果，说明重复数据已清理完成
