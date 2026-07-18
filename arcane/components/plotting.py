"""Draw a connected circuit as a schematic (with optional capture).

plot() walks the connect()ed structure end to end; with record/decor
dicts it also captures each component's line segments and decorations
for the layout/manim pipeline (see arcane.util.layout).
"""
import matplotlib.pyplot as plt
import numpy as np

from arcane.components.junction import Junction


def wrap_around(end_point, wrap_to=[0, 0], buffer=3., ax=None):
    if ax is None:
        ax = plt.gca()
    wire_line = np.array([[end_point[0], end_point[0] + buffer,
                           end_point[0] + buffer, wrap_to[0] - buffer,
                           wrap_to[0] - buffer, wrap_to[0]],
                          [end_point[1], end_point[1], end_point[1] - buffer,
                           end_point[1] - buffer, end_point[1], end_point[1]]])
    ax.plot(wire_line[0], wire_line[1])


def plot(comp_list, buffer=3., start_point=[0, 0], depth=0, ax=None, record=None,
         decor=None, show=True):
    """Draw the circuit; when record is a dict it also captures, per
    component, the xy line segments its symbol drew (used by the manim
    converter). When decor is a dict it likewise captures each component's
    text labels and circle patches (e.g. a LogicGate's label, the NOT
    gate's inversion circle) as {"texts": [(x, y, string)], "circles":
    [(x, y, radius)]}, for scenes that want to carry those over too.
    """
    n_components = len(comp_list)
    start_point_init = start_point.copy()
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(5, 5))

    def capture(comp, plot_call):
        if record is None and decor is None:
            return (plot_call())
        n0_lines = len(ax.lines)
        n0_texts = len(ax.texts)
        n0_patches = len(ax.patches)
        result = plot_call()
        if record is not None:
            record.setdefault(comp, []).extend(
                [np.array(line.get_data()) for line in ax.lines[n0_lines:]])
        if decor is not None:
            for text_obj in ax.texts[n0_texts:]:
                x, y = text_obj.get_position()
                decor.setdefault(comp, {}).setdefault('texts', []).append(
                    (x, y, text_obj.get_text()))
            for patch in ax.patches[n0_patches:]:
                if isinstance(patch, plt.Circle):
                    cx, cy = patch.center
                    decor.setdefault(comp, {}).setdefault('circles', []).append(
                        (cx, cy, patch.radius))
        return (result)

    for i in range(n_components):
        comp = comp_list[i]
        role = getattr(comp, 'junction_role', None)
        is_opening = isinstance(
            comp, Junction) and (
            role == 'open' or (
                role is None and "-" not in comp.name))
        is_closing = isinstance(
            comp, Junction) and (
            role == 'close' or (
                role is None and "-" in comp.name))
        if is_opening:
            end_points = capture(comp, lambda: comp.plot([start_point], ax=ax))
            # plot branches
            junction_close_points = []
            for k, scl in enumerate(comp_list[i + 1]):
                sub_end_point = plot(
                    scl,
                    start_point=end_points[k],
                    depth=depth + 1,
                    ax=ax,
                    record=record,
                    decor=decor)
                junction_close_points.append(sub_end_point)
            # plot closing
            end_point = capture(comp_list[i + 2], lambda: comp_list[i +
                                2].plot(junction_close_points, ax=ax))[0]
            start_point = np.array(end_point)

        elif isinstance(comp, list) or is_closing:
            continue
        else:
            end_point = capture(comp, lambda: comp.plot(start_point, ax=ax))
            start_point = np.array(end_point)  # + np.array([buffer,0])
    if depth == 0:
        if record is None:
            wrap_around(end_point, wrap_to=start_point_init, buffer=buffer, ax=ax)
        else:
            n0 = len(ax.lines)
            wrap_around(end_point, wrap_to=start_point_init, buffer=buffer, ax=ax)
            record.setdefault('__wrap__', []).extend(
                [np.array(line.get_data()) for line in ax.lines[n0:]])
        if show:
            plt.show()
        return (end_point)
    else:
        return (end_point)
