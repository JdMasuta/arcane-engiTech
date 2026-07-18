"""Schematic canvas that recolours each component by its energy at a step."""
from matplotlib.lines import Line2D
import numpy as np

from arcane import theme
from arcane.util.layout import trace_layout, WRAP_KEY
from arcane.gui.mpl_canvas import ThemedCanvas


class CircuitView(ThemedCanvas):
    """Draws the circuit once, then restyles its line segments on scrub."""

    def __init__(self, parent=None):
        super().__init__(parent, facecolor=theme.BACKGROUND)
        self.ax.set_axis_off()
        self.ax.set_aspect("equal")
        self._lines_by_name = {}
        self._Es = {}
        self._labels = []

    def set_circuit(self, comp_list):
        self.ax.clear()
        self.ax.set_axis_off()
        self.ax.set_aspect("equal")
        self._lines_by_name.clear()
        self._labels.clear()

        record, bbox = trace_layout(comp_list)
        idle = "#" + theme.IDLE_COLOR
        for comp, segments in record.items():
            name = getattr(comp, "name", None)
            drawn = []
            for seg in segments:
                line = Line2D(seg[0], seg[1], color=idle, solid_capstyle="round",
                              linewidth=theme.energy_stroke_width(0.0))
                self.ax.add_line(line)
                drawn.append(line)
            if name is not None and name != WRAP_KEY:
                self._lines_by_name.setdefault(name, []).extend(drawn)
                self._add_label(name, segments)

        x0, x1, y0, y1 = bbox
        mx = 0.08 * max(x1 - x0, 1e-6)
        my = 0.14 * max(y1 - y0, 1e-6)
        self.ax.set_xlim(x0 - mx, x1 + mx)
        self.ax.set_ylim(y0 - my, y1 + my)
        self.draw_idle()

    def _add_label(self, name, segments):
        if "wire" in name or "junction" in name:
            return
        pts = np.concatenate([seg for seg in segments], axis=1)
        cx, cy = float(pts[0].mean()), float(pts[1].max())
        text = self.ax.text(cx, cy + 0.35, name, ha="center", va="bottom",
                            fontsize=7, color="#" + theme.TEXT_MUTED)
        self._labels.append(text)

    def set_history(self, Es):
        self._Es = Es or {}

    def set_step(self, step):
        for name, lines in self._lines_by_name.items():
            frac = theme.energy_fraction(self._Es.get(name), step)
            color = theme.energy_color(frac)
            width = theme.energy_stroke_width(frac)
            for line in lines:
                line.set_color(color)
                line.set_linewidth(width)
        self.draw_idle()
