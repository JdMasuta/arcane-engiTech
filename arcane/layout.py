"""Turn a connected circuit into reusable 2D geometry.

trace_layout() replays the matplotlib plot() walk with recording enabled
and hands back the exact line segments each component symbol drew, keyed by
component. Both the GUI preview and the manim export build on this so they
never disagree about where a component sits.
"""
import matplotlib.pyplot as plt
import numpy as np

from arcane.components import plot as circuit_plot

WRAP_KEY = "__wrap__"


def trace_layout(comp_list):
    """Replay plot() silently and return (record, bbox).

    record maps each component (and the WRAP_KEY sentinel for the wrap-around
    wire) to a list of 2xN xy segment arrays. bbox is (xmin, xmax, ymin, ymax).
    """
    fig, ax = plt.subplots()
    record = {}
    circuit_plot(comp_list, ax=ax, record=record, show=False)
    plt.close(fig)
    all_segs = [seg for segs in record.values() for seg in segs]
    if not all_segs:
        return record, (0.0, 1.0, 0.0, 1.0)
    xs = np.concatenate([seg[0] for seg in all_segs])
    ys = np.concatenate([seg[1] for seg in all_segs])
    return record, (float(xs.min()), float(xs.max()), float(ys.min()), float(ys.max()))


def bbox_center_scale(bbox, frame_width, frame_height):
    """Center offset and uniform scale that fit bbox into a frame."""
    x0, x1, y0, y1 = bbox
    scale = min(frame_width / max(x1 - x0, 1e-6), frame_height / max(y1 - y0, 1e-6))
    return ((x0 + x1) / 2, (y0 + y1) / 2), scale
