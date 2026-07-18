"""Headless smoke tests for the Qt studio.

Run under the offscreen platform so no display is needed. They drive the
same methods the buttons call and assert the views and transport end up in
the expected state.
"""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from arcane.gui.app import build_app  # noqa: E402
from arcane.gui.session import SimulationSession  # noqa: E402


@pytest.fixture(scope="module")
def app_window():
    app, window = build_app([])
    yield app, window
    window.close()


def test_session_demo_runs_and_is_reproducible():
    session = SimulationSession.demo()
    t1, Es1, _ = session.run(200)
    peak_first = max(Es1["caster 1"])
    t2, Es2, _ = session.run(200)
    # reset_energy makes a second identical run reproduce the first exactly
    assert max(Es2["caster 1"]) == peak_first
    assert session.n_steps == 200


def test_switch_event_changes_outcome():
    session = SimulationSession.demo()
    session.switch_events = {"switch": None}  # never toggles on
    _, Es_off, _ = session.run(200)
    session.switch_events = {"switch": 10}    # flips on early
    _, Es_on, _ = session.run(200)
    assert max(Es_off["caster 1"]) == 0
    assert max(Es_on["caster 1"]) > 0


def test_per_caster_wave_params_from_json_spec_override_the_session_default():
    spec = {"circuit": [
        {"type": "Battery", "level": 1, "name": "b", "energy": 500},
        {"type": "Caster", "level": 1, "name": "c",
         "wave_range": 75, "wave_speed": 1.0},
    ]}
    session = SimulationSession.from_spec_dict(spec)
    assert session.wave_settings["max_range"] != 75  # sanity: differs from the global default
    session.run(150)
    assert session.cast_log, "the caster should have fired at least once"
    assert len(session.waves) == 1
    assert session.waves[0].max_range == 75
    assert session.waves[0].speed == 1.0


def test_build_app_and_run_flow(app_window):
    app, window = app_window
    window._load_demo()
    assert window.session is not None
    assert not window.controls.render_button.isEnabled()  # nothing simulated yet

    window._run_simulation(150)
    assert window.session.has_run()
    assert window.transport.slider.maximum() == 149

    # scrubbing updates both views without error and moves the cursor
    window.transport.slider.setValue(75)
    assert window.transport.current_step == 75
    assert window.energy_view._cursor is not None


def test_plumbing_toggle_controls_tracked_names(app_window):
    app, window = app_window
    window._load_demo()
    window.controls.plumbing_check.setChecked(False)
    lean = window.session.component_names(include_plumbing=False)
    full = window.session.component_names(include_plumbing=True)
    assert len(full) > len(lean)
    assert all("wire" not in n and "junction" not in n for n in lean)


def test_demo_run_spawns_spell_waves(app_window):
    app, window = app_window
    window._load_demo()
    window._run_simulation(300)
    assert window.session.cast_log, "demo circuit should cast at least once"
    assert len(window.session.waves) == len(window.session.cast_log)
    wave = window.session.waves[0]
    assert wave.start_step == window.session.cast_log[0]["step"]
    # wave tab exists and scrubbing to mid-flight fills the readout
    assert window.lower_tabs.count() == 2
    mid = wave.start_step + int(wave.flight_time() * 0.5)
    window.transport.slider.setValue(mid)
    assert "A(t)" in window.wave_view._readout.get_text()
    # without manim installed the wave and combined renders stay disabled
    from arcane.manim.circuit import MANIM_AVAILABLE
    assert window.controls.wave_render_button.isEnabled() == MANIM_AVAILABLE
    assert window.controls.combined_render_button.isEnabled() == MANIM_AVAILABLE


def test_combined_render_button_wiring_is_safe_without_manim(app_window, monkeypatch):
    from PySide6 import QtWidgets

    app, window = app_window
    window._load_demo()
    window._run_simulation(300)
    assert window.session.waves

    # simulate the user cancelling the save dialog: _launch_render must
    # return without starting a worker (and without ever calling manim,
    # since MANIM_AVAILABLE is False in this environment)
    monkeypatch.setattr(QtWidgets.QFileDialog, "getSaveFileName",
                        staticmethod(lambda *a, **k: ("", "")))
    window.controls.combinedRenderRequested.emit(
        {"fps": 30, "quality": "720p", "run_time": 8.0})
    assert window._render_worker is None


def test_render_progress_bar_lifecycle(app_window, monkeypatch, tmp_path):
    from PySide6 import QtWidgets

    app, window = app_window
    window._load_demo()
    window._run_simulation(300)
    assert not window.controls.render_progress.isVisible()

    # accept the save dialog; the render job then fails fast (no manim
    # installed here), which exercises show-on-start and hide-on-failure
    monkeypatch.setattr(
        QtWidgets.QFileDialog, "getSaveFileName",
        staticmethod(lambda *a, **k: (str(tmp_path / "out.mp4"), "")))
    window.controls.renderRequested.emit(
        {"fps": 30, "quality": "720p", "run_time": 8.0})
    assert window._render_worker is not None
    assert window.controls.render_progress.isVisibleTo(window.controls)

    window._render_worker.wait(5000)
    for _ in range(20):
        app.processEvents()
    assert not window.controls.render_progress.isVisibleTo(window.controls)
    assert "Render failed" in window.controls.render_status.text()


def test_wave_settings_flow_into_new_runs(app_window):
    app, window = app_window
    window._load_demo()
    window.controls.range_spin.setValue(50.0)
    window.controls.speed_spin.setValue(1.0)
    window._run_simulation(300)
    assert window.session.wave_settings["max_range"] == 50.0
    if window.session.waves:
        assert window.session.waves[0].max_range == 50.0
    window.controls.range_spin.setValue(30.0)
    window.controls.speed_spin.setValue(0.5)


def test_2d_field_toggle_switches_wave_view_to_imshow(app_window):
    from arcane.spellwave import SpellWave2D

    app, window = app_window
    window._load_demo()
    window.controls.field_2d_check.setChecked(True)
    try:
        window._run_simulation(300)
        assert window.session.waves, "demo circuit should cast at least once"
        assert all(isinstance(w, SpellWave2D) for w in window.session.waves)
        assert window.wave_view._is_2d is True
        assert window.wave_view._image is not None

        wave = window.session.waves[0]
        mid = wave.start_step + int(wave.flight_time() * 0.5)
        window.transport.slider.setValue(mid)
        assert window.wave_view._image.get_array().shape == (
            wave.y.size, wave.x.size)
        assert "A(t)" in window.wave_view._readout.get_text()
    finally:
        window.controls.field_2d_check.setChecked(False)
