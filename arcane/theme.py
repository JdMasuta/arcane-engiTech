"""Shared visual language for the whole app.

One palette and one energy gradient drive the Qt chrome, the matplotlib
preview canvases, and the manim export, so the interactive scrub and the
rendered video read as the same picture.
"""
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# Core "arcane" palette (hex, no leading '#').
BACKGROUND = "1a1b2e"
SURFACE = "24263a"
SURFACE_LIGHT = "2f3350"
BORDER = "3b3f63"
TEXT = "e8e6f5"
TEXT_MUTED = "9a98b8"
ACCENT = "b06cf0"      # primary arcane violet
ACCENT_DIM = "6c4a94"
GOLD = "ffd36e"

# Energy gradient: idle indigo -> arcane magenta -> hot gold.
ENERGY_STOPS = ["3a3f5f", "8a3fd0", "d94ec7", "ffd36e"]
IDLE_COLOR = ENERGY_STOPS[0]

energy_cmap = LinearSegmentedColormap.from_list(
    "arcane_energy", ["#" + stop for stop in ENERGY_STOPS]
)


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def energy_fraction(series, step):
    """Peak-normalised energy of a component at a step, clamped to [0, 1].

    Normalising to each series' own peak keeps low-capacity wires as
    readable as high-capacity batteries.
    """
    if not series:
        return 0.0
    peak = max(series) or 1e-9
    step = max(0, min(step, len(series) - 1))
    return float(np.clip(series[step] / peak, 0.0, 1.0))


def energy_color(fraction):
    """RGBA tuple from the shared gradient for a fraction in [0, 1]."""
    return energy_cmap(float(np.clip(fraction, 0.0, 1.0)))


def energy_stroke_width(fraction, base=1.6, gain=5.0):
    return base + gain * float(np.clip(fraction, 0.0, 1.0))
