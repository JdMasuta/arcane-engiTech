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
    # without manim installed the wave render stays disabled
    from arcane.manim_scene import MANIM_AVAILABLE
    assert window.controls.wave_render_button.isEnabled() == MANIM_AVAILABLE


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
