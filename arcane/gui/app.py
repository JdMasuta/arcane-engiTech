"""Entry point for the Arcane Engineering desktop studio."""
import sys

from PySide6 import QtGui, QtWidgets

from arcane.gui.main_window import MainWindow
from arcane.gui.style import STYLESHEET


def build_app(argv=None):
    """Create the QApplication and main window without starting the event
    loop, so tests can construct the UI headlessly."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(argv or sys.argv[:1])
    app.setApplicationName("Arcane Engineering")
    app.setStyleSheet(STYLESHEET)
    app.setFont(QtGui.QFont("Segoe UI", 10))
    window = MainWindow()
    return app, window


def main(argv=None):
    app, window = build_app(argv)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
