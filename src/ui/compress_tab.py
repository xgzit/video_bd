"""
youtobe_bd 视频压缩标签页
提供 GPU / CPU 加速的本地视频压缩功能
"""
import os
import threading
from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QProgressBar, QGroupBox, QFileDialog,
    QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread

from src.core.compressor import (
    Compressor, detect_available_encoders, get_output_path,
    ENCODERS, QUALITY_PRESETS
)
from src.utils.logger import LoggerManager


class CompressWorker(QThread):
    """在后台线程执行压缩，通过信号更新 UI"""

    progress = pyqtSignal(float, str)   # (percent, status)
    finished = pyqtSignal(bool, str)    # (success, message)

    def __init__(self, compressor: Compressor, input_path: str,
                 output_path: str, encoder_key: str, quality: int):
        super().__init__()
        self._compressor = compressor
        self._input = input_path
        self._output = output_path
        self._encoder_key = encoder_key
        self._quality = quality

    def run(self):
        ok, msg = self._compressor.compress(
            self._input,
            self._output,
            encoder_key=self._encoder_key,
            quality=self._quality,
            progress_callback=lambda p, s: self.progress.emit(p, s),
        )
        self.finished.emit(ok, msg)

    def cancel(self):
        self._compressor.cancel()


class CompressTab(QWidget):
    """视频压缩标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = LoggerManager().get_logger()
        self._compressor = Compressor()
        self._worker: Optional[CompressWorker] = None
        self._available_encoders = detect_available_encoders()
        self._init_ui()

    # ──────────────────────────────────────────────────────────
    #  UI 初始化
    # ──────────────────────────────────────────────────────────

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ── 输入文件 ──
        input_group = QGroupBox("输入文件")
        input_layout = QHBoxLayout(input_group)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("选择或拖入视频文件…")
        self.input_edit.setReadOnly(True)
        input_layout.addWidget(self.input_edit)

        browse_btn = QPushButton("浏览…")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_input)
        input_layout.addWidget(browse_btn)

        layout.addWidget(input_group)

        # ── 输出文件 ──
        output_group = QGroupBox("输出文件")
        output_layout = QHBoxLayout(output_group)

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("默认与输入文件同目录，自动添加 _compressed 后缀")
        output_layout.addWidget(self.output_edit)

        out_browse_btn = QPushButton("浏览…")
        out_browse_btn.setFixedWidth(80)
        out_browse_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(out_browse_btn)

        layout.addWidget(output_group)

        # ── 编码器 & 质量 ──
        options_group = QGroupBox("压缩选项")
        options_layout = QHBoxLayout(options_group)

        options_layout.addWidget(QLabel("编码器："))
        self.encoder_combo = QComboBox()
        for key in self._available_encoders:
            _, display = ENCODERS[key]
            self.encoder_combo.addItem(display, key)
        options_layout.addWidget(self.encoder_combo)

        options_layout.addSpacing(20)
        options_layout.addWidget(QLabel("画质："))
        self.quality_combo = QComboBox()
        for label, crf in QUALITY_PRESETS.items():
            self.quality_combo.addItem(label, crf)
        self.quality_combo.setCurrentIndex(1)   # 默认"高"
        options_layout.addWidget(self.quality_combo)

        options_layout.addStretch()
        layout.addWidget(options_group)

        # ── 进度条 ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # ── 操作按钮 ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.start_btn = QPushButton("开始压缩")
        self.start_btn.setMinimumWidth(120)
        self.start_btn.clicked.connect(self._start_compress)
        btn_layout.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setMinimumWidth(80)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_compress)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

    # ──────────────────────────────────────────────────────────
    #  事件处理
    # ──────────────────────────────────────────────────────────

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.mkv *.avi *.mov *.flv *.webm *.ts);;所有文件 (*)"
        )
        if path:
            self.input_edit.setText(path)
            # 自动填充输出路径
            if not self.output_edit.text():
                self.output_edit.setText(get_output_path(path))

    def _browse_output(self):
        default = self.output_edit.text() or get_output_path(
            self.input_edit.text() or "output.mp4"
        )
        path, _ = QFileDialog.getSaveFileName(
            self, "保存压缩后文件", default,
            "视频文件 (*.mp4 *.mkv *.avi *.mov);;所有文件 (*)"
        )
        if path:
            self.output_edit.setText(path)

    def _start_compress(self):
        input_path = self.input_edit.text().strip()
        if not input_path:
            QMessageBox.warning(self, "提示", "请先选择输入文件")
            return

        output_path = self.output_edit.text().strip() or get_output_path(input_path)
        self.output_edit.setText(output_path)

        encoder_key = self.encoder_combo.currentData()
        quality = self.quality_combo.currentData()

        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在启动…")

        self._worker = CompressWorker(
            self._compressor, input_path, output_path, encoder_key, quality
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _cancel_compress(self):
        if self._worker:
            self._worker.cancel()
        self.status_label.setText("正在取消…")
        self.cancel_btn.setEnabled(False)

    def _on_progress(self, percent: float, status: str):
        self.progress_bar.setValue(int(percent))
        self.status_label.setText(status)

    def _on_finished(self, success: bool, message: str):
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("压缩完成")
            QMessageBox.information(
                self, "完成",
                f"压缩完成！\n输出文件：{message}"
            )
        elif message == "已取消":
            self.progress_bar.setValue(0)
            self.status_label.setText("已取消")
        else:
            self.progress_bar.setValue(0)
            self.status_label.setText(f"失败：{message}")
            QMessageBox.warning(self, "压缩失败", message)
