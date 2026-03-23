# PyInstaller runtime hook - 在所有代码之前运行
# 通过环境变量让 Qt5 跟随系统 DPI 缩放
import os
import sys

os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

if sys.platform == 'win32':
    import ctypes
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)  # PerMonitorV2
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)      # PerMonitor
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()       # 兜底
            except Exception:
                pass
