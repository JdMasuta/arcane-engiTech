"""Manim scenes animating a spell wave's renormalized propagation.

The renormalized density sweeps from launch toward max range; a counter
shows the renormalization constant A(t) climbing as the absorber eats the
raw norm, and the display collapses when the spell fizzles. Uses the
wave's precomputed per-step arrays driven by a single ValueTracker.

make_spellwave_scene() dispatches on the wave's type: a SpellWave (1D
radial model) becomes a glowing curve sweeping toward a range marker; a
SpellWave2D becomes an animated heatmap image. The 2D path relies on
manim's ImageMobject.pixel_array being directly mutable per-frame, which
is the standard idiom for animating raster data in manim but — like the
rest of this module — is untested against a real manim install in this
environment; verify a real render before relying on it.

build_wave_mobjects() is the reusable half: it returns the mobjects
(and which of them carry updaters) for one wave positioned at a given
vertical offset and scale, without wrapping them in a Scene. manim_scene's
make_combined_scene() uses this to place a wave beneath a circuit
schematic on one shared ValueTracker; make_spellwave_scene() itself just
calls it with the standalone defaults.

manim is imported lazily so the rest of the package works without it.
"""
import numpy as np

from arcane.theme import ENERGY_STOPS, energy_cmap
from arcane.spellwave import SpellWave2D

try:
    from manim import (Scene, VMobject, Line, DashedLine, Text, DecimalNumber,
                       ValueTracker, ManimColor, ImageMobject, linear, UP, RIGHT)
    MANIM_AVAILABLE = True
except ImportError:
    MANIM_AVAILABLE = False

FRAME_WIDTH = 12.0
CURVE_HEIGHT = 4.5
BASELINE_Y = -2.5


def make_spellwave_scene(wave, run_time=8.0, name="SpellWaveScene"):
    """Build a Scene subclass animating one spell wave.

    wave is an arcane.spellwave.SpellWave or SpellWave2D; its precomputed
    history drives the animation over the wave's own lifetime (start_step
    .. n_steps).
    """
    if not MANIM_AVAILABLE:
        raise ImportError("manim is not installed; pip install manim to use make_spellwave_scene")

    duration = wave.P.shape[0]
    if duration < 2:
        raise ValueError("wave has no timeline to animate")

    class SpellWaveScene(Scene):
        def construct(self):
            self.camera.background_color = ManimColor("#1a1b2e")
            tracker = ValueTracker(0.0)
            mobjects, updated = build_wave_mobjects(wave, tracker)
            self.add(*mobjects)
            self.play(tracker.animate.set_value(duration - 1),
                      run_time=run_time, rate_func=linear)
            for mob in updated:
                mob.clear_updaters()
            self.wait(0.5)

    SpellWaveScene.__name__ = name
    SpellWaveScene.__qualname__ = name
    return SpellWaveScene


def build_wave_mobjects(wave, tracker, y_offset=0.0, height_scale=1.0,
                        frame_width=FRAME_WIDTH):
    """Build (mobjects_to_add, mobjects_with_updaters) for one wave.

    Dispatches on wave's type (SpellWave vs SpellWave2D). y_offset shifts
    the whole block vertically and height_scale shrinks it, so a caller
    (make_combined_scene) can fit a wave into part of a shared frame
    alongside other content while driving it from its own tracker.
    """
    if isinstance(wave, SpellWave2D):
        return _build_2d_wave_mobjects(wave, tracker, y_offset, height_scale)
    return _build_1d_wave_mobjects(wave, tracker, y_offset, height_scale, frame_width)


def _build_1d_wave_mobjects(wave, tracker, y_offset, height_scale, frame_width):
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
    curve_height = CURVE_HEIGHT * height_scale
    baseline_y = BASELINE_Y * height_scale + y_offset

    def to_point(x, y_frac):
        frame_x = (x - wave.x[0]) / x_span * frame_width - frame_width / 2
        return np.array([frame_x, baseline_y + y_frac * curve_height, 0.0])

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
        mob.set_points_as_corners([to_point(x, y) for x, y in zip(wave.x, ys)])
    curve.add_updater(update_curve)
    update_curve(curve)

    a_label = Text("A(t) =", font_size=24, color=gold)
    a_number = DecimalNumber(float(a_display[0]), num_decimal_places=2,
                             font_size=30, color=gold)

    def update_a(mob):
        i = min(int(tracker.get_value()), duration - 1)
        mob.set_value(float(a_display[i]))
    a_number.add_updater(update_a)
    a_anchor = np.array([frame_width / 2 - 2.6, baseline_y + curve_height * 0.85, 0.0])
    a_label.move_to(a_anchor)
    a_number.next_to(a_label, RIGHT, buff=0.15)

    mobjects = [baseline, range_marker, range_label, curve, a_label, a_number]
    return mobjects, [curve, a_number]


def _energy_to_rgba(field, peak):
    """Map a 2D energy-density array through the shared theme gradient to
    an RGBA uint8 image, for manim's ImageMobject."""
    norm = np.clip(field / (peak or 1.0), 0.0, 1.0)
    return (energy_cmap(norm) * 255).astype(np.uint8)


def _build_2d_wave_mobjects(wave, tracker, y_offset, height_scale):
    duration = wave.P.shape[0]
    if duration < 2:
        raise ValueError("wave has no timeline to animate")

    energy_density = wave.energy * wave.P  # shape (duration, ny, nx)
    peak = float(energy_density.max()) or 1.0
    frames_rgba = [_energy_to_rgba(energy_density[i], peak) for i in range(duration)]
    gold = ManimColor("#" + ENERGY_STOPS[3])
    # A(t) display: hold zero after the fizzle instead of propagating NaN
    a_display = np.where(wave.alive, np.nan_to_num(wave.A, nan=0.0), 0.0)
    image_height = (CURVE_HEIGHT + 2.0) * height_scale

    image = ImageMobject(frames_rgba[0])
    image.height = image_height
    image.move_to(np.array([0.0, y_offset, 0.0]))

    def update_image(mob):
        i = min(int(tracker.get_value()), duration - 1)
        mob.pixel_array = frames_rgba[i]
    image.add_updater(update_image)

    range_label = Text(f"max range = {wave.max_range:.0f}", font_size=20, color=gold)
    range_label.move_to(np.array([0.0, y_offset + image_height / 2 + 0.3, 0.0]))

    a_label = Text("A(t) =", font_size=24, color=gold)
    a_number = DecimalNumber(float(a_display[0]), num_decimal_places=2,
                             font_size=30, color=gold)
    a_label.move_to(np.array([image_height * 0.9, y_offset + image_height / 2 - 0.3, 0.0]))
    a_number.next_to(a_label, RIGHT, buff=0.15)

    def update_a(mob):
        i = min(int(tracker.get_value()), duration - 1)
        mob.set_value(float(a_display[i]))
    a_number.add_updater(update_a)

    mobjects = [image, range_label, a_label, a_number]
    return mobjects, [image, a_number]
