"""Spell propagation canvas: renormalized wave packets on the scrub timeline.

Two stacked axes on one themed figure:
- top (space): the renormalized energy density E*P(x) of every spell wave
  at the scrubbed step, with the max-range absorber marked and an A(t)
  readout showing the renormalization constant at work;
- bottom (time): the classical model's energy blowing up toward max range
  (the ultra-magic catastrophe, log scale) against the finite renormalized
  total, with the shared gold time cursor.
"""
from arcane import theme
from arcane.gui.energy_view import _TRACE_COLORS
from arcane.gui.mpl_canvas import ThemedCanvas


class SpellWaveView(ThemedCanvas):
    def __init__(self, parent=None):
        super().__init__(parent, facecolor=theme.SURFACE)
        self.figure.clf()
        grid = self.figure.add_gridspec(2, 1, height_ratios=(2.2, 1.0))
        self.ax_space = self.figure.add_subplot(grid[0])
        self.ax_time = self.figure.add_subplot(grid[1])
        self.ax = self.ax_space
        self._waves = []
        self._space_lines = []
        self._cursor = None
        self._readout = None
        self._hint = None
        self._show_empty_hint()

    def _show_empty_hint(self):
        for ax in (self.ax_space, self.ax_time):
            ax.clear()
            self._style_axes(ax)
            ax.set_xticks([])
            ax.set_yticks([])
        self._hint = self.ax_space.text(
            0.5, 0.5, "Run a simulation — every cast spawns a spell wave",
            transform=self.ax_space.transAxes, ha="center", va="center",
            color="#" + theme.TEXT_MUTED, fontsize=10)
        self.draw_idle()

    def _wave_color(self, index):
        return "#" + _TRACE_COLORS[index % len(_TRACE_COLORS)]

    def set_waves(self, waves, show_classical=True):
        """Rebuild both axes for a new simulation run's waves."""
        self._waves = list(waves or [])
        self._space_lines = []
        self._cursor = None
        self._readout = None
        if not self._waves:
            self._show_empty_hint()
            return

        for ax in (self.ax_space, self.ax_time):
            ax.clear()
            self._style_axes(ax)

        max_range = max(w.max_range for w in self._waves)
        x_max = max(float(w.x[-1]) for w in self._waves)
        peak = max(float((w.energy * w.P).max()) for w in self._waves) or 1.0

        self.ax_space.axvspan(max_range * 0.9, x_max,
                              color="#" + theme.ACCENT_DIM, alpha=0.18)
        self.ax_space.axvline(max_range, color="#" + theme.GOLD,
                              linewidth=1.1, ls="--", alpha=0.8)
        for i, wave in enumerate(self._waves):
            line, = self.ax_space.plot(wave.x, wave.density_at(-1),
                                       color=self._wave_color(i),
                                       linewidth=1.8,
                                       label=f"{wave.caster} @ {wave.start_step}")
            self._space_lines.append(line)
        self.ax_space.set_xlim(0, x_max)
        self.ax_space.set_ylim(0, peak * 1.08)
        self.ax_space.set_xlabel("Distance")
        self.ax_space.set_ylabel("Energy density")
        legend = self.ax_space.legend(loc="upper left", fontsize=7,
                                      framealpha=0.0)
        for text in legend.get_texts():
            text.set_color("#" + theme.TEXT)
        self._readout = self.ax_space.text(
            0.99, 0.95, "", transform=self.ax_space.transAxes, ha="right",
            va="top", color="#" + theme.GOLD, fontsize=9)

        for i, wave in enumerate(self._waves):
            steps, classical, renorm = wave.timeline()
            if show_classical:
                self.ax_time.plot(steps, classical, ls="--", linewidth=1.2,
                                  color="#" + theme.TEXT_MUTED,
                                  label="classical (catastrophe)" if i == 0 else None)
            self.ax_time.plot(steps, renorm.clip(min=1e-2), linewidth=1.6,
                              color=self._wave_color(i),
                              label="renormalized total" if i == 0 else None)
        self.ax_time.set_yscale("log")
        self.ax_time.set_xlabel("Time step")
        self.ax_time.set_ylabel("Energy")
        self.ax_time.grid(True, color="#" + theme.BORDER, alpha=0.4,
                          linewidth=0.6)
        legend = self.ax_time.legend(loc="upper left", fontsize=7,
                                     framealpha=0.0)
        for text in legend.get_texts():
            text.set_color("#" + theme.TEXT)
        self._cursor = self.ax_time.axvline(self._waves[0].start_step,
                                            color="#" + theme.GOLD,
                                            linewidth=1.2, alpha=0.9)
        self.draw_idle()

    def set_step(self, step):
        if not self._waves:
            return
        for wave, line in zip(self._waves, self._space_lines):
            line.set_ydata(wave.energy_density_at(step))
        self._cursor.set_xdata([step, step])
        self._readout.set_text(self._describe(step))
        self.draw_idle()

    def _describe(self, step):
        # report the most recently cast wave that is alive at this step
        for wave in sorted(self._waves, key=lambda w: -w.start_step):
            if wave.is_alive(step):
                return (f"{wave.caster}:  A(t) = {wave.A_at(step):.2f}   "
                        f"∫|Ψ|²dx = {wave.norm_at(step):.3f}")
        if any(step >= w.start_step for w in self._waves):
            return "spell fizzled — norm below threshold"
        return "no spell in flight"
