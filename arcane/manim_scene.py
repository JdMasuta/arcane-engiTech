"""Convert a connected circuit and its energy history into a manim Scene.

Geometry comes from arcane.layout.trace_layout(); colour comes from
arcane.theme, so an exported video matches the GUI's interactive preview.
Each component's segments recolour and thicken as its recorded energy
rises, driven by a single ValueTracker sweeping the time axis.

manim is imported lazily so the rest of the package works without it.
Render the built-in demo from the CLI (needs an editable install so the
`arcane` package is importable)::

    manim -pql arcane/manim_scene.py DemoScene

or build a scene for your own circuit::

    from arcane import connect, simulate, make_circuit_scene
    circuit = connect([...])
    t, Es, ET = simulate(circuit, 300)
    MyScene = make_circuit_scene(circuit, Es, run_time=10, name="MyScene")

Prefer arcane.render.render_circuit() to render to a file with explicit
fps/quality control. Known limits: only line segments are converted (patch
decorations like the NOT gate's inversion circle are skipped) and text
labels are not carried over.
"""
import numpy as np

from arcane.layout import trace_layout, bbox_center_scale
from arcane.theme import ENERGY_STOPS, energy_fraction, energy_stroke_width

try:
    from manim import (Scene, VGroup, Line, ValueTracker, ManimColor,
                       interpolate_color, linear)
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

    record, bbox = trace_layout(comp_list)
    (cx, cy), scale = bbox_center_scale(bbox, frame_width, frame_height)
    stops = _energy_gradient_colors()

    def to_point(x, y):
        return np.array([(x - cx) * scale, (y - cy) * scale, 0.0])

    n_steps = max((len(series) for series in Es.values()), default=0)

    class CircuitScene(Scene):
        def construct(self):
            self.camera.background_color = ManimColor("#1a1b2e")
            tracker = ValueTracker(0.0)
            groups = []
            for comp, segs in record.items():
                lines = VGroup(*[
                    Line(to_point(seg[0][k], seg[1][k]),
                         to_point(seg[0][k + 1], seg[1][k + 1]),
                         stroke_width=2, color=stops[0])
                    for seg in segs for k in range(seg.shape[1] - 1)
                ])
                self.add(lines)
                series = Es.get(getattr(comp, 'name', None))
                if series:
                    def updater(mob, series=series):
                        frac = energy_fraction(series, int(tracker.get_value()))
                        mob.set_stroke(color=_color_at(frac, stops),
                                       width=energy_stroke_width(frac))
                    lines.add_updater(updater)
                groups.append(lines)
            if n_steps > 1:
                self.play(tracker.animate.set_value(n_steps - 1),
                          run_time=run_time, rate_func=linear)
                for group in groups:
                    group.clear_updaters()
            self.wait(0.5)

    CircuitScene.__name__ = name
    CircuitScene.__qualname__ = name
    return CircuitScene


if MANIM_AVAILABLE:
    def _build_demo_scene():
        from arcane.components import Battery, Switch, Caster, connect
        from arcane.simulation import simulate

        battery = Battery(2, name="battery")
        battery.energy = 300
        switch = Switch(2, name="switch")
        casters = [Caster(2, name=f"caster {i}") for i in (1, 2)]
        circuit = connect([battery, switch, casters])
        t, Es, ET = simulate(circuit, 300, events={20: switch.toggle})
        return make_circuit_scene(circuit, Es, run_time=8.0, name="DemoScene")

    DemoScene = _build_demo_scene()
