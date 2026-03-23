"""
youtobe_bd Cookie 标签页模块
支持从浏览器自动提取（通用多站点）和手动导入 Netscape 文件
"""
import os
import tempfile
from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QMessageBox, QGroupBox, QStatusBar,
    QFileDialog, QComboBox, QFrame, QApplication, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices

from src.core.cookie_manager import CookieManager
from src.utils.logger import LoggerManager
from src.utils.platform import get_yt_dlp_path, run_subprocess


# yt-dlp 支持的浏览器列表
BROWSERS = ['chrome', 'firefox', 'edge', 'safari', 'brave', 'opera', 'chromium', 'vivaldi']


class BrowserExtractThread(QThread):
    """后台执行 yt-dlp --cookies-from-browser 提取 Cookie"""

    finished = pyqtSignal(bool, str, str)   # (success, cookie_file, message)

    def __init__(self, browser: str, output_path: str):
        super().__init__()
        self._browser = browser
        self._output = output_path

    def run(self):
        yt_dlp = str(get_yt_dlp_path())
        if not os.path.exists(yt_dlp):
            self.finished.emit(False, '', 'yt-dlp 未安装，请先在「版本」页下载')
            return

        # yt-dlp --cookies-from-browser <browser> --skip-download --cookies <file> <url>
        # 使用一个稳定的公开页面触发 cookie 提取
        cmd = [
            yt_dlp,
            '--cookies-from-browser', self._browser,
            '--skip-download',
            '--cookies', self._output,
            '--quiet',
            'https://www.youtube.com',
        ]
        try:
            result = run_subprocess(cmd, check=False, timeout=30)
            if os.path.exists(self._output) and os.path.getsize(self._output) > 0:
                self.finished.emit(True, self._output, '')
            else:
                err = (result.stderr or result.stdout or '').strip()[:200]
                self.finished.emit(False, '', err or f'未能从 {self._browser} 提取到 Cookie，请确认浏览器已安装且已登录目标网站')
        except Exception as e:
            self.finished.emit(False, '', str(e))


class CookieTab(QWidget):
    """Cookie 管理标签页"""

    def __init__(self, status_bar: QStatusBar = None):
        super().__init__()
        self.logger = LoggerManager().get_logger()
        self.status_bar = status_bar
        self.cookie_manager = CookieManager()
        self._extract_thread: Optional[BrowserExtractThread] = None
        self._init_ui()
        self.logger.info("Cookie 标签页初始化完成")

    # ──────────────────────────────────────────────────────────
    #  UI
    # ──────────────────────────────────────────────────────────

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # ── 状态区 ──
        status_group = QGroupBox("Cookie 状态")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("当前状态：未使用")
        self.status_label.setWordWrap(True)
        self.status_label.setTextFormat(Qt.RichText)
        status_layout.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        self.verify_button = QPushButton("验证文件格式")
        self.verify_button.clicked.connect(self._verify_cookie)
        btn_row.addWidget(self.verify_button)

        self.clear_button = QPushButton("清除 Cookie")
        self.clear_button.setObjectName("secondaryButton")
        self.clear_button.clicked.connect(self._clear_cookie)
        btn_row.addWidget(self.clear_button)
        btn_row.addStretch()
        status_layout.addLayout(btn_row)
        layout.addWidget(status_group)

        # ── 从浏览器提取 ──
        extract_group = QGroupBox("从浏览器自动提取（推荐）")
        extract_layout = QVBoxLayout(extract_group)

        desc = QLabel(
            "使用 yt-dlp 从本地浏览器提取 Cookie，支持所有站点。\n"
            "⚠️ 提取前请先完全关闭对应浏览器（含后台进程），否则数据库锁定将导致失败。\n"
            "⚠️ Chrome 127+ 启用了 App-Bound 加密，建议改用 Firefox 或 Edge 提取。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #64748B; font-size: 9pt;")
        extract_layout.addWidget(desc)

        browser_row = QHBoxLayout()
        browser_row.addWidget(QLabel("浏览器："))
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(BROWSERS)
        browser_row.addWidget(self.browser_combo)

        self.extract_button = QPushButton("提取 Cookie")
        self.extract_button.clicked.connect(self._extract_from_browser)
        browser_row.addWidget(self.extract_button)
        browser_row.addStretch()
        extract_layout.addLayout(browser_row)
        layout.addWidget(extract_group)

        # ── 手动导入 ──
        file_group = QGroupBox("手动导入 Cookie 文件")
        file_layout = QVBoxLayout(file_group)

        file_desc = QLabel("支持 Netscape 格式的 Cookie 文件，可通过浏览器插件导出：")
        file_desc.setStyleSheet("color: #64748B; font-size: 9pt;")
        file_layout.addWidget(file_desc)

        # 插件名称行：可复制的只读输入框 + 两个快捷按钮
        plugin_row = QHBoxLayout()
        self.plugin_name_edit = QLineEdit("Get cookies.txt LOCALLY")
        self.plugin_name_edit.setReadOnly(True)
        self.plugin_name_edit.setStyleSheet("")  # 继承全局 QSS，与其他输入框保持一致
        self.plugin_name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        plugin_row.addWidget(self.plugin_name_edit)

        copy_name_btn = QPushButton("复制名称")
        copy_name_btn.setObjectName("secondaryButton")
        copy_name_btn.setMinimumWidth(76)
        copy_name_btn.setMaximumWidth(100)
        copy_name_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        copy_name_btn.setToolTip("复制插件名称到剪贴板，可直接在浏览器扩展商店搜索")
        copy_name_btn.clicked.connect(self._copy_plugin_name)
        plugin_row.addWidget(copy_name_btn)

        open_store_btn = QPushButton("去下载")
        open_store_btn.setObjectName("secondaryButton")
        open_store_btn.setMinimumWidth(72)
        open_store_btn.setMaximumWidth(100)
        open_store_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        open_store_btn.setToolTip("在浏览器中打开 Chrome Web Store 插件页面")
        open_store_btn.clicked.connect(self._open_plugin_store)
        plugin_row.addWidget(open_store_btn)

        file_layout.addLayout(plugin_row)

        # Cookie 文件路径行
        path_row = QHBoxLayout()
        self.cookie_file_input = QLineEdit()
        self.cookie_file_input.setPlaceholderText("Cookie 文件路径…")
        self.cookie_file_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        path_row.addWidget(self.cookie_file_input)

        browse_btn = QPushButton("浏览…")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.setMinimumWidth(64)
        browse_btn.setMaximumWidth(90)
        browse_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        browse_btn.clicked.connect(self._browse_cookie_file)
        path_row.addWidget(browse_btn)
        file_layout.addLayout(path_row)
        layout.addWidget(file_group)

        # ── 分隔线 ──
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #E2E8F0;")
        layout.addWidget(line)

        # ── 使用说明 ──
        note = QLabel(
            "Cookie 不是必需的，仅在以下情况需要：\n"
            "  • 下载会员专属内容\n"
            "  • 下载年龄限制视频\n"
            "  • 下载需要登录才能查看的私人内容"
        )
        note.setStyleSheet("color: #64748B; font-size: 9pt;")
        note.setWordWrap(True)
        layout.addWidget(note)

        # ── Cookie 内容预览 ──
        preview_group = QGroupBox("Cookie 文件预览")
        preview_layout = QVBoxLayout(preview_group)
        self.cookie_content = QTextEdit()
        self.cookie_content.setReadOnly(True)
        self.cookie_content.setPlaceholderText("加载 Cookie 文件后将在此显示内容")
        self.cookie_content.setMaximumHeight(140)
        preview_layout.addWidget(self.cookie_content)
        layout.addWidget(preview_group)

        layout.addStretch()

    # ──────────────────────────────────────────────────────────
    #  事件处理
    # ──────────────────────────────────────────────────────────

    def _extract_from_browser(self):
        """调用 yt-dlp 从浏览器提取 Cookie"""
        browser = self.browser_combo.currentText()
        output_dir = os.path.dirname(self.cookie_file_input.text() or '') or tempfile.gettempdir()
        output_path = os.path.join(output_dir, f'cookies_{browser}.txt')

        self.extract_button.setEnabled(False)
        self.extract_button.setText("提取中…")
        self._update_status_bar(f"正在从 {browser} 提取 Cookie…")

        self._extract_thread = BrowserExtractThread(browser, output_path)
        self._extract_thread.finished.connect(self._on_extract_finished)
        self._extract_thread.start()

    def _on_extract_finished(self, success: bool, cookie_file: str, message: str):
        self.extract_button.setEnabled(True)
        self.extract_button.setText("提取 Cookie")

        if success:
            self.cookie_file_input.setText(cookie_file)
            self._load_cookie_preview(cookie_file)
            self._set_status(True, f"已从 {self.browser_combo.currentText()} 提取 Cookie")
            self._update_status_bar("Cookie 提取成功")
            QMessageBox.information(self, "成功", f"Cookie 提取成功！\n文件：{cookie_file}")
        else:
            self._set_status(False, "提取失败")
            self._update_status_bar("Cookie 提取失败")
            # 识别常见错误，给出针对性提示
            browser = self.browser_combo.currentText()
            msg = message or ""
            if "Could not copy" in msg and "cookie database" in msg:
                hint = (
                    f"无法读取 {browser} 的 Cookie 数据库，浏览器正在运行时会锁定该文件。\n\n"
                    f"解决方法：\n"
                    f"1. 完全退出 {browser}（包括系统托盘/后台进程）\n"
                    f"2. 再次点击【提取 Cookie】\n\n"
                    f"或改用「手动导入」：在浏览器中安装插件\n"
                    f"Get cookies.txt LOCALLY，导出后手动选择文件。"
                )
                QMessageBox.warning(self, "浏览器未关闭", hint)
            elif "DPAPI" in msg or "decrypt" in msg.lower() or "App-Bound" in msg:
                hint = (
                    "Chrome 127+ 启用了 App-Bound 加密，yt-dlp 暂无法直接解密其 Cookie。\n\n"
                    "推荐解决方案：\n"
                    "1. 切换为 Firefox 或 Edge 提取（下拉框选择对应浏览器）\n"
                    "2. 或在 Chrome 中安装插件「Get cookies.txt LOCALLY」\n"
                    "   手动导出后使用「手动导入」功能加载文件"
                )
                QMessageBox.warning(self, "Chrome 加密限制", hint)
            else:
                QMessageBox.warning(self, "提取失败", msg or "未能提取到 Cookie")

    def _copy_plugin_name(self):
        """复制插件名称到剪贴板"""
        QApplication.clipboard().setText(self.plugin_name_edit.text())
        self._update_status_bar("插件名称已复制到剪贴板")

    def _open_plugin_store(self):
        """在浏览器中打开插件下载页"""
        # Chrome Web Store 页面
        url = "https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"
        QDesktopServices.openUrl(QUrl(url))
        self._update_status_bar("已在浏览器中打开插件下载页")

    def _browse_cookie_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Cookie 文件", "",
            "Cookie 文件 (*.txt);;所有文件 (*.*)"
        )
        if path:
            self.cookie_file_input.setText(path)
            self._load_cookie_preview(path)

    def _verify_cookie(self):
        """验证 Cookie 文件格式是否为 Netscape 格式"""
        path = self.cookie_file_input.text().strip()
        if not path:
            QMessageBox.warning(self, "提示", "请先选择或提取 Cookie 文件")
            return
        if not os.path.exists(path):
            QMessageBox.warning(self, "提示", "文件不存在")
            return

        ok, msg = self.cookie_manager.validate_cookie_file(path)
        if ok:
            self._set_status(True, "Cookie 文件格式有效（Netscape 格式）")
            self._update_status_bar("Cookie 验证通过")
            QMessageBox.information(self, "验证通过", "Cookie 文件格式正确，可以正常使用。")
        else:
            self._set_status(False, f"格式无效：{msg}")
            self._update_status_bar("Cookie 验证失败")
            QMessageBox.warning(self, "验证失败", msg)

    def _clear_cookie(self):
        self.cookie_file_input.clear()
        self.cookie_content.clear()
        self._set_status(False, "未使用")
        self._update_status_bar("已清除 Cookie")
        QMessageBox.information(self, "操作成功", "已清除 Cookie 信息。")

    def _load_cookie_preview(self, path: str):
        """加载并预览 Cookie 文件内容"""
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(4096)   # 只预览前 4KB
            if len(content) == 4096:
                content += '\n… (文件较大，仅显示前 4KB)'
            self.cookie_content.setPlainText(content)
            self._update_status_bar("Cookie 文件已加载")
        except Exception as e:
            self.logger.error(f"加载 Cookie 文件失败: {e}")
            QMessageBox.critical(self, "错误", f"加载文件失败：{e}")

    # ──────────────────────────────────────────────────────────
    #  辅助
    # ──────────────────────────────────────────────────────────

    def _set_status(self, active: bool, message: str):
        color = '#10B981' if active else '#64748B'
        self.status_label.setText(
            f'<span style="color:{color}; font-weight:600;">当前状态：{message}</span>'
        )

    def _update_status_bar(self, msg: str):
        if self.status_bar:
            self.status_bar.showMessage(msg)

    # ── 公开接口（供 multi_download_tab 调用） ──

    def get_cookie_file(self) -> str:
        return self.cookie_file_input.text().strip()

    def is_cookie_available(self) -> bool:
        path = self.get_cookie_file()
        return bool(path and os.path.exists(path))
