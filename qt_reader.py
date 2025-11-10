import sys
import os
import json
import chardet
import keyboard
from PyQt6.QtGui import QTextOption
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton,
    QColorDialog, QHBoxLayout, QTextEdit, QAbstractSlider, QFontDialog,
    QComboBox, QCheckBox, QMessageBox, QListWidget, QSplitter
)
from PyQt6.QtGui import QFont, QMouseEvent, QKeyEvent, QResizeEvent
from PyQt6.QtCore import Qt, QPoint, QTimer
import re

# --- 配置加载和存储辅助 ---

CONFIG_PATH = "config.json"
CACHE_PATH = "encoding_cache.json"

def load_config():
    """读取 JSON 配置文件，并为新选项提供默认值"""
    default_config = {
        "file_path": "novel.txt",
        "font_family": "Microsoft YaHei",
        "font_size": 10,
        "font_color": "#E0E0E0",
        "background_color": "transparent",
        "window_width": 500,
        "window_height": 300,
        "window_x": 100,
        "window_y": 100,
        "code": "utf-8",
        "chinese_fill_chars": ["★", "☆", "※"],
        "auto_font_color": True,
        "window_opacity": 0.9,
        "show_catalog": False,
        "catalog_width": 200,
        "left_click_mode": "move",  # "move" 或 "page"
        "line_scroll_lines": 4,
        "reading_progress": {}
    }

    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                # 合并默认配置，确保所有键都存在
                for key, value in default_config.items():
                    config.setdefault(key, value)
                return config
        else:
            return default_config
    except Exception as e:
        print(f"加载配置失败: {e}，使用默认配置")
        return default_config

def save_config(config):
    """保存配置到JSON文件"""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存配置失败: {e}")

def get_file_encoding(file_path):
    """使用 chardet 检测文件编码并缓存"""
    cache = {}
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as cache_file:
                cache = json.load(cache_file)
        except:
            cache = {}

    try:
        file_mtime = os.path.getmtime(file_path)
        if file_path in cache and cache[file_path].get('mtime') == file_mtime:
            return cache[file_path]['encoding']
    except FileNotFoundError:
        print(f"错误: 文本文件 '{file_path}' 未找到。")
        return 'utf-8'

    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'

            cache[file_path] = {'encoding': encoding, 'mtime': file_mtime}
            with open(CACHE_PATH, 'w', encoding='utf-8') as cache_file:
                json.dump(cache, cache_file, ensure_ascii=False, indent=4)
            return encoding
    except Exception as e:
        print(f"检测编码失败: {e}")
        return 'utf-8'

def calculate_luminance(color_hex):
    """计算颜色的亮度（0-1之间），用于确定字体颜色应该用黑色还是白色"""
    if color_hex.lower() == "transparent":
        return 0.5

    if color_hex.startswith('#'):
        color_hex = color_hex[1:]

    try:
        r = int(color_hex[0:2], 16) / 255.0
        g = int(color_hex[2:4], 16) / 255.0
        b = int(color_hex[4:6], 16) / 255.0
    except:
        return 0.5

    # 相对亮度计算
    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4

    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return luminance

def get_contrast_color(color_hex):
    """根据背景色返回对比度最高的字体颜色（黑色或白色）"""
    luminance = calculate_luminance(color_hex)
    return "#000000" if luminance > 0.5 else "#FFFFFF"

# --- 设置窗口 ---

class SettingsWindow(QWidget):
    def __init__(self, parent):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.main_window = parent
        self.setWindowTitle("阅读器设置")
        self.setFixedSize(400, 420)

        # 设置窗口样式
        self.setStyleSheet("""
            QWidget {
                background-color: #F5F5F5;
                color: #333333;
            }
            QLabel {
                color: #333333;
                font-size: 11pt;
            }
            QPushButton {
                background-color: #FFFFFF;
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #E8E8E8;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background-color: #D0D0D0;
            }
            QComboBox {
                background-color: #FFFFFF;
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 10pt;
            }
            QComboBox:hover {
                border: 1px solid #999999;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #333333;
                selection-background-color: #4A90E2;
                selection-color: #FFFFFF;
            }
            QCheckBox {
                color: #333333;
                font-size: 10pt;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #999999;
            }
            QCheckBox::indicator:checked {
                background-color: #4A90E2;
                border: 1px solid #4A90E2;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # 字体设置
        font_layout = QHBoxLayout()
        font_label = QLabel("字体:")
        font_label.setMinimumWidth(90)
        font_layout.addWidget(font_label)

        self.font_combo = QComboBox()
        self.font_combo.addItems(["Microsoft YaHei", "SimHei", "KaiTi", "SimSun", "FangSong",
                                   "Arial", "Times New Roman", "Courier New"])
        self.font_combo.setCurrentText(self.main_window.font_family)
        self.font_combo.currentTextChanged.connect(self.change_font_family)
        font_layout.addWidget(self.font_combo)

        self.font_btn = QPushButton("更多字体")
        self.font_btn.clicked.connect(self.choose_font)
        font_layout.addWidget(self.font_btn)
        layout.addLayout(font_layout)

        # 字体大小设置
        size_layout = QHBoxLayout()
        size_label = QLabel("字体大小:")
        size_label.setMinimumWidth(90)
        size_layout.addWidget(size_label)

        self.size_btn_smaller = QPushButton("−")
        self.size_btn_smaller.setFixedWidth(40)
        self.size_btn_smaller.clicked.connect(lambda: self.main_window.update_font_size(-1))
        size_layout.addWidget(self.size_btn_smaller)

        self.size_label = QLabel(str(self.main_window.font_size))
        self.size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.size_label.setFixedWidth(40)
        self.size_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        size_layout.addWidget(self.size_label)

        self.size_btn_larger = QPushButton("+")
        self.size_btn_larger.setFixedWidth(40)
        self.size_btn_larger.clicked.connect(lambda: self.main_window.update_font_size(1))
        size_layout.addWidget(self.size_btn_larger)
        size_layout.addStretch()
        layout.addLayout(size_layout)

        # 背景颜色设置
        bg_layout = QHBoxLayout()
        bg_label = QLabel("背景颜色:")
        bg_label.setMinimumWidth(90)
        bg_layout.addWidget(bg_label)

        self.bg_btn = QPushButton("设置背景色")
        self.bg_btn.clicked.connect(self.choose_bg_color)
        bg_layout.addWidget(self.bg_btn)

        self.bg_show = QLabel()
        self.bg_show.setFixedSize(60, 25)
        self.bg_show.setStyleSheet("border: 1px solid #999999; border-radius: 3px;")
        bg_layout.addWidget(self.bg_show)

        self.transparent_btn = QPushButton("透明")
        self.transparent_btn.clicked.connect(self.set_transparent_bg)
        bg_layout.addWidget(self.transparent_btn)
        layout.addLayout(bg_layout)

        # 字体颜色设置
        font_color_layout = QHBoxLayout()
        font_color_label = QLabel("字体颜色:")
        font_color_label.setMinimumWidth(90)
        font_color_layout.addWidget(font_color_label)

        self.font_color_btn = QPushButton("设置字体颜色")
        self.font_color_btn.clicked.connect(self.choose_font_color)
        font_color_layout.addWidget(self.font_color_btn)

        self.font_color_show = QLabel()
        self.font_color_show.setFixedSize(60, 25)
        self.font_color_show.setStyleSheet("border: 1px solid #999999; border-radius: 3px;")
        font_color_layout.addWidget(self.font_color_show)
        layout.addLayout(font_color_layout)

        # 自动字体颜色开关
        auto_color_layout = QHBoxLayout()
        self.auto_color_checkbox = QCheckBox("自动调整字体颜色（根据背景色）")
        self.auto_color_checkbox.setChecked(self.main_window.config.get('auto_font_color', True))
        self.auto_color_checkbox.stateChanged.connect(self.toggle_auto_font_color)
        auto_color_layout.addWidget(self.auto_color_checkbox)
        layout.addLayout(auto_color_layout)

        # 显示目录开关
        catalog_layout = QHBoxLayout()
        self.catalog_checkbox = QCheckBox("显示章节目录")
        self.catalog_checkbox.setChecked(self.main_window.config.get('show_catalog', False))
        self.catalog_checkbox.stateChanged.connect(self.toggle_catalog)
        catalog_layout.addWidget(self.catalog_checkbox)
        layout.addLayout(catalog_layout)

        # 左键模式选择
        left_click_layout = QHBoxLayout()
        left_click_label = QLabel("左键点击:")
        left_click_label.setMinimumWidth(90)
        left_click_layout.addWidget(left_click_label)

        self.left_click_combo = QComboBox()
        self.left_click_combo.addItems(["移动窗口", "翻页"])
        current_mode = self.main_window.config.get('left_click_mode', 'move')
        self.left_click_combo.setCurrentIndex(0 if current_mode == 'move' else 1)
        self.left_click_combo.currentTextChanged.connect(self.change_left_click_mode)
        left_click_layout.addWidget(self.left_click_combo)
        left_click_layout.addStretch()
        layout.addLayout(left_click_layout)

        # 透明度设置
        transparency_layout = QHBoxLayout()
        transparency_label = QLabel("窗口透明度:")
        transparency_label.setMinimumWidth(90)
        transparency_layout.addWidget(transparency_label)

        self.transparency_slider = QComboBox()
        self.transparency_slider.addItems(["不透明", "10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%"])
        current_opacity = self.main_window.config.get('window_opacity', 0.9)
        opacity_index = int((1.0 - current_opacity) * 10)
        if opacity_index < self.transparency_slider.count():
            self.transparency_slider.setCurrentIndex(opacity_index)
        self.transparency_slider.currentTextChanged.connect(self.change_transparency)
        transparency_layout.addWidget(self.transparency_slider)
        transparency_layout.addStretch()
        layout.addLayout(transparency_layout)

        # 帮助按钮
        help_layout = QHBoxLayout()
        help_btn = QPushButton("快捷键帮助")
        help_btn.clicked.connect(self.show_help)
        help_layout.addWidget(help_btn)
        help_layout.addStretch()
        layout.addLayout(help_layout)

        layout.addStretch()
        self.setLayout(layout)
        self._update_color_previews()

    def show_help(self):
        """显示快捷键帮助"""
        help_text = """
<h3>快捷键说明</h3>

<h4>鼠标操作：</h4>
<p>
• <b>左键点击</b>：移动窗口或翻页（可在设置中切换）<br>
• <b>右键拖动</b>：移动窗口<br>
• <b>中键拖动</b>：调整窗口大小
</p>

<h4>键盘快捷键：</h4>
<p>
• <b>↓ 下箭头</b>：下一页<br>
• <b>↑ 上箭头</b>：上一页<br>
• <b>Alt + ↑</b>：增大字体<br>
• <b>Alt + ↓</b>：减小字体<br>
• <b>Ctrl + S</b>：打开/关闭设置窗口<br>
• <b>Ctrl + M</b>：最小化窗口<br>
• <b>Ctrl + D</b>：显示/隐藏目录<br>
• <b>Ctrl + Alt</b>：暂停/恢复全局快捷键<br>
• <b>ESC</b>：关闭窗口
</p>

<h4>提示：</h4>
<p>
• 右键始终可以移动窗口<br>
• 无论左键设置为何种模式，右键拖动功能不受影响
</p>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("快捷键帮助")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.exec()

    def choose_font(self):
        """打开字体选择对话框"""
        font, ok = QFontDialog.getFont(QFont(self.main_window.font_family, self.main_window.font_size), self)
        if ok:
            self.main_window.set_font_family(font.family())
            self.main_window.update_font_size_direct(font.pointSize())
            self.font_combo.setCurrentText(font.family())
            self.size_label.setText(str(font.pointSize()))

    def change_font_family(self, font_family):
        """改变字体家族"""
        self.main_window.set_font_family(font_family)

    def change_transparency(self, transparency_text):
        """改变窗口透明度"""
        transparency_map = {
            "不透明": 1.0,
            "10%": 0.9,
            "20%": 0.8,
            "30%": 0.7,
            "40%": 0.6,
            "50%": 0.5,
            "60%": 0.4,
            "70%": 0.3,
            "80%": 0.2,
            "90%": 0.1
        }
        opacity = transparency_map.get(transparency_text, 0.9)
        self.main_window.setWindowOpacity(opacity)
        self.main_window.config['window_opacity'] = opacity
        save_config(self.main_window.config)

    def change_left_click_mode(self, mode_text):
        """改变左键点击模式"""
        mode = 'move' if mode_text == "移动窗口" else 'page'
        self.main_window.config['left_click_mode'] = mode
        save_config(self.main_window.config)

    def toggle_auto_font_color(self, state):
        """切换自动字体颜色功能"""
        auto_enabled = state == Qt.CheckState.Checked.value
        self.main_window.config['auto_font_color'] = auto_enabled
        self.main_window.auto_font_color = auto_enabled

        if auto_enabled:
            self.main_window.auto_adjust_font_color()

        save_config(self.main_window.config)

    def toggle_catalog(self, state):
        """切换目录显示"""
        show_catalog = state == Qt.CheckState.Checked.value
        self.main_window.toggle_catalog_panel(show_catalog)

    def choose_bg_color(self):
        """选择背景颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name()
            self.main_window.set_background_color(hex_color)
            self._update_color_previews()

    def set_transparent_bg(self):
        """设置背景为透明"""
        self.main_window.set_background_color("transparent")
        self._update_color_previews()

    def choose_font_color(self):
        """选择字体颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name()
            self.main_window.set_font_color(hex_color)
            self._update_color_previews()

    def _update_color_previews(self):
        """更新设置窗口中的颜色预览小方块"""
        bg_color = self.main_window.config.get('background_color', 'transparent')
        if bg_color.lower() == 'transparent':
            bg_style = "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #E0E0E0, stop:1 #FFFFFF); border: 1px solid #999999; border-radius: 3px;"
        else:
            bg_style = f"background-color: {bg_color}; border: 1px solid #999999; border-radius: 3px;"
        self.bg_show.setStyleSheet(bg_style)

        font_color = self.main_window.config.get('font_color', '#E0E0E0')
        font_style = f"background-color: {font_color}; border: 1px solid #999999; border-radius: 3px;"
        self.font_color_show.setStyleSheet(font_style)

    def showEvent(self, event):
        """窗口显示时，确保数据是最新的"""
        self._update_color_previews()
        self.size_label.setText(str(self.main_window.font_size))
        self.font_combo.setCurrentText(self.main_window.font_family)
        self.auto_color_checkbox.setChecked(self.main_window.config.get('auto_font_color', True))
        self.catalog_checkbox.setChecked(self.main_window.config.get('show_catalog', False))
        current_mode = self.main_window.config.get('left_click_mode', 'move')
        self.left_click_combo.setCurrentIndex(0 if current_mode == 'move' else 1)
        super().showEvent(event)


# --- 主阅读窗口 ---

class ReaderWindow(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self._load_variables_from_config()

        # 初始化状态变量
        self.current_scroll_value = 0
        self.is_monitoring_active = False
        self.auto_font_color = self.config.get('auto_font_color', True)
        self.chapters = []  # 章节列表

        # 拖动和调整大小标志
        self._is_dragging = False
        self._is_resizing = False
        self._drag_position = QPoint()
        self._resize_start_pos = QPoint()
        self._resize_start_geom = None

        # 设置窗口属性
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setGeometry(self.window_x, self.window_y, self.window_width, self.window_height)
        self.setWindowOpacity(self.config.get('window_opacity', 0.9))

        # 字体对象
        self.font = QFont(self.font_family, self.font_size)

        # 创建主布局
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 创建分隔器
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # 创建目录面板
        self.catalog_widget = QWidget()
        catalog_layout = QVBoxLayout(self.catalog_widget)
        catalog_layout.setContentsMargins(5, 5, 5, 5)

        catalog_title = QLabel("章节目录")
        catalog_title.setStyleSheet("font-weight: bold; font-size: 12pt; color: #333333;")
        catalog_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        catalog_layout.addWidget(catalog_title)

        self.catalog_list = QListWidget()
        self.catalog_list.setStyleSheet("""
            QListWidget {
                background-color: #F8F8F8;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                font-size: 10pt;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #E0E0E0;
            }
            QListWidget::item:hover {
                background-color: #E8E8E8;
            }
            QListWidget::item:selected {
                background-color: #4A90E2;
                color: white;
            }
        """)
        self.catalog_list.itemClicked.connect(self.jump_to_chapter)
        catalog_layout.addWidget(self.catalog_list)

        self.catalog_widget.setStyleSheet("background-color: #F5F5F5;")
        self.catalog_widget.setFixedWidth(self.config.get('catalog_width', 200))

        # 创建阅读区域容器
        self.reading_widget = QWidget()
        reading_layout = QVBoxLayout(self.reading_widget)
        reading_layout.setContentsMargins(10, 10, 10, 10)

        # 使用 QTextEdit 组件来显示文本
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.text_edit.setFont(self.font)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_edit.setContentsMargins(0, 0, 0, 0)
        self.text_edit.setFrameShape(QTextEdit.Shape.NoFrame)

        reading_layout.addWidget(self.text_edit)

        # 添加到分隔器
        self.splitter.addWidget(self.catalog_widget)
        self.splitter.addWidget(self.reading_widget)

        # 设置分隔器样式
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #CCCCCC;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #999999;
            }
        """)

        self.main_layout.addWidget(self.splitter)
        self.setLayout(self.main_layout)

        # 应用背景和字体颜色样式
        self._apply_stylesheet()

        # 标题栏按钮
        self._create_title_buttons()

        # 加载文本文件内容
        self.encoding = get_file_encoding(self.file_path)
        self.full_text_content = self._load_text()
        self._extract_chapters()
        self._load_progress()

        # 初始化显示文本
        self._show_current_page()

        # 初始化目录显示状态
        if not self.config.get('show_catalog', False):
            self.catalog_widget.hide()

        # 创建设置窗口实例（初始隐藏）
        self.settings_window = SettingsWindow(self)

        # 自动保存定时器
        self.save_timer = QTimer(self)
        self.save_timer.timeout.connect(self._auto_save_progress)
        self.save_timer.start(5000)  # 每5秒自动保存一次

        # 绑定键盘全局监控
        self.toggle_all_monitoring()

    def _create_title_buttons(self):
        """创建标题栏按钮（最小化、设置、关闭）"""
        button_style = """
            QPushButton {
                background-color: rgba(0, 0, 0, 0.3);
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 0.6);
            }
        """

        # 目录按钮
        self.catalog_button = QPushButton("☰", self)
        self.catalog_button.setFixedSize(25, 25)
        self.catalog_button.setStyleSheet(button_style + "font-size: 14px;")
        self.catalog_button.clicked.connect(lambda: self.toggle_catalog_panel())
        self.catalog_button.setToolTip("显示/隐藏目录 (Ctrl+D)")

        # 最小化按钮
        self.minimize_button = QPushButton("−", self)
        self.minimize_button.setFixedSize(25, 25)
        self.minimize_button.setStyleSheet(button_style + "font-size: 14px;")
        self.minimize_button.clicked.connect(self.showMinimized)
        self.minimize_button.setToolTip("最小化 (Ctrl+M)")

        # 设置按钮
        self.settings_button = QPushButton("⚙", self)
        self.settings_button.setFixedSize(25, 25)
        self.settings_button.setStyleSheet(button_style + "font-size: 12px;")
        self.settings_button.clicked.connect(self.toggle_settings_window)
        self.settings_button.setToolTip("设置 (Ctrl+S)")

        # 关闭按钮
        self.close_button = QPushButton("×", self)
        self.close_button.setFixedSize(25, 25)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(200, 0, 0, 0.6);
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 0.8);
            }
        """)
        self.close_button.clicked.connect(self.close)
        self.close_button.setToolTip("关闭 (ESC)")

        self._update_title_buttons_position()

    def _update_title_buttons_position(self):
        """更新标题栏按钮位置"""
        margin = 5
        button_width = 25

        self.close_button.move(self.width() - button_width - margin, margin)
        self.settings_button.move(self.width() - 2 * button_width - margin - 2, margin)
        self.minimize_button.move(self.width() - 3 * button_width - margin - 4, margin)
        self.catalog_button.move(self.width() - 4 * button_width - margin - 6, margin)

    def _load_variables_from_config(self):
        """从配置字典加载所有成员变量"""
        self.file_path = self.config.get("file_path", "novel.txt")
        self.file_memo = os.path.splitext(self.file_path)[0] + "_memo.txt"
        self.font_family = self.config.get("font_family", "Microsoft YaHei")
        self.font_size = self.config.get("font_size", 10)
        self.font_color = self.config.get("font_color", "#E0E0E0")
        self.background_color = self.config.get("background_color", "transparent")
        self.window_width = self.config.get("window_width", 500)
        self.window_height = self.config.get("window_height", 300)
        self.window_x = self.config.get("window_x", 100)
        self.window_y = self.config.get("window_y", 100)
        self.config.setdefault('reading_progress', {})
        line_scroll_default = self.config.get("line_scroll_lines", 4)
        try:
            self.lines_per_scroll = max(1, int(line_scroll_default))
        except (ValueError, TypeError):
            self.lines_per_scroll = 4
        self.config['line_scroll_lines'] = self.lines_per_scroll

    def _load_text(self):
        """读取整个文本文件的内容到一个字符串"""
        try:
            if not os.path.exists(self.file_path):
                return f"错误：文件 '{self.file_path}' 不存在。\n\n请在配置文件中设置正确的文件路径。"

            with open(self.file_path, encoding=self.encoding, errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"读取文件 '{self.file_path}' 错误: {e}")
            return f"错误：无法加载文本文件。\n{str(e)}"

    def _extract_chapters(self):
        """提取章节信息"""
        self.chapters = []
        self.catalog_list.clear()

        if not self.full_text_content:
            return

        # 常见的章节标题模式
        patterns = [
            r'^第[零一二三四五六七八九十百千0-9]+章\s*.+',
            r'^第[零一二三四五六七八九十百千0-9]+节\s*.+',
            r'^Chapter\s+\d+.+',
            r'^\d+[\s\.、]+.+',
            r'^[零一二三四五六七八九十百千]+[\s、\.]+.+'
        ]

        lines = self.full_text_content.split('\n')
        char_count = 0

        for i, line in enumerate(lines):
            line = line.strip()
            if line:
                # 检查是否匹配章节模式
                for pattern in patterns:
                    if re.match(pattern, line, re.IGNORECASE):
                        self.chapters.append({
                            'title': line,
                            'position': char_count,
                            'line_number': i
                        })
                        self.catalog_list.addItem(line)
                        break

            char_count += len(line) + 1  # +1 for newline

        print(f"找到 {len(self.chapters)} 个章节")

    def jump_to_chapter(self, item):
        """跳转到选中的章节"""
        index = self.catalog_list.row(item)
        if 0 <= index < len(self.chapters):
            chapter = self.chapters[index]

            # 使用QTextCursor定位
            cursor = self.text_edit.textCursor()
            cursor.setPosition(chapter['position'])
            self.text_edit.setTextCursor(cursor)
            self.text_edit.ensureCursorVisible()

            self.current_scroll_value = self.text_edit.verticalScrollBar().value()
            self._save_progress()

    def toggle_catalog_panel(self, show=None):
        """切换目录面板显示"""
        if show is None:
            show = not self.catalog_widget.isVisible()

        if show:
            self.catalog_widget.show()
        else:
            self.catalog_widget.hide()

        self.config['show_catalog'] = show
        save_config(self.config)

    def _apply_stylesheet(self):
        """根据配置的背景和字体颜色统一应用样式"""
        if self.background_color == "transparent":
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setStyleSheet("background-color: transparent;")
            self.reading_widget.setStyleSheet("background-color: transparent;")
            self.text_edit.setStyleSheet(f"color: {self.font_color}; background-color: transparent; border: none;")
        else:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setStyleSheet(f"background-color: {self.background_color};")
            self.reading_widget.setStyleSheet(f"background-color: {self.background_color};")
            self.text_edit.setStyleSheet(f"color: {self.font_color}; background-color: {self.background_color}; border: none;")

    def _is_background_black(self):
        """判断背景颜色是否为纯黑色"""
        color_value = (self.background_color or "").strip().lower()
        if color_value in {"#000000", "black"}:
            return True
        if color_value.startswith("rgb"):
            digits = [int(value) for value in re.findall(r'\d+', color_value)]
            if len(digits) >= 3 and all(value == 0 for value in digits[:3]):
                if len(digits) < 4 or digits[3] > 0:
                    return True
        return False

    def _start_window_drag(self, event: QMouseEvent):
        """开始窗口拖动"""
        self._is_dragging = True
        self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _reset_drag_state_if_needed(self):
        """背景不满足要求时，立即停止拖动"""
        if not self._is_background_black():
            self._is_dragging = False

    def auto_adjust_font_color(self):
        """根据背景色自动调整字体颜色"""
        if not self.auto_font_color:
            return

        if self.background_color != "transparent":
            contrast_color = get_contrast_color(self.background_color)
            self.set_font_color(contrast_color, save=False)

    def _show_current_page(self):
        """将全部文本加载到QTextEdit，并滚动到当前保存的位置"""
        if not self.full_text_content:
            return

        self.text_edit.setText(self.full_text_content)

        # 使用QTimer延迟设置滚动位置，确保文本已经渲染
        QTimer.singleShot(50, self._restore_scroll_position)

    def _restore_scroll_position(self):
        """恢复滚动位置"""
        max_scroll_value = self.text_edit.verticalScrollBar().maximum()
        self.current_scroll_value = max(0, min(self.current_scroll_value, max_scroll_value))
        self.text_edit.verticalScrollBar().setValue(self.current_scroll_value)

    def _scroll_lines(self, line_count: int):
        """按指定行数滚动文本"""
        if line_count == 0:
            return
        scrollbar = self.text_edit.verticalScrollBar()
        line_height = self.text_edit.fontMetrics().lineSpacing()
        delta = line_height * line_count
        new_value = scrollbar.value() + delta
        clamped = max(scrollbar.minimum(), min(scrollbar.maximum(), new_value))
        scrollbar.setValue(clamped)
        self.current_scroll_value = scrollbar.value()

    def next_page(self, *args):
        """翻到下一页"""
        self._scroll_lines(self.lines_per_scroll)

    def prev_page(self):
        """翻到上一页"""
        self._scroll_lines(-self.lines_per_scroll)

    def _auto_save_progress(self):
        """自动保存进度（由定时器调用）"""
        self.current_scroll_value = self.text_edit.verticalScrollBar().value()
        self._save_progress()

    def _save_progress(self):
        """保存当前滚动位置到memo文件"""
        try:
            with open(self.file_memo, "w", encoding='utf-8') as f:
                f.write(str(self.current_scroll_value))
        except Exception as e:
            print(f"保存进度时出错: {e}")
        progress_map = self.config.setdefault('reading_progress', {})
        progress_map[self.file_path] = self.current_scroll_value
        save_config(self.config)

    def _load_progress(self):
        """从memo文件加载上次的滚动位置"""
        progress_map = self.config.get('reading_progress', {})
        saved_value = progress_map.get(self.file_path)
        if isinstance(saved_value, int):
            self.current_scroll_value = saved_value
            return
        if isinstance(saved_value, str) and saved_value.isdigit():
            self.current_scroll_value = int(saved_value)
            return

        if os.path.exists(self.file_memo):
            try:
                with open(self.file_memo, "r", encoding='utf-8') as f:
                    saved = f.readline().strip()
                    if saved.isdigit():
                        self.current_scroll_value = int(saved)
                        progress_map[self.file_path] = self.current_scroll_value
                        save_config(self.config)
            except Exception as e:
                print(f"加载进度时出错: {e}")

    def update_font_size(self, delta):
        """调整字体大小"""
        self.font_size = max(6, min(72, self.font_size + delta))
        self.font.setPointSize(self.font_size)
        self.text_edit.setFont(self.font)
        self.config['font_size'] = self.font_size

        if hasattr(self, 'settings_window') and self.settings_window.isVisible():
            self.settings_window.size_label.setText(str(self.font_size))

    def update_font_size_direct(self, new_size):
        """直接设置字体大小"""
        self.font_size = max(6, min(72, new_size))
        self.font.setPointSize(self.font_size)
        self.text_edit.setFont(self.font)
        self.config['font_size'] = self.font_size

        if hasattr(self, 'settings_window') and self.settings_window.isVisible():
            self.settings_window.size_label.setText(str(self.font_size))

    def set_font_family(self, font_family):
        """设置字体家族"""
        self.font_family = font_family
        self.config['font_family'] = font_family
        self.font.setFamily(font_family)
        self.text_edit.setFont(self.font)
        save_config(self.config)

    def set_background_color(self, color, save=True):
        """设置背景颜色并更新样式"""
        self.background_color = color
        self.config['background_color'] = color

        if self.auto_font_color:
            self.auto_adjust_font_color()

        self._apply_stylesheet()
        self._reset_drag_state_if_needed()
        if save:
            save_config(self.config)

    def set_font_color(self, color, save=True):
        """设置字体颜色并更新样式"""
        self.font_color = color
        self.config['font_color'] = color
        self._apply_stylesheet()
        if save:
            save_config(self.config)

    def start_all_monitoring(self):
        """启动所有键盘热键监控"""
        if not self.is_monitoring_active:
            self.is_monitoring_active = True
            try:
                keyboard.add_hotkey('down', self.next_page, suppress=True)
                keyboard.add_hotkey('up', self.prev_page, suppress=True)
                keyboard.add_hotkey('alt+up', lambda: self.update_font_size(1), suppress=True)
                keyboard.add_hotkey('alt+down', lambda: self.update_font_size(-1), suppress=True)
                keyboard.add_hotkey('ctrl+s', self.toggle_settings_window, suppress=True)
                keyboard.add_hotkey('ctrl+m', self.showMinimized, suppress=True)
                keyboard.add_hotkey('ctrl+d', lambda: self.toggle_catalog_panel(), suppress=True)
                print("全局监控已启用")
            except Exception as e:
                print(f"启动全局监控失败: {e}")

    def stop_all_monitoring(self):
        """停止所有键盘热键监控"""
        if self.is_monitoring_active:
            self.is_monitoring_active = False
            try:
                keyboard.remove_all_hotkeys()
                keyboard.add_hotkey('ctrl+alt', self.toggle_all_monitoring)
                print("全局监控已暂停")
            except Exception as e:
                print(f"停止全局监控失败: {e}")

    def toggle_all_monitoring(self):
        """切换所有监控的开关状态"""
        if self.is_monitoring_active:
            self.stop_all_monitoring()
        else:
            self.start_all_monitoring()

    def toggle_settings_window(self):
        """切换设置窗口的显示/隐藏状态"""
        if self.settings_window.isVisible():
            self.settings_window.hide()
        else:
            # 将设置窗口定位在主窗口附近
            self.settings_window.move(self.x() + 50, self.y() + 50)
            self.settings_window.show()
            self.settings_window.raise_()
            self.settings_window.activateWindow()

    # --- 事件处理方法 ---
    def resizeEvent(self, event: QResizeEvent):
        """窗口大小改变事件"""
        self._update_title_buttons_position()
        self.current_scroll_value = self.text_edit.verticalScrollBar().value()
        super().resizeEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
       
        """鼠标按下事件"""
        # 检查是否点击在标题栏按钮区域
        button_rect = self.close_button.geometry()
        button_rect = button_rect.united(self.settings_button.geometry())
        button_rect = button_rect.united(self.minimize_button.geometry())
        button_rect = button_rect.united(self.catalog_button.geometry())

        if button_rect.contains(event.position().toPoint()):
            super().mousePressEvent(event)
            return

        can_drag_window = self._is_background_black()

        if event.button() == Qt.MouseButton.LeftButton:
            left_click_mode = self.config.get('left_click_mode', 'move')
            if left_click_mode == 'move':
                if can_drag_window:
                    self._start_window_drag(event)
                event.accept()
                return
            else:
                self.next_page()
                event.accept()
                return
        elif event.button() == Qt.MouseButton.RightButton:
            if can_drag_window:
                self._start_window_drag(event)
            event.accept()
            return
        elif event.button() == Qt.MouseButton.MiddleButton:
            self._is_resizing = True
            self._resize_start_pos = event.globalPosition().toPoint()
            self._resize_start_geom = self.geometry()
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件"""
        can_drag_window = self._is_background_black()

        # 左键或右键拖动窗口（仅在背景为黑色时允许）
        if self._is_dragging:
            if can_drag_window and (event.buttons() & Qt.MouseButton.LeftButton or event.buttons() & Qt.MouseButton.RightButton):
                self.move(event.globalPosition().toPoint() - self._drag_position)
            else:
                self._is_dragging = False
        # 中键调整大小 - 保留原有功能
        elif self._is_resizing and event.buttons() & Qt.MouseButton.MiddleButton:
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            new_geom = self._resize_start_geom.translated(0, 0)
            new_geom.setWidth(max(200, self._resize_start_geom.width() + delta.x()))
            new_geom.setHeight(max(100, self._resize_start_geom.height() + delta.y()))
            self.setGeometry(new_geom)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton or event.button() == Qt.MouseButton.RightButton:
            self._is_dragging = False
        elif event.button() == Qt.MouseButton.MiddleButton:
            self._is_resizing = False
        event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        """键盘按下事件"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        event.accept()

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存窗口配置
        self.config['window_width'] = self.width()
        self.config['window_height'] = self.height()
        self.config['window_x'] = self.x()
        self.config['window_y'] = self.y()
        self.config['font_size'] = self.font_size
        self.config['font_family'] = self.font_family

        # 保存目录宽度
        if self.catalog_widget.isVisible():
            self.config['catalog_width'] = self.catalog_widget.width()

        # 保存阅读进度
        self.current_scroll_value = self.text_edit.verticalScrollBar().value()
        self._save_progress()

        # 保存配置文件
        save_config(self.config)

        # 清理资源
        self.save_timer.stop()
        self.stop_all_monitoring()
        keyboard.unhook_all()

        print("窗口关闭，配置和进度已保存。")
        event.accept()


# --- 程序入口 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置应用程序属性
    app.setApplicationName("文本阅读器")
    app.setOrganizationName("TextReader")

    config = load_config()
    window = ReaderWindow(config)
    window.show()

    sys.exit(app.exec())
