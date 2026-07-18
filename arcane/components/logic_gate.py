"""Base for gates: n inputs merged into 1 output, gated by a rule."""
import matplotlib.pyplot as plt
import numpy as np

from arcane.components.junction import Junction


class LogicGate(Junction):
    """Base for gates: n inputs merged into 1 output, gated by a boolean rule.

    An input counts as *active* when it holds at least `threshold` energy
    and allows output. When gate_open(active) is True the gate pulls up to
    1 energy per step from each active input and pushes what it holds
    onward; when False nothing moves through it.

    Multi-input gates are placed directly after a branch list, where
    connect() uses them as that branch list's closing junction.
    """
    label = '?'

    def __init__(self, n_inputs, threshold=0.5, level=None, energy=0, name="gate"):
        super().__init__(n_inputs, 1, level=level, energy=energy, name=name)
        self.threshold = threshold
        self.color = 'g'
        self.junction_role = 'inline'

    def input_active(self):
        return ([pc.energy >= self.threshold and pc.allow_output for pc in self.previous_comp])

    def gate_open(self, active):
        raise NotImplementedError

    def step(self):
        active = self.input_active()
        if self.gate_open(active):
            for i, a in enumerate(active):
                if a and self.energy < self.max_energy:
                    de = min([self.previous_comp[i].energy, 1])
                    self.energy += de
                    self.previous_comp[i].energy -= de
        de = self.energy
        nxt = self.next_comp[0]
        nxt_has_room = nxt.energy + de < nxt.max_energy
        if de > 0 and nxt.allow_input and not nxt.self_managed_links and nxt_has_room:
            nxt.energy += de
            self.energy -= de

    def plot(self, start_point=[[0, 0]], x_size=2, y_size=2, ax=None, buffer=0.1):
        if ax is None:
            ax = plt.gca()
        end_points = super().plot(start_point=start_point, x_size=x_size,
                                  y_size=y_size, ax=ax, buffer=buffer)
        if self.n_inputs > 1:
            mid_y = np.mean([sp[1] for sp in start_point])
        else:
            mid_y = start_point[0][1]
        ax.text(
            end_points[0][0] -
            x_size /
            2,
            mid_y +
            y_size /
            2 +
            buffer,
            self.label,
            color=self.color,
            ha='center')
        return (end_points)
