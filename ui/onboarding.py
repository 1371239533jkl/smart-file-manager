"""
首次启动引导对话框 - 新用户快速上手指引
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QScrollArea, QWidget
)
from PyQt6.QtCore import Qt

from utils.display_utils import get_platform_font


TIPS = [
    ("📂 扫描文件", "在「扫描管理」中添加要管理的目录，系统会自动扫描并录入文件信息。"),
    ("🏷️ 智能分类", "扫描完成后，系统会按文件类型、修改日期、关键词自动分类，也可自定义规则。"),
    ("🔍 搜索与导出", "在「文件搜索」中按名称、类型、大小等条件筛选，支持导出 CSV。"),
    ("🔀 去重清理", "扫描后自动检测重复文件，可一键去重（移入回收区，支持撤销恢复）。"),
    ("📋 操作历史", "所有操作（重命名、移动、删除等）都有历史记录，支持逐条或按批次撤销。"),
    ("🏷️ 标签管理", "给文件打自定义标签，方便跨目录快速筛选。"),
    ("⌨️ 快捷键", "Ctrl+Z 可快速撤销最近一次操作。"),
]


class OnboardingDialog(QDialog):
    """首次启动引导对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("欢迎使用智能文件管家")
        self.setFixedSize(520, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # 标题
        title = QLabel("欢迎使用智能文件管家！")
        title.setFont(get_platform_font(18))
        title.setStyleSheet("font-weight: bold; color: #cba6f7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("以下是快速上手指南，帮助您快速了解核心功能：")
        subtitle.setStyleSheet("color: #a6adc8; font-size: 13px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # 提示列表（可滚动）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        tips_widget = QWidget()
        tips_layout = QVBoxLayout(tips_widget)
        tips_layout.setContentsMargins(8, 4, 8, 4)
        tips_layout.setSpacing(14)

        for icon_title, desc in TIPS:
            tip_label = QLabel(f"<b style='font-size:14px; color:#89b4fa;'>{icon_title}</b>"
                               f"<br><span style='font-size:13px; color:#cdd6f4;'>{desc}</span>")
            tip_label.setWordWrap(True)
            tip_label.setTextFormat(Qt.TextFormat.RichText)
            tips_layout.addWidget(tip_label)

        tips_layout.addStretch()
        scroll.setWidget(tips_widget)
        layout.addWidget(scroll, 1)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        start_btn = QPushButton("开始使用")
        start_btn.setFixedSize(120, 36)
        start_btn.setStyleSheet(
            "QPushButton { background-color: #cba6f7; color: #1e1e2e; "
            "border: none; border-radius: 6px; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background-color: #b4befe; }")
        start_btn.clicked.connect(self.accept)
        btn_layout.addWidget(start_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)
