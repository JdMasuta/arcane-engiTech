"""Convert a connected circuit and its energy history into a manim Scene.

The geometry is not re-invented: trace_layout() replays the existing
matplotlib plot() walk with recording enabled and reuses the exact line
segments each component symbol draws. Each component's segments are then
animated by recolouring/thickening them as its recorded energy rises,
driven by a single ValueTracker sweeping the time axis.

Requires manim (pip install manim), which is only imported when available
so the rest of the package works without it. Render the built-in demo with:

    manim -pql scripts/manim_scene.py DemoScene

or build a scene for your own circuit:

    from components import *
    from simulation import simulate
    from manim_scene import make_circuit_scene

    circuit = connect([...])
    t, Es, ET = simulate(circuit, 300)
    MyScene = make_circuit_scene(circuit, Es, run_time=10, name="MyScene")

Known limits: only line segments are converted (patch decorations like the
NOT gate's inversion circle are skipped), and text labels are not carried
over.
"""
import numpy as np
import matplotlib.pyplot as plt

from components import plot as circuit_plot

try:
    from manim import Scene, VGroup, Line, ValueTracker, interpolate_color, GREY, YELLOW, linear
    MANIM_AVAILABLE = True
except ImportError:
    MANIM_AVAILABLE = False


def trace_layout(comp_list):
    """Replay plot() silently and return ({component: segments}, bbox).

    Segments are 2xN arrays of xy data; the '__wrap__' key holds the
    depth-0 wrap-around wire. bbox is (xmin, xmax, ymin, ymax).
    """
    fig, ax = plt.subplots()
    record = {}
    circuit_plot(comp_list, ax=ax, record=record, show=False)
    plt.close(fig)
    all_segs = [seg for segs in record.values() for seg in segs]
    xs = np.concatenate([seg[0] for seg in all_segs])
    ys = np.concatenate([seg[1] for seg in all_segs])
    return record, (xs.min(), xs.max(), ys.min(), ys.max())


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

    record, (x0, x1, y0, y1) = trace_layout(comp_list)
    scale = min(frame_width / max(x1 - x0, 1e-6), frame_height / max(y1 - y0, 1e-6))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

    def to_point(x, y):
        return np.array([(x - cx) * scale, (y - cy) * scale, 0.0])

    n_steps = max((len(series) for series in Es.values()), default=0)

    class CircuitScene(Scene):
        def construct(self):
            tracker = ValueTracker(0.0)
            groups = []
            for comp, segs in record.items():
                lines = VGroup(*[
                    Line(to_point(seg[0][k], seg[1][k]),
                         to_point(seg[0][k + 1], seg[1][k + 1]),
                         stroke_width=2, color=GREY)
                    for seg in segs for k in range(seg.shape[1] - 1)
                ])
                self.add(lines)
                series = Es.get(getattr(comp, 'name', None))
                if series:
                    norm = max(max(series), 1e-9)

                    def updater(mob, series=series, norm=norm):
                        i = min(int(tracker.get_value()), len(series) - 1)
                        frac = min(series[i] / norm, 1.0)
                        mob.set_stroke(color=interpolate_color(GREY, YELLOW, frac),
                                       width=2 + 6 * frac)
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
        from components import Battery, Switch, Caster, connect
        from simulation import simulate

        battery = Battery(2, name="battery")
        battery.energy = 300
        switch = Switch(2, name="switch")
        casters = [Caster(2, name=f"caster {i}") for i in (1, 2)]
        circuit = connect([battery, switch, casters])
        t, Es, ET = simulate(circuit, 300, events={20: switch.toggle})
        return make_circuit_scene(circuit, Es, run_time=8.0, name="DemoScene")

    DemoScene = _build_demo_scene()
