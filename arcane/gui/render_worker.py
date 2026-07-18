"""Background thread that runs a render job without freezing the UI."""
from PySide6 import QtCore


class RenderWorker(QtCore.QThread):
    """Runs `job` (a callable returning the output path) off the UI thread."""

    finished_ok = QtCore.Signal(str)
    failed = QtCore.Signal(str)

    def __init__(self, job, parent=None):
        super().__init__(parent)
        self._job = job

    def run(self):
        try:
            path = self._job()
            self.finished_ok.emit(str(path))
        except Exception as exc:  # surfaced to the user in the status label
            self.failed.emit(str(exc))
