"""Energy-over-time canvas with a scrubbable time cursor."""
from arcane import theme
from arcane.gui.mpl_canvas import ThemedCanvas

# Distinct hues for component traces, cycled; total energy is drawn separately.
_TRACE_COLORS = ["b06cf0", "ffd36e", "4ec9b0", "e06c9a", "6c9ae0", "d0913f",
                 "9a6ce0", "5fd0a0"]


class EnergyView(ThemedCanvas):
    """Plots per-component energy series and a movable time cursor."""

    def __init__(self, parent=None):
        super().__init__(parent, facecolor=theme.SURFACE)
        self._cursor = None
        self._t = []
        self.ax.set_xlabel("Time step")
        self.ax.set_ylabel("Energy")

    def set_history(self, t, Es, ET, names, log_scale=False):
        self.ax.clear()
        self._style_axes()
        self._t = t
        self.ax.set_xlabel("Time step")
        self.ax.set_ylabel("Energy")
        self.ax.grid(True, color="#" + theme.BORDER, alpha=0.4, linewidth=0.6)

        for i, name in enumerate(names):
            series = Es.get(name)
            if series is None:
                continue
            self.ax.plot(t, series, label=name, linewidth=1.4,
                         color="#" + _TRACE_COLORS[i % len(_TRACE_COLORS)])
        if ET:
            self.ax.plot(t, ET, label="Total", linewidth=1.6, ls="--",
                         color="#" + theme.TEXT_MUTED)
        if log_scale:
            self.ax.set_yscale("log")
        if names or ET:
            legend = self.ax.legend(loc="upper right", fontsize=7, ncol=2,
                                    framealpha=0.0)
            for text in legend.get_texts():
                text.set_color("#" + theme.TEXT)
        self._cursor = self.ax.axvline(t[0] if t else 0, color="#" + theme.GOLD,
                                       linewidth=1.2, alpha=0.9)
        self.draw_idle()

    def set_step(self, step):
        if self._cursor is None or not self._t:
            return
        step = max(0, min(step, len(self._t) - 1))
        self._cursor.set_xdata([self._t[step], self._t[step]])
        self.draw_idle()
