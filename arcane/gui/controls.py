"""Left-hand control panel: circuit source, simulation, and render settings."""
from PySide6 import QtCore, QtWidgets

from arcane.manim.render import DEFAULT_QUALITY
from arcane.spellwave import DEFAULT_MAX_RANGE, DEFAULT_SPEED, DEFAULT_WIDTH


class ControlPanel(QtWidgets.QScrollArea):
    loadRequested = QtCore.Signal()
    exampleRequested = QtCore.Signal()
    builderRequested = QtCore.Signal()
    runRequested = QtCore.Signal(int)
    renderRequested = QtCore.Signal(dict)
    waveRenderRequested = QtCore.Signal(dict)
    combinedRenderRequested = QtCore.Signal(dict)
    waveSettingsChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._switch_rows = {}

        body = QtWidgets.QWidget()
        self.setWidget(body)
        root = QtWidgets.QVBoxLayout(body)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(14)

        root.addWidget(self._header())
        root.addWidget(self._source_group())
        root.addWidget(self._simulation_group())
        root.addWidget(self._switch_group())
        root.addWidget(self._wave_group())
        root.addWidget(self._render_group())
        root.addStretch(1)

    # -- sections ------------------------------------------------------------
    def _header(self):
        box = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        title = QtWidgets.QLabel("Arcane Engineering")
        title.setObjectName("Title")
        subtitle = QtWidgets.QLabel("circuit studio")
        subtitle.setObjectName("Subtitle")
        lay.addWidget(title)
        lay.addWidget(subtitle)
        return box

    def _source_group(self):
        group = QtWidgets.QGroupBox("Circuit")
        lay = QtWidgets.QVBoxLayout(group)
        self.source_label = QtWidgets.QLabel("No circuit loaded")
        self.source_label.setObjectName("Subtitle")
        self.source_label.setWordWrap(True)
        load_btn = QtWidgets.QPushButton("Open JSON spec…")
        load_btn.clicked.connect(self.loadRequested)
        example_btn = QtWidgets.QPushButton("Load demo circuit")
        example_btn.clicked.connect(self.exampleRequested)
        build_btn = QtWidgets.QPushButton("New circuit (builder)…")
        build_btn.clicked.connect(self.builderRequested)
        lay.addWidget(self.source_label)
        lay.addWidget(load_btn)
        lay.addWidget(example_btn)
        lay.addWidget(build_btn)
        return group

    def _simulation_group(self):
        group = QtWidgets.QGroupBox("Simulation")
        form = QtWidgets.QFormLayout(group)
        self.steps_spin = QtWidgets.QSpinBox()
        self.steps_spin.setRange(2, 100000)
        self.steps_spin.setValue(300)
        self.steps_spin.setSingleStep(50)
        form.addRow("Steps", self.steps_spin)

        self.log_check = QtWidgets.QCheckBox("Log-scale energy axis")
        form.addRow(self.log_check)
        self.plumbing_check = QtWidgets.QCheckBox("Show wires and junctions")
        form.addRow(self.plumbing_check)

        self.run_button = QtWidgets.QPushButton("Run simulation")
        self.run_button.setObjectName("Primary")
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(
            lambda: self.runRequested.emit(self.steps_spin.value()))
        form.addRow(self.run_button)
        return group

    def _switch_group(self):
        self.switch_group = QtWidgets.QGroupBox("Switch events")
        lay = QtWidgets.QVBoxLayout(self.switch_group)
        self.switch_hint = QtWidgets.QLabel("Load a circuit with switches to "
                                            "schedule when they flip on.")
        self.switch_hint.setObjectName("Subtitle")
        self.switch_hint.setWordWrap(True)
        lay.addWidget(self.switch_hint)
        self.switch_form = QtWidgets.QFormLayout()
        lay.addLayout(self.switch_form)
        return self.switch_group

    def _wave_group(self):
        group = QtWidgets.QGroupBox("Spell wave")
        form = QtWidgets.QFormLayout(group)
        self.range_spin = QtWidgets.QDoubleSpinBox()
        self.range_spin.setRange(5.0, 500.0)
        self.range_spin.setValue(DEFAULT_MAX_RANGE)
        form.addRow("Max range", self.range_spin)

        self.speed_spin = QtWidgets.QDoubleSpinBox()
        self.speed_spin.setRange(0.05, 10.0)
        self.speed_spin.setSingleStep(0.05)
        self.speed_spin.setValue(DEFAULT_SPEED)
        form.addRow("Speed", self.speed_spin)

        self.width_spin = QtWidgets.QDoubleSpinBox()
        self.width_spin.setRange(0.5, 20.0)
        self.width_spin.setSingleStep(0.5)
        self.width_spin.setValue(DEFAULT_WIDTH)
        form.addRow("Packet width", self.width_spin)

        self.classical_check = QtWidgets.QCheckBox("Show classical model")
        self.classical_check.setChecked(True)
        self.classical_check.toggled.connect(
            lambda _: self.waveSettingsChanged.emit())
        form.addRow(self.classical_check)

        self.field_2d_check = QtWidgets.QCheckBox("2D field")
        self.field_2d_check.setToolTip("Render the full 2D wave field "
                                       "instead of the 1D radial slice. "
                                       "Takes effect on the next run.")
        form.addRow(self.field_2d_check)
        return group

    def _render_group(self):
        group = QtWidgets.QGroupBox("Manim render")
        form = QtWidgets.QFormLayout(group)
        self.fps_spin = QtWidgets.QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(30)
        form.addRow("Frame rate", self.fps_spin)

        self.quality_combo = QtWidgets.QComboBox()
        self.quality_combo.addItems(["480p", "720p", "1080p", "1440p", "4k"])
        self.quality_combo.setCurrentText(DEFAULT_QUALITY)
        form.addRow("Resolution", self.quality_combo)

        self.runtime_spin = QtWidgets.QDoubleSpinBox()
        self.runtime_spin.setRange(0.5, 120.0)
        self.runtime_spin.setValue(8.0)
        self.runtime_spin.setSuffix(" s")
        form.addRow("Duration", self.runtime_spin)

        self.render_button = QtWidgets.QPushButton("Render circuit…")
        self.render_button.setEnabled(False)
        self.render_button.clicked.connect(self._emit_render)
        form.addRow(self.render_button)

        self.wave_render_button = QtWidgets.QPushButton("Render spell wave…")
        self.wave_render_button.setEnabled(False)
        self.wave_render_button.setToolTip("Renders the most recently cast "
                                           "spell wave")
        self.wave_render_button.clicked.connect(self._emit_wave_render)
        form.addRow(self.wave_render_button)

        self.combined_render_button = QtWidgets.QPushButton("Render circuit + wave…")
        self.combined_render_button.setEnabled(False)
        self.combined_render_button.setToolTip("Renders the circuit schematic "
                                               "above the most recently cast "
                                               "spell wave, one timeline")
        self.combined_render_button.clicked.connect(self._emit_combined_render)
        form.addRow(self.combined_render_button)

        # manim's Python API exposes no per-frame callback, so this is an
        # honest busy indicator (indeterminate) rather than a percentage
        self.render_progress = QtWidgets.QProgressBar()
        self.render_progress.setRange(0, 0)
        self.render_progress.setTextVisible(False)
        self.render_progress.setVisible(False)
        form.addRow(self.render_progress)

        self.render_status = QtWidgets.QLabel("")
        self.render_status.setObjectName("Subtitle")
        self.render_status.setWordWrap(True)
        form.addRow(self.render_status)
        return group

    # -- session binding -----------------------------------------------------
    def bind_session(self, session):
        self.source_label.setText(_describe_source(session))
        self.run_button.setEnabled(True)
        for i in reversed(range(self.switch_form.rowCount())):
            self.switch_form.removeRow(i)
        self._switch_rows.clear()

        switches = session.switches()
        self.switch_hint.setVisible(not switches)
        for switch in switches:
            spin = QtWidgets.QSpinBox()
            spin.setRange(0, 100000)
            spin.setSpecialValueText("never")
            preset = session.switch_events.get(switch.name)
            spin.setValue(preset if preset else 0)
            self.switch_form.addRow(switch.name, spin)
            self._switch_rows[switch.name] = spin

    def read_switch_events(self):
        events = {}
        for name, spin in self._switch_rows.items():
            events[name] = None if spin.value() == 0 else spin.value()
        return events

    @property
    def run_time(self):
        return self.runtime_spin.value()

    @property
    def fps(self):
        return self.fps_spin.value()

    def read_wave_settings(self):
        return {
            "max_range": self.range_spin.value(),
            "speed": self.speed_spin.value(),
            "width": self.width_spin.value(),
        }

    @property
    def show_classical(self):
        return self.classical_check.isChecked()

    @property
    def use_2d_waves(self):
        return self.field_2d_check.isChecked()

    def _render_options(self):
        return {
            "fps": self.fps_spin.value(),
            "quality": self.quality_combo.currentText(),
            "run_time": self.runtime_spin.value(),
        }

    def _emit_render(self):
        self.renderRequested.emit(self._render_options())

    def _emit_wave_render(self):
        self.waveRenderRequested.emit(self._render_options())

    def _emit_combined_render(self):
        self.combinedRenderRequested.emit(self._render_options())


def _describe_source(session):
    if session.source:
        import os
        return f"Loaded: {os.path.basename(session.source)}"
    return "Loaded circuit"
