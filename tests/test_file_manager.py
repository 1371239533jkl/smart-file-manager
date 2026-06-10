"""
测试 file_manager 回收区功能（_move_to_trash / _restore_from_trash）
使用真实临时文件，不依赖数据库
"""
import os
import tempfile
import shutil
import pytest
from unittest.mock import patch


class TestTrashOperations:
    """测试回收区的移入/恢复功能"""

    def setup_method(self):
        """创建临时测试目录"""
        self.test_dir = tempfile.mkdtemp(prefix='sfm_test_')
        # mock _APP_DIR 和 _TRASH_DIR 指向测试目录
        self.trash_dir = os.path.join(self.test_dir, '.trash')

    def teardown_method(self):
        """清理临时目录"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_temp_file(self, filename='test.txt', content='hello') -> str:
        """在测试目录中创建临时文件"""
        path = os.path.join(self.test_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path

    def test_move_to_trash(self):
        """文件应成功移入回收区"""
        src = self._create_temp_file('myfile.txt')
        assert os.path.exists(src)

        # 调用被测函数
        from core.file_manager import _move_to_trash, _TRASH_DIR
        # 临时替换 _TRASH_DIR
        import core.file_manager as fm
        original_trash = fm._TRASH_DIR
        fm._TRASH_DIR = self.trash_dir
        try:
            trash_path = _move_to_trash(src)
            assert not os.path.exists(src), "原文件应被移走"
            assert os.path.exists(trash_path), "回收区应有文件"
            assert trash_path.startswith(self.trash_dir), "应在回收区目录下"
        finally:
            fm._TRASH_DIR = original_trash

    def test_move_to_trash_preserves_content(self):
        """移入回收区后文件内容不变"""
        content = 'important data'
        src = self._create_temp_file('data.txt', content)

        import core.file_manager as fm
        original_trash = fm._TRASH_DIR
        fm._TRASH_DIR = self.trash_dir
        try:
            trash_path = fm._move_to_trash(src)
            with open(trash_path, 'r', encoding='utf-8') as f:
                assert f.read() == content
        finally:
            fm._TRASH_DIR = original_trash

    def test_move_to_trash_unique_name(self):
        """多个同名文件移入回收区后应有不同路径"""
        import core.file_manager as fm
        original_trash = fm._TRASH_DIR
        fm._TRASH_DIR = self.trash_dir
        try:
            src1 = self._create_temp_file('dup.txt', '1')
            trash1 = fm._move_to_trash(src1)

            src2 = self._create_temp_file('dup.txt', '2')
            trash2 = fm._move_to_trash(src2)

            assert trash1 != trash2, "同名文件应产生不同的回收区路径"
        finally:
            fm._TRASH_DIR = original_trash

    def test_restore_from_trash(self):
        """文件应从回收区恢复到原路径"""
        import core.file_manager as fm
        original_trash = fm._TRASH_DIR
        fm._TRASH_DIR = self.trash_dir
        try:
            src = self._create_temp_file('restore_me.txt', 'restore content')
            trash_path = fm._move_to_trash(src)
            assert not os.path.exists(src)

            # 恢复
            fm._restore_from_trash(trash_path, src)
            assert os.path.exists(src), "文件应被恢复"
            assert not os.path.exists(trash_path), "回收区文件应被移走"
            with open(src, 'r', encoding='utf-8') as f:
                assert f.read() == 'restore content'
        finally:
            fm._TRASH_DIR = original_trash

    def test_restore_from_trash_file_not_found(self):
        """回收区文件不存在时应抛出 FileNotFoundError"""
        import core.file_manager as fm
        original_trash = fm._TRASH_DIR
        fm._TRASH_DIR = self.trash_dir
        try:
            fake_trash_path = os.path.join(self.trash_dir, 'nonexistent.txt')
            with pytest.raises(FileNotFoundError):
                fm._restore_from_trash(fake_trash_path, '/some/original/path.txt')
        finally:
            fm._TRASH_DIR = original_trash

    def test_restore_from_trash_original_occupied(self):
        """原路径已被占用时应抛出 FileExistsError"""
        import core.file_manager as fm
        original_trash = fm._TRASH_DIR
        fm._TRASH_DIR = self.trash_dir
        try:
            src = self._create_temp_file('occupied.txt', 'original')
            trash_path = fm._move_to_trash(src)

            # 在原路径创建一个新文件（占用路径）
            with open(src, 'w') as f:
                f.write('new file')

            with pytest.raises(FileExistsError):
                fm._restore_from_trash(trash_path, src)
        finally:
            fm._TRASH_DIR = original_trash

    def test_restore_creates_parent_dir(self):
        """恢复时如果父目录不存在，应自动创建"""
        import core.file_manager as fm
        original_trash = fm._TRASH_DIR
        fm._TRASH_DIR = self.trash_dir
        try:
            src = self._create_temp_file('sub_dir_file.txt', 'data')
            trash_path = fm._move_to_trash(src)

            # 恢复到一个不存在的子目录
            new_original = os.path.join(self.test_dir, 'new_subdir', 'restored.txt')
            fm._restore_from_trash(trash_path, new_original)
            assert os.path.exists(new_original)
        finally:
            fm._TRASH_DIR = original_trash
