"""
youtobe_bd 的主窗口模块
负责创建和管理主窗口界面
"""
import os
import sys
import threading
from typing import Optional, List, Dict, Tuple

# 导入 PyQt5 模块
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit,
    QProgressBar, QFileDialog, QRadioButton, QComboBox,
    QMessageBox, QGroupBox, QSplitter, QFrame, QStatusBar,
    QAction, QMenu, QDialog, QSplashScreen, QProgressDialog, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap

# 导入自定义模块
from src.ui.multi_download_tab import MultiDownloadTab
from src.ui.compress_tab import CompressTab
from src.ui.version_tab import VersionTab
from src.core.version_manager import VersionManager
from src.utils.logger import LoggerManager
from src.utils.config import ConfigManager
from src.ui.cookie_tab import CookieTab
from src.ui.proxy_tab import ProxyTab
from src.config.get_software_version import get_software_version

class VersionCheckThread(QThread):
    """版本检查线程类"""
    
    def __init__(self, version_tab):
        """初始化版本检查线程"""
        super().__init__()
        self.version_tab = version_tab
    
    def run(self):
        """执行版本检查"""
        # 延迟一段时间再执行版本检查，避免影响启动速度
        self.msleep(500)  # 延迟500毫秒
        self.version_tab.check_versions()


class AboutDialog(QDialog):
    """关于对话框类"""
    
    def __init__(self, parent=None):
        """初始化关于对话框"""
        super().__init__(parent)
        
        # 设置窗口属性
        self.setWindowTitle("关于")
        self.setFixedSize(400, 350)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 获取图标路径
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_path = os.path.join(base_dir, 'resources', 'icons', 'app_icon_horizontal.png')
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # 应用图标
        if os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(pixmap)
                icon_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(icon_label)
        
        # 应用名称
        app_name_label = QLabel("video_bd")
        app_name_label.setAlignment(Qt.AlignCenter)
        app_name_label.setStyleSheet("font-size: 18px; font-weight: normal;")
        layout.addWidget(app_name_label)

        # 版本信息
        version_label = QLabel(f"版本 v{get_software_version()}")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # 作者信息
        author_label = QLabel("By xgzit")
        author_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(author_label)

        # 版权信息
        copyright_label = QLabel("许可：GNU AGPL-3.0")
        copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_label)

        # GitHub 信息
        github_label = QLabel('<a href="https://github.com/xgzit/video_bd">GitHub</a>　基于 <a href="https://github.com/hwangzhun/youtube_downloader">hwangzhun/youtube_downloader</a> 二次开发')
        github_label.setOpenExternalLinks(True)
        github_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(github_label)

        # 描述信息
        description_label = QLabel("支持 1000+ 网站（YouTube、TikTok、Twitter/X、Instagram 等）视频批量下载，可选清晰度与格式，内置 Cookie、代理及自动更新功能。")
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(description_label)
        
        # 弹性空间
        layout.addStretch()
        
        # 确定按钮
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        ok_button.setFixedWidth(100)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)


class InstructionDialog(QDialog):
    """使用说明对话框类"""
    
    def __init__(self, parent=None, on_close_callback=None):
        """初始化使用说明对话框"""
        super().__init__(parent)
        self.on_close_callback = on_close_callback
        
        # 设置窗口属性
        self.setWindowTitle("使用说明")
        self.resize(600, 450)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # 文本框
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        # 支持富文本/Markdown样式
        self.text_edit.setMarkdown(
"""
# 欢迎使用 video_bd 🚀

支持 **1000+ 网站**批量下载，包括 YouTube、TikTok、Twitter/X、Instagram、Facebook、Bilibili 等。

### 📌 基本步骤：
1. **复制链接**：复制任意支持网站的**视频**、**播放列表**或**频道**链接。
    - 单个视频：`https://www.youtube.com/watch?v=...`、`https://www.tiktok.com/@user/video/...`
    - 播放列表：`https://www.youtube.com/playlist?list=...`
    - 频道/主页：`https://www.youtube.com/@username`、`https://www.tiktok.com/@username`
2. **粘贴内容**：在"视频下载"页面的输入框中粘贴链接（支持多行同时粘贴）。
3. **环境设置**：选择下载保存目录和全局首选音视频质量。
4. **解析链接**：点击 **"解析链接"**，频道或播放列表会自动展开所有视频。
5. **开始下载**：解析完毕后视频进入队列，点击 **"全部开始"** 即可一键下载！

### 🛠️ 进阶提示：
- **Cookie 机制**：如遇**年龄限制**、**会员专属**或登录后可见的内容，可到 **"Cookie"** 页面从浏览器一键提取 Cookie（支持 Chrome、Firefox、Edge 等），然后在下载页勾选"使用 Cookie"。
- **网络代理**：如需翻墙访问受限内容，请在 **"代理"** 页面配置 HTTP 或 SOCKS 代理。
- **自动回退**：链接类型无法判断时会自动尝试所有解析方式，两种途径均失败才报错。

### ⚠️ 注意事项：
- 除单视频外，**频道链接**和**播放列表链接**一次只能有一个，请勿混杂多个以免影响稳定性。
- 解析后可在表格中为每个视频单独调整清晰度和音频质量。
- 频道/列表展开结果缓存 **90 分钟**，单视频信息缓存 **24 小时**，重复解析无需等待。
"""
        )
        layout.addWidget(self.text_edit)
        
        # 下次不再显示勾选框
        self.no_show_checkbox = QCheckBox("下次启动不再自动显示使用说明")
        layout.addWidget(self.no_show_checkbox)
        
        # 确定按钮
        ok_button = QPushButton("关闭")
        ok_button.clicked.connect(self._on_close)
        ok_button.setFixedWidth(100)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _on_close(self):
        """关闭时回调，传递劾选状态"""
        if self.on_close_callback:
            self.on_close_callback(self.no_show_checkbox.isChecked())
        self.accept()


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self, splash_screen=None, skip_update_check=False):
        """
        初始化主窗口
        
        Args:
            splash_screen: 启动画面
            skip_update_check: 是否跳过更新检查
        """
        super().__init__()
        
        # 保存启动画面引用
        self.splash_screen = splash_screen
        
        # 初始化日志和配置
        self.logger = LoggerManager().get_logger()
        self.config_manager = ConfigManager()
        
        # 初始化版本管理器
        self.version_manager = VersionManager()
        
        # 设置窗口属性
        self.setWindowTitle(f"video_bd - v{get_software_version()}")
        self.setMinimumSize(800, 600)
        
        # 获取当前脚本所在目录
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # icon_path = os.path.join(base_dir, 'resources', 'icons', 'app_icon.ico')
        icon_vertical_path = os.path.join(base_dir, 'resources', 'icons', 'app_icon.ico')
        
        # 设置窗口图标
        if os.path.exists(icon_vertical_path):
            self.setWindowIcon(QIcon(icon_vertical_path))
        
        # 初始化 UI
        self.init_ui()
        
        # 初始化更新检查
        if not skip_update_check:
            self.check_updates()
        
        # 关闭启动画面
        if self.splash_screen:
            self.splash_screen.finish(self)
            self.splash_screen = None
        
        # 检查 JavaScript 运行时
        self.check_javascript_runtime()
        
        # 如需，主窗口渲染完成后再弹出使用说明
        if self.config_manager.get('show_instruction_on_startup', True):
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(800, self.show_instruction_dialog)
        
        # 记录日志
        self.logger.info("主窗口初始化完成")
    
    def init_ui(self):
        """初始化 UI"""
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 更新启动画面状态
        if self.splash_screen:
            self.splash_screen.showMessage("正在加载界面组件...", Qt.AlignBottom | Qt.AlignCenter, Qt.black)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 更新启动画面状态
        if self.splash_screen:
            self.splash_screen.showMessage("正在加载下载模块...", Qt.AlignBottom | Qt.AlignCenter, Qt.black)
        
        # 创建下载标签页
        self.cookie_tab = CookieTab(self.status_bar)
        self.proxy_tab = ProxyTab(self.config_manager, self.status_bar)
        self.multi_download_tab = MultiDownloadTab(self.config_manager, self.status_bar, self.cookie_tab)
        self.compress_tab = CompressTab()
        self.version_tab = VersionTab(self.status_bar, auto_check=False)

        # 添加标签页
        self.tab_widget.addTab(self.multi_download_tab, "视频下载")
        self.tab_widget.addTab(self.compress_tab, "视频压缩")
        self.tab_widget.addTab(self.cookie_tab, "Cookie")
        self.tab_widget.addTab(self.proxy_tab, "代理")
        self.tab_widget.addTab(self.version_tab, "版本")
        
        # 添加标签页到主布局
        main_layout.addWidget(self.tab_widget)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 设置状态栏初始状态
        self.status_bar.showMessage("就绪")
        
        # 添加作者信息到状态栏
        self.author_label = QLabel("By xgzit | AGPL-3.0")
        self.author_label.setStyleSheet("color: #94A3B8; padding: 0 8px;")
        self.status_bar.addPermanentWidget(self.author_label)
        
        # 应用 Metro 风格
        self.apply_metro_style()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        # 创建菜单栏
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        
        # 退出动作
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")
        
        # 关于动作
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
        # 使用说明按钮
        instruction_action = menu_bar.addAction("使用说明")
        instruction_action.triggered.connect(self.show_instruction_dialog)
    
    def show_about_dialog(self):
        """显示关于对话框"""
        about_dialog = AboutDialog(self)
        about_dialog.exec_()
        
    def show_instruction_dialog(self):
        """显示使用说明对话框"""
        instruction_dialog = InstructionDialog(
            self,
            on_close_callback=self._on_instruction_dialog_closed
        )
        instruction_dialog.exec_()
    
    def _on_instruction_dialog_closed(self, no_show_next_time: bool):
        """使用说明关闭回调"""
        if no_show_next_time:
            self.config_manager.set('show_instruction_on_startup', False)
            self.config_manager.save_config()
    
    def apply_metro_style(self):
        """应用现代化样式（自适应系统 DPI 缩放）"""
        # ── 根据实际屏幕 DPI 计算缩放比例 ──────────────────────
        # Qt pt 单位会自动跟随 DPI，px 单位不会；
        # 这里把所有 px 值换算成与 96 DPI 基准等比的逻辑像素。
        from PyQt5.QtWidgets import QApplication
        from src.utils.platform import get_project_root
        screen = QApplication.primaryScreen()
        dpi    = screen.logicalDotsPerInch() if screen else 96.0
        s      = max(1.0, dpi / 96.0)          # 缩放系数：100%→1.0，150%→1.5

        def p(n: float) -> int:
            """将基准 px 值按 DPI 缩放，最小返回 1"""
            return max(1, round(n * s))

        # 图标路径（正斜杠，Qt QSS 要求）
        icons_dir   = str(get_project_root() / 'resources' / 'icons').replace('\\', '/')
        check_url   = f"{icons_dir}/checkmark.svg"
        radio_url   = f"{icons_dir}/radio_dot.svg"

        # ── 字体大小（pt 单位，Qt 自动缩放，无需额外处理）──────
        fs   = 10   # 正文字号
        fs_s = 9    # 次要/辅助字号

        self.setStyleSheet(f"""
            /* ── 主窗口 ── */
            QMainWindow {{
                background-color: #F8FAFC;
            }}

            QWidget {{
                font-family: "Microsoft YaHei UI", "Segoe UI", Arial, sans-serif;
                font-size: {fs}pt;
                color: #0F172A;
            }}

            /* ── 标签页 ── */
            QTabWidget::pane {{
                border: none;
                background-color: white;
                border-radius: {p(12)}px;
                margin-top: {p(8)}px;
            }}

            QTabBar::tab {{
                background-color: transparent;
                color: #64748B;
                padding: {p(10)}px {p(22)}px;
                margin-right: {p(4)}px;
                border: none;
                border-top-left-radius: {p(8)}px;
                border-top-right-radius: {p(8)}px;
                font-weight: 500;
                font-size: {fs}pt;
            }}

            QTabBar::tab:selected {{
                background-color: white;
                color: #0F172A;
                font-weight: 600;
            }}

            QTabBar::tab:hover:!selected {{
                background-color: #F1F5F9;
                color: #475569;
            }}

            /* ── 按钮（主要） ── */
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #EF4444, stop:1 #DC2626);
                color: white;
                border: none;
                border-radius: {p(6)}px;
                padding: {p(4)}px {p(16)}px;
                font-weight: 600;
                font-size: {fs}pt;
                min-height: {p(18)}px;
            }}

            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #DC2626, stop:1 #B91C1C);
            }}

            QPushButton:pressed {{
                background-color: #991B1B;
            }}

            QPushButton:disabled {{
                background: none;
                background-color: #E2E8F0;
                color: #94A3B8;
            }}

            /* ── 次要按钮 ── */
            QPushButton[objectName="secondaryButton"] {{
                background: none;
                background-color: white;
                color: #475569;
                border: {p(2)}px solid #E2E8F0;
                padding: {p(4)}px {p(12)}px;
                min-height: 0;
            }}

            QPushButton[objectName="secondaryButton"]:hover {{
                border-color: #CBD5E1;
                background-color: #F8FAFC;
            }}

            /* ── 输入框 ── */
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: white;
                border: {p(2)}px solid #E2E8F0;
                border-radius: {p(6)}px;
                padding: {p(4)}px {p(10)}px;
                color: #0F172A;
                font-size: {fs}pt;
                selection-background-color: #EF4444;
            }}

            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border-color: #EF4444;
            }}

            QLineEdit:disabled, QTextEdit:disabled {{
                background-color: #F1F5F9;
                color: #94A3B8;
            }}

            /* ── 下拉框 ── */
            QComboBox {{
                background-color: white;
                border: {p(2)}px solid #E2E8F0;
                border-radius: {p(6)}px;
                padding: {p(3)}px {p(10)}px;
                min-width: {p(100)}px;
                min-height: {p(18)}px;
                font-size: {fs}pt;
            }}

            QComboBox:hover {{
                border-color: #CBD5E1;
            }}

            QComboBox:focus {{
                border-color: #EF4444;
            }}

            QComboBox::drop-down {{
                border: none;
                width: {p(26)}px;
            }}

            QComboBox QAbstractItemView {{
                background-color: white;
                border: {p(2)}px solid #E2E8F0;
                border-radius: {p(8)}px;
                padding: {p(4)}px;
                selection-background-color: #FEE2E2;
                selection-color: #0F172A;
                outline: none;
                font-size: {fs}pt;
            }}

            QComboBox QAbstractItemView::item {{
                padding: {p(6)}px {p(12)}px;
                border-radius: {p(4)}px;
                min-height: {p(24)}px;
            }}

            QComboBox QAbstractItemView::item:hover {{
                background-color: #FEE2E2;
            }}

            /* ── 复选框 ── */
            QCheckBox {{
                spacing: {p(8)}px;
                color: #0F172A;
                font-size: {fs}pt;
            }}

            QCheckBox::indicator {{
                width: {p(18)}px;
                height: {p(18)}px;
                border-radius: {p(4)}px;
                border: {p(2)}px solid #CBD5E1;
                background-color: white;
            }}

            QCheckBox::indicator:hover {{
                border-color: #EF4444;
            }}

            QCheckBox::indicator:checked {{
                background-color: #EF4444;
                border-color: #EF4444;
                image: url({check_url});
            }}

            /* ── 进度条 ── */
            QProgressBar {{
                border: none;
                border-radius: {p(6)}px;
                background-color: #F1F5F9;
                text-align: center;
                color: #475569;
                font-weight: 600;
                font-size: {fs_s}pt;
                min-height: {p(14)}px;
            }}

            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #EF4444, stop:1 #DC2626);
                border-radius: {p(6)}px;
            }}

            /* ── 分组框 ── */
            QGroupBox {{
                background-color: white;
                border: {p(2)}px solid #E2E8F0;
                border-radius: {p(10)}px;
                margin-top: {p(14)}px;
                padding-top: {p(4)}px;
                font-weight: 600;
                font-size: {fs}pt;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: {p(2)}px {p(10)}px;
                background-color: transparent;
                color: #0F172A;
                font-size: {fs}pt;
            }}

            /* ── 表格 ── */
            QTableWidget {{
                background-color: white;
                border: none;
                gridline-color: #F1F5F9;
                selection-background-color: #FEE2E2;
                selection-color: #0F172A;
                font-size: {fs}pt;
            }}

            QTableWidget::item {{
                padding: {p(5)}px;
                border-bottom: 1px solid #F1F5F9;
            }}

            QTableWidget::item:selected {{
                background-color: #FEE2E2;
            }}

            QHeaderView::section {{
                background-color: #F8FAFC;
                color: #64748B;
                padding: {p(7)}px {p(8)}px;
                border: none;
                border-bottom: {p(2)}px solid #E2E8F0;
                font-weight: 600;
                font-size: {fs_s}pt;
            }}

            QHeaderView::section:hover {{
                background-color: #F1F5F9;
            }}

            QTableWidget QTableCornerButton::section {{
                background-color: #F8FAFC;
                border: none;
            }}

            /* ── 滚动条 ── */
            QScrollBar:vertical {{
                background-color: #F8FAFC;
                width: {p(12)}px;
                border-radius: {p(6)}px;
            }}

            QScrollBar::handle:vertical {{
                background-color: #CBD5E1;
                border-radius: {p(6)}px;
                min-height: {p(32)}px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: #94A3B8;
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QScrollBar:horizontal {{
                background-color: #F8FAFC;
                height: {p(12)}px;
                border-radius: {p(6)}px;
            }}

            QScrollBar::handle:horizontal {{
                background-color: #CBD5E1;
                border-radius: {p(6)}px;
                min-width: {p(32)}px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background-color: #94A3B8;
            }}

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}

            /* ── 状态栏 ── */
            QStatusBar {{
                background-color: #F1F5F9;
                color: #64748B;
                border-top: 1px solid #E2E8F0;
                font-size: {fs_s}pt;
            }}

            /* ── 菜单栏 ── */
            QMenuBar {{
                background-color: #F8FAFC;
                border-bottom: 1px solid #E2E8F0;
                font-size: {fs}pt;
            }}

            QMenuBar::item {{
                padding: {p(6)}px {p(12)}px;
                background: transparent;
                border-radius: {p(4)}px;
            }}

            QMenuBar::item:selected {{
                background-color: #FEE2E2;
                color: #DC2626;
            }}

            QMenu {{
                background-color: white;
                border: {p(2)}px solid #E2E8F0;
                border-radius: {p(8)}px;
                padding: {p(4)}px;
                font-size: {fs}pt;
            }}

            QMenu::item {{
                padding: {p(8)}px {p(20)}px;
                border-radius: {p(4)}px;
                min-height: {p(24)}px;
            }}

            QMenu::item:selected {{
                background-color: #FEE2E2;
                color: #DC2626;
            }}

            /* ── 单选按钮 ── */
            QRadioButton {{
                spacing: {p(8)}px;
                font-size: {fs}pt;
            }}

            QRadioButton::indicator {{
                width: {p(18)}px;
                height: {p(18)}px;
                border-radius: {p(9)}px;
                border: {p(2)}px solid #CBD5E1;
                background-color: white;
            }}

            QRadioButton::indicator:checked {{
                background-color: #EF4444;
                border-color: #EF4444;
                image: url({radio_url});
            }}

            QRadioButton::indicator:hover {{
                border-color: #EF4444;
            }}

            /* ── 标签 ── */
            QLabel {{
                color: #0F172A;
                font-size: {fs}pt;
            }}

            /* ── 表格内小按钮（objectName="tableBtn"）── */
            QPushButton[objectName="tableBtn"] {{
                background: none;
                background-color: #F1F5F9;
                border: 1px solid #E2E8F0;
                border-radius: {p(4)}px;
                padding: {p(2)}px {p(4)}px;
                color: #475569;
                font-size: {fs_s}pt;
                min-height: {p(22)}px;
            }}

            QPushButton[objectName="tableBtn"]:hover {{
                background-color: #E2E8F0;
                border-color: #CBD5E1;
            }}

            QPushButton[objectName="tableBtn"]:pressed {{
                background-color: #CBD5E1;
            }}

            /* ── 表格内下拉框（objectName="tableCombo"）── */
            QComboBox[objectName="tableCombo"] {{
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: {p(4)}px;
                padding: {p(3)}px {p(6)}px;
                color: #0F172A;
                min-width: {p(80)}px;
                font-size: {fs_s}pt;
            }}

            QComboBox[objectName="tableCombo"]:hover {{
                border-color: #94A3B8;
                background-color: white;
            }}

            QComboBox[objectName="tableCombo"]::drop-down {{
                border: none;
                width: {p(20)}px;
            }}

            QComboBox[objectName="tableCombo"] QAbstractItemView {{
                background-color: white;
                border: 1px solid #CBD5E1;
                border-radius: {p(4)}px;
                selection-background-color: #FEE2E2;
                selection-color: #0F172A;
                font-size: {fs_s}pt;
            }}
        """)
    
    def check_updates(self):
        """检查更新"""
        try:
            # TODO: 实现更新检查逻辑
            pass
        except Exception as e:
            self.logger.error(f"检查更新失败: {str(e)}")
    
    def check_binaries(self):
        """检查并下载必要的二进制文件"""
        try:
            # 优先判断是否都存在
            if self.version_manager.binaries_exist():
                self.logger.info("二进制文件已存在，无需下载")
                return
            self.logger.info("开始检查二进制文件")
            # 创建进度对话框
            progress = QProgressDialog("正在检查必要的组件...", "取消", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setWindowTitle("初始化")
            progress.setAutoClose(True)
            progress.setAutoReset(True)
            def update_progress(value, status):
                progress.setValue(value)
                progress.setLabelText(status)
            # 检查并下载二进制文件
            success, error = self.version_manager.check_and_download_binaries(update_progress)
            if not success:
                self.logger.error(f"检查二进制文件失败: {error}")
                QMessageBox.critical(self, "错误", f"检查必要的组件时发生错误：\n{error}")
                sys.exit(1)
            self.logger.info("二进制文件检查完成")
        except Exception as e:
            self.logger.error(f"检查二进制文件时发生错误: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"检查必要的组件时发生错误：\n{str(e)}")
            sys.exit(1)
    
    def check_javascript_runtime(self):
        """检查 JavaScript 运行时，如果没有则提示用户"""
        from src.utils.platform import find_javascript_runtime
        import webbrowser
        
        runtime = find_javascript_runtime()
        if not runtime:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("缺少 JavaScript 运行时")
            msg.setText("检测到您的系统未安装 JavaScript 运行时")
            msg.setInformativeText(
                "YouTube 现在需要 JavaScript 运行时来提取视频信息。\n\n"
                "推荐安装 Node.js：https://nodejs.org/\n\n"
                "您可以选择自动安装（需要 Windows 10 1709+ 或 Windows 11）\n"
                "或手动下载安装。安装完成后请重启应用程序。"
            )
            
            # 添加按钮
            auto_install = QPushButton("自动安装 Node.js")
            open_nodejs = QPushButton("打开 Node.js 官网")
            ignore = QPushButton("稍后提醒")
            
            msg.addButton(auto_install, QMessageBox.ActionRole)
            msg.addButton(open_nodejs, QMessageBox.ActionRole)
            msg.addButton(ignore, QMessageBox.RejectRole)
            
            result = msg.exec_()
            
            if result == 0:  # 自动安装 Node.js
                self.logger.info("用户选择自动安装 Node.js")
                self._install_nodejs_via_winget()
            elif result == 1:  # 打开 Node.js 官网
                webbrowser.open('https://nodejs.org/')
                self.logger.info("用户点击打开 Node.js 官网")
            else:
                self.logger.info("用户选择稍后提醒")
        else:
            self.logger.info(f"检测到 JavaScript 运行时: {runtime}")
    
    def _install_nodejs_via_winget(self):
        """使用 winget 安装 Node.js"""
        import subprocess
        import webbrowser
        
        # 显示安装进度对话框
        progress = QProgressDialog("正在安装 Node.js，请稍候...", "取消", 0, 0, self)
        progress.setWindowTitle("安装 Node.js")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        QApplication.processEvents()
        
        try:
            # 检查 winget 是否可用
            check_winget = subprocess.run(
                ['winget', '--version'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if check_winget.returncode != 0:
                progress.close()
                QMessageBox.warning(
                    self, 
                    "winget 不可用",
                    "您的系统未安装 winget（Windows 包管理器）。\n\n"
                    "请手动下载安装 Node.js，或升级到 Windows 10 1709+ / Windows 11。"
                )
                webbrowser.open('https://nodejs.org/')
                return
            
            # 使用 winget 安装 Node.js LTS
            self.logger.info("开始使用 winget 安装 Node.js LTS")
            install_process = subprocess.run(
                [
                    'winget', 'install', 'OpenJS.NodeJS.LTS',
                    '--accept-source-agreements',
                    '--accept-package-agreements',
                    '--silent'
                ],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            progress.close()
            
            if install_process.returncode == 0:
                self.logger.info("Node.js 安装成功")
                QMessageBox.information(
                    self,
                    "安装成功",
                    "Node.js 已成功安装！\n\n"
                    "请重启应用程序以使更改生效。"
                )
            else:
                # 检查是否已安装
                if "已安装" in install_process.stdout or "already installed" in install_process.stdout.lower():
                    self.logger.info("Node.js 已经安装")
                    QMessageBox.information(
                        self,
                        "已安装",
                        "Node.js 已经安装在您的系统中。\n\n"
                        "请重启应用程序以使更改生效。"
                    )
                else:
                    self.logger.error(f"Node.js 安装失败: {install_process.stderr}")
                    QMessageBox.warning(
                        self,
                        "安装失败",
                        f"自动安装失败，请手动下载安装 Node.js。\n\n"
                        f"错误信息：{install_process.stderr[:200] if install_process.stderr else '未知错误'}"
                    )
                    webbrowser.open('https://nodejs.org/')
                    
        except FileNotFoundError:
            progress.close()
            self.logger.error("winget 命令未找到")
            QMessageBox.warning(
                self,
                "winget 不可用",
                "您的系统未安装 winget（Windows 包管理器）。\n\n"
                "请手动下载安装 Node.js。"
            )
            webbrowser.open('https://nodejs.org/')
        except Exception as e:
            progress.close()
            self.logger.error(f"安装 Node.js 时发生错误: {str(e)}")
            QMessageBox.warning(
                self,
                "安装错误",
                f"安装过程中发生错误：{str(e)}\n\n"
                "请手动下载安装 Node.js。"
            )
            webbrowser.open('https://nodejs.org/')
    
    def closeEvent(self, event):
        """关闭窗口事件处理"""
        # 保存配置
        self.config_manager.save_config()
        
        # 记录日志
        self.logger.info("应用程序关闭")
        
        # 接受关闭事件
        event.accept()
