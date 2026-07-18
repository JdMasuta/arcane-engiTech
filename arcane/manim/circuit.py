"""Convert a connected circuit and its energy history into a manim Scene.

Geometry comes from arcane.util.layout.trace_layout(); colour comes from
arcane.theme, so an exported video matches the GUI's interactive preview.
Each component's segments recolour and thicken as its recorded energy
rises, driven by a single ValueTracker sweeping the time axis.

manim is imported lazily so the rest of the package works without it.
Render the built-in demo from the CLI (needs an editable install so the
`arcane` package is importable)::

    manim -pql arcane/manim/circuit.py DemoScene

or build a scene for your own circuit::

    from arcane import connect, simulate, make_circuit_scene
    circuit = connect([...])
    t, Es, ET = simulate(circuit, 300)
    MyScene = make_circuit_scene(circuit, Es, run_time=10, name="MyScene")

Prefer arcane.manim.render.render_circuit() to render to a file with explicit
fps/quality control. Text labels (e.g. a LogicGate's "AND") and the NOT
gate's inversion circle are carried over as static mobjects; they don't
animate with energy the way component lines do.
"""
import numpy as np

from arcane.util.layout import trace_layout_with_decor, bbox_center_scale
from arcane.theme import ENERGY_STOPS, energy_fraction, energy_stroke_width

try:
    from manim import (Scene, VGroup, Line, Text, Circle, ValueTracker,
                       ManimColor, interpolate_color, linear)
    MANIM_AVAILABLE = True
except ImportError:
    MANIM_AVAILABLE = False


def _energy_gradient_colors():
    return [ManimColor("#" + stop) for stop in ENERGY_STOPS]


def _color_at(fraction, stops):
    """Piecewise interpolation across the shared multi-stop energy gradient."""
    if fraction <= 0:
        return stops[0]
    if fraction >= 1:
        return stops[-1]
    span = 1.0 / (len(stops) - 1)
    idx = min(int(fraction / span), len(stops) - 2)
    local = (fraction - idx * span) / span
    return interpolate_color(stops[idx], stops[idx + 1], local)


def make_circuit_scene(comp_list, Es, run_time=10.0, name="ArcaneCircuitScene",
                       frame_width=12.0, frame_height=6.0):
    """Build a Scene subclass animating energy flow through the circuit.

    comp_list is a connect()ed circuit and Es a name -> energy-series dict
    as returned by simulation.simulate(). Each component's brightness is
    normalised to its own peak energy so wires and batteries are equally
    readable.
    """
    if not MANIM_AVAILABLE:
        raise ImportError("manim is not installed; pip install manim to use make_circuit_scene")

    n_steps = max((len(series) for series in Es.values()), default=0)

    class CircuitScene(Scene):
        def construct(self):
            self.camera.background_color = ManimColor("#1a1b2e")
            tracker = ValueTracker(0.0)
            groups, decorations = _circuit_mobjects(comp_list, Es, tracker,
                                                    frame_width, frame_height)
            self.add(*groups, *decorations)
            if n_steps > 1:
                self.play(tracker.animate.set_value(n_steps - 1),
                          run_time=run_time, rate_func=linear)
                for group in groups:
                    group.clear_updaters()
            self.wait(0.5)

    CircuitScene.__name__ = name
    CircuitScene.__qualname__ = name
    return CircuitScene


def _circuit_mobjects(comp_list, Es, tracker, frame_width, frame_height, y_offset=0.0):
    """Build the circuit's VGroups (one per component, with an energy
    updater already attached) and its static decorations (gate labels, the
    NOT gate's inversion circle), shifted vertically by y_offset. Returns
    (groups, decorations). Shared by make_circuit_scene and
    make_combined_scene so both draw the same way.
    """
    record, decor, bbox = trace_layout_with_decor(comp_list)
    (cx, cy), scale = bbox_center_scale(bbox, frame_width, frame_height)
    stops = _energy_gradient_colors()

    def to_point(x, y):
        return np.array([(x - cx) * scale, (y - cy) * scale + y_offset, 0.0])

    groups = []
    for comp, segs in record.items():
        lines = VGroup(*[
            Line(to_point(seg[0][k], seg[1][k]),
                 to_point(seg[0][k + 1], seg[1][k + 1]),
                 stroke_width=2, color=stops[0])
            for seg in segs for k in range(seg.shape[1] - 1)
        ])
        series = Es.get(getattr(comp, 'name', None))
        if series:
            def updater(mob, series=series):
                frac = energy_fraction(series, int(tracker.get_value()))
                mob.set_stroke(color=_color_at(frac, stops),
                               width=energy_stroke_width(frac))
            lines.add_updater(updater)
        groups.append(lines)

    decorations = []
    for entries in decor.values():
        for x, y, text in entries.get('texts', []):
            label = Text(text, font_size=16, color=stops[0])
            label.move_to(to_point(x, y))
            decorations.append(label)
        for x, y, radius in entries.get('circles', []):
            circle = Circle(radius=radius * scale, color=stops[0])
            circle.move_to(to_point(x, y))
            decorations.append(circle)

    return groups, decorations


def make_combined_scene(comp_list, Es, wave, run_time=10.0,
                        name="ArcaneCombinedScene", frame_width=12.0):
    """Build a Scene with the circuit schematic above the spell wave it
    cast, sharing one ValueTracker so both halves animate on the same
    circuit-step timeline.

    wave (a SpellWave or SpellWave2D) must come from the same run that
    produced Es — e.g. simulation.simulate(circuit, n, cast_log=log) then
    spellwave.waves_from_cast_log(log, n) — since both are driven by the
    same global circuit-step index.
    """
    if not MANIM_AVAILABLE:
        raise ImportError("manim is not installed; pip install manim to use make_combined_scene")

    from arcane.manim.wave import build_wave_mobjects

    n_steps = max((len(series) for series in Es.values()), default=0)
    duration = max(n_steps, wave.P.shape[0] + wave.start_step)

    class CombinedScene(Scene):
        def construct(self):
            self.camera.background_color = ManimColor("#1a1b2e")
            tracker = ValueTracker(0.0)

            circuit_groups, circuit_decor = _circuit_mobjects(
                comp_list, Es, tracker, frame_width, frame_height=4.2, y_offset=2.0)
            wave_mobjects, wave_updated = build_wave_mobjects(
                wave, tracker, y_offset=-2.2, height_scale=0.55, frame_width=frame_width)

            self.add(*circuit_groups, *circuit_decor, *wave_mobjects)
            self.play(tracker.animate.set_value(duration - 1),
                      run_time=run_time, rate_func=linear)
            for group in circuit_groups:
                group.clear_updaters()
            for mob in wave_updated:
                mob.clear_updaters()
            self.wait(0.5)

    CombinedScene.__name__ = name
    CombinedScene.__qualname__ = name
    return CombinedScene


if MANIM_AVAILABLE:
    def _build_demo_scene():
        from arcane.components import Battery, Switch, Caster, connect
        from arcane.util.simulation import simulate

        battery = Battery(2, name="battery")
        battery.energy = 300
        switch = Switch(2, name="switch")
        casters = [Caster(2, name=f"caster {i}") for i in (1, 2)]
        circuit = connect([battery, switch, casters])
        t, Es, ET = simulate(circuit, 300, events={20: switch.toggle})
        return make_circuit_scene(circuit, Es, run_time=8.0, name="DemoScene")

    DemoScene = _build_demo_scene()
