"""
youtobe_bd 版本标签页模块
负责创建和管理版本标签页界面
"""
import os
import sys
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict, Tuple

# 导入 PyQt5 模块
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QGroupBox, QMessageBox, QApplication, QStatusBar, QFrame, QTextEdit,
    QGridLayout, QScrollArea, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette

# 导入自定义模块
from src.core.version_manager import VersionManager
from src.utils.logger import LoggerManager
from src.utils.config import ConfigManager


class UpdateWorker(QThread):
    """更新工作线程类"""
    
    # 定义信号
    progress_updated = pyqtSignal(int, str)
    update_completed = pyqtSignal(bool, str)
    
    def __init__(self, version_manager: VersionManager, update_type: str, download_url: str):
        """
        初始化更新工作线程
        
        Args:
            version_manager: 版本管理器
            update_type: 更新类型，'yt-dlp' 或 'ffmpeg' 或 'init'
            download_url: 下载URL
        """
        super().__init__()
        self.version_manager = version_manager
        self.update_type = update_type
        self.download_url = download_url
    
    def run(self):
        """执行更新任务"""
        try:
            if self.update_type == 'init':
                success, error = self.version_manager.check_and_download_binaries(
                    self._progress_callback
                )
                self.update_completed.emit(success, "" if success else error)
            elif self.update_type == 'yt-dlp':
                success, version = self.version_manager.update_yt_dlp(
                    self.download_url,
                    self._progress_callback
                )
                self.update_completed.emit(success, version if success else "更新失败")
            else:  # ffmpeg
                success, version = self.version_manager.update_ffmpeg(
                    self.download_url,
                    self._progress_callback
                )
                self.update_completed.emit(success, version if success else "更新失败")
        except Exception as e:
            self.update_completed.emit(False, str(e))
    
    def _progress_callback(self, progress: int, status: str):
        """进度回调函数"""
        self.progress_updated.emit(progress, status)


class VersionCheckThread(QThread):
    """版本检查线程类"""
    
    # 定义信号 - 增加 release notes 和文件大小信息
    check_completed = pyqtSignal(dict)  # 使用字典传递所有信息
    check_error = pyqtSignal(str)
    progress_updated = pyqtSignal(str)
    
    def __init__(self, version_manager: VersionManager):
        """
        初始化版本检查线程
        
        Args:
            version_manager: 版本管理器
        """
        super().__init__()
        self.version_manager = version_manager
    
    def run(self):
        """执行版本检查任务"""
        try:
            result = {}
            
            # 发送进度信号
            self.progress_updated.emit("正在检查 yt-dlp 版本...")
            
            # 检查 yt-dlp 版本
            yt_dlp_success, yt_dlp_current_version = self.version_manager.get_yt_dlp_version()
            yt_dlp_has_update, yt_dlp_latest_version, yt_dlp_download_url = self.version_manager.check_yt_dlp_update()
            
            # 获取 yt-dlp 的 release notes 和文件大小
            yt_dlp_release_notes = self.version_manager.get_yt_dlp_release_notes()
            yt_dlp_file_size = self.version_manager.get_yt_dlp_file_size()
            
            result['yt_dlp'] = {
                'success': yt_dlp_success,
                'current_version': yt_dlp_current_version,
                'has_update': yt_dlp_has_update,
                'latest_version': yt_dlp_latest_version,
                'download_url': yt_dlp_download_url,
                'release_notes': yt_dlp_release_notes,
                'file_size': yt_dlp_file_size,
                'install_path': self.version_manager.yt_dlp_path
            }
            
            # 发送进度信号
            self.progress_updated.emit("正在检查 ffmpeg 版本...")
            
            # 检查 ffmpeg 版本
            ffmpeg_success, ffmpeg_current_version = self.version_manager.get_ffmpeg_version()
            ffmpeg_has_update, ffmpeg_latest_version, ffmpeg_download_url = self.version_manager.check_ffmpeg_update()
            
            # 获取 ffmpeg 的 release notes 和文件大小
            ffmpeg_release_notes = self.version_manager.get_ffmpeg_release_notes()
            ffmpeg_file_size = self.version_manager.get_ffmpeg_total_size()
            
            # 修正 ffmpeg 最新版本显示问题
            if ffmpeg_latest_version == "last":
                ffmpeg_latest_version = "最新版本"
            
            result['ffmpeg'] = {
                'success': ffmpeg_success,
                'current_version': ffmpeg_current_version,
                'has_update': ffmpeg_has_update,
                'latest_version': ffmpeg_latest_version,
                'download_url': ffmpeg_download_url,
                'release_notes': ffmpeg_release_notes,
                'file_size': ffmpeg_file_size,
                'install_path': self.version_manager.ffmpeg_dir
            }
            
            # 发送信号
            self.check_completed.emit(result)
        except Exception as e:
            self.check_error.emit(str(e))


class VersionTab(QWidget):
    """版本标签页类"""
    
    # 状态图标和颜色定义
    STATUS_ICONS = {
        'latest': ('✓', '#28a745'),      # 绿色 - 已是最新
        'update': ('⬆', '#ffc107'),      # 黄色 - 有更新
        'not_installed': ('✗', '#dc3545'), # 红色 - 未安装
        'checking': ('⟳', '#6c757d'),    # 灰色 - 检查中
        'error': ('⚠', '#dc3545')        # 红色 - 错误
    }
    
    def __init__(self, status_bar: QStatusBar = None, auto_check: bool = True):
        """
        初始化版本标签页
        
        Args:
            status_bar: 状态栏
            auto_check: 是否自动检查版本
        """
        super().__init__()
        
        # 初始化日志
        self.logger = LoggerManager().get_logger()
        self.status_bar = status_bar
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化版本管理器
        self.version_manager = VersionManager()
        
        # 更新状态
        self.is_updating_yt_dlp = False
        self.is_updating_ffmpeg = False
        self.yt_dlp_update_worker = None
        self.ffmpeg_update_worker = None
        self.version_check_thread = None
        
        # 版本信息
        self.yt_dlp_current_version = ""
        self.yt_dlp_latest_version = ""
        self.yt_dlp_download_url = ""
        self.ffmpeg_current_version = ""
        self.ffmpeg_latest_version = ""
        self.ffmpeg_download_url = ""
        
        # Release Notes
        self.yt_dlp_release_notes = ""
        self.ffmpeg_release_notes = ""
        
        # 初始化 UI
        self.init_ui()
        
        # 记录日志
        self.logger.info("版本标签页初始化完成")
        
        # 检查二进制文件是否存在
        if not self.version_manager.binaries_exist():
            self.logger.info("检测到缺少必要的二进制文件，开始初始化下载")
            self.init_binaries()
        elif auto_check:
            self.check_versions()
        
        # 获取当前脚本所在目录
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_path = os.path.join(base_dir, 'resources', 'icons', 'app_icon.ico')

        # 设置窗口图标
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
    
    def init_ui(self):
        """初始化 UI"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        
        # 创建上次检查时间标签
        self.last_check_label = QLabel()
        self.last_check_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        self._update_last_check_label()
        main_layout.addWidget(self.last_check_label)
        
        # 创建 yt-dlp 版本信息区域
        yt_dlp_group = self._create_component_group(
            "yt-dlp",
            "YouTube 视频下载核心组件"
        )
        main_layout.addWidget(yt_dlp_group)
        
        # 创建 ffmpeg 版本信息区域
        ffmpeg_group = self._create_ffmpeg_group()
        main_layout.addWidget(ffmpeg_group)
        
        # 创建 Release Notes 区域
        notes_group = self._create_release_notes_group()
        main_layout.addWidget(notes_group)
        
        # 添加检查更新按钮
        check_layout = QHBoxLayout()
        check_layout.addStretch()
        
        self.check_updates_button = QPushButton("🔄 检查更新")
        self.check_updates_button.setMinimumWidth(120)
        self.check_updates_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.check_updates_button.clicked.connect(self.check_versions)
        check_layout.addWidget(self.check_updates_button)
        
        main_layout.addLayout(check_layout)
        
        # 添加弹性空间
        main_layout.addStretch()
    
    def _create_component_group(self, name: str, description: str) -> QGroupBox:
        """创建组件版本信息组"""
        group = QGroupBox(f"{name} 版本信息")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 15, 12, 12)
        layout.setSpacing(8)
        
        # 描述标签
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #6c757d; font-size: 11px; font-weight: normal;")
        layout.addWidget(desc_label)
        
        # 版本信息网格
        info_grid = QGridLayout()
        info_grid.setSpacing(8)
        
        # 状态图标
        status_icon_label = QLabel("⟳")
        status_icon_label.setStyleSheet("font-size: 24px; color: #6c757d;")
        status_icon_label.setFixedWidth(40)
        status_icon_label.setAlignment(Qt.AlignCenter)
        info_grid.addWidget(status_icon_label, 0, 0, 3, 1)
        
        # 当前版本
        info_grid.addWidget(QLabel("当前版本:"), 0, 1)
        current_version_label = QLabel("检查中...")
        current_version_label.setStyleSheet("font-weight: bold;")
        info_grid.addWidget(current_version_label, 0, 2)
        
        # 最新版本
        info_grid.addWidget(QLabel("最新版本:"), 1, 1)
        latest_version_label = QLabel("检查中...")
        info_grid.addWidget(latest_version_label, 1, 2)
        
        # 文件大小
        info_grid.addWidget(QLabel("文件大小:"), 2, 1)
        file_size_label = QLabel("--")
        file_size_label.setStyleSheet("color: #6c757d;")
        info_grid.addWidget(file_size_label, 2, 2)
        
        # 安装路径
        info_grid.addWidget(QLabel("安装路径:"), 3, 1)
        install_path_label = QLabel("--")
        install_path_label.setStyleSheet("color: #6c757d; font-size: 10px;")
        install_path_label.setWordWrap(True)
        info_grid.addWidget(install_path_label, 3, 2)
        
        info_grid.setColumnStretch(2, 1)
        layout.addLayout(info_grid)
        
        # 进度条和按钮
        progress_layout = QHBoxLayout()
        
        update_button = QPushButton("更新")
        update_button.setMinimumWidth(80)
        update_button.setEnabled(False)
        update_button.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        progress_layout.addWidget(update_button)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(progress_bar)
        
        layout.addLayout(progress_layout)
        
        # 状态标签
        status_label = QLabel("")
        status_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        layout.addWidget(status_label)
        
        # 保存 yt-dlp 的控件引用
        self.yt_dlp_status_icon = status_icon_label
        self.yt_dlp_current_version_label = current_version_label
        self.yt_dlp_latest_version_label = latest_version_label
        self.yt_dlp_file_size_label = file_size_label
        self.yt_dlp_install_path_label = install_path_label
        self.yt_dlp_update_button = update_button
        self.yt_dlp_progress_bar = progress_bar
        self.yt_dlp_status_label = status_label
        
        # 连接按钮事件
        update_button.clicked.connect(self.update_yt_dlp)
        
        return group
    
    def _create_ffmpeg_group(self) -> QGroupBox:
        """创建 ffmpeg 组件版本信息组"""
        group = QGroupBox("ffmpeg 版本信息")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 15, 12, 12)
        layout.setSpacing(8)
        
        # 描述标签
        desc_label = QLabel("音视频处理和格式转换组件")
        desc_label.setStyleSheet("color: #6c757d; font-size: 11px; font-weight: normal;")
        layout.addWidget(desc_label)
        
        # 版本信息网格
        info_grid = QGridLayout()
        info_grid.setSpacing(8)
        
        # 状态图标
        self.ffmpeg_status_icon = QLabel("⟳")
        self.ffmpeg_status_icon.setStyleSheet("font-size: 24px; color: #6c757d;")
        self.ffmpeg_status_icon.setFixedWidth(40)
        self.ffmpeg_status_icon.setAlignment(Qt.AlignCenter)
        info_grid.addWidget(self.ffmpeg_status_icon, 0, 0, 3, 1)
        
        # 当前版本
        info_grid.addWidget(QLabel("当前版本:"), 0, 1)
        self.ffmpeg_current_version_label = QLabel("检查中...")
        self.ffmpeg_current_version_label.setStyleSheet("font-weight: bold;")
        info_grid.addWidget(self.ffmpeg_current_version_label, 0, 2)
        
        # 最新版本
        info_grid.addWidget(QLabel("最新版本:"), 1, 1)
        self.ffmpeg_latest_version_label = QLabel("检查中...")
        info_grid.addWidget(self.ffmpeg_latest_version_label, 1, 2)
        
        # 文件大小
        info_grid.addWidget(QLabel("文件大小:"), 2, 1)
        self.ffmpeg_file_size_label = QLabel("--")
        self.ffmpeg_file_size_label.setStyleSheet("color: #6c757d;")
        info_grid.addWidget(self.ffmpeg_file_size_label, 2, 2)
        
        # 安装路径
        info_grid.addWidget(QLabel("安装路径:"), 3, 1)
        self.ffmpeg_install_path_label = QLabel("--")
        self.ffmpeg_install_path_label.setStyleSheet("color: #6c757d; font-size: 10px;")
        self.ffmpeg_install_path_label.setWordWrap(True)
        info_grid.addWidget(self.ffmpeg_install_path_label, 3, 2)
        
        info_grid.setColumnStretch(2, 1)
        layout.addLayout(info_grid)
        
        # 进度条和按钮
        progress_layout = QHBoxLayout()
        
        self.ffmpeg_update_button = QPushButton("更新")
        self.ffmpeg_update_button.setMinimumWidth(80)
        self.ffmpeg_update_button.setEnabled(False)
        self.ffmpeg_update_button.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.ffmpeg_update_button.clicked.connect(self.update_ffmpeg)
        progress_layout.addWidget(self.ffmpeg_update_button)
        
        self.ffmpeg_progress_bar = QProgressBar()
        self.ffmpeg_progress_bar.setRange(0, 100)
        self.ffmpeg_progress_bar.setValue(0)
        self.ffmpeg_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.ffmpeg_progress_bar)
        
        layout.addLayout(progress_layout)
        
        # 状态标签
        self.ffmpeg_status_label = QLabel("")
        self.ffmpeg_status_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        layout.addWidget(self.ffmpeg_status_label)
        
        return group
    
    def _create_release_notes_group(self) -> QGroupBox:
        """创建 Release Notes 展示区域"""
        group = QGroupBox("📋 更新日志")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 15, 12, 12)
        layout.setSpacing(8)
        
        # 选择标签页的按钮
        tab_layout = QHBoxLayout()
        
        self.yt_dlp_notes_btn = QPushButton("yt-dlp")
        self.yt_dlp_notes_btn.setCheckable(True)
        self.yt_dlp_notes_btn.setChecked(True)
        self.yt_dlp_notes_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 12px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: #007bff;
                color: white;
            }
            QPushButton:!checked {
                background-color: white;
                color: #495057;
            }
            QPushButton:hover:!checked {
                background-color: #e9ecef;
            }
        """)
        self.yt_dlp_notes_btn.clicked.connect(lambda: self._switch_release_notes('yt_dlp'))
        tab_layout.addWidget(self.yt_dlp_notes_btn)
        
        self.ffmpeg_notes_btn = QPushButton("ffmpeg")
        self.ffmpeg_notes_btn.setCheckable(True)
        self.ffmpeg_notes_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 12px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
                color: #495057;
            }
            QPushButton:checked {
                background-color: #007bff;
                color: white;
            }
            QPushButton:hover:!checked {
                background-color: #e9ecef;
            }
        """)
        self.ffmpeg_notes_btn.clicked.connect(lambda: self._switch_release_notes('ffmpeg'))
        tab_layout.addWidget(self.ffmpeg_notes_btn)
        
        tab_layout.addStretch()
        layout.addLayout(tab_layout)
        
        # Release Notes 文本框
        self.release_notes_text = QTextEdit()
        self.release_notes_text.setReadOnly(True)
        self.release_notes_text.setMaximumHeight(150)
        self.release_notes_text.setPlaceholderText("点击「检查更新」获取最新的更新日志...")
        self.release_notes_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                background-color: #f8f9fa;
                font-size: 11px;
                font-family: Consolas, Monaco, monospace;
            }
        """)
        layout.addWidget(self.release_notes_text)
        
        return group
    
    def _switch_release_notes(self, component: str):
        """切换 Release Notes 显示"""
        if component == 'yt_dlp':
            self.yt_dlp_notes_btn.setChecked(True)
            self.ffmpeg_notes_btn.setChecked(False)
            self.release_notes_text.setText(self.yt_dlp_release_notes or "暂无更新日志")
        else:
            self.yt_dlp_notes_btn.setChecked(False)
            self.ffmpeg_notes_btn.setChecked(True)
            self.release_notes_text.setText(self.ffmpeg_release_notes or "暂无更新日志")
        
        # 更新按钮样式
        self._update_notes_button_style()
    
    def _update_notes_button_style(self):
        """更新 notes 按钮样式"""
        checked_style = """
            QPushButton {
                padding: 4px 12px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: #007bff;
                color: white;
            }
        """
        unchecked_style = """
            QPushButton {
                padding: 4px 12px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
                color: #495057;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """
        
        if self.yt_dlp_notes_btn.isChecked():
            self.yt_dlp_notes_btn.setStyleSheet(checked_style)
            self.ffmpeg_notes_btn.setStyleSheet(unchecked_style)
        else:
            self.yt_dlp_notes_btn.setStyleSheet(unchecked_style)
            self.ffmpeg_notes_btn.setStyleSheet(checked_style)
    
    def _update_status_icon(self, icon_label: QLabel, status: str):
        """更新状态图标"""
        icon, color = self.STATUS_ICONS.get(status, ('?', '#6c757d'))
        icon_label.setText(icon)
        icon_label.setStyleSheet(f"font-size: 24px; color: {color};")
    
    def _update_last_check_label(self):
        """更新上次检查时间标签"""
        last_check = self.config_manager.get('last_version_check', 0)
        if last_check > 0:
            check_time = datetime.fromtimestamp(last_check)
            time_str = check_time.strftime("%Y-%m-%d %H:%M:%S")
            self.last_check_label.setText(f"⏱ 上次检查时间: {time_str}")
        else:
            self.last_check_label.setText("⏱ 上次检查时间: 从未检查")
    
    def _save_check_time(self):
        """保存检查时间"""
        self.config_manager.set('last_version_check', int(time.time()))
        self.config_manager.save_config()
        self._update_last_check_label()
    
    def update_status_message(self, message):
        """更新状态栏消息"""
        if self.status_bar:
            # 使用 QTimer.singleShot 确保在主线程中更新 UI
            QTimer.singleShot(0, lambda: self.status_bar.showMessage(message))
    
    def check_versions(self):
        """检查版本"""
        # 如果已经在检查中，直接返回
        if hasattr(self, 'version_check_thread') and self.version_check_thread and self.version_check_thread.isRunning():
            return
            
        # 禁用检查更新按钮
        self.check_updates_button.setEnabled(False)
        
        # 更新状态图标为检查中
        self._update_status_icon(self.yt_dlp_status_icon, 'checking')
        self._update_status_icon(self.ffmpeg_status_icon, 'checking')
        
        # 更新状态
        self.yt_dlp_status_label.setText("⟳ 正在检查...")
        self.ffmpeg_status_label.setText("⟳ 正在检查...")
        self.yt_dlp_current_version_label.setText("检查中...")
        self.ffmpeg_current_version_label.setText("检查中...")
        self.yt_dlp_latest_version_label.setText("检查中...")
        self.ffmpeg_latest_version_label.setText("检查中...")
        
        # 更新状态栏
        self.update_status_message("正在检查版本信息...")
        
        # 创建并启动版本检查线程
        self.version_check_thread = VersionCheckThread(self.version_manager)
        self.version_check_thread.check_completed.connect(self.on_version_check_completed)
        self.version_check_thread.check_error.connect(self.on_version_check_error)
        self.version_check_thread.progress_updated.connect(self.update_status_message)
        self.version_check_thread.start()
    
    def on_version_check_completed(self, result: dict):
        """版本检查完成回调"""
        # 保存检查时间
        self._save_check_time()
        
        # 获取 yt-dlp 信息
        yt_dlp_info = result.get('yt_dlp', {})
        yt_dlp_success = yt_dlp_info.get('success', False)
        yt_dlp_current_version = yt_dlp_info.get('current_version', '')
        yt_dlp_has_update = yt_dlp_info.get('has_update', False)
        yt_dlp_latest_version = yt_dlp_info.get('latest_version', '')
        yt_dlp_download_url = yt_dlp_info.get('download_url', '')
        yt_dlp_release_notes = yt_dlp_info.get('release_notes', '')
        yt_dlp_file_size = yt_dlp_info.get('file_size', '--')
        yt_dlp_install_path = yt_dlp_info.get('install_path', '--')
        
        # 更新 yt-dlp 版本信息
        if yt_dlp_success:
            self.yt_dlp_current_version = yt_dlp_current_version
            self.yt_dlp_current_version_label.setText(yt_dlp_current_version)
        else:
            self.yt_dlp_current_version_label.setText("未安装")
        
        if yt_dlp_latest_version:
            self.yt_dlp_latest_version = yt_dlp_latest_version
            self.yt_dlp_latest_version_label.setText(yt_dlp_latest_version)
        else:
            self.yt_dlp_latest_version_label.setText("无法获取")
        
        # 更新 yt-dlp 附加信息
        self.yt_dlp_file_size_label.setText(yt_dlp_file_size)
        self.yt_dlp_install_path_label.setText(yt_dlp_install_path)
        self.yt_dlp_release_notes = yt_dlp_release_notes
        
        # 保存下载链接
        self.yt_dlp_download_url = yt_dlp_download_url
        
        # 判断yt-dlp按钮状态和图标
        if not yt_dlp_success:
            self.yt_dlp_update_button.setText("下载")
            self.yt_dlp_update_button.setEnabled(True)
            self.yt_dlp_status_label.setText("❌ 未安装，需下载")
            self._update_status_icon(self.yt_dlp_status_icon, 'not_installed')
        elif yt_dlp_has_update and yt_dlp_download_url:
            self.yt_dlp_update_button.setText("更新")
            self.yt_dlp_update_button.setEnabled(True)
            self.yt_dlp_status_label.setText("⬆ 有新版本可用")
            self._update_status_icon(self.yt_dlp_status_icon, 'update')
        else:
            self.yt_dlp_update_button.setText("更新")
            self.yt_dlp_update_button.setEnabled(False)
            self.yt_dlp_status_label.setText("✓ 已是最新版本")
            self._update_status_icon(self.yt_dlp_status_icon, 'latest')
        
        # 获取 ffmpeg 信息
        ffmpeg_info = result.get('ffmpeg', {})
        ffmpeg_success = ffmpeg_info.get('success', False)
        ffmpeg_current_version = ffmpeg_info.get('current_version', '')
        ffmpeg_has_update = ffmpeg_info.get('has_update', False)
        ffmpeg_latest_version = ffmpeg_info.get('latest_version', '')
        ffmpeg_download_url = ffmpeg_info.get('download_url', '')
        ffmpeg_release_notes = ffmpeg_info.get('release_notes', '')
        ffmpeg_file_size = ffmpeg_info.get('file_size', '--')
        ffmpeg_install_path = ffmpeg_info.get('install_path', '--')
        
        # 更新 ffmpeg 版本信息
        if ffmpeg_success:
            self.ffmpeg_current_version = ffmpeg_current_version
            self.ffmpeg_current_version_label.setText(ffmpeg_current_version)
        else:
            self.ffmpeg_current_version_label.setText("未安装")
        
        if ffmpeg_latest_version:
            self.ffmpeg_latest_version = ffmpeg_latest_version
            self.ffmpeg_latest_version_label.setText(ffmpeg_latest_version)
        else:
            self.ffmpeg_latest_version_label.setText("无法获取")
        
        # 更新 ffmpeg 附加信息
        self.ffmpeg_file_size_label.setText(ffmpeg_file_size)
        self.ffmpeg_install_path_label.setText(ffmpeg_install_path)
        self.ffmpeg_release_notes = ffmpeg_release_notes
        
        # 保存下载链接
        self.ffmpeg_download_url = ffmpeg_download_url
        
        # 判断ffmpeg按钮状态和图标
        if not ffmpeg_success:
            self.ffmpeg_update_button.setText("下载")
            self.ffmpeg_update_button.setEnabled(True)
            self.ffmpeg_status_label.setText("❌ 未安装，需下载")
            self._update_status_icon(self.ffmpeg_status_icon, 'not_installed')
        elif ffmpeg_has_update and ffmpeg_download_url:
            self.ffmpeg_update_button.setText("更新")
            self.ffmpeg_update_button.setEnabled(True)
            self.ffmpeg_status_label.setText("⬆ 有新版本可用")
            self._update_status_icon(self.ffmpeg_status_icon, 'update')
        else:
            self.ffmpeg_update_button.setText("更新")
            self.ffmpeg_update_button.setEnabled(False)
            self.ffmpeg_status_label.setText("✓ 已是最新版本")
            self._update_status_icon(self.ffmpeg_status_icon, 'latest')
        
        # 更新 Release Notes 显示
        if self.yt_dlp_notes_btn.isChecked():
            self.release_notes_text.setText(self.yt_dlp_release_notes or "暂无更新日志")
        else:
            self.release_notes_text.setText(self.ffmpeg_release_notes or "暂无更新日志")
        
        # 启用检查更新按钮
        self.check_updates_button.setEnabled(True)
        
        # 更新状态栏
        self.update_status_message("版本检查完成")
    
    def on_version_check_error(self, error_message):
        """版本检查错误回调"""
        QMessageBox.critical(self, "错误", f"检查版本时发生错误: {error_message}")
        
        # 更新状态标签和图标
        self.yt_dlp_status_label.setText("⚠ 检查失败")
        self.ffmpeg_status_label.setText("⚠ 检查失败")
        self.yt_dlp_current_version_label.setText("检查失败")
        self.ffmpeg_current_version_label.setText("检查失败")
        self._update_status_icon(self.yt_dlp_status_icon, 'error')
        self._update_status_icon(self.ffmpeg_status_icon, 'error')
        
        self.check_updates_button.setEnabled(True)
        
        # 更新状态栏
        self.update_status_message(f"版本检查失败: {error_message}")
        
        # 记录日志
        self.logger.error(f"检查版本时发生错误: {error_message}")
    
    def update_yt_dlp(self):
        """更新/下载 yt-dlp"""
        # 检查是否已在更新
        if self.is_updating_yt_dlp:
            return
        
        # 检查下载 URL
        if not self.yt_dlp_download_url:
            QMessageBox.warning(self, "错误", "无法获取 yt-dlp 下载链接")
            return
        
        # 判断是下载还是更新
        is_download = not self.yt_dlp_current_version or self.yt_dlp_current_version == "未安装"
        
        # 确认对话框
        if is_download:
            title = "确认下载"
            message = f"确定要下载 yt-dlp {self.yt_dlp_latest_version} 吗？"
        else:
            title = "确认更新"
            message = f"确定要将 yt-dlp 从 {self.yt_dlp_current_version} 更新到 {self.yt_dlp_latest_version} 吗？"
        
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 更新 UI
        self.is_updating_yt_dlp = True
        self.yt_dlp_update_button.setEnabled(False)
        self.yt_dlp_progress_bar.setValue(0)
        action_text = "下载" if is_download else "更新"
        self.yt_dlp_status_label.setText(f"⬇ 正在{action_text}...")
        
        # 更新状态栏
        self.update_status_message("正在更新 yt-dlp...")
        
        # 创建并启动更新工作线程
        self.yt_dlp_update_worker = UpdateWorker(
            version_manager=self.version_manager,
            update_type='yt-dlp',
            download_url=self.yt_dlp_download_url
        )
        
        # 连接信号
        self.yt_dlp_update_worker.progress_updated.connect(self.update_yt_dlp_progress)
        self.yt_dlp_update_worker.update_completed.connect(self.yt_dlp_update_completed)
        
        # 启动工作线程
        self.yt_dlp_update_worker.start()
    
    def update_yt_dlp_progress(self, progress, status):
        """更新 yt-dlp 进度"""
        self.yt_dlp_progress_bar.setValue(progress)
        self.yt_dlp_status_label.setText(status)
        
        # 更新状态栏
        self.update_status_message(f"更新 yt-dlp: {progress}% - {status}")
    
    def yt_dlp_update_completed(self, success, result):
        """yt-dlp 更新完成"""
        # 更新 UI
        self.is_updating_yt_dlp = False
        
        if success:
            # 更新版本信息
            self.yt_dlp_current_version = result
            self.yt_dlp_current_version_label.setText(result)
            self.yt_dlp_update_button.setEnabled(False)
            self.yt_dlp_status_label.setText("✓ 更新成功")
            self._update_status_icon(self.yt_dlp_status_icon, 'latest')
            
            # 更新文件大小
            self.yt_dlp_file_size_label.setText(self.version_manager.get_yt_dlp_file_size())
            
            # 显示成功消息
            QMessageBox.information(self, "更新成功", f"yt-dlp 已成功更新到版本 {result}")
            
            # 更新状态栏
            self.update_status_message(f"yt-dlp 更新成功: 版本 {result}")
        else:
            # 启用更新按钮
            self.yt_dlp_update_button.setEnabled(True)
            self.yt_dlp_status_label.setText(f"⚠ 更新失败: {result}")
            self._update_status_icon(self.yt_dlp_status_icon, 'error')
            
            # 显示错误消息
            QMessageBox.critical(self, "更新失败", f"yt-dlp 更新失败: {result}")
            
            # 更新状态栏
            self.update_status_message(f"yt-dlp 更新失败: {result}")
    
    def update_ffmpeg(self):
        """更新/下载 ffmpeg"""
        # 检查是否已在更新
        if self.is_updating_ffmpeg:
            return
        
        # 检查下载 URL
        if not self.ffmpeg_download_url:
            QMessageBox.warning(self, "错误", "无法获取 ffmpeg 下载链接")
            return
        
        # 判断是下载还是更新
        is_download = not self.ffmpeg_current_version or self.ffmpeg_current_version == "未安装"
        
        # 确认对话框
        if is_download:
            title = "确认下载"
            message = f"确定要下载 ffmpeg {self.ffmpeg_latest_version} 吗？\n\n注意：下载可能需要几分钟时间。"
        else:
            title = "确认更新"
            message = f"确定要将 ffmpeg 从 {self.ffmpeg_current_version} 更新到 {self.ffmpeg_latest_version} 吗？\n\n注意：更新可能需要几分钟时间。"
        
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 更新 UI
        self.is_updating_ffmpeg = True
        self.ffmpeg_update_button.setEnabled(False)
        self.ffmpeg_progress_bar.setValue(0)
        action_text = "下载" if is_download else "更新"
        self.ffmpeg_status_label.setText(f"⬇ 正在{action_text}...")
        
        # 更新状态栏
        self.update_status_message(f"正在{action_text} ffmpeg...")
        
        # 创建并启动更新工作线程
        self.ffmpeg_update_worker = UpdateWorker(
            version_manager=self.version_manager,
            update_type='ffmpeg',
            download_url=self.ffmpeg_download_url
        )
        
        # 连接信号
        self.ffmpeg_update_worker.progress_updated.connect(self.update_ffmpeg_progress)
        self.ffmpeg_update_worker.update_completed.connect(self.ffmpeg_update_completed)
        
        # 启动工作线程
        self.ffmpeg_update_worker.start()
    
    def update_ffmpeg_progress(self, progress, status):
        """更新 ffmpeg 进度"""
        self.ffmpeg_progress_bar.setValue(progress)
        self.ffmpeg_status_label.setText(status)
        
        # 更新状态栏
        self.update_status_message(f"更新 ffmpeg: {progress}% - {status}")
    
    def ffmpeg_update_completed(self, success, result):
        """ffmpeg 更新完成"""
        # 更新 UI
        self.is_updating_ffmpeg = False
        
        if success:
            # 更新版本信息
            self.ffmpeg_current_version = result
            self.ffmpeg_current_version_label.setText(result)
            self.ffmpeg_update_button.setEnabled(False)
            self.ffmpeg_status_label.setText("✓ 更新成功")
            self._update_status_icon(self.ffmpeg_status_icon, 'latest')
            
            # 更新文件大小
            self.ffmpeg_file_size_label.setText(self.version_manager.get_ffmpeg_total_size())
            
            # 显示成功消息
            QMessageBox.information(self, "更新成功", f"ffmpeg 已成功更新到版本 {result}")
            
            # 更新状态栏
            self.update_status_message(f"ffmpeg 更新成功: 版本 {result}")
        else:
            # 启用更新按钮
            self.ffmpeg_update_button.setEnabled(True)
            self.ffmpeg_status_label.setText(f"⚠ 更新失败: {result}")
            self._update_status_icon(self.ffmpeg_status_icon, 'error')
            
            # 显示错误消息
            QMessageBox.critical(self, "更新失败", f"ffmpeg 更新失败: {result}")
            
            # 更新状态栏
            self.update_status_message(f"ffmpeg 更新失败: {result}")

    def init_binaries(self):
        """初始化下载必要的二进制文件"""
        # 更新状态图标
        self._update_status_icon(self.yt_dlp_status_icon, 'checking')
        self._update_status_icon(self.ffmpeg_status_icon, 'checking')
        
        # 更新状态
        self.yt_dlp_status_label.setText("⬇ 正在初始化下载...")
        self.ffmpeg_status_label.setText("⬇ 正在初始化下载...")
        
        # 更新状态栏
        self.update_status_message("正在初始化下载必要的文件...")
        
        # 创建并启动初始化下载线程
        self.init_worker = UpdateWorker(
            version_manager=self.version_manager,
            update_type='init',
            download_url=None
        )
        
        # 连接信号
        self.init_worker.progress_updated.connect(self.update_init_progress)
        self.init_worker.update_completed.connect(self.init_completed)
        
        # 启动工作线程
        self.init_worker.start()
    
    def update_init_progress(self, progress, status):
        """更新初始化进度"""
        self.yt_dlp_progress_bar.setValue(progress)
        self.ffmpeg_progress_bar.setValue(progress)
        self.yt_dlp_status_label.setText(f"⬇ {status}")
        self.ffmpeg_status_label.setText(f"⬇ {status}")
        
        # 更新状态栏
        self.update_status_message(f"初始化下载: {progress}% - {status}")
    
    def init_completed(self, success, result):
        """初始化完成"""
        if success:
            # 更新状态
            self.yt_dlp_status_label.setText("✓ 初始化完成")
            self.ffmpeg_status_label.setText("✓ 初始化完成")
            self._update_status_icon(self.yt_dlp_status_icon, 'latest')
            self._update_status_icon(self.ffmpeg_status_icon, 'latest')
            
            # 更新状态栏
            self.update_status_message("初始化下载完成")
            
            # 检查版本
            self.check_versions()
        else:
            # 更新状态
            self.yt_dlp_status_label.setText(f"⚠ 初始化失败: {result}")
            self.ffmpeg_status_label.setText(f"⚠ 初始化失败: {result}")
            self._update_status_icon(self.yt_dlp_status_icon, 'error')
            self._update_status_icon(self.ffmpeg_status_icon, 'error')
            
            # 更新状态栏
            self.update_status_message(f"初始化下载失败: {result}")
            
            # 显示错误消息
            QMessageBox.critical(self, "初始化失败", f"无法下载必要的文件: {result}\n请检查网络连接后重试。")
