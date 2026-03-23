"""
youtobe_bd 视频压缩模块
支持 GPU 加速（NVIDIA/AMD/Intel）和 CPU 软件编码
"""
import os
import re
import subprocess
from typing import Optional, Callable

from src.utils.platform import get_ffmpeg_path, create_popen, run_subprocess, IS_WINDOWS


# 编码器定义：名称 → (ffmpeg encoder id, 显示名称)
ENCODERS = {
    'cpu':   ('libx264',    'CPU (libx264)'),
    'nvenc': ('h264_nvenc', 'NVIDIA GPU (h264_nvenc)'),
    'amf':   ('h264_amf',   'AMD GPU (h264_amf)'),
    'qsv':   ('h264_qsv',   'Intel GPU (h264_qsv)'),
}

# 画质预设：CRF 值（CPU）或 qp 值（GPU 编码器）
QUALITY_PRESETS = {
    '极高（几乎无损）': 18,
    '高':               23,
    '中':               28,
    '低（体积最小）':   35,
}


def detect_available_encoders() -> list[str]:
    """
    检测当前系统可用的硬件编码器。
    返回可用的 key 列表，始终包含 'cpu'。
    """
    available = ['cpu']
    ffmpeg = str(get_ffmpeg_path())
    if not os.path.exists(ffmpeg):
        return available

    for key, (enc_id, _) in ENCODERS.items():
        if key == 'cpu':
            continue
        try:
            result = run_subprocess(
                [ffmpeg, '-hide_banner', '-encoders'],
                capture_output=True, text=True, check=False, timeout=5
            )
            if enc_id in (result.stdout or ''):
                available.append(key)
        except Exception:
            pass
    return available


def get_output_path(input_path: str) -> str:
    """根据输入路径生成默认输出路径（在同目录加 _compressed 后缀）"""
    base, ext = os.path.splitext(input_path)
    return f"{base}_compressed{ext or '.mp4'}"


class Compressor:
    """
    视频压缩器。
    通过 FFmpeg 压缩视频，支持硬件加速编码。
    """

    def __init__(self):
        self.ffmpeg_path = str(get_ffmpeg_path())
        self._process: Optional[subprocess.Popen] = None
        self._cancelled = False

    def compress(
        self,
        input_path: str,
        output_path: str,
        encoder_key: str = 'cpu',
        quality: int = 23,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> tuple[bool, str]:
        """
        压缩视频文件。

        Args:
            input_path:        源文件路径
            output_path:       输出文件路径
            encoder_key:       编码器 key（cpu / nvenc / amf / qsv）
            quality:           质量值（CRF/qp，18–35）
            progress_callback: 回调 (percent: float, status: str)

        Returns:
            (success, message)
        """
        self._cancelled = False

        if not os.path.exists(self.ffmpeg_path):
            return False, "未找到 FFmpeg，请先在「版本管理」页安装。"

        if not os.path.exists(input_path):
            return False, f"文件不存在：{input_path}"

        encoder_id, _ = ENCODERS.get(encoder_key, ENCODERS['cpu'])

        # 获取视频时长用于进度计算
        duration = self._get_duration(input_path)

        # 构建 FFmpeg 命令
        cmd = [self.ffmpeg_path, '-y', '-i', input_path]

        if encoder_key == 'cpu':
            cmd += ['-c:v', encoder_id, '-crf', str(quality), '-preset', 'medium']
        else:
            cmd += ['-c:v', encoder_id, '-qp', str(quality)]

        cmd += ['-c:a', 'copy', output_path]

        try:
            self._process = create_popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

            for line in self._process.stdout:
                if self._cancelled:
                    self._process.terminate()
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    return False, "已取消"

                # 解析 FFmpeg 进度行：time=HH:MM:SS.ms
                if progress_callback and duration > 0:
                    m = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
                    if m:
                        elapsed = (int(m.group(1)) * 3600
                                   + int(m.group(2)) * 60
                                   + float(m.group(3)))
                        pct = min(elapsed / duration * 100, 99.9)
                        progress_callback(pct, f"压缩中 {pct:.1f}%")

            self._process.wait()
            rc = self._process.returncode

            if rc != 0:
                return False, f"FFmpeg 返回错误码 {rc}"

            if progress_callback:
                progress_callback(100.0, "压缩完成")
            return True, output_path

        except Exception as e:
            return False, str(e)
        finally:
            self._process = None

    def cancel(self):
        """取消当前压缩任务"""
        self._cancelled = True
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass

    def _get_duration(self, path: str) -> float:
        """获取视频时长（秒），失败返回 0"""
        try:
            result = run_subprocess(
                [self.ffmpeg_path, '-i', path],
                capture_output=True, text=True, check=False, timeout=10
            )
            output = (result.stdout or '') + (result.stderr or '')
            m = re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)', output)
            if m:
                return (int(m.group(1)) * 3600
                        + int(m.group(2)) * 60
                        + float(m.group(3)))
        except Exception:
            pass
        return 0
