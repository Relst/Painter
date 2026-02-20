import sys
from PyQt6.QtCore import Qt, QPoint, QRectF
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QPen, QBrush, QLinearGradient
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QToolButton, QButtonGroup, QTabWidget,
    QFrame, QSizePolicy, QScrollArea, QPushButton,
    QColorDialog, QSplitter, QSlider
)


# ---------------- Reusable small input box ----------------

def make_value_box(text: str, suffix: str = ""):
    box = QFrame()
    box.setFixedHeight(28)
    box.setStyleSheet("""
        QFrame {
            background-color: #2a2a2a;
            border: 1px solid #1f1f1f;
            border-radius: 4px;
        }
        QFrame:hover {
            background-color: #2d2d2d;
            border: 1px solid #252525;
        }
    """)
    h = QHBoxLayout(box)
    h.setContentsMargins(8, 0, 8, 0)
    h.setSpacing(4)

    label = QLabel(text)
    label.setStyleSheet("color: #f0f0f0; font-size: 11px; font-weight: 500;")
    h.addWidget(label)

    if suffix:
        s = QLabel(suffix)
        s.setStyleSheet("color: #7a7a7a; font-size: 10px;")
        h.addWidget(s)

    h.addStretch()
    return box, label


# ---------------- Color swatch with picker ----------------

class ColorSwatch(QFrame):
    def __init__(self, initial_color: QColor, border_style: str, parent=None):
        super().__init__(parent)
        self._color = initial_color
        self.setFixedSize(28, 28)
        self._border_style = border_style
        self._update_style()

    def _update_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._color.name()};
                {self._border_style}
                border-radius: 3px;
            }}
            QFrame:hover {{
                border-width: 3px;
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            color = QColorDialog.getColor(self._color, self, "Select Color")
            if color.isValid():
                self._color = color
                self._update_style()
        super().mousePressEvent(event)


# ---------------- Canvas with checkerboard pattern ----------------

class CanvasArea(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background-color: #3a3a3a;
                border: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # Window-like canvas container with shadow effect
        canvas_window = QFrame()
        canvas_window.setStyleSheet("""
            QFrame {
                background-color: #4a4a4a;
                border-radius: 8px;
                border: 1px solid #262626;
            }
        """)
        canvas_window_layout = QVBoxLayout(canvas_window)
        canvas_window_layout.setContentsMargins(1, 1, 1, 1)
        canvas_window_layout.setSpacing(0)

        # Title bar for canvas
        title_bar = QFrame()
        title_bar.setFixedHeight(28)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: #353535;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
        """)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(10, 0, 10, 0)
        tb_layout.setSpacing(8)

        # Window control dots (macOS style)
        dots_widget = QWidget()
        dots_layout = QHBoxLayout(dots_widget)
        dots_layout.setContentsMargins(0, 0, 0, 0)
        dots_layout.setSpacing(6)

        for color in ["#ff5f56", "#ffbd2e", "#27c93f"]:
            dot = QFrame()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"""
                QFrame {{
                    background-color: {color};
                    border-radius: 5px;
                    border: 1px solid {color};
                }}
            """)
            dots_layout.addWidget(dot)

        tb_layout.addWidget(dots_widget)

        title = QLabel("Untitled-1 @ 100%")
        title.setStyleSheet("color: #d0d0d0; font-size: 11px; font-weight: 500;")
        tb_layout.addWidget(title)
        tb_layout.addStretch()

        canvas_window_layout.addWidget(title_bar)

        # Canvas background with subtle pattern
        canvas_bg = QFrame()
        canvas_bg.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)
        cb_layout = QVBoxLayout(canvas_bg)
        cb_layout.setContentsMargins(20, 20, 20, 20)

        canvas_widget = QWidget()
        canvas_widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #1a1a1a;
            }
        """)
        canvas_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cb_layout.addWidget(canvas_widget)

        canvas_window_layout.addWidget(canvas_bg)
        layout.addWidget(canvas_window)


# ---------------- Tool Button with Icon ----------------

class ToolButton(QToolButton):
    def __init__(self, icon_text, name, shortcut=""):
        super().__init__()
        self.icon_text = icon_text
        self.tool_name = name
        self.shortcut = shortcut

        self.setToolTip(f"{name} ({shortcut})" if shortcut else name)
        self.setCheckable(True)
        self.setFixedSize(48, 48)
        self.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
            }
            QToolButton:hover {
                background-color: #383838;
            }
            QToolButton:checked {
                background-color: #454545;
                border: 2px solid #1473e6;
            }
            QToolButton:pressed {
                background-color: #303030;
            }
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(QColor("#f5f5f5") if self.isChecked() else QColor("#b8b8b8"))
        font = painter.font()
        font.setPixelSize(22)
        font.setBold(True)
        painter.setFont(font)

        rect = self.rect()
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.icon_text)


# ---------------- Toolbar (left) ----------------

class ToolBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(80)
        self.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-right: 1px solid #1a1a1a;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(4)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        tools = [
            ("🖌", "Brush Tool", "B"),
            ("✏", "Pencil Tool", "P"),
            ("🪣", "Bucket Fill", "G"),
            ("⌫", "Eraser Tool", "E"),
            ("✋", "Hand Tool", "H"),
            ("🔍", "Zoom Tool", "Z"),
        ]

        for icon, name, shortcut in tools:
            btn = ToolButton(icon, name, shortcut)
            layout.addWidget(btn)
            self.group.addButton(btn)

        layout.addSpacing(16)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #1a1a1a; max-height: 1px;")
        layout.addWidget(separator)
        layout.addSpacing(16)

        # Color section with gradient background
        color_widget = QFrame()
        color_widget.setStyleSheet("""
            QFrame {
                background-color: #353535;
                border-radius: 8px;
                border: 1px solid #2a2a2a;
            }
        """)
        color_layout = QVBoxLayout(color_widget)
        color_layout.setContentsMargins(10, 10, 10, 10)
        color_layout.setSpacing(6)

        color_label = QLabel("Colors")
        color_label.setStyleSheet("color: #a8a8a8; font-size: 9px; font-weight: bold;")
        color_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color_layout.addWidget(color_label)

        color_container = QWidget()
        color_container.setFixedSize(44, 44)

        self.fg_color = ColorSwatch(
            QColor("#000000"),
            "border: 2px solid #f0f0f0;",
            color_container
        )
        self.fg_color.move(2, 2)

        self.bg_color = ColorSwatch(
            QColor("#ffffff"),
            "border: 2px solid #5a5a5a;",
            color_container
        )
        self.bg_color.move(16, 16)

        color_layout.addWidget(color_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Reset button
        reset_btn = QPushButton("⟲")
        reset_btn.setFixedSize(32, 24)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #1f1f1f;
                border-radius: 4px;
                color: #b8b8b8;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #353535;
                color: #f0f0f0;
            }
        """)
        color_layout.addWidget(reset_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(color_widget)
        layout.addStretch(1)


# ---------------- Tool Options Bar (top) ----------------

class ToolOptionsBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(56)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d3d3d, stop:1 #383838);
                border-bottom: 1px solid #242424;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(20)

        # Tool info section
        tool_info = QWidget()
        tool_info_layout = QHBoxLayout(tool_info)
        tool_info_layout.setContentsMargins(0, 0, 0, 0)
        tool_info_layout.setSpacing(10)

        self.tool_icon = QLabel("🖌")
        self.tool_icon.setStyleSheet("color: #f5f5f5; font-size: 24px;")
        tool_info_layout.addWidget(self.tool_icon)

        self.tool_label = QLabel("Brush Tool")
        self.tool_label.setStyleSheet("""
            color: #f5f5f5;
            font-size: 13px;
            font-weight: bold;
        """)
        tool_info_layout.addWidget(self.tool_label)

        layout.addWidget(tool_info)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet("background-color: #2a2a2a; max-width: 1px;")
        layout.addWidget(sep1)

        # Control section with labels
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(16)

        # Size control
        size_section = QWidget()
        size_layout = QVBoxLayout(size_section)
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.setSpacing(2)

        size_label = QLabel("Size")
        size_label.setStyleSheet("color: #a8a8a8; font-size: 9px; font-weight: bold;")
        size_layout.addWidget(size_label)

        self.size_display, self.size_value = make_value_box("25", "px")
        self.size_display.setFixedWidth(75)
        size_layout.addWidget(self.size_display)

        controls_layout.addWidget(size_section)

        # Hardness control
        hardness_section = QWidget()
        hardness_layout = QVBoxLayout(hardness_section)
        hardness_layout.setContentsMargins(0, 0, 0, 0)
        hardness_layout.setSpacing(2)

        hardness_label = QLabel("Hardness")
        hardness_label.setStyleSheet("color: #a8a8a8; font-size: 9px; font-weight: bold;")
        hardness_layout.addWidget(hardness_label)

        self.hardness_display, self.hardness_value = make_value_box("100", "%")
        self.hardness_display.setFixedWidth(75)
        hardness_layout.addWidget(self.hardness_display)

        controls_layout.addWidget(hardness_section)

        # Opacity control
        opacity_section = QWidget()
        opacity_layout = QVBoxLayout(opacity_section)
        opacity_layout.setContentsMargins(0, 0, 0, 0)
        opacity_layout.setSpacing(2)

        opacity_label = QLabel("Opacity")
        opacity_label.setStyleSheet("color: #a8a8a8; font-size: 9px; font-weight: bold;")
        opacity_layout.addWidget(opacity_label)

        self.opacity_display, self.opacity_value = make_value_box("100", "%")
        self.opacity_display.setFixedWidth(75)
        opacity_layout.addWidget(self.opacity_display)

        controls_layout.addWidget(opacity_section)

        layout.addLayout(controls_layout)
        layout.addStretch(1)

    def update_tool(self, icon, name):
        self.tool_icon.setText(icon)
        self.tool_label.setText(name)


# ---------------- Layer Item ----------------

class LayerItem(QFrame):
    def __init__(self, name="Layer", visible=True, selected=False):
        super().__init__()
        self.setFixedHeight(56)
        bg_color = "#454545" if selected else "#363636"
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid #282828;
                border-radius: 4px;
            }}
            QFrame:hover {{
                background-color: #484848;
                border: 1px solid #2f2f2f;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        vis_btn = QPushButton("👁" if visible else "")
        vis_btn.setFixedSize(24, 24)
        vis_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #b8b8b8;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                color: #ffffff;
                background-color: #4a4a4a;
            }
        """)
        layout.addWidget(vis_btn)

        thumb = QFrame()
        thumb.setFixedSize(40, 40)
        thumb.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #242424;
                border-radius: 3px;
            }
        """)
        layout.addWidget(thumb)

        name_label = QLabel(name)
        name_label.setStyleSheet("""
            color: #f5f5f5;
            font-size: 11px;
            font-weight: 500;
        """)
        layout.addWidget(name_label)

        layout.addStretch()


# ---------------- Layers Panel Content ----------------

class LayersPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar with gradient
        header = QFrame()
        header.setFixedHeight(32)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #353535, stop:1 #2f2f2f);
                border-bottom: 1px solid #1f1f1f;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        header_layout.setSpacing(8)

        title = QLabel("LAYERS")
        title.setStyleSheet("color: #b8b8b8; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(header)

        content = QFrame()
        content.setStyleSheet("""
            QFrame {
                background-color: #323232;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(8)

        # Blend mode and opacity section
        controls = QFrame()
        controls.setFixedHeight(36)
        controls.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #1f1f1f;
                border-radius: 6px;
            }
        """)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(10, 4, 10, 4)
        controls_layout.setSpacing(8)

        mode_label = QLabel("Mode")
        mode_label.setStyleSheet("color: #a8a8a8; font-size: 9px; font-weight: bold;")
        controls_layout.addWidget(mode_label)

        mode_box, _ = make_value_box("Normal", "")
        mode_box.setFixedWidth(90)
        controls_layout.addWidget(mode_box)

        controls_layout.addSpacing(8)

        opacity_label = QLabel("Opacity")
        opacity_label.setStyleSheet("color: #a8a8a8; font-size: 9px; font-weight: bold;")
        controls_layout.addWidget(opacity_label)

        opacity_box, _ = make_value_box("100", "%")
        opacity_box.setFixedWidth(70)
        controls_layout.addWidget(opacity_box)

        controls_layout.addStretch()
        content_layout.addWidget(controls)

        # Layer list with custom scrollbar
        layer_scroll = QScrollArea()
        layer_scroll.setWidgetResizable(True)
        layer_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #282828;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #4a4a4a;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #555555;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        layer_container = QWidget()
        layer_list_layout = QVBoxLayout(layer_container)
        layer_list_layout.setContentsMargins(0, 0, 0, 0)
        layer_list_layout.setSpacing(4)

        layer_list_layout.addWidget(LayerItem("Layer 3", True, True))
        layer_list_layout.addWidget(LayerItem("Layer 2", True, False))
        layer_list_layout.addWidget(LayerItem("Background", True, False))
        layer_list_layout.addStretch()

        layer_scroll.setWidget(layer_container)
        content_layout.addWidget(layer_scroll)

        # Layer controls at bottom
        controls_bottom = QFrame()
        controls_bottom.setFixedHeight(40)
        controls_bottom.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #1f1f1f;
                border-radius: 6px;
            }
        """)
        controls_bottom_layout = QHBoxLayout(controls_bottom)
        controls_bottom_layout.setContentsMargins(6, 6, 6, 6)
        controls_bottom_layout.setSpacing(6)

        btn_style = """
            QPushButton {
                background-color: #343434;
                border: 1px solid #1f1f1f;
                color: #b8b8b8;
                font-size: 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3f3f3f;
                color: #f0f0f0;
                border: 1px solid #2a2a2a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """

        add_btn = QPushButton("+")
        add_btn.setFixedSize(32, 28)
        add_btn.setStyleSheet(btn_style)
        add_btn.setToolTip("New Layer")
        controls_bottom_layout.addWidget(add_btn)

        del_btn = QPushButton("−")
        del_btn.setFixedSize(32, 28)
        del_btn.setStyleSheet(btn_style)
        del_btn.setToolTip("Delete Layer")
        controls_bottom_layout.addWidget(del_btn)

        folder_btn = QPushButton("📁")
        folder_btn.setFixedSize(32, 28)
        folder_btn.setStyleSheet(btn_style)
        folder_btn.setToolTip("New Group")
        controls_bottom_layout.addWidget(folder_btn)

        controls_bottom_layout.addStretch()
        content_layout.addWidget(controls_bottom)

        layout.addWidget(content)


# ---------------- Right Context Window with Protrusion ----------------

class RightContextWindow(QFrame):
    """
    Floating-style panel on the right with a visible protrusion (lip)
    that extends left from the main panel border.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background-color: transparent; }")
        self.setMinimumWidth(330)
        self.setMaximumWidth(450)

        self._hovered = False
        self._hover_animation = 0.0
        self._open = False

        self.protrusion_depth = 20

        from PyQt6.QtCore import QTimer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._animate)
        self.animation_timer.setInterval(16)

        self.setMouseTracking(True)

        # Inner layout with space for the protrusion
        self.inner = QVBoxLayout(self)
        self.inner.setContentsMargins(self.protrusion_depth + 8, 8, 8, 8)
        self.inner.setSpacing(0)

        # Panel frame
        self.panel_frame = QFrame()
        self.panel_frame.setStyleSheet("""
            QFrame {
                background-color: #323232;
                border-radius: 12px;
                border: 1px solid #1a1a1a;
            }
        """)
        panel_layout = QVBoxLayout(self.panel_frame)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        self.inner.addWidget(self.panel_frame)

    def set_open(self, is_open: bool):
        self._open = is_open
        self.update()

    def _animate(self):
        target = 1.0 if self._hovered else 0.0
        speed = 0.2

        if abs(self._hover_animation - target) < 0.01:
            self._hover_animation = target
            self.animation_timer.stop()
        else:
            self._hover_animation += (target - self._hover_animation) * speed

        self.update()

    def mouseMoveEvent(self, event):
        h = self.height()
        bump_h = max(90, int(h * 0.18))
        bump_y = int((h - bump_h) / 2)

        mouse_y = event.pos().y()
        mouse_x = event.pos().x()

        if 0 <= mouse_x <= self.protrusion_depth + 6 and bump_y <= mouse_y <= (bump_y + bump_h):
            if not self._hovered:
                self._hovered = True
                if not self.animation_timer.isActive():
                    self.animation_timer.start()
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            if self._hovered:
                self._hovered = False
                if not self.animation_timer.isActive():
                    self.animation_timer.start()
            self.setCursor(Qt.CursorShape.ArrowCursor)

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        if not self.animation_timer.isActive():
            self.animation_timer.start()
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        h = self.height()
        bump_h = max(90, int(h * 0.18))
        bump_y = int((h - bump_h) / 2)

        mouse_y = event.pos().y()
        mouse_x = event.pos().x()

        if 0 <= mouse_x <= self.protrusion_depth + 6 and bump_y <= mouse_y <= (bump_y + bump_h):
            if hasattr(self.parent(), 'toggle_navigator'):
                self.parent().toggle_navigator()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        bump_h = max(90, int(h * 0.18))
        bump_y = int((h - bump_h) / 2)

        base_protrusion = self.protrusion_depth
        hover_extension = 5
        protrusion = base_protrusion + (hover_extension * self._hover_animation)

        # Colors with gradient for depth
        border_color = QColor("#1a1a1a")
        shadow_color = QColor("#0a0a0a")

        if self._hover_animation > 0:
            border_color = border_color.lighter(100 + int(15 * self._hover_animation))

        # Draw shadow behind the protrusion
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow_color))
        painter.setOpacity(0.4)

        shadow_path = QPainterPath()
        x0 = protrusion
        shadow_offset = 2

        shadow_path.moveTo(x0 + shadow_offset, bump_y + shadow_offset)
        shadow_path.cubicTo(
            x0 + shadow_offset, bump_y + bump_h * 0.1 + shadow_offset,
            x0 - protrusion * 0.6 + shadow_offset, bump_y + bump_h * 0.2 + shadow_offset,
            x0 - protrusion + shadow_offset, bump_y + bump_h * 0.35 + shadow_offset
        )
        shadow_path.lineTo(x0 - protrusion + shadow_offset, bump_y + bump_h * 0.65 + shadow_offset)
        shadow_path.cubicTo(
            x0 - protrusion * 0.6 + shadow_offset, bump_y + bump_h * 0.8 + shadow_offset,
            x0 + shadow_offset, bump_y + bump_h * 0.9 + shadow_offset,
            x0 + shadow_offset, bump_y + bump_h + shadow_offset
        )
        shadow_path.lineTo(x0 + shadow_offset, bump_y + shadow_offset)
        painter.drawPath(shadow_path)

        painter.setOpacity(1.0)

        # Main panel border path with protrusion
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        x0 = protrusion
        radius = 12

        path = QPainterPath()

        # Start at top-left after rounded corner
        path.moveTo(x0 + radius, 6)

        # Top edge
        path.lineTo(w - radius - 6, 6)
        path.quadTo(w - 6, 6, w - 6, 6 + radius)

        # Right edge
        path.lineTo(w - 6, h - radius - 6)
        path.quadTo(w - 6, h - 6, w - radius - 6, h - 6)

        # Bottom edge
        path.lineTo(x0 + radius, h - 6)
        path.quadTo(x0, h - 6, x0, h - radius - 6)

        # Left edge down to protrusion
        path.lineTo(x0, bump_y + bump_h)

        # Bottom curve of protrusion
        path.cubicTo(
            x0, bump_y + bump_h * 0.9,
                x0 - protrusion * 0.6, bump_y + bump_h * 0.8,
                x0 - protrusion, bump_y + bump_h * 0.65
        )

        # Vertical part of protrusion (leftmost edge)
        path.lineTo(x0 - protrusion, bump_y + bump_h * 0.35)

        # Top curve of protrusion
        path.cubicTo(
            x0 - protrusion * 0.6, bump_y + bump_h * 0.2,
            x0, bump_y + bump_h * 0.1,
            x0, bump_y
        )

        # Continue up left edge
        path.lineTo(x0, 6 + radius)
        path.quadTo(x0, 6, x0 + radius, 6)

        painter.drawPath(path)

        # Add gradient highlight on protrusion
        gradient = QLinearGradient(x0 - protrusion, bump_y, x0 - protrusion, bump_y + bump_h)
        gradient.setColorAt(0, QColor("#3a3a3a"))
        gradient.setColorAt(0.5, QColor("#323232"))
        gradient.setColorAt(1, QColor("#2a2a2a"))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)

        fill_path = QPainterPath()
        fill_path.moveTo(x0, bump_y)
        fill_path.cubicTo(
            x0, bump_y + bump_h * 0.1,
                x0 - protrusion * 0.6, bump_y + bump_h * 0.2,
                x0 - protrusion, bump_y + bump_h * 0.35
        )
        fill_path.lineTo(x0 - protrusion, bump_y + bump_h * 0.65)
        fill_path.cubicTo(
            x0 - protrusion * 0.6, bump_y + bump_h * 0.8,
            x0, bump_y + bump_h * 0.9,
            x0, bump_y + bump_h
        )
        fill_path.lineTo(x0, bump_y)
        painter.drawPath(fill_path)

        # Arrow and grip dots on the protrusion
        arrow_color = QColor("#c8c8c8")
        if self._hover_animation > 0:
            arrow_color = arrow_color.lighter(100 + int(25 * self._hover_animation))

        painter.setPen(QPen(arrow_color, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))

        mid_y = bump_y + bump_h // 2
        arrow_x = x0 - protrusion / 2
        arrow_size = 7

        if not self._open:
            # Arrow pointing left
            painter.drawLine(int(arrow_x + arrow_size), mid_y - arrow_size, int(arrow_x), mid_y)
            painter.drawLine(int(arrow_x + arrow_size), mid_y + arrow_size, int(arrow_x), mid_y)
        else:
            # Arrow pointing right
            painter.drawLine(int(arrow_x - arrow_size), mid_y - arrow_size, int(arrow_x), mid_y)
            painter.drawLine(int(arrow_x - arrow_size), mid_y + arrow_size, int(arrow_x), mid_y)

        # Grip dots
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(arrow_color))

        dot_radius = 1.8
        dot_spacing = 5
        dots_x = arrow_x

        for i in range(3):
            dot_y = mid_y - arrow_size - 14 - (i * dot_spacing)
            painter.drawEllipse(
                QRectF(dots_x - dot_radius, dot_y - dot_radius, dot_radius * 2, dot_radius * 2)
            )

        for i in range(3):
            dot_y = mid_y + arrow_size + 14 + (i * dot_spacing)
            painter.drawEllipse(
                QRectF(dots_x - dot_radius, dot_y - dot_radius, dot_radius * 2, dot_radius * 2)
            )


# ---------------- Navigator (free-floating) ----------------

class NavigatorWindow(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.parent_window = parent
        self.setStyleSheet("""
            QFrame {
                background-color: #323232;
                border: 1px solid #1a1a1a;
                border-radius: 10px;
            }
        """)
        self.setFixedSize(280, 220)

        self.dragging = False
        self.drag_position = QPoint()

        # Drop shadow effect would be nice but requires QGraphicsDropShadowEffect

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
        title_bar = QFrame()
        title_bar.setFixedHeight(32)
        title_bar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #353535, stop:1 #2f2f2f);
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid #1f1f1f;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 0, 6, 0)

        title = QLabel("Navigator")
        title.setStyleSheet("color: #f5f5f5; font-size: 11px; font-weight: bold;")
        title_layout.addWidget(title)
        title_layout.addStretch()

        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #b8b8b8;
                font-size: 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                color: #ffffff;
                background-color: #4a4a4a;
            }
        """)
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn)

        layout.addWidget(title_bar)

        # Preview area
        preview = QFrame()
        preview.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: none;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(20, 20, 20, 20)

        preview_inner = QFrame()
        preview_inner.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #0a0a0a;
                border-radius: 4px;
            }
        """)
        pi_layout = QVBoxLayout(preview_inner)

        preview_label = QLabel("Canvas Preview")
        preview_label.setStyleSheet("color: #5a5a5a; font-size: 10px;")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pi_layout.addWidget(preview_label)

        preview_layout.addWidget(preview_inner)
        layout.addWidget(preview)

        title_bar.mousePressEvent = self.title_mouse_press
        title_bar.mouseMoveEvent = self.title_mouse_move

    def title_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def title_mouse_move(self, event):
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def closeEvent(self, event):
        if self.parent_window:
            self.parent_window.navigator_visible = False
            self.parent_window.right_window.set_open(False)
        event.accept()


# ---------------- Main Window ----------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Paint Application")
        self.resize(1680, 960)
        self.setStyleSheet("background-color: #2a2a2a;")

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.options_bar = ToolOptionsBar()
        root_layout.addWidget(self.options_bar)

        # Main area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #1a1a1a;
            }
            QSplitter::handle:hover {
                background-color: #2a2a2a;
            }
        """)

        left_container = QWidget()
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.toolbar = ToolBar()
        left_layout.addWidget(self.toolbar)

        self.canvas = CanvasArea()
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout.addWidget(self.canvas)

        splitter.addWidget(left_container)

        # Right panel with protrusion
        self.right_window = RightContextWindow(self)
        self.layers_panel = LayersPanel()
        self.right_window.panel_frame.layout().addWidget(self.layers_panel)
        splitter.addWidget(self.right_window)

        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)

        root_layout.addWidget(splitter)
        self.setCentralWidget(root)

        # Navigator window
        self.navigator = NavigatorWindow(self)
        self.navigator_visible = False

        # Connect tool buttons
        for btn in self.toolbar.group.buttons():
            btn.clicked.connect(self.on_tool_selected)

        if self.toolbar.group.buttons():
            self.toolbar.group.buttons()[0].setChecked(True)

    def on_tool_selected(self):
        btn = self.sender()
        if isinstance(btn, ToolButton):
            self.options_bar.update_tool(btn.icon_text, btn.tool_name)

    def toggle_navigator(self):
        self.navigator_visible = not self.navigator_visible

        if self.navigator_visible:
            # Position navigator to the left of the right panel
            global_pos = self.right_window.mapToGlobal(self.right_window.rect().topLeft())
            self.navigator.move(global_pos + QPoint(-self.navigator.width() - 20, 50))
            self.navigator.show()
            self.right_window.set_open(True)
        else:
            self.navigator.hide()
            self.right_window.set_open(False)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()