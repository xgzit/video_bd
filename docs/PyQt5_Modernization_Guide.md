# PyQt5 YouTube 下载器界面美化指南

## 🎨 现代化设计方案

### 配色方案
```python
# 主题色彩定义
COLORS = {
    'primary': '#EF4444',        # 红色主题（YouTube风格）
    'primary_hover': '#DC2626',  # 深红色（悬停）
    'secondary': '#64748B',      # 灰蓝色
    'background': '#F8FAFC',     # 浅灰背景
    'surface': '#FFFFFF',        # 白色表面
    'border': '#E2E8F0',         # 边框颜色
    'text_primary': '#0F172A',   # 主要文字
    'text_secondary': '#64748B', # 次要文字
    'success': '#10B981',        # 成功绿色
    'warning': '#F59E0B',        # 警告橙色
    'error': '#EF4444',          # 错误红色
}
```

---

## 📝 完整的 QSS 样式表

### 1. 主窗口样式

```python
MAIN_WINDOW_STYLE = """
QMainWindow {
    background-color: #F8FAFC;
}

QWidget {
    font-family: "Microsoft YaHei UI", "Segoe UI", Arial, sans-serif;
    font-size: 9pt;
    color: #0F172A;
}
"""
```

### 2. 标签页 (QTabWidget) 样式

```python
TAB_WIDGET_STYLE = """
QTabWidget::pane {
    border: none;
    background-color: white;
    border-radius: 12px;
    margin-top: 10px;
}

QTabBar::tab {
    background-color: transparent;
    color: #64748B;
    padding: 12px 24px;
    margin-right: 4px;
    border: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: white;
    color: #0F172A;
    font-weight: 600;
    box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.05);
}

QTabBar::tab:hover:!selected {
    background-color: #F1F5F9;
    color: #475569;
}
"""
```

### 3. 按钮样式

```python
BUTTON_STYLE = """
/* 主要按钮 - 红色渐变 */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #EF4444, stop:1 #DC2626);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 9pt;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #DC2626, stop:1 #B91C1C);
}

QPushButton:pressed {
    background: #991B1B;
    padding-top: 12px;
    padding-bottom: 8px;
}

QPushButton:disabled {
    background-color: #E2E8F0;
    color: #94A3B8;
}

/* 次要按钮 */
QPushButton[objectName="secondaryButton"] {
    background-color: white;
    color: #475569;
    border: 2px solid #E2E8F0;
}

QPushButton[objectName="secondaryButton"]:hover {
    border-color: #CBD5E1;
    background-color: #F8FAFC;
}

/* 图标按钮 */
QPushButton[objectName="iconButton"] {
    background-color: transparent;
    border: none;
    padding: 6px;
    border-radius: 6px;
}

QPushButton[objectName="iconButton"]:hover {
    background-color: #F1F5F9;
}
"""
```

### 4. 输入框样式

```python
INPUT_STYLE = """
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: white;
    border: 2px solid #E2E8F0;
    border-radius: 8px;
    padding: 10px 12px;
    color: #0F172A;
    selection-background-color: #EF4444;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #EF4444;
    outline: none;
}

QLineEdit:disabled, QTextEdit:disabled {
    background-color: #F1F5F9;
    color: #94A3B8;
}

/* 占位符文本 */
QLineEdit[placeholderText] {
    color: #94A3B8;
}
"""
```

### 5. 下拉框样式

```python
COMBOBOX_STYLE = """
QComboBox {
    background-color: white;
    border: 2px solid #E2E8F0;
    border-radius: 8px;
    padding: 8px 12px;
    min-width: 120px;
}

QComboBox:hover {
    border-color: #CBD5E1;
}

QComboBox:focus {
    border-color: #EF4444;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: url(icons/arrow-down.png);
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: white;
    border: 2px solid #E2E8F0;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: #FEE2E2;
    selection-color: #0F172A;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 8px 12px;
    border-radius: 4px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #FEE2E2;
}
"""
```

### 6. 复选框样式

```python
CHECKBOX_STYLE = """
QCheckBox {
    spacing: 8px;
    color: #0F172A;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #E2E8F0;
    background-color: white;
}

QCheckBox::indicator:hover {
    border-color: #EF4444;
}

QCheckBox::indicator:checked {
    background-color: #EF4444;
    border-color: #EF4444;
    image: url(icons/check.png);
}

QCheckBox::indicator:checked:hover {
    background-color: #DC2626;
}
"""
```

### 7. 进度条样式

```python
PROGRESS_STYLE = """
QProgressBar {
    border: none;
    border-radius: 6px;
    background-color: #F1F5F9;
    text-align: center;
    color: #475569;
    font-weight: 600;
    height: 12px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #EF4444, stop:1 #DC2626);
    border-radius: 6px;
}
"""
```

### 8. 表格样式

```python
TABLE_STYLE = """
QTableWidget {
    background-color: white;
    border: 2px solid #E2E8F0;
    border-radius: 8px;
    gridline-color: #F1F5F9;
    selection-background-color: #FEE2E2;
    selection-color: #0F172A;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #F1F5F9;
}

QTableWidget::item:selected {
    background-color: #FEE2E2;
}

QHeaderView::section {
    background-color: #F8FAFC;
    color: #64748B;
    padding: 10px;
    border: none;
    border-bottom: 2px solid #E2E8F0;
    font-weight: 600;
}

QHeaderView::section:hover {
    background-color: #F1F5F9;
}
"""
```

### 9. 滚动条样式

```python
SCROLLBAR_STYLE = """
QScrollBar:vertical {
    background-color: #F8FAFC;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #CBD5E1;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #94A3B8;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #F8FAFC;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #CBD5E1;
    border-radius: 6px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #94A3B8;
}
"""
```

### 10. 分组框样式

```python
GROUPBOX_STYLE = """
QGroupBox {
    background-color: white;
    border: 2px solid #E2E8F0;
    border-radius: 12px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    background-color: transparent;
    color: #0F172A;
}
"""
```

---

## 🔧 Python 代码实现示例

### 主窗口代码

```python
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QLabel, QPushButton,
                             QLineEdit, QTextEdit, QComboBox, QCheckBox,
                             QProgressBar, QTableWidget, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

class ModernYouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('YouTube Downloader')
        self.setGeometry(100, 100, 1000, 700)
        
        # 应用样式表
        self.setStyleSheet(self.get_stylesheet())
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 添加头部
        header = self.create_header()
        main_layout.addWidget(header)
        
        # 添加标签页
        tabs = self.create_tabs()
        main_layout.addWidget(tabs)
        
        # 添加底部
        footer = self.create_footer()
        main_layout.addWidget(footer)
        
    def create_header(self):
        """创建头部"""
        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        
        layout = QHBoxLayout(header)
        
        # 图标和标题
        title_label = QLabel('🎥 YouTube Downloader')
        title_label.setStyleSheet("""
            font-size: 18pt;
            font-weight: bold;
            color: #0F172A;
        """)
        
        version_label = QLabel('v1.0.0')
        version_label.setStyleSheet("""
            color: #64748B;
            font-size: 9pt;
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addStretch()
        
        return header
    
    def create_tabs(self):
        """创建标签页"""
        tab_widget = QTabWidget()
        
        # 添加各个标签页
        tab_widget.addTab(self.create_download_tab(), '视频下载')
        tab_widget.addTab(self.create_cookie_tab(), 'Cookie')
        tab_widget.addTab(self.create_proxy_tab(), '代理')
        tab_widget.addTab(self.create_version_tab(), '版本')
        
        return tab_widget
    
    def create_download_tab(self):
        """创建下载标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # 视频链接区域
        link_group = QGroupBox('📎 视频链接')
        link_layout = QVBoxLayout(link_group)
        
        url_input = QTextEdit()
        url_input.setPlaceholderText(
            '在此输入多个 YouTube 视频链接，每行一个。\n'
            '支持：\n'
            '• 单个视频链接\n'
            '• 播放列表链接\n'
            '• 频道链接'
        )
        url_input.setMaximumHeight(120)
        link_layout.addWidget(url_input)
        
        # Cookie 和解析按钮
        button_layout = QHBoxLayout()
        
        use_cookie = QCheckBox('使用 Cookie')
        button_layout.addWidget(use_cookie)
        button_layout.addStretch()
        
        parse_btn = QPushButton('🔍 解析链接')
        parse_btn.setMinimumWidth(120)
        button_layout.addWidget(parse_btn)
        
        link_layout.addLayout(button_layout)
        layout.addWidget(link_group)
        
        # 下载设置
        settings_group = QGroupBox('⚙️ 下载设置')
        settings_layout = QHBoxLayout(settings_group)
        
        settings_layout.addWidget(QLabel('下载目录:'))
        path_input = QLineEdit('D:/迅雷下载/lucy')
        settings_layout.addWidget(path_input, 1)
        
        browse_btn = QPushButton('📂 浏览')
        browse_btn.setObjectName('secondaryButton')
        browse_btn.setMinimumWidth(100)
        settings_layout.addWidget(browse_btn)
        
        open_btn = QPushButton('📁 打开目录')
        open_btn.setMinimumWidth(100)
        settings_layout.addWidget(open_btn)
        
        layout.addWidget(settings_group)
        
        # 质量选择
        quality_group = QGroupBox('🎬 质量选择')
        quality_layout = QHBoxLayout(quality_group)
        
        quality_layout.addWidget(QLabel('视频质量:'))
        video_quality = QComboBox()
        video_quality.addItems(['720p (HD)', '1080p (Full HD)', '1440p (2K)', '2160p (4K)'])
        quality_layout.addWidget(video_quality)
        
        quality_layout.addWidget(QLabel('音频质量:'))
        audio_quality = QComboBox()
        audio_quality.addItems(['最佳质量(自动选择)', '320kbps', '256kbps', '192kbps'])
        quality_layout.addWidget(audio_quality)
        
        quality_layout.addStretch()
        layout.addWidget(quality_group)
        
        # 进度条
        progress_group = QGroupBox('📊 总体进度')
        progress_layout = QVBoxLayout(progress_group)
        
        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        progress_bar.setTextVisible(True)
        progress_layout.addWidget(progress_bar)
        
        stats_layout = QHBoxLayout()
        stats_layout.addWidget(QLabel('已完成: 0/0'))
        stats_layout.addWidget(QLabel('下载中: 0'))
        stats_layout.addWidget(QLabel('等待中: 0'))
        stats_layout.addStretch()
        stats_layout.addWidget(QLabel('总速度: 0 B/s'))
        progress_layout.addLayout(stats_layout)
        
        layout.addWidget(progress_group)
        layout.addStretch()
        
        return tab
    
    def create_cookie_tab(self):
        """创建 Cookie 标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        group = QGroupBox('🍪 Cookie 管理')
        group_layout = QVBoxLayout(group)
        
        info_label = QLabel('在此粘贴您的 YouTube Cookie 以访问受限内容或提高下载成功率。')
        info_label.setStyleSheet('color: #64748B; font-size: 9pt;')
        group_layout.addWidget(info_label)
        
        cookie_input = QTextEdit()
        cookie_input.setPlaceholderText('粘贴您的 Cookie 内容...')
        group_layout.addWidget(cookie_input)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        import_btn = QPushButton('📥 导入 Cookie 文件')
        button_layout.addWidget(import_btn)
        
        export_btn = QPushButton('📤 导出 Cookie 文件')
        export_btn.setObjectName('secondaryButton')
        button_layout.addWidget(export_btn)
        
        clear_btn = QPushButton('🗑️ 清除 Cookie')
        clear_btn.setObjectName('secondaryButton')
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        group_layout.addLayout(button_layout)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return tab
    
    def create_proxy_tab(self):
        """创建代理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        group = QGroupBox('🌐 代理设置')
        group_layout = QVBoxLayout(group)
        
        # 代理类型和地址
        proxy_layout = QHBoxLayout()
        
        proxy_layout.addWidget(QLabel('代理类型:'))
        proxy_type = QComboBox()
        proxy_type.addItems(['HTTP', 'HTTPS', 'SOCKS5'])
        proxy_layout.addWidget(proxy_type)
        
        proxy_layout.addWidget(QLabel('主机地址:'))
        host_input = QLineEdit()
        host_input.setPlaceholderText('例如: 127.0.0.1')
        proxy_layout.addWidget(host_input)
        
        proxy_layout.addWidget(QLabel('端口:'))
        port_input = QLineEdit()
        port_input.setPlaceholderText('例如: 7890')
        port_input.setMaximumWidth(100)
        proxy_layout.addWidget(port_input)
        
        group_layout.addLayout(proxy_layout)
        
        # 用户名和密码
        auth_layout = QHBoxLayout()
        
        auth_layout.addWidget(QLabel('用户名:'))
        username_input = QLineEdit()
        username_input.setPlaceholderText('可选')
        auth_layout.addWidget(username_input)
        
        auth_layout.addWidget(QLabel('密码:'))
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.Password)
        password_input.setPlaceholderText('可选')
        auth_layout.addWidget(password_input)
        
        group_layout.addLayout(auth_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton('💾 保存设置')
        button_layout.addWidget(save_btn)
        
        test_btn = QPushButton('🧪 测试连接')
        test_btn.setObjectName('secondaryButton')
        button_layout.addWidget(test_btn)
        
        button_layout.addStretch()
        group_layout.addLayout(button_layout)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return tab
    
    def create_version_tab(self):
        """创建版本标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        group = QGroupBox('ℹ️ 版本信息')
        group_layout = QVBoxLayout(group)
        
        info_text = """
        <h3 style='color: #0F172A;'>YouTube Downloader v1.0.0</h3>
        <p style='color: #64748B;'>发布日期: 2024-03-20</p>
        <p style='color: #64748B;'>许可证: AGPL-3.0</p>
        <p style='color: #64748B;'>开发者: xgzit</p>
        
        <h4 style='color: #0F172A; margin-top: 20px;'>更新日志</h4>
        <ul style='color: #475569;'>
            <li>全新的现代化界面设计</li>
            <li>优化下载队列管理</li>
            <li>改进代理设置功能</li>
            <li>修复已知问题</li>
        </ul>
        """
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        group_layout.addWidget(info_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        check_btn = QPushButton('🔄 检查更新')
        button_layout.addWidget(check_btn)
        
        github_btn = QPushButton('💻 GitHub')
        github_btn.setObjectName('secondaryButton')
        button_layout.addWidget(github_btn)
        
        button_layout.addStretch()
        group_layout.addLayout(button_layout)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return tab
    
    def create_footer(self):
        """创建底部"""
        footer = QLabel('By xgzit | AGPL-3.0')
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("""
            color: #94A3B8;
            font-size: 8pt;
            padding: 10px;
        """)
        return footer
    
    def get_stylesheet(self):
        """获取完整样式表"""
        return """
            /* 主窗口 */
            QMainWindow {
                background-color: #F8FAFC;
            }
            
            QWidget {
                font-family: "Microsoft YaHei UI", "Segoe UI", Arial;
                font-size: 9pt;
                color: #0F172A;
            }
            
            /* 标签页 */
            QTabWidget::pane {
                border: none;
                background-color: white;
                border-radius: 12px;
                margin-top: 10px;
            }
            
            QTabBar::tab {
                background-color: transparent;
                color: #64748B;
                padding: 12px 24px;
                margin-right: 4px;
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                color: #0F172A;
                font-weight: 600;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #F1F5F9;
            }
            
            /* 按钮 */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #EF4444, stop:1 #DC2626);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #DC2626, stop:1 #B91C1C);
            }
            
            QPushButton:pressed {
                background: #991B1B;
            }
            
            QPushButton[objectName="secondaryButton"] {
                background-color: white;
                color: #475569;
                border: 2px solid #E2E8F0;
            }
            
            QPushButton[objectName="secondaryButton"]:hover {
                border-color: #CBD5E1;
                background-color: #F8FAFC;
            }
            
            /* 输入框 */
            QLineEdit, QTextEdit {
                background-color: white;
                border: 2px solid #E2E8F0;
                border-radius: 8px;
                padding: 8px 12px;
                color: #0F172A;
            }
            
            QLineEdit:focus, QTextEdit:focus {
                border-color: #EF4444;
            }
            
            /* 下拉框 */
            QComboBox {
                background-color: white;
                border: 2px solid #E2E8F0;
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 120px;
            }
            
            QComboBox:hover {
                border-color: #CBD5E1;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            
            QComboBox QAbstractItemView {
                background-color: white;
                border: 2px solid #E2E8F0;
                border-radius: 8px;
                selection-background-color: #FEE2E2;
                outline: none;
            }
            
            /* 复选框 */
            QCheckBox {
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #E2E8F0;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                background-color: #EF4444;
                border-color: #EF4444;
            }
            
            /* 进度条 */
            QProgressBar {
                border: none;
                border-radius: 6px;
                background-color: #F1F5F9;
                text-align: center;
                color: #475569;
                font-weight: 600;
                height: 20px;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #EF4444, stop:1 #DC2626);
                border-radius: 6px;
            }
            
            /* 分组框 */
            QGroupBox {
                background-color: white;
                border: 2px solid #E2E8F0;
                border-radius: 12px;
                margin-top: 16px;
                padding-top: 20px;
                font-weight: 600;
                font-size: 10pt;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 12px;
                color: #0F172A;
            }
            
            /* 滚动条 */
            QScrollBar:vertical {
                background-color: #F8FAFC;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #CBD5E1;
                border-radius: 6px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #94A3B8;
            }
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置应用程序字体
    font = QFont("Microsoft YaHei UI", 9)
    app.setFont(font)
    
    window = ModernYouTubeDownloader()
    window.show()
    
    sys.exit(app.exec_())
```

---

## 💡 额外优化建议

### 1. 添加图标
```python
# 使用 QtAwesome 库添加图标
pip install QtAwesome

import qtawesome as qta

# 在按钮上添加图标
parse_btn.setIcon(qta.icon('fa5s.search', color='white'))
download_btn.setIcon(qta.icon('fa5s.download', color='white'))
```

### 2. 添加阴影效果
```python
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor

def add_shadow(widget):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(15)
    shadow.setXOffset(0)
    shadow.setYOffset(2)
    shadow.setColor(QColor(0, 0, 0, 30))
    widget.setGraphicsEffect(shadow)

# 使用
add_shadow(some_widget)
```

### 3. 添加动画
```python
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve

def animate_button(button):
    animation = QPropertyAnimation(button, b"geometry")
    animation.setDuration(200)
    animation.setEasingCurve(QEasingCurve.OutCubic)
    # 设置动画参数
    animation.start()
```

### 4. 使用无边框窗口
```python
self.setWindowFlags(Qt.FramelessWindowHint)
self.setAttribute(Qt.WA_TranslucentBackground)

# 添加自定义标题栏
```

---

## 📚 参考资源

- **Qt官方文档**: https://doc.qt.io/qt-5/stylesheet.html
- **QtAwesome图标库**: https://github.com/spyder-ide/qtawesome
- **QSS示例**: https://qss-stock.devsecstudio.com/

---

## ✅ 实施步骤

1. **复制样式代码** - 将上面的 QSS 代码复制到你的项目中
2. **应用样式** - 使用 `setStyleSheet()` 方法应用样式
3. **调整颜色** - 根据喜好调整颜色变量
4. **添加图标** - 安装 QtAwesome 并添加图标
5. **测试效果** - 运行程序查看效果
6. **微调细节** - 根据实际效果调整间距、圆角等

---

**祝你的 PyQt5 应用界面焕然一新！🎉**
