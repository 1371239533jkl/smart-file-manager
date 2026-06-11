"""
清空所有数据脚本
运行方式：python scripts/clear_all_data.py
"""
import sys
import os

# 确保项目根目录在路径中
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from database.db_manager import db
from utils.logger import logger


def clear_all_data(confirm: bool = False):
    """清空所有数据"""
    if not confirm:
        print("=" * 60)
        print("⚠️  警告：此操作将清空智能文件管家中的所有数据！")
        print("=" * 60)
        print("\n将清空以下内容：")
        print("  • 所有文件记录（files 表）")
        print("  • 文件元数据（file_metadata 表）")
        print("  • 文件分类（file_classifications 表）")
        print("  • 操作历史（operation_history 表）")
        print("  • 扫描目录配置（scan_directories 表）")
        print("  • 文件标签（file_tags 表）")
        print("\n⚠️  注意：")
        print("  • 此操作不可撤销！")
        print("  • 磁盘上的实际文件不会被删除")
        print("  • 回收区中的文件不会被删除")
        print()
        
        answer = input("请输入 'YES' 确认清空（其他任何输入取消）: ")
        if answer.strip().upper() != 'YES':
            print("❌ 操作已取消")
            return
    
    try:
        logger.info("开始清空所有数据...")
        
        # 1. 查询当前数据量
        file_count = db.execute_one("SELECT COUNT(*) as count FROM files")['count']
        dir_count = db.execute_one("SELECT COUNT(*) as count FROM scan_directories")['count']
        
        if file_count == 0 and dir_count == 0:
            logger.info("✅ 数据库已经是空的，无需清空")
            return
        
        logger.info(f"当前数据量: {file_count} 个文件, {dir_count} 个扫描目录")
        
        # 2. 清空数据（按外键依赖顺序）
        tables = [
            'file_tags',              # 文件标签
            'file_classifications',   # 文件分类
            'file_metadata',          # 文件元数据
            'operation_history',      # 操作历史
            'files',                  # 文件记录
            'scan_directories',       # 扫描目录配置
        ]
        
        for table in tables:
            try:
                db.execute_update(f"TRUNCATE TABLE {table}")
                logger.info(f"✅ 已清空 {table}")
            except Exception as e:
                logger.warning(f"⚠️  清空 {table} 失败: {e}")
        
        # 3. 验证结果
        remaining_files = db.execute_one("SELECT COUNT(*) as count FROM files")['count']
        remaining_dirs = db.execute_one("SELECT COUNT(*) as count FROM scan_directories")['count']
        
        if remaining_files == 0 and remaining_dirs == 0:
            logger.info("✅ 所有数据已成功清空！")
            print("\n✅ 所有数据已成功清空！")
        else:
            logger.warning(f"⚠️  清空不完全: 剩余 {remaining_files} 个文件, {remaining_dirs} 个目录")
            print(f"\n⚠️  清空不完全: 剩余 {remaining_files} 个文件, {remaining_dirs} 个目录")
            
    except Exception as e:
        logger.error(f"❌ 清空失败: {e}")
        print(f"\n❌ 清空失败: {e}")
        raise


if __name__ == '__main__':
    clear_all_data()
