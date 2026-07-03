"""Playback transport: a scrubber slider plus play/pause driven by a timer.

Playback advances so a full sweep takes the configured run_time seconds at
the preview frame rate, matching the duration of an exported manim video.
"""
from PySide6 import QtCore, QtWidgets


class TransportBar(QtWidgets.QWidget):
    stepChanged = QtCore.Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._n_steps = 0
        self._run_time = 8.0
        self._fps = 30

        self.play_button = QtWidgets.QPushButton("▶  Play")
        self.play_button.setCheckable(True)
        self.play_button.setEnabled(False)
        self.play_button.toggled.connect(self._on_play_toggled)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.valueChanged.connect(self._on_slider)

        self.step_label = QtWidgets.QLabel("– / –")
        self.step_label.setObjectName("StatusValue")
        self.step_label.setMinimumWidth(90)
        self.step_label.setAlignment(QtCore.Qt.AlignCenter)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.play_button)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.step_label)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._advance)

    def configure(self, n_steps, run_time, fps):
        self._n_steps = n_steps
        self._run_time = max(run_time, 0.1)
        self._fps = max(fps, 1)
        enabled = n_steps > 1
        self.slider.setEnabled(enabled)
        self.play_button.setEnabled(enabled)
        self.slider.blockSignals(True)
        self.slider.setRange(0, max(n_steps - 1, 0))
        self.slider.setValue(0)
        self.slider.blockSignals(False)
        self._update_label(0)
        self.stepChanged.emit(0)

    @property
    def current_step(self):
        return self.slider.value()

    def _steps_per_tick(self):
        total_frames = max(int(self._run_time * self._fps), 1)
        return max(self._n_steps / total_frames, 1e-6)

    def _on_play_toggled(self, playing):
        if playing and self._n_steps > 1:
            self.play_button.setText("‖  Pause")
            if self.slider.value() >= self._n_steps - 1:
                self.slider.setValue(0)
            self._accum = float(self.slider.value())
            self.timer.start(int(1000 / self._fps))
        else:
            self.play_button.setChecked(False)
            self.play_button.setText("▶  Play")
            self.timer.stop()

    def _advance(self):
        self._accum += self._steps_per_tick()
        value = int(self._accum)
        if value >= self._n_steps - 1:
            self.slider.setValue(self._n_steps - 1)
            self.play_button.setChecked(False)
        else:
            self.slider.setValue(value)

    def _on_slider(self, value):
        self._update_label(value)
        self.stepChanged.emit(value)

    def _update_label(self, value):
        total = self._n_steps - 1 if self._n_steps else 0
        self.step_label.setText(f"{value} / {total}")
