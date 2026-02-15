from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QWidget,
    QColorDialog, QHBoxLayout, QLabel, QSlider, QWidgetAction, QToolBar,
)
from PyQt6.QtGui import (
    QAction,
    QPainter,
    QImage, QActionGroup,
)
from PyQt6.QtCore import Qt, QPoint, QTimer

from Painter.application_manager import PaintAppManager
from Painter.simple_file import SimpleFile


class MainWindow(QMainWindow):
    """
    Main application window with menus and canvas widget.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Karanbir Paint")

        self.app_manager = PaintAppManager()
        self.canvas_widget = CanvasWidget(self.app_manager)
        self.setCentralWidget(self.canvas_widget)

        self.toolbar = QToolBar("Brush Change", self)
        self.addToolBar(self.toolbar)

        self._create_actions()
        self._create_menu()

        # Start with a new blank document
        self.app_manager.new_document(name="Paint", width=2400, height=3000, filetype="png")
        self.resize(1200, 800)
        self.__post__init__()

    def __post__init__(self):
        self.interp_slider.setValue(np.iinfo(np.uint16).max)



    def _create_actions(self):
        #self.new_action = QAction("New", self)
        #self.new_action.triggered.connect(self.new_document)

        self.open_action = QAction("Open…", self)
        self.open_action.triggered.connect(self.open_document)

        self.save_action = QAction("Save", self)
        self.save_action.triggered.connect(self.save_document)

        self.save_as_action = QAction("Save As…", self)
        self.save_as_action.triggered.connect(self.save_document_as)

        self.export_png_action = QAction("Export PNG…", self)
        self.export_png_action.triggered.connect(self.export_png)

        self.color_action = QAction("Choose Color…", self)
        self.color_action.triggered.connect(self.choose_color)

        self.brush_regular_action = QAction("Regular Brush", self)
        self.brush_regular_action.setCheckable(True)

        self.brush_spline_action = QAction("Spline Brush", self)
        self.brush_spline_action.setCheckable(True)


        self.brush_group = QActionGroup(self)
        self.brush_group.addAction(self.brush_regular_action)
        self.brush_group.addAction(self.brush_spline_action)



        self.brush_regular_action.setChecked(True)

        self.brush_regular_action.triggered.connect(
            lambda: self.canvas_widget.set_brush_type(CanvasWidget.BRUSH_REGULAR)
        )
        self.brush_spline_action.triggered.connect(
            lambda: self.canvas_widget.set_brush_type(CanvasWidget.BRUSH_SPLINE)
        )



        self.reset_action = QAction("Reset Canvas…", self)
        self.reset_action.triggered.connect(self.reset_layer_active)

        size_slider = QSlider(Qt.Orientation.Horizontal)
        size_slider.setRange(1, 1000)

        slider_action = QWidgetAction(self)
        slider_action.setDefaultWidget(size_slider)

        self.toolbar.addAction(slider_action)
        size_slider.valueChanged.connect(
            self.set_brush_size
        )




    def _create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        #file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.export_png_action)

        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction(self.color_action)
        brush_menu = menubar.addMenu("Brush")
        brush_menu.addAction(self.brush_regular_action)
        brush_menu.addAction(self.brush_spline_action)

        reset_menu = menubar.addMenu("Reset")
        reset_menu.addAction(self.reset_action)

        slider_widget = QWidget()
        layout = QHBoxLayout()
        slider_widget.setLayout(layout)

        self.interp_label = QLabel("Interpolation Alpha:")
        self.interp_slider = QSlider(Qt.Orientation.Horizontal)
        self.interp_slider.setMinimum(0)
        self.interp_slider.setMaximum(65535)  # match uint16 max
        self.interp_slider.valueChanged.connect(self.update_interpolation_alpha)

        layout.addWidget(self.interp_label)
        layout.addWidget(self.interp_slider)

        # Add slider widget to a toolbar
        self.addToolBar("Interpolation").addWidget(slider_widget)



    # ---------- Menu callbacks ----------

    def set_brush_size(self, brush_size: int):
        self.canvas_widget.brush_size = brush_size

    def update_interpolation_alpha(self, value):
        layer = self.app_manager.file.canvas.active_layer
        if layer:
            layer.interpolation_alpha = value

    def reset_layer_active(self):
        if self.app_manager.file.canvas.active_layer:
            self.app_manager.file.canvas.active_layer.reset()
            self.canvas_widget._cache_dirty = True
            self.canvas_widget.update()

    def new_document(self):
        self.app_manager.new_document()
        self.canvas_widget.update()

    def open_document(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "All Files (*);;KSP Files (*.ksp);;PNG Files (*.png)",
        )
        if path:
            self.app_manager.open_document(path)
            print(self.app_manager.file.canvas.active_layer.shape,
                  self.app_manager.file.canvas.active_layer.dtype)
            self.canvas_widget._cache_dirty = True
            self.canvas_widget.update()

    def save_document(self):
        try:
            self.app_manager.save_document()
        except RuntimeError:
            self.save_document_as()

    def save_document_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            "",
            "KSP Files (*.ksp);;All Files (*)",
        )
        if path:
            self.app_manager.save_document(path)

    def export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export PNG",
            "",
            "PNG Files (*.png);;All Files (*)",
        )
        if path:
            self.app_manager.export_png(path)

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            scale = 257  # 255 → 65535
            self.canvas_widget.brush_color = (
                color.red() * scale,
                color.green() * scale,
                color.blue() * scale,
                color.alpha() * scale,
            )

    # ---------- Qt entry ----------


class CanvasWidget(QWidget):
    BRUSH_REGULAR = 0
    BRUSH_SPLINE = 1
    def __init__(self, app_manager: PaintAppManager, parent=None):
        super().__init__(parent)
        self._hold_pos = None
        self.app_manager = app_manager
        self.setMouseTracking(True)

        # Default brush
        self._brush_type = CanvasWidget.BRUSH_REGULAR
        self.brush_size = 20
        self.brush_color = (65535, 0, 0, 65535)


        # main.py (CanvasWidget.__init__)
        self._qimage_cache: QImage | None = None
        self._cache_dirty = True
        self._data8 = None  # will be a preallocated uint8 array matching canvas shape
        self._mouse_pressed = False

        self.q_timer = QTimer()
        self.q_timer.timeout.connect(self.onTimer)


    def set_brush_type(self, brush_type: int):
        self._brush_type = brush_type
        self.app_manager.file.canvas.active_layer.pixel_points.clear()

    def _ensure_qimage_cache(self):
        if not self._cache_dirty and self._qimage_cache is not None:
            return

        try:
            buffer = self.app_manager.render()  # returns the shared render buffer (uint16)
            print(self.app_manager.file.canvas.layers)
        except RuntimeError:
            self._qimage_cache = None
            self._cache_dirty = False
            return

        buffer = self.app_manager.render()  # shared render buffer (uint16)
        h, w, _ = buffer.shape
        if self._data8 is None or self._data8.shape != (h, w, 4):
            self._data8 = np.empty((h, w, 4), dtype=np.uint8)

        np.right_shift(buffer, 8, out=self._data8, casting='unsafe')  # no temporaries

        if self._qimage_cache is None:
            self._qimage_cache = QImage(self._data8.data, w, h, 4 * w, QImage.Format.Format_RGBA8888)
            self._qimage_cache._py_buffer = self._data8
        else:
            self._qimage_cache._py_buffer = self._data8

        self._cache_dirty = False



    def paintEvent(self, event):
        painter = QPainter(self)

        # If render fails, fill white
        if self._cache_dirty:
            self._ensure_qimage_cache()

        if self._qimage_cache is None:
            painter.fillRect(self.rect(), Qt.GlobalColor.white)
            return

        # Draw scaled to widget size
        painter.drawImage(self.rect(), self._qimage_cache)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_pressed = True
            pos = event.position().toPoint()
            self._apply_brush(pos)
            self._hold_pos = event.position().toPoint()
            self.q_timer.start(16)

    def onTimer(self):
        if not self._mouse_pressed or (self._hold_pos is None):
            self.q_timer.stop()
            return

        self._apply_brush(self._hold_pos)
        print("Fired")

    def mouseMoveEvent(self, event):
        # replace the original check with this (keeps your subtraction style,
        # uses Euclidean distance via squared comparison, handles None safely)
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.q_timer.stop()
            last = self.app_manager.file.canvas.active_layer.last_pos


            if last is None:
                # no previous point -> stamp and set last_pos
                pos = event.position().toPoint()
                self._apply_brush(pos)
                return


            # keep your subtraction approach; ensure both are QPoint
            cur = event.position().toPoint()
            self._hold_pos = cur
            delta = last - cur
            dx = int(delta.x())
            dy = int(delta.y())

            # compare squared distances to avoid sqrt (brush_size treated as radius)

            pos = cur
            self._apply_brush(pos)
            self.q_timer.start()






    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.app_manager.file.canvas.set_active_last_pos(None)
            self.app_manager.file.canvas.active_layer.pixel_points.clear()
            self._mouse_pressed = False
            self.q_timer.stop()
            self._hold_pos = None



    def _apply_brush(self, pos: QPoint):
        canvas = self.app_manager.file.canvas
        w, h = canvas.width, canvas.height
        if w == 0 or h == 0:
            return

        x = int(pos.x() * w / self.width())
        y = int(pos.y() * h / self.height())

        if self._brush_type == CanvasWidget.BRUSH_REGULAR:
            self.app_manager.draw_brush(
                x, y, self.brush_size, self.brush_color
            )

        elif self._brush_type == CanvasWidget.BRUSH_SPLINE:
            self.app_manager.draw_spline_brush(x, y, self.brush_size, self.brush_color)

        self._cache_dirty = True
        self.update()

    def _apply_brush_hold(self):
        if self._mouse_pressed:
            self._apply_brush(self._hold_pos)
