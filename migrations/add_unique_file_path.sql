-- ============================================================
-- 迁移：为 files.file_path 添加 UNIQUE 约束，防止重复扫描产生重复记录
-- 执行方式: mysql -u root -p smart_file_manager < add_unique_file_path.sql
-- ============================================================

-- Step 1: 找出所有重复 file_path 中需要删除的 ID（保留最小的 id）
CREATE TEMPORARY TABLE dup_ids AS
SELECT f1.id FROM files f1
INNER JOIN files f2 ON f1.file_path = f2.file_path AND f1.id > f2.id;

-- Step 2: 删除重复文件关联的分类记录
DELETE FROM file_classifications WHERE file_id IN (SELECT id FROM dup_ids);

-- Step 3: 删除重复文件关联的元数据
DELETE FROM file_metadata WHERE file_id IN (SELECT id FROM dup_ids);

-- Step 4: 删除重复文件关联的操作历史
DELETE FROM operation_history WHERE file_id IN (SELECT id FROM dup_ids);

-- Step 5: 删除重复的文件记录
DELETE FROM files WHERE id IN (SELECT id FROM dup_ids);

-- Step 6: 清理临时表
DROP TEMPORARY TABLE dup_ids;

-- Step 7: 添加 UNIQUE 索引（如果已存在则忽略）
-- 使用存储过程避免重复添加报错
DELIMITER //
CREATE PROCEDURE add_unique_if_not_exists()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = 'files'
          AND index_name = 'idx_file_path_unique'
    ) THEN
        ALTER TABLE files ADD UNIQUE INDEX idx_file_path_unique (file_path);
    END IF;
END //
DELIMITER ;

CALL add_unique_if_not_exists();
DROP PROCEDURE add_unique_if_not_exists;
