"""
youtobe_bd 多视频下载标签页模块
支持批量URL输入、播放列表解析和队列管理
"""
import os
import re
import threading
from typing import Optional, List, Dict, Tuple
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit,
    QProgressBar, QFileDialog, QComboBox, QMessageBox, QGroupBox,
    QApplication, QStatusBar, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMenu, QAction, QSplitter, QDialog, QFrame,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QColor, QBrush
from PyQt5.QtWidgets import QStyle

from src.core.downloader import VideoDownloader, EnhancedDownloader
from src.core.download_queue import DownloadQueue, QueuedTask, download_queue
from src.core.cookie_manager import CookieManager
from src.core.event_bus import event_bus, Events
from src.core.video_info.video_info_parser import VideoInfoParser
from src.utils.config import ConfigManager
from src.utils.logger import LoggerManager
from src.utils.error_messages import ErrorMessages
from src.types import DownloadStatus, DownloadOptions, DownloadPriority


class BatchVideoInfoThread(QThread):
    """批量视频信息获取线程"""
    
    # 信号定义
    video_info_retrieved = pyqtSignal(str, dict)   # URL, 视频信息
    video_info_error = pyqtSignal(str, str)        # URL, 错误信息
    all_completed = pyqtSignal()                    # 全部完成
    progress_updated = pyqtSignal(int, int, str)   # 当前, 总数, 状态
    playlist_expanded = pyqtSignal(str, int)       # 播放列表URL, 视频数量
    paused_changed = pyqtSignal(bool)              # 暂停状态变化
    
    def __init__(self, urls: List[str], video_info_parser: VideoInfoParser, 
                 use_cookies: bool = False, cookies_file: str = None, proxy_url: str = None):
        super().__init__()
        self.urls = urls
        self.video_info_parser = video_info_parser
        self.use_cookies = use_cookies
        self.cookies_file = cookies_file
        self.proxy_url = proxy_url
        self.is_cancelled = False
        self.is_paused = False
        self._pause_lock = threading.Event()
        self._pause_lock.set()  # 初始为非暂停状态
        self.logger = LoggerManager().get_logger()
    
    def run(self):
        """执行批量视频信息获取"""
        # ── 阶段一：展开播放列表/频道，失败时静默回退到单视频处理 ──
        expanded_urls = []

        for url in self.urls:
            if self.is_cancelled:
                break
            self._wait_if_paused()
            if self.is_cancelled:
                break

            is_playlist = self.video_info_parser.is_playlist_url(url)
            is_channel  = self.video_info_parser.is_channel_url(url)

            if is_playlist or is_channel:
                label = "播放列表" if is_playlist else "频道"
                self.progress_updated.emit(0, 0, f"正在展开{label}: {url[:50]}...")
                expand_fn = (self.video_info_parser.get_playlist_videos if is_playlist
                             else self.video_info_parser.get_channel_videos)
                try:
                    videos = expand_fn(url, self.use_cookies, self.cookies_file, self.proxy_url)
                    if videos:
                        self.logger.info(f"{label}展开成功，共 {len(videos)} 个视频")
                        self.playlist_expanded.emit(url, len(videos))
                        for v in videos:
                            expanded_urls.append(v['url'])
                        continue
                except Exception as e:
                    self.logger.warning(f"{label}展开失败，将尝试作为单个视频处理: {url} - {e}")
                # 展开失败或结果为空 → 当做单个视频，由阶段二决定

            expanded_urls.append(url)

        # ── 去重 ──
        seen: set = set()
        parse_list: List[str] = []
        for url in expanded_urls:
            key = self._extract_video_id(url) or url
            if key not in seen:
                seen.add(key)
                parse_list.append(url)

        # ── 阶段二：解析每个 URL，带全回退链 ──
        #   单视频解析失败 → 尝试展开为频道/播放列表
        #   展开也失败 → 报错（两种途径均失败）
        self.logger.info(f"开始解析 {len(parse_list)} 个视频（动态队列）")
        idx = 0
        while idx < len(parse_list) and not self.is_cancelled:
            self._wait_if_paused()
            if self.is_cancelled:
                break

            url = parse_list[idx]
            idx += 1
            self.progress_updated.emit(idx, len(parse_list),
                                       f"正在解析 ({idx}/{len(parse_list)}): {url[:50]}...")

            # 尝试 1：单个视频解析
            single_error: Optional[Exception] = None
            try:
                video_info = self.video_info_parser.parse_video(
                    url,
                    use_cookies=self.use_cookies,
                    cookies_file=self.cookies_file,
                    proxy_url=self.proxy_url,
                )
                self.video_info_retrieved.emit(url, video_info)
                continue
            except Exception as e:
                single_error = e
                self.logger.warning(f"单视频解析失败，尝试展开: {url} - {e}")

            # 尝试 2：展开为频道或播放列表
            expand_success = False
            for expand_fn in [
                self.video_info_parser.get_channel_videos,
                self.video_info_parser.get_playlist_videos,
            ]:
                if self.is_cancelled:
                    break
                try:
                    videos = expand_fn(url, self.use_cookies, self.cookies_file, self.proxy_url)
                    if videos:
                        self.logger.info(f"回退展开成功，追加 {len(videos)} 个视频: {url}")
                        self.playlist_expanded.emit(url, len(videos))
                        for v in videos:
                            v_url = v['url']
                            key = self._extract_video_id(v_url) or v_url
                            if key not in seen:
                                seen.add(key)
                                parse_list.append(v_url)
                        expand_success = True
                        break
                except Exception as expand_err:
                    self.logger.warning(f"展开回退也失败: {url} - {expand_err}")

            if not expand_success:
                # 两种途径均失败，报告错误
                self.logger.error(f"解析完全失败: {url} - {single_error}")
                self.video_info_error.emit(url, str(single_error))

        self.all_completed.emit()
    
    def _wait_if_paused(self):
        """如果暂停则等待"""
        while self.is_paused and not self.is_cancelled:
            self._pause_lock.wait(0.5)  # 每0.5秒检查一次
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """从URL中提取视频ID"""
        import re
        patterns = [
            r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'(?:embed/|shorts/)([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def cancel(self):
        """取消解析"""
        self.is_cancelled = True
        self.is_paused = False
        self._pause_lock.set()  # 解除暂停状态以便线程能够退出
    
    def pause(self):
        """暂停解析"""
        if not self.is_paused:
            self.is_paused = True
            self._pause_lock.clear()
            self.paused_changed.emit(True)
            self.logger.info("解析已暂停")
    
    def resume(self):
        """恢复解析"""
        if self.is_paused:
            self.is_paused = False
            self._pause_lock.set()
            self.paused_changed.emit(False)
            self.logger.info("解析已恢复")


class MultiDownloadThread(QThread):
    """多视频下载线程"""
    
    # 信号定义
    task_progress = pyqtSignal(str, float, str, str)  # task_id, 进度, 速度, ETA
    task_completed = pyqtSignal(str)                   # task_id
    task_failed = pyqtSignal(str, str)                 # task_id, 错误信息
    
    def __init__(self, task: QueuedTask, downloader: VideoDownloader):
        super().__init__()
        self.task = task
        self.downloader = downloader
        self.is_cancelled = False
        self.logger = LoggerManager().get_logger()
    
    def run(self):
        """执行下载任务"""
        try:
            # 设置回调
            self.downloader.set_callbacks(
                progress_callback=self._on_progress,
                completion_callback=self._on_completion,
                error_callback=self._on_error
            )
            
            # 开始下载
            format_id = self.task.get_format_id()
            self.downloader.download_videos(
                urls=[self.task.url],
                output_dir=self.task.output_dir,
                format_id=format_id,
                use_cookies=self.task.use_cookies,
                cookies_file=self.task.cookies_file,
                prefer_mp4=self.task.prefer_mp4,
                no_playlist=self.task.no_playlist,
                overwrite=self.task.overwrite,
                proxy_url=self.task.proxy_url
            )
            
        except Exception as e:
            self.logger.error(f"下载任务失败: {self.task.id} - {str(e)}")
            self.task_failed.emit(self.task.id, str(e))
    
    def _on_progress(self, progress: float, speed: str, eta: str, 
                     title: str, video_index: int, total_videos: int):
        """进度回调"""
        self.task_progress.emit(self.task.id, progress, speed, eta)
    
    def _on_completion(self, success: bool, output_dir: str, error_message: str = None):
        """完成回调"""
        if success:
            self.task_completed.emit(self.task.id)
        else:
            self.task_failed.emit(self.task.id, error_message or "下载失败")
    
    def _on_error(self, error_message: str):
        """错误回调"""
        self.task_failed.emit(self.task.id, error_message)
    
    def cancel(self):
        """取消下载"""
        self.is_cancelled = True
        self.downloader.cancel_download()


class ParseErrorDialog(QDialog):
    """自定义解析错误展示框：支持选中、复制、滚动条、最大100条限制"""
    def __init__(self, errors: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("解析错误")
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        # 使文本只可读且可选
        self.text_edit.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        
        error_text = "以下链接解析失败：\n\n"
        max_errors = 100
        for i, (url, error_msg) in enumerate(errors[:max_errors], 1):
            error_text += f"{i}. {url}\n   错误: {error_msg}\n\n"
            
        if len(errors) > max_errors:
            error_text += f"... 还有 {len(errors) - max_errors} 个错误未显示\n"
            
        error_text += "提示：请检查链接是否有效，或尝试使用 Cookie。"
        self.text_edit.setPlainText(error_text)
        layout.addWidget(self.text_edit)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.copy_btn = QPushButton("复制到剪切板", self)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        btn_layout.addWidget(self.copy_btn)
        
        self.close_btn = QPushButton("关闭", self)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.text_edit.toPlainText())
        QMessageBox.information(self, "提示", "已复制到剪切板")


class MultiDownloadTab(QWidget):
    """多视频下载标签页"""
    
    def __init__(self, config_manager: ConfigManager = None, 
                 status_bar: QStatusBar = None, cookie_tab=None):
        super().__init__()
        
        # 初始化日志和配置
        self.logger = LoggerManager().get_logger()
        self.config_manager = config_manager or ConfigManager()
        self.status_bar = status_bar
        self.cookie_tab = cookie_tab
        
        # 初始化核心组件
        self.video_info_parser = VideoInfoParser()
        self.download_queue = download_queue
        
        # 任务管理
        self._tasks: Dict[str, QueuedTask] = {}
        self._download_threads: Dict[str, MultiDownloadThread] = {}
        self._task_rows: Dict[str, int] = {}  # task_id -> row index
        self._task_formats: Dict[str, List[Dict]] = {}  # task_id -> 可用格式列表
        self._task_video_info: Dict[str, Dict] = {}  # task_id -> 视频完整信息
        
        # 线程
        self.batch_info_thread: Optional[BatchVideoInfoThread] = None
        
        # 解析错误统计
        self._parse_errors: List[Tuple[str, str]] = []  # (url, error_message)
        
        # 最大并发下载数
        self.max_concurrent = 2
        
        # 初始化 UI
        self._init_ui()
        
        # 连接事件总线
        self._connect_events()
        
        # 设置定时器更新统计
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_statistics)
        self._update_timer.start(1000)  # 每秒更新
        
        self.logger.info("多视频下载标签页初始化完成")
    
    def _init_ui(self):
        """初始化 UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # ===== URL 输入区域 =====
        input_group = QGroupBox("视频链接")
        input_layout = QVBoxLayout(input_group)
        input_layout.setContentsMargins(8, 6, 8, 6)
        input_layout.setSpacing(6)
        
        # URL 输入框
        self.url_input = QTextEdit()
        self.url_input.setAcceptRichText(False)
        self.url_input.setPlaceholderText(
            "在此输入多个视频链接，每行一个（支持 YouTube、TikTok、Twitter、Instagram 等 1000+ 网站）\n"
            "支持：\n"
            "  • 单个视频链接\n"
            "  • 播放列表链接 例如：https://www.youtube.com/playlist?list=...\n"
            "  • 频道链接 例如：https://www.youtube.com/@EnglishwithLucy\n"
            "  • 批量粘贴多个链接\n"
            "注意：除视频链接外，频道链接和列表链接一次只能有一个。"
        )
        self.url_input.setMinimumHeight(100)
        self.url_input.setMaximumHeight(120)
        input_layout.addWidget(self.url_input)
        
        # 选项行
        options_layout = QHBoxLayout()
        
        self.use_cookie_checkbox = QCheckBox("使用 Cookie")
        self.use_cookie_checkbox.setToolTip("用于会员或年龄限制视频")
        options_layout.addWidget(self.use_cookie_checkbox)
        
        options_layout.addStretch()
        
        # 暂停解析按钮
        self.pause_parse_button = QPushButton("暂停解析")
        self.pause_parse_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.pause_parse_button.clicked.connect(self._on_pause_parse_clicked)
        self.pause_parse_button.setMinimumWidth(100)
        self.pause_parse_button.setVisible(False)  # 初始隐藏
        options_layout.addWidget(self.pause_parse_button)
        
        # 取消解析按钮
        self.cancel_parse_button = QPushButton("取消解析")
        self.cancel_parse_button.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        self.cancel_parse_button.clicked.connect(self._on_cancel_parse_clicked)
        self.cancel_parse_button.setMinimumWidth(100)
        self.cancel_parse_button.setVisible(False)  # 初始隐藏
        options_layout.addWidget(self.cancel_parse_button)
        
        # 解析按钮
        self.parse_button = QPushButton("解析链接")
        self.parse_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
        self.parse_button.clicked.connect(self._on_parse_clicked)
        self.parse_button.setMinimumWidth(100)
        options_layout.addWidget(self.parse_button)
        
        input_layout.addLayout(options_layout)
        main_layout.addWidget(input_group)
        
        # ===== 下载设置区域 =====
        settings_group = QGroupBox("下载设置")
        settings_layout = QHBoxLayout(settings_group)
        settings_layout.setContentsMargins(8, 6, 8, 6)
        settings_layout.setSpacing(6)
        
        # 下载目录
        settings_layout.addWidget(QLabel("下载目录:"))
        self.dir_input = QLineEdit()
        self.dir_input.setReadOnly(True)
        self.dir_input.setPlaceholderText("请选择下载目录")
        self.dir_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        settings_layout.addWidget(self.dir_input, 1)
        self.browse_button = QPushButton("浏览")
        self.browse_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.browse_button.clicked.connect(self._browse_download_dir)
        settings_layout.addWidget(self.browse_button)

        self.open_dir_button = QPushButton("打开目录")
        self.open_dir_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.open_dir_button.clicked.connect(self._open_download_dir)
        settings_layout.addWidget(self.open_dir_button)
        
        main_layout.addWidget(settings_group)
        
        # ===== 下载队列区域 =====
        queue_group = QGroupBox("下载队列")
        queue_layout = QVBoxLayout(queue_group)
        queue_layout.setContentsMargins(8, 6, 8, 12)
        queue_layout.setSpacing(6)
        
        # 第一行：队列信息 + 解析进度
        queue_top_layout = QHBoxLayout()
        self.queue_info_label = QLabel("队列: 0 个任务")
        queue_top_layout.addWidget(self.queue_info_label)
        self.parse_progress_label = QLabel()
        self.parse_progress_label.setStyleSheet("color: #888888;")
        self.parse_progress_label.setVisible(False)
        queue_top_layout.addWidget(self.parse_progress_label)
        queue_top_layout.addStretch()
        queue_layout.addLayout(queue_top_layout)

        # 第二行：质量选择（左） + 操作按钮（右）
        queue_buttons_layout = QHBoxLayout()

        queue_buttons_layout.addWidget(QLabel("视频质量:"))
        self.global_video_combo = QComboBox()
        self.global_video_combo.addItems([
            "最高画质", "4K", "2K", "1080p", "720p", "480p", "360p"
        ])
        self.global_video_combo.setCurrentIndex(4)  # 默认 720p
        # 对应高度映射: None, 2160, 1440, 1080, 720, 480, 360
        self._target_heights = [None, 2160, 1440, 1080, 720, 480, 360]
        self.global_video_combo.currentIndexChanged.connect(self._on_global_quality_changed)
        queue_buttons_layout.addWidget(self.global_video_combo)

        queue_buttons_layout.addSpacing(10)
        queue_buttons_layout.addWidget(QLabel("音频质量:"))
        self.global_audio_combo = QComboBox()
        self.global_audio_combo.addItems([
            "最佳质量", "第一档(最大)", "第二档(中等)", "最小(省流量)"
        ])
        self.global_audio_combo.currentIndexChanged.connect(self._on_global_quality_changed)
        queue_buttons_layout.addWidget(self.global_audio_combo)

        queue_buttons_layout.addStretch()

        self.start_all_button = QPushButton("全部开始")
        self.start_all_button.clicked.connect(self._start_all_tasks)
        self.start_all_button.setEnabled(False)
        queue_buttons_layout.addWidget(self.start_all_button)

        self.pause_all_button = QPushButton("全部暂停")
        self.pause_all_button.clicked.connect(self._pause_all_tasks)
        self.pause_all_button.setEnabled(False)
        queue_buttons_layout.addWidget(self.pause_all_button)

        self.clear_completed_button = QPushButton("清除已完成")
        self.clear_completed_button.clicked.connect(self._clear_completed_tasks)
        queue_buttons_layout.addWidget(self.clear_completed_button)

        self.clear_all_button = QPushButton("清空")
        self.clear_all_button.clicked.connect(self._clear_all_tasks)
        queue_buttons_layout.addWidget(self.clear_all_button)

        queue_layout.addLayout(queue_buttons_layout)
        
        # 任务表格
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(8)
        self.task_table.setHorizontalHeaderLabels([
            "标题", "视频质量", "音频质量", "状态", "进度", "速度", "剩余时间", "操作"
        ])
        
        # 设置表格属性
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.task_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(self._show_context_menu)
        
        # 设置列宽
        header = self.task_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 标题列自动拉伸
        header.setSectionResizeMode(1, QHeaderView.Fixed)    # 视频质量
        header.setSectionResizeMode(2, QHeaderView.Fixed)    # 音频质量
        header.setSectionResizeMode(3, QHeaderView.Fixed)    # 状态
        header.setSectionResizeMode(4, QHeaderView.Fixed)    # 进度
        header.setSectionResizeMode(5, QHeaderView.Fixed)    # 速度
        header.setSectionResizeMode(6, QHeaderView.Fixed)    # 剩余时间
        header.setSectionResizeMode(7, QHeaderView.Fixed)    # 操作
        
        self.task_table.setColumnWidth(1, 140)  # 视频质量
        self.task_table.setColumnWidth(2, 120)  # 音频质量
        self.task_table.setColumnWidth(3, 70)   # 状态
        self.task_table.setColumnWidth(4, 100)  # 进度
        self.task_table.setColumnWidth(5, 80)   # 速度
        self.task_table.setColumnWidth(6, 70)   # 剩余时间
        self.task_table.setColumnWidth(7, 80)   # 操作（增加宽度以显示图标）
        
        # 固定行高 32px，表头约 28px，显示 5 行 = 32*5+28 = 188，留余量设 220
        self.task_table.verticalHeader().setDefaultSectionSize(32)
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.setMinimumHeight(220)
        self.task_table.setFrameShape(QFrame.NoFrame)
        queue_layout.addWidget(self.task_table)
        
        main_layout.addWidget(queue_group, 1)  # 给队列区域更多空间
        
        # ===== 总体进度区域 =====
        progress_group = QGroupBox("总体进度")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setContentsMargins(8, 6, 8, 8)
        progress_layout.setSpacing(6)
        
        self.total_progress_bar = QProgressBar()
        self.total_progress_bar.setRange(0, 100)
        self.total_progress_bar.setValue(0)
        self.total_progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.total_progress_bar)
        
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("已完成: 0/0   下载中: 0   等待中: 0")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        self.speed_label = QLabel("总速度: 0 B/s")
        stats_layout.addWidget(self.speed_label)
        progress_layout.addLayout(stats_layout)
        
        main_layout.addWidget(progress_group)
        
        # 设置默认下载目录
        self._set_default_download_dir()
    
    def _connect_events(self):
        """连接事件总线"""
        event_bus.subscribe(Events.DOWNLOAD_PROGRESS, self._on_event_download_progress)
        event_bus.subscribe(Events.DOWNLOAD_COMPLETED, self._on_event_download_completed)
        event_bus.subscribe(Events.DOWNLOAD_FAILED, self._on_event_download_failed)
        event_bus.subscribe(Events.DOWNLOAD_CANCELLED, self._on_event_download_cancelled)
    
    def _validate_url(self, url: str) -> Tuple[bool, str]:
        """验证 URL"""
        if not re.match(r'https?://', url):
            return False, "无效的链接格式"
        return True, ""
    
    def _extract_urls(self, text: str) -> List[str]:
        """从文本中提取 URL"""
        lines = text.strip().splitlines()
        urls = []
        seen = set()
        
        for line in lines:
            url = line.strip()
            if url and url not in seen:
                if not url.startswith('http://') and not url.startswith('https://'):
                    url = 'https://' + url
                is_valid, _ = self._validate_url(url)
                if is_valid:
                    urls.append(url)
                    seen.add(url)
        
        return urls
    
    def _on_parse_clicked(self):
        """解析按钮点击"""
        text = self.url_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请输入视频链接")
            return
        
        urls = self._extract_urls(text)
        if not urls:
            QMessageBox.warning(self, "警告", "未找到有效的视频链接")
            return
        
        # 检查频道链接和列表链接数量限制
        collection_urls = 0
        for u in urls:
            if self.video_info_parser.is_playlist_url(u) or self.video_info_parser.is_channel_url(u):
                collection_urls += 1
        
        if collection_urls > 1:
            QMessageBox.warning(self, "警告", "除视频链接外，频道链接和列表链接一次只能有一个")
            return
        
        # 清空之前的错误
        self._parse_errors.clear()
        
        # 检查 Cookie
        use_cookies = self.use_cookie_checkbox.isChecked()
        cookies_file = None
        if use_cookies:
            if not self.cookie_tab or not self.cookie_tab.is_cookie_available():
                reply = QMessageBox.question(
                    self, "Cookie 未设置",
                    "您选择了使用 Cookie，但当前没有可用的 Cookie。\n是否继续（不使用 Cookie）？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
                use_cookies = False
                self.use_cookie_checkbox.setChecked(False)
            else:
                cookies_file = self.cookie_tab.get_cookie_file()
        
        # 禁用解析按钮，显示暂停和取消按钮
        self.parse_button.setEnabled(False)
        self.parse_button.setText("解析中...")
        self.pause_parse_button.setVisible(True)
        self.pause_parse_button.setText("暂停解析")
        self.pause_parse_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.cancel_parse_button.setVisible(True)
        
        # 获取代理设置
        proxy_url = self._get_proxy_url()
        
        # 启动批量解析线程
        self.batch_info_thread = BatchVideoInfoThread(
            urls, self.video_info_parser, use_cookies, cookies_file, proxy_url
        )
        self.batch_info_thread.video_info_retrieved.connect(self._on_video_info_retrieved)
        self.batch_info_thread.video_info_error.connect(self._on_video_info_error)
        self.batch_info_thread.all_completed.connect(self._on_all_parsed)
        self.batch_info_thread.progress_updated.connect(self._on_parse_progress)
        self.batch_info_thread.playlist_expanded.connect(self._on_playlist_expanded)
        self.batch_info_thread.paused_changed.connect(self._on_parse_paused_changed)
        self.batch_info_thread.start()
    
    def _on_pause_parse_clicked(self):
        """暂停/恢复解析按钮点击"""
        if not self.batch_info_thread:
            return
        
        if self.batch_info_thread.is_paused:
            # 恢复解析
            self.batch_info_thread.resume()
        else:
            # 暂停解析
            self.batch_info_thread.pause()
    
    def _on_cancel_parse_clicked(self):
        """取消解析按钮点击"""
        if not self.batch_info_thread:
            return
        
        reply = QMessageBox.question(
            self, "确认",
            "确定要取消解析吗？\n已解析的视频将保留在列表中。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.batch_info_thread.cancel()
            
            # 恢复解析按钮状态
            self.parse_button.setEnabled(True)
            self.parse_button.setText("解析链接")
            
            # 隐藏解析进度和暂停、取消按钮
            self.parse_progress_label.setVisible(False)
            self.pause_parse_button.setVisible(False)
            self.cancel_parse_button.setVisible(False)

            # 更新下载队列按钮状态
            self._update_button_states()

            if self.status_bar:
                self.status_bar.showMessage("解析已取消")
    
    def _on_parse_paused_changed(self, is_paused: bool):
        """解析暂停状态变化"""
        if is_paused:
            self.pause_parse_button.setText("继续解析")
            self.pause_parse_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            if self.status_bar:
                self.status_bar.showMessage("解析已暂停，点击「继续解析」恢复")
        else:
            self.pause_parse_button.setText("暂停解析")
            self.pause_parse_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
    
    def _on_video_info_retrieved(self, url: str, video_info: dict):
        """视频信息获取成功"""
        # 检查是否为直播
        if video_info.get('is_live'):
            self.logger.warning(f"跳过直播视频: {url}")
            return
        
        # 获取并格式化可用格式
        formats = self.video_info_parser.get_available_formats(video_info)
        formatted_formats = self.video_info_parser.get_formatted_formats(formats)
        
        # 检查是有可用格式，如果没有，标记为失败
        status = DownloadStatus.PENDING
        error_msg = ""
        if not formatted_formats:
            status = DownloadStatus.FAILED
            error_msg = "无可用格式（解析失败）"
            self.logger.warning(f"视频无可用格式: {url}")

        # 创建任务（默认使用最高质量）
        task = QueuedTask(
            priority=DownloadPriority.NORMAL.value,
            url=url,
            title=video_info.get('title', '未知标题'),
            output_dir=self.dir_input.text(),
            video_format_id="best",  # 默认最高画质
            audio_format_id="best",  # 默认最高音质
            use_cookies=self.use_cookie_checkbox.isChecked(),
            cookies_file=self.cookie_tab.get_cookie_file() if self.cookie_tab and self.cookie_tab.is_cookie_available() else None,
            prefer_mp4=True,
            no_playlist=True,
            status=status,
            error_message=error_msg,
            proxy_url=self._get_proxy_url()
        )
        
        # 添加到任务列表
        self._tasks[task.id] = task
        self._task_formats[task.id] = formatted_formats
        self._task_video_info[task.id] = video_info
        
        # Apply global quality on initialization
        target_height = self._target_heights[self.global_video_combo.currentIndex()]
        video_idx = self._find_best_video_format_index(formatted_formats, target_height)
        
        audio_tier = self.global_audio_combo.currentIndex()
        audio_idx = self._find_best_audio_format_index(formatted_formats, audio_tier)
        
        self._add_task_to_table(task, formatted_formats, video_idx, audio_idx)
        
        self.logger.info(f"添加任务: {task.title}")
    
    def _on_video_info_error(self, url: str, error_message: str):
        """视频信息获取失败"""
        self.logger.error(f"解析失败: {url} - {error_message}")
        # 记录错误 (暂时仍然在数组里记一下，以免其他逻辑需要)
        self._parse_errors.append((url, error_message))
        
        # 将解析失败的视频也添加到列表中，状态置为 FAILED，点击开始不会启动，自动跳过
        task = QueuedTask(
            priority=DownloadPriority.NORMAL.value,
            url=url,
            title=f"[解析失败] {url}",
            output_dir=self.dir_input.text(),
            video_format_id="",
            audio_format_id="",
            status=DownloadStatus.FAILED,
            error_message=ErrorMessages.get_user_message(error_message, include_suggestion=False),
            proxy_url=self._get_proxy_url()
        )
        
        self._tasks[task.id] = task
        self._task_formats[task.id] = []
        self._task_video_info[task.id] = {}
        
        self._add_task_to_table(task, [], 0, 0)
    
    def _on_parse_progress(self, current: int, total: int, status: str):
        """解析进度更新"""
        if total > 0:
            self.parse_progress_label.setText(f"| 解析中 {current}/{total}")
        else:
            self.parse_progress_label.setText("| 解析中...")
        self.parse_progress_label.setVisible(True)
        if self.status_bar:
            if total > 0:
                self.status_bar.showMessage(f"解析进度: {current}/{total} - {status}")
            else:
                self.status_bar.showMessage(status)
    
    def _on_playlist_expanded(self, playlist_url: str, video_count: int):
        """播放列表展开完成"""
        self.logger.info(f"播放列表展开: {playlist_url} -> {video_count} 个视频")
        if self.status_bar:
            self.status_bar.showMessage(f"播放列表已展开，共 {video_count} 个视频")
    
    def _on_all_parsed(self):
        """所有链接解析完成"""
        self.parse_button.setEnabled(True)
        self.parse_button.setText("解析链接")

        # 隐藏解析进度
        self.parse_progress_label.setVisible(False)

        # 隐藏暂停和取消按钮
        self.pause_parse_button.setVisible(False)
        self.cancel_parse_button.setVisible(False)
        
        # 显示解析结果
        total_tasks_count = len(self._tasks)
        parse_failed_count = sum(1 for t in self._tasks.values() if str(t.title).startswith("[解析失败]"))
        success_count = total_tasks_count - parse_failed_count
        error_count = len(self._parse_errors)
        
        if self.status_bar:
            if error_count > 0:
                self.status_bar.showMessage(
                    f"解析完成：本次失败 {error_count} 个，当前队列成功解析共 {success_count} 个"
                )
            else:
                self.status_bar.showMessage(f"解析完成，当前队列共 {success_count} 个任务")
        
        # 如果有错误，显示错误对话框
        if error_count > 0:
            self._show_parse_errors()
        
        # 清空错误列表
        self._parse_errors.clear()
        
        self._update_button_states()
    
    def _show_parse_errors(self):
        """显示解析错误信息"""
        if not self._parse_errors:
            return
            
        dialog = ParseErrorDialog(self._parse_errors, self)
        dialog.exec_()
    
    def _add_task_to_table(self, task: QueuedTask, formatted_formats: List[Dict] = None, initial_video_idx: int = 0, initial_audio_idx: int = 0):
        """添加任务到表格"""
        row = self.task_table.rowCount()
        self.task_table.insertRow(row)
        self._task_rows[task.id] = row
        
        # 列0: 标题
        title_item = QTableWidgetItem(task.title)
        title_item.setData(Qt.UserRole, task.id)  # 存储 task_id
        title_item.setToolTip(task.url)
        self.task_table.setItem(row, 0, title_item)
        
        # 列1: 视频质量下拉框
        video_combo = QComboBox()
        video_combo.setObjectName("tableCombo")
        video_combo.addItem("最高画质", "best")
        if formatted_formats:
            for fmt in formatted_formats:
                if fmt['type'] == 'video':
                    video_combo.addItem(fmt['display'], fmt['format_id'])
        video_combo.setProperty("task_id", task.id)
        if initial_video_idx < video_combo.count():
            video_combo.setCurrentIndex(initial_video_idx)
            task.video_format_id = video_combo.currentData()
            
        video_combo.currentIndexChanged.connect(
            lambda idx, tid=task.id: self._on_video_format_changed(tid)
        )
        self.task_table.setCellWidget(row, 1, video_combo)
        
        # 列2: 音频质量下拉框
        audio_combo = QComboBox()
        audio_combo.setObjectName("tableCombo")
        audio_combo.addItem("最高音质", "best")
        if formatted_formats:
            for fmt in formatted_formats:
                if fmt['type'] == 'audio':
                    audio_combo.addItem(fmt['display'], fmt['format_id'])
        audio_combo.setProperty("task_id", task.id)
        if initial_audio_idx < audio_combo.count():
            audio_combo.setCurrentIndex(initial_audio_idx)
            task.audio_format_id = audio_combo.currentData()
            
        audio_combo.currentIndexChanged.connect(
            lambda idx, tid=task.id: self._on_audio_format_changed(tid)
        )
        self.task_table.setCellWidget(row, 2, audio_combo)
        
        # 列3: 状态
        status_item = QTableWidgetItem(self._get_status_text(task.status))
        status_item.setTextAlignment(Qt.AlignCenter)
        self._set_status_color(status_item, task.status)
        self.task_table.setItem(row, 3, status_item)
        
        # 列4: 进度 - 使用进度条
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(int(task.progress))
        progress_bar.setTextVisible(True)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #F1F5F9;
                text-align: center;
                color: #475569;
                font-weight: 600;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #EF4444, stop:1 #DC2626);
                border-radius: 4px;
            }
        """)
        self.task_table.setCellWidget(row, 4, progress_bar)
        
        # 列5: 速度
        speed_item = QTableWidgetItem(task.speed or "-")
        speed_item.setTextAlignment(Qt.AlignCenter)
        self.task_table.setItem(row, 5, speed_item)
        
        # 列6: 剩余时间
        eta_item = QTableWidgetItem(task.eta or "-")
        eta_item.setTextAlignment(Qt.AlignCenter)
        self.task_table.setItem(row, 6, eta_item)
        
        # 列7: 操作按钮
        action_widget = self._create_action_buttons(task)
        self.task_table.setCellWidget(row, 7, action_widget)
        
        self._update_queue_info()
    
    def _on_video_format_changed(self, task_id: str):
        """视频格式选择改变"""
        if task_id not in self._tasks or task_id not in self._task_rows:
            return
        
        row = self._task_rows[task_id]
        video_combo = self.task_table.cellWidget(row, 1)
        if isinstance(video_combo, QComboBox):
            self._tasks[task_id].video_format_id = video_combo.currentData()
            self.logger.debug(f"任务 {task_id} 视频格式改为: {video_combo.currentData()}")
    
    def _on_audio_format_changed(self, task_id: str):
        """音频格式选择改变"""
        if task_id not in self._tasks or task_id not in self._task_rows:
            return
        
        row = self._task_rows[task_id]
        audio_combo = self.task_table.cellWidget(row, 2)
        if isinstance(audio_combo, QComboBox):
            self._tasks[task_id].audio_format_id = audio_combo.currentData()
            self.logger.debug(f"任务 {task_id} 音频格式改为: {audio_combo.currentData()}")
            
    def _find_best_video_format_index(self, formatted_formats: List[Dict], target_height: Optional[int]) -> int:
        """寻找最接近对应分辨率的视频格式索引"""
        if target_height is None or not formatted_formats:
            return 0  # 自动选择最佳
            
        min_diff = float('inf')
        best_video_index = 0
        video_index = 1  # 索引 0 是 "best"
        
        for fmt in formatted_formats:
            if fmt['type'] == 'video':
                resolution = fmt.get('resolution', '')
                if 'x' in resolution:
                    try:
                        height = int(resolution.split('x')[1])
                        diff = abs(height - target_height)
                        # 如果差异更小，或者差异相同但分辨率更大(更高画质)
                        if diff < min_diff:
                            min_diff = diff
                            best_video_index = video_index
                    except ValueError:
                        pass
                video_index += 1
                
        return best_video_index

    def _find_best_audio_format_index(self, formatted_formats: List[Dict], target_tier: int) -> int:
        """寻找最接近对应音频档位的格式索引
        target_tier: 0=自动选择最佳, 1=第一档(最大), 2=第二档, 3=最小
        """
        if target_tier == 0 or not formatted_formats:
            return 0
            
        audio_options = []
        audio_index = 1
        
        for fmt in formatted_formats:
            if fmt['type'] == 'audio':
                abr = fmt.get('abr', 0)
                if abr is None:
                    abr = 0
                audio_options.append({
                    'index': audio_index,
                    'abr': float(abr)
                })
                audio_index += 1
                
        if not audio_options:
            return 0
            
        # 根据码率降序排序（高音质在前面）
        audio_options.sort(key=lambda x: x['abr'], reverse=True)
        
        if target_tier == 1:
            # 第一档（最大）
            return audio_options[0]['index']
        elif target_tier == 2:
            # 第二档
            if len(audio_options) >= 2:
                return audio_options[1]['index']
            else:
                return audio_options[0]['index']
        elif target_tier == 3:
            # 最小
            return audio_options[-1]['index']
            
        return 0

    def _on_global_quality_changed(self):
        """全局质量设置改变时更新所有等待中和暂停中的任务"""
        target_height = self._target_heights[self.global_video_combo.currentIndex()]
        audio_tier = self.global_audio_combo.currentIndex()
        
        for task_id, task in self._tasks.items():
            if task.status in (DownloadStatus.PENDING, DownloadStatus.PAUSED, DownloadStatus.FAILED, DownloadStatus.CANCELLED):
                row = self._task_rows.get(task_id)
                if row is not None:
                    formatted_formats = self._task_formats.get(task_id, [])
                    video_idx = self._find_best_video_format_index(formatted_formats, target_height)
                    audio_idx = self._find_best_audio_format_index(formatted_formats, audio_tier)
                    
                    video_combo = self.task_table.cellWidget(row, 1)
                    if isinstance(video_combo, QComboBox) and video_idx < video_combo.count():
                        video_combo.setCurrentIndex(video_idx)
                        task.video_format_id = video_combo.currentData()
                        
                    audio_combo = self.task_table.cellWidget(row, 2)
                    if isinstance(audio_combo, QComboBox) and audio_idx < audio_combo.count():
                        audio_combo.setCurrentIndex(audio_idx)
                        task.audio_format_id = audio_combo.currentData()
    
    def _create_action_buttons(self, task: QueuedTask) -> QWidget:
        """创建操作按钮"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # 开始/暂停按钮
        start_pause_btn = QPushButton()
        start_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        start_pause_btn.setFixedSize(30, 24)
        start_pause_btn.setToolTip("开始下载")
        start_pause_btn.setObjectName("tableBtn")
        start_pause_btn.setProperty("task_btn_id", f"start_{task.id}")
        start_pause_btn.clicked.connect(lambda: self._toggle_task(task.id))
        layout.addWidget(start_pause_btn)

        # 取消按钮
        cancel_btn = QPushButton()
        cancel_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        cancel_btn.setFixedSize(30, 24)
        cancel_btn.setToolTip("取消任务")
        cancel_btn.setObjectName("tableBtn")
        cancel_btn.setProperty("task_btn_id", f"cancel_{task.id}")
        cancel_btn.clicked.connect(lambda: self._remove_task(task.id))
        layout.addWidget(cancel_btn)
        
        return widget
    
    def _get_status_text(self, status: DownloadStatus) -> str:
        """获取状态文本"""
        status_map = {
            DownloadStatus.PENDING: "等待中",
            DownloadStatus.QUEUED: "队列中",
            DownloadStatus.DOWNLOADING: "下载中",
            DownloadStatus.PAUSED: "已暂停",
            DownloadStatus.COMPLETED: "已完成",
            DownloadStatus.FAILED: "失败",
            DownloadStatus.CANCELLED: "已取消"
        }
        return status_map.get(status, "未知")
    
    def _set_status_color(self, item: QTableWidgetItem, status: DownloadStatus):
        """设置状态颜色"""
        color_map = {
            DownloadStatus.PENDING: QColor("#888888"),
            DownloadStatus.QUEUED: QColor("#2196F3"),
            DownloadStatus.DOWNLOADING: QColor("#0078D7"),
            DownloadStatus.PAUSED: QColor("#FF9800"),
            DownloadStatus.COMPLETED: QColor("#4CAF50"),
            DownloadStatus.FAILED: QColor("#F44336"),
            DownloadStatus.CANCELLED: QColor("#9E9E9E")
        }
        color = color_map.get(status, QColor("#000000"))
        item.setForeground(QBrush(color))
    
    def _update_task_row(self, task_id: str):
        """更新任务行"""
        if task_id not in self._task_rows or task_id not in self._tasks:
            return
        
        row = self._task_rows[task_id]
        task = self._tasks[task_id]
        
        # 更新状态（列3）
        status_item = self.task_table.item(row, 3)
        if status_item:
            status_item.setText(self._get_status_text(task.status))
            self._set_status_color(status_item, task.status)
        
        # 下载中时禁用格式选择
        is_downloading = task.status == DownloadStatus.DOWNLOADING
        video_combo = self.task_table.cellWidget(row, 1)
        audio_combo = self.task_table.cellWidget(row, 2)
        if isinstance(video_combo, QComboBox):
            video_combo.setEnabled(not is_downloading)
        if isinstance(audio_combo, QComboBox):
            audio_combo.setEnabled(not is_downloading)
        
        # 更新进度条（列4）
        progress_bar = self.task_table.cellWidget(row, 4)
        if isinstance(progress_bar, QProgressBar):
            progress_bar.setValue(int(task.progress))
        
        # 更新速度（列5）
        speed_item = self.task_table.item(row, 5)
        if speed_item:
            speed_item.setText(task.speed or "-")
        
        # 更新剩余时间（列6）
        eta_item = self.task_table.item(row, 6)
        if eta_item:
            eta_item.setText(task.eta or "-")
        
        # 更新操作按钮图标（列7）
        action_widget = self.task_table.cellWidget(row, 7)
        if action_widget:
            start_btn = next(
                (b for b in action_widget.findChildren(QPushButton)
                 if b.property("task_btn_id") == f"start_{task_id}"),
                None
            )
            if start_btn:
                if task.status == DownloadStatus.DOWNLOADING:
                    start_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
                    start_btn.setToolTip("暂停下载")
                elif task.status == DownloadStatus.COMPLETED:
                    start_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
                    start_btn.setToolTip("重新下载 (覆盖原文件)")
                    start_btn.setEnabled(True)
                elif task.status in (DownloadStatus.FAILED, DownloadStatus.CANCELLED):
                    start_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
                    start_btn.setToolTip("重试")
                else:
                    start_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
                    start_btn.setToolTip("开始下载")
    
    def _toggle_task(self, task_id: str):
        """切换任务状态（开始/暂停）"""
        if task_id not in self._tasks:
            return
        
        task = self._tasks[task_id]
        
        if task.status == DownloadStatus.PENDING:
            self._start_task(task_id)
        elif task.status == DownloadStatus.DOWNLOADING:
            self._pause_task(task_id)
        elif task.status == DownloadStatus.PAUSED:
            self._start_task(task_id)
        elif task.status in (DownloadStatus.FAILED, DownloadStatus.CANCELLED):
            # 如果是解析失败且没有任何格式，可以提示用户重新添加或者将其重置并重试
            # 重试
            task.status = DownloadStatus.PENDING
            task.overwrite = False
            task.progress = 0
            task.error_message = ""
            self._update_task_row(task_id)
            self._start_task(task_id)
        elif task.status == DownloadStatus.COMPLETED:
            # 重新下载
            task.status = DownloadStatus.PENDING
            task.overwrite = True
            task.progress = 0
            task.error_message = ""
            self._update_task_row(task_id)
            self._start_task(task_id)
    
    def _start_task(self, task_id: str):
        """开始下载任务"""
        if task_id not in self._tasks:
            return
        
        # 检查并发限制
        active_count = sum(1 for t in self._tasks.values() 
                         if t.status == DownloadStatus.DOWNLOADING)
        if active_count >= self.max_concurrent:
            # 加入队列
            self._tasks[task_id].status = DownloadStatus.QUEUED
            self._update_task_row(task_id)
            return
        
        task = self._tasks[task_id]
        
        # 检查下载目录，不存在则自动创建
        if not task.output_dir:
            task.output_dir = self.dir_input.text()
        if not task.output_dir:
            QMessageBox.warning(self, "警告", "请先选择下载目录")
            return
        if not os.path.exists(task.output_dir):
            try:
                os.makedirs(task.output_dir, exist_ok=True)
            except Exception as e:
                QMessageBox.warning(self, "警告", f"无法创建下载目录：{e}")
                return
        
        # 更新状态
        task.status = DownloadStatus.DOWNLOADING
        task.started_at = datetime.now()
        self._update_task_row(task_id)
        
        # 创建下载器和线程
        downloader = VideoDownloader()
        thread = MultiDownloadThread(task, downloader)
        thread.task_progress.connect(self._on_task_progress)
        thread.task_completed.connect(self._on_task_completed)
        thread.task_failed.connect(self._on_task_failed)
        
        self._download_threads[task_id] = thread
        thread.start()
        
        self.logger.info(f"开始下载任务: {task.title}")
        self._update_button_states()
    
    def _pause_task(self, task_id: str):
        """暂停任务"""
        if task_id in self._download_threads:
            thread = self._download_threads[task_id]
            thread.cancel()
            del self._download_threads[task_id]
        
        if task_id in self._tasks:
            self._tasks[task_id].status = DownloadStatus.PAUSED
            self._update_task_row(task_id)
        
        self._update_button_states()
    
    def _remove_task(self, task_id: str):
        """移除任务"""
        # 如果正在下载，先取消
        if task_id in self._download_threads:
            thread = self._download_threads[task_id]
            thread.cancel()
            thread.wait(1000)
            del self._download_threads[task_id]
        
        # 从表格中移除
        if task_id in self._task_rows:
            row = self._task_rows[task_id]
            self.task_table.removeRow(row)
            
            # 更新行索引
            del self._task_rows[task_id]
            for tid, r in self._task_rows.items():
                if r > row:
                    self._task_rows[tid] = r - 1
        
        # 从任务列表移除
        if task_id in self._tasks:
            del self._tasks[task_id]
        
        # 清理格式信息
        if task_id in self._task_formats:
            del self._task_formats[task_id]
        if task_id in self._task_video_info:
            del self._task_video_info[task_id]
        
        self._update_queue_info()
        self._update_button_states()
        
        # 尝试启动队列中的任务
        self._try_start_queued_tasks()
    
    def _on_task_progress(self, task_id: str, progress: float, speed: str, eta: str):
        """任务进度更新"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.progress = progress
            task.speed = speed
            task.eta = eta
            self._update_task_row(task_id)
    
    def _on_task_completed(self, task_id: str):
        """任务完成"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.status = DownloadStatus.COMPLETED
            task.progress = 100
            task.completed_at = datetime.now()
            task.speed = ""
            task.eta = ""
            self._update_task_row(task_id)
        
        if task_id in self._download_threads:
            del self._download_threads[task_id]
        
        self._update_button_states()
        self._try_start_queued_tasks()
        
        self.logger.info(f"任务完成: {task_id}")
    
    def _on_task_failed(self, task_id: str, error_message: str):
        """任务失败"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.status = DownloadStatus.FAILED
            # 使用 ErrorMessages 格式化错误消息
            formatted_message = ErrorMessages.get_user_message(error_message, include_suggestion=True)
            task.error_message = formatted_message
            task.speed = ""
            task.eta = ""
            self._update_task_row(task_id)
        
        if task_id in self._download_threads:
            del self._download_threads[task_id]
        
        self._update_button_states()
        self._try_start_queued_tasks()
        
        self.logger.error(f"任务失败: {task_id} - {error_message}")
        
        # 检测是否需要 cookies，如果需要且未启用，显示提示
        needs_cookie = ErrorMessages.needs_cookie(error_message)
        use_cookies = self.use_cookie_checkbox.isChecked()
        has_cookie_available = self.cookie_tab and self.cookie_tab.is_cookie_available()
        
        if needs_cookie and (not use_cookies or not has_cookie_available):
            # 只在第一个需要 cookies 的错误时显示提示，避免重复提示
            if not hasattr(self, '_cookie_prompt_shown'):
                self._cookie_prompt_shown = True
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("下载失败 - 需要 Cookie")
                msg_box.setText("部分任务需要 Cookie 才能下载。")
                msg_box.setInformativeText("请在 Cookie 页面设置您的浏览器 Cookie，然后重新启动失败的任务。")
                
                # 添加按钮
                goto_cookie_button = msg_box.addButton("前往设置 Cookie", QMessageBox.ActionRole)
                cancel_button = msg_box.addButton("知道了", QMessageBox.RejectRole)
                
                msg_box.exec_()
                
                clicked_button = msg_box.clickedButton()
                if clicked_button == goto_cookie_button:
                    # 切换到 Cookie 标签页
                    main_window = self.window()
                    if main_window and hasattr(main_window, 'tab_widget'):
                        main_window.tab_widget.setCurrentWidget(self.cookie_tab)
                
                # 重置标志，允许下次再提示
                self._cookie_prompt_shown = False
    
    def _try_start_queued_tasks(self):
        """尝试启动队列中的任务"""
        active_count = sum(1 for t in self._tasks.values() 
                         if t.status == DownloadStatus.DOWNLOADING)
        
        for task_id, task in self._tasks.items():
            if active_count >= self.max_concurrent:
                break
            if task.status == DownloadStatus.QUEUED:
                self._start_task(task_id)
                active_count += 1
    
    def _start_all_tasks(self):
        """开始所有任务"""
        for task_id, task in self._tasks.items():
            if task.status in (DownloadStatus.PENDING, DownloadStatus.PAUSED):
                task.status = DownloadStatus.QUEUED
                self._update_task_row(task_id)
        
        self._try_start_queued_tasks()
        self._update_button_states()
    
    def _pause_all_tasks(self):
        """暂停所有任务"""
        for task_id in list(self._download_threads.keys()):
            self._pause_task(task_id)
        
        # 将队列中的任务改为等待
        for task_id, task in self._tasks.items():
            if task.status == DownloadStatus.QUEUED:
                task.status = DownloadStatus.PENDING
                self._update_task_row(task_id)
        
        self._update_button_states()
    
    def _clear_completed_tasks(self):
        """清除已完成的任务"""
        to_remove = [
            task_id for task_id, task in self._tasks.items()
            if task.status in (DownloadStatus.COMPLETED, DownloadStatus.CANCELLED)
        ]
        
        for task_id in to_remove:
            self._remove_task(task_id)
    
    def _clear_all_tasks(self):
        """清空所有任务"""
        if not self._tasks:
            return
        
        reply = QMessageBox.question(
            self, "确认",
            "确定要清空所有任务吗？\n正在下载的任务将被取消。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 取消所有下载
        for task_id in list(self._download_threads.keys()):
            thread = self._download_threads[task_id]
            thread.cancel()
        
        # 等待线程结束
        for thread in self._download_threads.values():
            thread.wait(1000)
        
        self._download_threads.clear()
        self._tasks.clear()
        self._task_rows.clear()
        self._task_formats.clear()
        self._task_video_info.clear()
        self.task_table.setRowCount(0)
        
        self._update_queue_info()
        self._update_button_states()
    
    def _show_context_menu(self, position):
        """显示右键菜单"""
        item = self.task_table.itemAt(position)
        if not item:
            return
        
        row = item.row()
        title_item = self.task_table.item(row, 0)
        if not title_item:
            return
        
        task_id = title_item.data(Qt.UserRole)
        if task_id not in self._tasks:
            return
        
        task = self._tasks[task_id]
        
        menu = QMenu(self)
        
        # 根据状态添加不同操作
        if task.status in (DownloadStatus.PENDING, DownloadStatus.PAUSED):
            start_action = QAction("开始下载", self)
            start_action.triggered.connect(lambda: self._start_task(task_id))
            menu.addAction(start_action)
        
        if task.status == DownloadStatus.DOWNLOADING:
            pause_action = QAction("暂停", self)
            pause_action.triggered.connect(lambda: self._pause_task(task_id))
            menu.addAction(pause_action)
        
        if task.status in (DownloadStatus.FAILED, DownloadStatus.CANCELLED):
            retry_action = QAction("重试", self)
            retry_action.triggered.connect(lambda: self._toggle_task(task_id))
            menu.addAction(retry_action)
        
        menu.addSeparator()
        
        # 复制链接
        copy_action = QAction("复制链接", self)
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(task.url))
        menu.addAction(copy_action)
        
        # 移除任务
        remove_action = QAction("移除任务", self)
        remove_action.triggered.connect(lambda: self._remove_task(task_id))
        menu.addAction(remove_action)
        
        menu.exec_(self.task_table.viewport().mapToGlobal(position))
    
    def _update_queue_info(self):
        """更新队列信息"""
        total = len(self._tasks)
        self.queue_info_label.setText(f"队列: {total} 个任务")
    
    def _update_button_states(self):
        """更新按钮状态"""
        has_tasks = len(self._tasks) > 0
        has_pending = any(t.status in (DownloadStatus.PENDING, DownloadStatus.QUEUED, DownloadStatus.PAUSED) 
                        for t in self._tasks.values())
        has_downloading = any(t.status == DownloadStatus.DOWNLOADING for t in self._tasks.values())
        
        self.start_all_button.setEnabled(has_pending)
        self.pause_all_button.setEnabled(has_downloading)
        self.clear_all_button.setEnabled(has_tasks)
    
    def _update_statistics(self):
        """更新统计信息"""
        if not self._tasks:
            self.total_progress_bar.setValue(0)
            self.stats_label.setText("已完成: 0/0   下载中: 0   等待中: 0")
            self.speed_label.setText("总速度: 0 B/s")
            return
        
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks.values() if t.status == DownloadStatus.COMPLETED)
        downloading = sum(1 for t in self._tasks.values() if t.status == DownloadStatus.DOWNLOADING)
        pending = sum(1 for t in self._tasks.values() 
                     if t.status in (DownloadStatus.PENDING, DownloadStatus.QUEUED))
        
        # 计算总进度
        if total > 0:
            total_progress = sum(t.progress for t in self._tasks.values()) / total
            self.total_progress_bar.setValue(int(total_progress))
        
        self.stats_label.setText(
            f"已完成: {completed}/{total}   下载中: {downloading}   等待中: {pending}"
        )
        
        # 计算总速度（简化显示）
        if downloading > 0:
            speeds = [t.speed for t in self._tasks.values() 
                     if t.status == DownloadStatus.DOWNLOADING and t.speed]
            if speeds:
                self.speed_label.setText(f"下载中: {downloading} 个")
            else:
                self.speed_label.setText("总速度: 计算中...")
        else:
            self.speed_label.setText("总速度: 0 B/s")
    
    def _browse_download_dir(self):
        """浏览下载目录"""
        current_dir = self.dir_input.text() or os.path.expanduser("~/Desktop")
        
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择下载文件夹", current_dir
        )
        
        if dir_path:
            self.dir_input.setText(dir_path)
            if self.config_manager:
                self.config_manager.set('download_dir', dir_path)

    def _open_download_dir(self):
        """在文件管理器中打开下载目录（跨平台）"""
        import sys
        dir_path = self.dir_input.text()
        if not dir_path or not os.path.exists(dir_path):
            QMessageBox.warning(self, "警告", "下载目录不存在，请先选择有效的目录")
            return
        if sys.platform == 'win32':
            os.startfile(dir_path)
        elif sys.platform == 'darwin':
            import subprocess
            subprocess.Popen(['open', dir_path])
        else:
            import subprocess
            subprocess.Popen(['xdg-open', dir_path])
    
    def _set_default_download_dir(self):
        """设置默认下载目录"""
        if self.config_manager:
            last_dir = self.config_manager.get('download_dir')
            if last_dir:
                self.dir_input.setText(last_dir)
                return

        # 默认目录：D:\youtobe_bd_data
        default_dir = r"D:\youtobe_bd_data"
        self.dir_input.setText(default_dir)
    
    # ===== 事件总线回调 =====
    
    def _on_event_download_progress(self, event):
        """处理下载进度事件"""
        data = event.data
        task_id = data.get('task_id')
        if task_id and task_id in self._tasks:
            self._tasks[task_id].progress = data.get('progress', 0)
            self._tasks[task_id].speed = data.get('speed', '')
            self._tasks[task_id].eta = data.get('eta', '')
            self._update_task_row(task_id)
    
    def _on_event_download_completed(self, event):
        """处理下载完成事件"""
        task_id = event.data.get('task_id')
        if task_id:
            self._on_task_completed(task_id)
    
    def _on_event_download_failed(self, event):
        """处理下载失败事件"""
        task_id = event.data.get('task_id')
        error = event.data.get('error', '下载失败')
        if task_id:
            self._on_task_failed(task_id, error)
    
    def _on_event_download_cancelled(self, event):
        """处理下载取消事件"""
        task_id = event.data.get('task_id')
        if task_id and task_id in self._tasks:
            self._tasks[task_id].status = DownloadStatus.CANCELLED
            self._update_task_row(task_id)
    
    def _get_proxy_url(self) -> Optional[str]:
        """
        从配置中获取代理URL
        
        Returns:
            代理URL，如果未启用代理则返回None
        """
        if not self.config_manager.get('proxy_enabled', False):
            return None
        
        proxy_type = self.config_manager.get('proxy_type', 'http')
        proxy_host = self.config_manager.get('proxy_host', '127.0.0.1')
        proxy_port = self.config_manager.get('proxy_port', 7890)
        proxy_username = self.config_manager.get('proxy_username', '')
        proxy_password = self.config_manager.get('proxy_password', '')
        
        if not proxy_host:
            return None
        
        # 构建代理URL
        if proxy_username and proxy_password:
            return f"{proxy_type}://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"
        else:
            return f"{proxy_type}://{proxy_host}:{proxy_port}"
