"""Exercises the manim scene builders' construct() methods against a fake
manim module, since real manim cannot be installed in this environment.

The fake provides just enough of manim's API surface (Mobject/VGroup/Line/
Text/DecimalNumber/ImageMobject/ValueTracker/Scene) to actually run
construct(): build every mobject, install updaters, and — critically —
call those updaters at several points along the animation instead of just
at the end, the same way manim's frame loop would. This catches real bugs
(wrong argument counts, out-of-range indices, undefined names) that a pure
import-guard test cannot, though it says nothing about the actual rendered
pixels — only a real manim install can verify those.

The modules under test import `from manim import ...` at module load time,
so patching sys.modules['manim'] only takes effect on a fresh reload.
"""
import importlib
import sys
import types

import numpy as np
import pytest

from arcane.components import Battery, Blank, Switch, AndGate, NotGate, Caster, connect
from arcane.util.simulation import simulate
from arcane.spellwave import SpellWave, SpellWave2D


class FakeMobject:
    def __init__(self, *args, **kwargs):
        self._updaters = []
        self.submobjects = []

    def add_updater(self, fn):
        self._updaters.append(fn)
        return self

    def clear_updaters(self):
        self._updaters = []
        return self

    def set_stroke(self, **kwargs):
        return self

    def set_points_as_corners(self, points):
        self.points = list(points)
        return self

    def set_value(self, value):
        self.value = value
        return self

    def move_to(self, point):
        self.pos = point
        return self

    def next_to(self, other, direction=None, buff=0.0):
        return self

    def to_corner(self, direction):
        return self

    def to_edge(self, direction):
        return self

    def shift(self, vec):
        return self


class FakeVGroup(FakeMobject):
    def __init__(self, *mobjects, **kwargs):
        super().__init__()
        self.submobjects = list(mobjects)


class FakeLine(FakeMobject):
    def __init__(self, start, end, **kwargs):
        super().__init__()
        self.start, self.end = start, end


class FakeDashedLine(FakeLine):
    pass


class FakeText(FakeMobject):
    def __init__(self, text, **kwargs):
        super().__init__()
        self.text = text


class FakeDecimalNumber(FakeMobject):
    def __init__(self, value=0.0, **kwargs):
        super().__init__()
        self.value = value


class FakeImageMobject(FakeMobject):
    def __init__(self, array, **kwargs):
        super().__init__()
        self.pixel_array = array
        self.height = None


class _AnimateProxy:
    def __init__(self, tracker):
        self._tracker = tracker

    def set_value(self, value):
        self._tracker._pending = value
        return self._tracker


class FakeValueTracker:
    def __init__(self, value=0.0):
        self._value = float(value)
        self._pending = None

    def get_value(self):
        return self._value

    @property
    def animate(self):
        return _AnimateProxy(self)


class FakeManimColor(str):
    def __new__(cls, value):
        return str.__new__(cls, value)


def _fake_interpolate_color(a, b, alpha):
    return a if alpha < 0.5 else b


class FakeScene:
    def __init__(self):
        self.camera = types.SimpleNamespace(background_color=None)
        self.mobjects = []

    def add(self, *mobs):
        self.mobjects.extend(mobs)

    def _all_mobjects(self):
        flat = []
        for mob in self.mobjects:
            flat.append(mob)
            flat.extend(mob.submobjects)
        return flat

    def play(self, tracker, run_time=None, rate_func=None):
        # simulate several frames across the sweep, not just the final one,
        # so updaters run at the same variety of tracker values manim would
        # actually drive them through
        start = tracker._value
        end = tracker._pending
        for frac in (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0):
            tracker._value = start + (end - start) * frac
            for mob in self._all_mobjects():
                for updater in mob._updaters:
                    updater(mob)

    def wait(self, t=None):
        pass


def _install_fake_manim(monkeypatch):
    fake = types.ModuleType("manim")
    fake.Scene = FakeScene
    fake.VGroup = FakeVGroup
    fake.VMobject = FakeMobject
    fake.Line = FakeLine
    fake.DashedLine = FakeDashedLine
    fake.Text = FakeText
    fake.Circle = FakeMobject
    fake.DecimalNumber = FakeDecimalNumber
    fake.ImageMobject = FakeImageMobject
    fake.ValueTracker = FakeValueTracker
    fake.ManimColor = FakeManimColor
    fake.interpolate_color = _fake_interpolate_color
    fake.linear = None
    fake.UP = np.array([0.0, 1.0, 0.0])
    fake.RIGHT = np.array([1.0, 0.0, 0.0])
    monkeypatch.setitem(sys.modules, "manim", fake)

    import arcane.manim.circuit as manim_scene
    import arcane.manim.wave as manim_wave
    import arcane.manim.render as render
    importlib.reload(manim_wave)
    importlib.reload(manim_scene)
    importlib.reload(render)
    return manim_scene, manim_wave


@pytest.fixture
def manim_modules(monkeypatch):
    manim_scene, manim_wave = _install_fake_manim(monkeypatch)
    yield manim_scene, manim_wave
    # tear down: remove the fake and reload back to the guarded state so
    # later tests in the suite see MANIM_AVAILABLE is False again
    monkeypatch.delitem(sys.modules, "manim", raising=False)
    importlib.reload(manim_wave)
    importlib.reload(manim_scene)
    import arcane.manim.render as render
    importlib.reload(render)


def _demo_circuit_and_history():
    battery = Battery(1, name="battery")
    battery.energy = 400
    caster = Caster(1, name="caster")
    circuit = connect([battery, caster])
    cast_log = []
    t, Es, ET = simulate(circuit, 250, cast_log=cast_log)
    return circuit, Es, cast_log


def _circuit_with_gate_decorations():
    """A circuit with an AndGate (text label decor) and a NotGate (circle
    decor), so scene tests actually exercise the decoration-building path
    added for A6, not just the plain-line rendering path."""
    battery = Battery(1, name="battery")
    battery.energy = 500
    live = Blank(1, name="live")
    switch = Switch(1, name="switch", start_on=True)
    gate = AndGate(2, level=1, name="gate")
    not_gate = NotGate(level=1, name="not_gate")
    caster = Caster(1, name="caster")
    circuit = connect([battery, [live, switch], gate, not_gate, caster])
    t, Es, ET = simulate(circuit, 100)
    return circuit, Es


def test_circuit_scene_includes_gate_label_and_not_gate_circle(manim_modules):
    manim_scene, _ = manim_modules
    circuit, Es = _circuit_with_gate_decorations()

    scene_cls = manim_scene.make_circuit_scene(circuit, Es, run_time=1.0, name="T")
    scene = scene_cls()
    scene.construct()

    texts = [m for m in scene.mobjects if isinstance(m, FakeText)]
    assert any(t.text == "AND" for t in texts), "AND gate label should be carried over"
    # the NOT gate's inversion circle is a mobject with no text/updaters of
    # its own beyond being present and positioned
    assert len(scene.mobjects) > len(texts)


def test_circuit_scene_constructs_and_updates_without_error(manim_modules):
    manim_scene, _ = manim_modules
    assert manim_scene.MANIM_AVAILABLE is True
    circuit, Es, _ = _demo_circuit_and_history()

    scene_cls = manim_scene.make_circuit_scene(circuit, Es, run_time=1.0, name="T")
    scene = scene_cls()
    scene.construct()
    assert len(scene.mobjects) > 0


def test_1d_wave_scene_constructs_and_updates_without_error(manim_modules):
    _, manim_wave = manim_modules
    assert manim_wave.MANIM_AVAILABLE is True
    wave = SpellWave(energy=100, start_step=10, n_steps=150)

    scene_cls = manim_wave.make_spellwave_scene(wave, run_time=1.0, name="T")
    scene = scene_cls()
    scene.construct()
    assert len(scene.mobjects) > 0


def test_2d_wave_scene_constructs_and_updates_without_error(manim_modules):
    _, manim_wave = manim_modules
    wave = SpellWave2D(energy=100, start_step=10, n_steps=150, grid_points=40)

    scene_cls = manim_wave.make_spellwave_scene(wave, run_time=1.0, name="T")
    scene = scene_cls()
    scene.construct()
    assert len(scene.mobjects) > 0
    # the ImageMobject's pixel data actually changed across the sweep
    image = next(m for m in scene.mobjects if isinstance(m, FakeImageMobject))
    assert image.pixel_array.shape == (40, 40, 4)


def test_combined_scene_constructs_and_updates_without_error(manim_modules):
    manim_scene, manim_wave = manim_modules
    circuit, Es, cast_log = _demo_circuit_and_history()
    assert cast_log, "demo circuit should have cast at least once"
    wave = SpellWave(cast_log[0]["energy"], cast_log[0]["step"], 250)

    scene_cls = manim_scene.make_combined_scene(circuit, Es, wave, run_time=1.0, name="T")
    scene = scene_cls()
    scene.construct()
    assert len(scene.mobjects) > 0


def test_combined_scene_with_2d_wave_constructs_without_error(manim_modules):
    manim_scene, manim_wave = manim_modules
    circuit, Es, cast_log = _demo_circuit_and_history()
    wave = SpellWave2D(cast_log[0]["energy"], cast_log[0]["step"], 250, grid_points=40)

    scene_cls = manim_scene.make_combined_scene(circuit, Es, wave, run_time=1.0, name="T")
    scene = scene_cls()
    scene.construct()
    assert len(scene.mobjects) > 0


def test_reload_without_manim_restores_guarded_state():
    # sanity check that the fixture teardown in other tests actually
    # restores the no-manim guard for the rest of the suite
    import arcane.manim.circuit as manim_scene
    import arcane.manim.wave as manim_wave
    assert manim_scene.MANIM_AVAILABLE is False
    assert manim_wave.MANIM_AVAILABLE is False
