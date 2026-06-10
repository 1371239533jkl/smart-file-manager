"""
测试 FileClassifier 内存分类逻辑（不依赖数据库）
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestFileClassifierInMemory:
    """测试 _classify_file_in_memory 系列方法"""

    def setup_method(self):
        """每次测试前：mock 掉 DB 依赖"""
        with patch('core.file_classifier.ClassificationDAO'), \
             patch('core.file_classifier.ClassificationRuleDAO'):
            from core.file_classifier import FileClassifier
            self.classifier = FileClassifier()
            # 强制缓存为空（不查数据库）
            self.classifier._db_rules_cache = []

    # ── 按类型分类 ──

    def test_classify_by_type_known(self):
        record = {'file_type': 'image'}
        assert self.classifier._classify_by_type(record) == '图片'

    def test_classify_by_type_video(self):
        record = {'file_type': 'video'}
        assert self.classifier._classify_by_type(record) == '视频'

    def test_classify_by_type_unknown(self):
        record = {'file_type': 'nonexistent_type'}
        assert self.classifier._classify_by_type(record) == '其他'

    def test_classify_by_type_missing(self):
        record = {}
        assert self.classifier._classify_by_type(record) == '其他'

    # ── 按日期分类 ──

    def test_classify_by_date_datetime(self):
        record = {'modify_time': datetime(2024, 3, 15, 10, 0)}
        assert self.classifier._classify_by_date(record) == '2024年03月'

    def test_classify_by_date_string(self):
        record = {'modify_time': '2023-12-25 08:30:00'}
        assert self.classifier._classify_by_date(record) == '2023年12月'

    def test_classify_by_date_fallback_to_create_time(self):
        record = {'create_time': datetime(2022, 1, 5)}
        assert self.classifier._classify_by_date(record) == '2022年01月'

    def test_classify_by_date_none(self):
        record = {}
        assert self.classifier._classify_by_date(record) is None

    def test_classify_by_date_invalid(self):
        record = {'modify_time': 'not-a-date'}
        assert self.classifier._classify_by_date(record) is None

    # ── 按关键词规则分类 ──

    def test_classify_by_rules_photo(self):
        record = {'file_name': 'IMG_20240101.jpg', 'file_path': 'C:/photos/'}
        results = self.classifier._classify_by_rules(record)
        categories = [c for c, _ in results]
        assert '照片' in categories

    def test_classify_by_rules_office(self):
        record = {'file_name': '合同_v2.docx', 'file_path': 'C:/docs/'}
        results = self.classifier._classify_by_rules(record)
        categories = [c for c, _ in results]
        assert '办公文档' in categories

    def test_classify_by_rules_installer(self):
        record = {'file_name': 'setup.exe', 'file_path': 'C:/downloads/'}
        results = self.classifier._classify_by_rules(record)
        categories = [c for c, _ in results]
        assert '安装包' in categories

    def test_classify_by_rules_archive(self):
        record = {'file_name': 'backup_2024.zip', 'file_path': 'C:/'}
        results = self.classifier._classify_by_rules(record)
        categories = [c for c, _ in results]
        assert '压缩包' in categories

    def test_classify_by_rules_desktop_path(self):
        record = {'file_name': 'notes.txt', 'file_path': 'C:/Users/admin/Desktop/'}
        results = self.classifier._classify_by_rules(record)
        categories = [c for c, _ in results]
        assert '桌面文件' in categories

    def test_classify_by_rules_download_path(self):
        record = {'file_name': 'file.pdf', 'file_path': 'C:/Users/admin/Downloads/'}
        results = self.classifier._classify_by_rules(record)
        categories = [c for c, _ in results]
        assert '下载文件' in categories

    def test_classify_by_rules_no_match(self):
        record = {'file_name': 'abc123.xyz', 'file_path': 'C:/random/'}
        results = self.classifier._classify_by_rules(record)
        assert results == []

    def test_classify_by_rules_confidence_range(self):
        """置信度应在 [0.5, 0.95] 范围内"""
        record = {'file_name': 'screenshot_2024.png', 'file_path': 'C:/'}
        results = self.classifier._classify_by_rules(record)
        for _, conf in results:
            assert 0.5 <= conf <= 0.95, f"置信度 {conf} 不在范围内"

    def test_classify_by_rules_no_duplicate_category(self):
        """同一分类不应出现两次"""
        record = {'file_name': '合同_报告_备份.zip', 'file_path': 'C:/'}
        results = self.classifier._classify_by_rules(record)
        categories = [c for c, _ in results]
        assert len(categories) == len(set(categories)), "分类有重复"

    # ── 内存全分类 ──

    def test_classify_file_in_memory_full(self):
        record = {
            'id': 1,
            'file_name': 'IMG_截图.png',
            'file_path': 'C:/Desktop/',
            'file_type': 'image',
            'modify_time': datetime(2024, 6, 10),
        }
        results = self.classifier._classify_file_in_memory(record)
        types = [r[0] for r in results]
        assert 'by_type' in types
        assert 'by_date' in types
        # IMG_ 在 name 里命中，Desktop 在 path 里命中
        assert 'by_keyword' in types

    def test_classify_file_in_memory_empty_record(self):
        record = {'id': 1}
        results = self.classifier._classify_file_in_memory(record)
        # 至少有 by_type（默认 '其他'）
        assert any(r[0] == 'by_type' for r in results)

    # ── 规则缓存 ──

    def test_invalidate_rules_cache(self):
        self.classifier._db_rules_cache = [('分类A', ['kw1'])]
        self.classifier.invalidate_rules_cache()
        assert self.classifier._db_rules_cache is None

    def test_load_db_rules_uses_cache(self):
        """设置缓存后不应再调用 rule_dao"""
        self.classifier._db_rules_cache = [('缓存分类', ['kw'])]
        result = self.classifier._load_db_rules()
        assert result == [('缓存分类', ['kw'])]

    # ── 数据库规则匹配 ──

    def test_classify_with_db_rules(self):
        """模拟数据库自定义规则"""
        self.classifier._db_rules_cache = [
            ('学习资料', ['课件', '笔记', 'ppt']),
        ]
        record = {'file_name': '课件_第一章.pdf', 'file_path': 'C:/study/'}
        results = self.classifier._classify_by_rules(record)
        categories = [c for c, _ in results]
        assert '学习资料' in categories
