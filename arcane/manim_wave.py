"""Manim scene animating a SpellWave's renormalized propagation.

The renormalized density P(x, t) sweeps from launch toward max range as a
glowing curve; a counter shows the renormalization constant A(t) climbing
as the absorber eats the raw norm, and the curve collapses when the spell
fizzles. Uses the wave's precomputed per-step arrays driven by a single
ValueTracker, mirroring the manim_scene.py pattern.

manim is imported lazily so the rest of the package works without it.
"""
import numpy as np

from arcane.theme import ENERGY_STOPS

try:
    from manim import (Scene, VMobject, Line, DashedLine, Text, DecimalNumber,
                       ValueTracker, ManimColor, linear, UP, RIGHT)
    MANIM_AVAILABLE = True
except ImportError:
    MANIM_AVAILABLE = False

FRAME_WIDTH = 12.0
CURVE_HEIGHT = 4.5
BASELINE_Y = -2.5


def make_spellwave_scene(wave, run_time=8.0, name="SpellWaveScene"):
    """Build a Scene subclass animating one SpellWave.

    wave is an arcane.spellwave.SpellWave; its precomputed history drives
    the animation over the wave's own lifetime (start_step .. n_steps).
    """
    if not MANIM_AVAILABLE:
        raise ImportError("manim is not installed; pip install manim to use make_spellwave_scene")

    duration = wave.P.shape[0]
    if duration < 2:
        raise ValueError("wave has no timeline to animate")

    energy_density = wave.energy * wave.P
    peak = float(energy_density.max()) or 1.0
    x_span = float(wave.x[-1] - wave.x[0])
    accent = ManimColor("#" + ENERGY_STOPS[2])
    gold = ManimColor("#" + ENERGY_STOPS[3])
    idle = ManimColor("#" + ENERGY_STOPS[0])
    # A(t) display: hold zero after the fizzle instead of propagating NaN
    a_display = np.where(wave.alive, np.nan_to_num(wave.A, nan=0.0), 0.0)

    def to_point(x, y_frac):
        frame_x = (x - wave.x[0]) / x_span * FRAME_WIDTH - FRAME_WIDTH / 2
        return np.array([frame_x, BASELINE_Y + y_frac * CURVE_HEIGHT, 0.0])

    class SpellWaveScene(Scene):
        def construct(self):
            self.camera.background_color = ManimColor("#1a1b2e")
            tracker = ValueTracker(0.0)

            baseline = Line(to_point(wave.x[0], 0.0), to_point(wave.x[-1], 0.0),
                            stroke_width=2, color=idle)
            range_marker = DashedLine(to_point(wave.max_range, 0.0),
                                      to_point(wave.max_range, 1.0),
                                      stroke_width=2, color=gold)
            range_label = Text("max range", font_size=20, color=gold)
            range_label.next_to(range_marker, UP, buff=0.15)

            curve = VMobject(stroke_width=4, color=accent)

            def update_curve(mob):
                i = min(int(tracker.get_value()), duration - 1)
                ys = energy_density[i] / peak
                mob.set_points_as_corners(
                    [to_point(x, y) for x, y in zip(wave.x, ys)])
            curve.add_updater(update_curve)
            update_curve(curve)

            a_label = Text("A(t) =", font_size=24, color=gold)
            a_number = DecimalNumber(float(a_display[0]), num_decimal_places=2,
                                     font_size=30, color=gold)

            def update_a(mob):
                i = min(int(tracker.get_value()), duration - 1)
                mob.set_value(float(a_display[i]))
            a_number.add_updater(update_a)
            a_group_anchor = a_label.to_corner(UP + RIGHT).shift(
                np.array([-1.2, 0.0, 0.0]))
            a_number.next_to(a_group_anchor, RIGHT, buff=0.15)

            self.add(baseline, range_marker, range_label, curve,
                     a_label, a_number)
            self.play(tracker.animate.set_value(duration - 1),
                      run_time=run_time, rate_func=linear)
            curve.clear_updaters()
            a_number.clear_updaters()
            self.wait(0.5)

    SpellWaveScene.__name__ = name
    SpellWaveScene.__qualname__ = name
    return SpellWaveScene
