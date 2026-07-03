"""Background thread that renders a manim video without freezing the UI."""
from PySide6 import QtCore

from arcane.render import render_circuit


class RenderWorker(QtCore.QThread):
    finished_ok = QtCore.Signal(str)
    failed = QtCore.Signal(str)

    def __init__(self, comp_list, Es, output_path, fps, quality, run_time, parent=None):
        super().__init__(parent)
        self._comp_list = comp_list
        self._Es = Es
        self._output_path = output_path
        self._fps = fps
        self._quality = quality
        self._run_time = run_time

    def run(self):
        try:
            path = render_circuit(self._comp_list, self._Es, self._output_path,
                                  fps=self._fps, quality=self._quality,
                                  run_time=self._run_time)
            self.finished_ok.emit(str(path))
        except Exception as exc:  # surfaced to the user in the status label
            self.failed.emit(str(exc))
