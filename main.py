import sys
from pathlib import Path
import numpy as np
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QWidget,
    QColorDialog, QHBoxLayout, QLabel, QSlider, QWidgetAction, QToolBar, QSizePolicy, QDockWidget, QVBoxLayout
)
from PyQt6.QtGui import (
    QAction,
    QPainter,
    QImage, QActionGroup, QIcon, QMouseEvent, QGuiApplication,
)
from PyQt6.QtCore import Qt, QPoint, QTimer, QSize, QEvent

from Painter.utilities import get_icon

class ToolPanel(QDockWidget):

    def __init__(self):
        super().__init__("Tools")

        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea |
            Qt.DockWidgetArea.TopDockWidgetArea |
            Qt.DockWidgetArea.BottomDockWidgetArea
        )

        # Internal widget (dock widgets need a container widget)
        container = QWidget()
        layout = QVBoxLayout(container)


        self.setWidget(container)

        # Minimum size
        self.setMinimumWidth(120)
        self.setMinimumHeight(80)



class ToolBar(QToolBar):

    def __init__(self):
        super().__init__()
        self.setMovable(True)

        for j in range(2):
            self.addWidget(QLabel(f"Tool {j}"))

        self.addWidget(QLabel("Tool 1"))
        self.addWidget(QLabel("Tool 2"))
        self.minimumSizeHor = QSize(200, 0)

        self.orientationChanged.connect(self.onOrientationChange)
        self.setOrientation(Qt.Orientation.Vertical)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)





    def onOrientationChange(self, orientation):
        print(self.minimumSizeHor, self.minimumSizeHint())
        if orientation == Qt.Orientation.Horizontal:
            self.setMinimumSize(self.minimumSizeHor)
        else:
            self.setMinimumSize(
                self.minimumSizeHor.transposed()
            )
        print(self.minimumSizeHor, self.minimumSizeHint())









class MainWindow(QMainWindow):

    def __init__(self):
        #Main Window
        super().__init__()
        self.setWindowTitle("PainterProto")
        screen = QGuiApplication.primaryScreen().availableGeometry()
        print(f"screen: {screen}")

        self.resize(screen.size())


        self.dockWidget = QDockWidget()

        #Toolbar
        self.toolbar = ToolBar()
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.toolbar)



        #self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dockWidget)












def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(get_icon())

    window = MainWindow()
    window.show()


    sys.exit(app.exec())


if __name__ == "__main__":
    main()
