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
    record, _decor, bbox = _trace(comp_list, capture_decor=False)
    return record, bbox


def trace_layout_with_decor(comp_list):
    """Like trace_layout, but also captures each component's text labels
    and circle patches (a LogicGate's label, the NOT gate's inversion
    circle) as {"texts": [(x, y, string)], "circles": [(x, y, radius)]}
    per component. Returns (record, decor, bbox). Used by the manim
    converter to carry those decorations into rendered scenes; the GUI
    preview doesn't need them and keeps using plain trace_layout.
    """
    return _trace(comp_list, capture_decor=True)


def _trace(comp_list, capture_decor):
    fig, ax = plt.subplots()
    record = {}
    decor = {} if capture_decor else None
    circuit_plot(comp_list, ax=ax, record=record, decor=decor, show=False)
    plt.close(fig)
    all_segs = [seg for segs in record.values() for seg in segs]
    if not all_segs:
        bbox = (0.0, 1.0, 0.0, 1.0)
    else:
        xs = np.concatenate([seg[0] for seg in all_segs])
        ys = np.concatenate([seg[1] for seg in all_segs])
        bbox = (float(xs.min()), float(xs.max()), float(ys.min()), float(ys.max()))
    return record, (decor if decor is not None else {}), bbox


def bbox_center_scale(bbox, frame_width, frame_height):
    """Center offset and uniform scale that fit bbox into a frame."""
    x0, x1, y0, y1 = bbox
    scale = min(frame_width / max(x1 - x0, 1e-6), frame_height / max(y1 - y0, 1e-6))
    return ((x0 + x1) / 2, (y0 + y1) / 2), scale
