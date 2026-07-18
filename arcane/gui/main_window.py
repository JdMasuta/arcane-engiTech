"""Main application window wiring the panels, canvases, and transport."""
from PySide6 import QtCore, QtWidgets

from arcane.manim_scene import MANIM_AVAILABLE
from arcane.gui.circuit_view import CircuitView
from arcane.gui.controls import ControlPanel
from arcane.gui.energy_view import EnergyView
from arcane.gui.render_worker import RenderWorker
from arcane.gui.session import SimulationSession
from arcane.gui.transport import TransportBar
from arcane.gui.wave_view import SpellWaveView


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arcane Engineering — Circuit Studio")
        self.resize(1280, 800)
        self.session = None
        self._render_worker = None

        self.controls = ControlPanel()
        self.controls.setFixedWidth(320)
        self.controls.loadRequested.connect(self._load_from_dialog)
        self.controls.exampleRequested.connect(self._load_demo)
        self.controls.runRequested.connect(self._run_simulation)
        self.controls.renderRequested.connect(self._start_render)
        self.controls.waveRenderRequested.connect(self._start_wave_render)
        self.controls.waveSettingsChanged.connect(self._refresh_wave_view)

        self.circuit_view = CircuitView()
        self.energy_view = EnergyView()
        self.wave_view = SpellWaveView()
        self.lower_tabs = QtWidgets.QTabWidget()
        self.lower_tabs.addTab(self._titled("Energy over time", self.energy_view),
                               "Energy over time")
        self.lower_tabs.addTab(self._titled("Spell propagation", self.wave_view),
                               "Spell propagation")
        canvas_split = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        canvas_split.addWidget(self._titled("Circuit", self.circuit_view))
        canvas_split.addWidget(self.lower_tabs)
        canvas_split.setSizes([440, 340])

        self.transport = TransportBar()
        self.transport.stepChanged.connect(self._on_step)

        center = QtWidgets.QWidget()
        center_layout = QtWidgets.QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(canvas_split, 1)
        center_layout.addWidget(self._transport_frame())

        root = QtWidgets.QWidget()
        root_layout = QtWidgets.QHBoxLayout(root)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)
        root_layout.addWidget(self.controls)
        root_layout.addWidget(center, 1)
        self.setCentralWidget(root)

        self.status = self.statusBar()
        self._set_status("Load the demo circuit or open a JSON spec to begin.")
        if not MANIM_AVAILABLE:
            self.controls.render_status.setText("Install manim to enable video "
                                                "rendering (pip install manim).")

    # -- layout helpers ------------------------------------------------------
    def _titled(self, title, widget):
        frame = QtWidgets.QFrame()
        frame.setObjectName("Panel")
        lay = QtWidgets.QVBoxLayout(frame)
        lay.setContentsMargins(10, 8, 10, 10)
        label = QtWidgets.QLabel(title)
        label.setObjectName("Subtitle")
        lay.addWidget(label)
        lay.addWidget(widget, 1)
        return frame

    def _transport_frame(self):
        frame = QtWidgets.QFrame()
        frame.setObjectName("Panel")
        lay = QtWidgets.QVBoxLayout(frame)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.addWidget(self.transport)
        return frame

    # -- loading -------------------------------------------------------------
    def _load_demo(self):
        self._set_session(SimulationSession.demo())
        self._set_status("Loaded the demo circuit. Press Run simulation.")

    def _load_from_dialog(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open circuit spec", "", "JSON circuit (*.json);;All files (*)")
        if not path:
            return
        try:
            session = SimulationSession.from_spec_file(path)
        except Exception as exc:
            self._set_status(f"Could not load circuit: {exc}")
            return
        self._set_session(session)
        self._set_status(f"Loaded {path}. Press Run simulation.")

    def _set_session(self, session):
        self.session = session
        self.controls.bind_session(session)
        self.circuit_view.set_circuit(session.comp_list)
        self.circuit_view.set_history({})
        self.circuit_view.set_step(0)
        self.wave_view.set_waves([])
        self.transport.configure(0, self.controls.run_time, self.controls.fps)
        self.controls.render_button.setEnabled(False)
        self.controls.wave_render_button.setEnabled(False)

    # -- simulation ----------------------------------------------------------
    def _run_simulation(self, n_steps):
        if self.session is None:
            return
        self.session.switch_events = self.controls.read_switch_events()
        self.session.wave_settings = self.controls.read_wave_settings()
        t, Es, ET = self.session.run(n_steps)
        names = self.session.component_names(
            include_plumbing=self.controls.plumbing_check.isChecked())
        self.circuit_view.set_history(Es)
        self.energy_view.set_history(t, Es, ET, names,
                                     log_scale=self.controls.log_check.isChecked())
        self.wave_view.set_waves(self.session.waves,
                                 show_classical=self.controls.show_classical)
        self.transport.configure(self.session.n_steps, self.controls.run_time,
                                 self.controls.fps)
        self.controls.render_button.setEnabled(MANIM_AVAILABLE)
        self.controls.wave_render_button.setEnabled(
            MANIM_AVAILABLE and bool(self.session.waves))
        n_casts = len(self.session.cast_log)
        self._set_status(f"Simulated {n_steps} steps · {len(names)} tracked "
                         f"components · {n_casts} cast(s) · scrub or play to "
                         f"inspect.")

    def _refresh_wave_view(self):
        if self.session and self.session.has_run():
            self.wave_view.set_waves(self.session.waves,
                                     show_classical=self.controls.show_classical)
            self.wave_view.set_step(self.transport.current_step)

    def _on_step(self, step):
        self.circuit_view.set_step(step)
        self.energy_view.set_step(step)
        self.wave_view.set_step(step)
        if self.session and self.session.has_run():
            total = self.session.ET[step]
            self.status.showMessage(f"Step {step} / {self.session.n_steps - 1}"
                                    f"    ·    total energy {total:.1f}")

    # -- rendering -----------------------------------------------------------
    def _start_render(self, options):
        if self.session is None or not self.session.has_run():
            self._set_status("Run a simulation before rendering.")
            return
        from arcane.render import render_circuit

        session = self.session

        def job(path, opts=options):
            return render_circuit(session.comp_list, session.Es, path,
                                  fps=opts["fps"], quality=opts["quality"],
                                  run_time=opts["run_time"])
        self._launch_render(job, "arcane_circuit.mp4")

    def _start_wave_render(self, options):
        if self.session is None or not self.session.waves:
            self._set_status("Run a simulation that casts before rendering "
                             "a spell wave.")
            return
        from arcane.render import render_wave

        wave = max(self.session.waves, key=lambda w: w.start_step)

        def job(path, opts=options):
            return render_wave(wave, path, fps=opts["fps"],
                               quality=opts["quality"],
                               run_time=opts["run_time"])
        self._launch_render(job, "spell_wave.mp4")

    def _launch_render(self, job, default_name):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Render video to", default_name, "MP4 video (*.mp4)")
        if not path:
            return
        self.controls.render_button.setEnabled(False)
        self.controls.wave_render_button.setEnabled(False)
        self.controls.render_status.setText("Rendering… this can take a while.")
        self._render_worker = RenderWorker(lambda: job(path))
        self._render_worker.finished_ok.connect(self._on_render_done)
        self._render_worker.failed.connect(self._on_render_failed)
        self._render_worker.start()

    def _on_render_done(self, path):
        self.controls.render_status.setText(f"Saved {path}")
        self._restore_render_buttons()
        self._set_status(f"Render complete: {path}")

    def _on_render_failed(self, message):
        self.controls.render_status.setText(f"Render failed: {message}")
        self._restore_render_buttons()

    def _restore_render_buttons(self):
        self.controls.render_button.setEnabled(MANIM_AVAILABLE)
        self.controls.wave_render_button.setEnabled(
            MANIM_AVAILABLE and bool(self.session and self.session.waves))

    def _set_status(self, message):
        self.status.showMessage(message)
