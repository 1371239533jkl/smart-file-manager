"""
数据库迁移脚本 - 修复分类重复问题
运行方式：python migrations/fix_duplicate_classifications.py
"""
import sys
import os

# 确保项目根目录在路径中
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from database.db_manager import db
from utils.logger import logger


def fix_duplicate_classifications():
    """修复分类重复问题"""
    logger.info("开始修复分类重复问题...")
    
    try:
        # 1. 查询重复数据数量
        sql_check = """
            SELECT COUNT(*) as total FROM (
                SELECT file_id, classification_type, classification_value, COUNT(*) as count
                FROM file_classifications
                GROUP BY file_id, classification_type, classification_value
                HAVING count > 1
            ) t
        """
        result = db.execute_one(sql_check)
        duplicate_count = result['total'] if result else 0
        
        if duplicate_count == 0:
            logger.info("✅ 没有发现重复的分类数据")
            return
        
        logger.info(f"发现 {duplicate_count} 个重复的分类组合，开始清理...")
        
        # 2. 删除重复数据（保留最新的记录）
        sql_delete = """
            DELETE t1 FROM file_classifications t1
            INNER JOIN file_classifications t2 
            WHERE 
                t1.id < t2.id 
                AND t1.file_id = t2.file_id 
                AND t1.classification_type = t2.classification_type 
                AND t1.classification_value = t2.classification_value
        """
        deleted = db.execute_update(sql_delete)
        logger.info(f"✅ 删除了 {deleted} 条重复的分类记录")
        
        # 3. 添加唯一索引
        try:
            sql_index = """
                ALTER IGNORE TABLE file_classifications 
                ADD UNIQUE INDEX idx_file_cls_unique (file_id, classification_type, classification_value)
            """
            db.execute_update(sql_index)
            logger.info("✅ 成功添加唯一索引 idx_file_cls_unique")
        except Exception as e:
            if 'Duplicate key name' in str(e):
                logger.info("ℹ️  唯一索引已存在，跳过创建")
            else:
                logger.error(f"❌ 添加唯一索引失败: {e}")
                raise
        
        # 4. 验证结果
        result = db.execute_one(sql_check)
        remaining = result['total'] if result else 0
        
        if remaining == 0:
            logger.info("✅ 分类重复问题修复完成！")
        else:
            logger.warning(f"⚠️  仍有 {remaining} 个重复项，请手动检查")
            
    except Exception as e:
        logger.error(f"❌ 修复失败: {e}")
        raise


if __name__ == '__main__':
    fix_duplicate_classifications()
