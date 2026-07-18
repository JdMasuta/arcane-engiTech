"""Flow throttle: transfers 1/resistance energy per step."""
import matplotlib.pyplot as plt
import numpy as np

from arcane.components.wire import Wire
from arcane.exceptions import CircuitException


class Resistor(Wire):
    """A Wire that throttles flow instead of passing everything through.

    Ohm's-law analogue for a discrete-step simulation: the per-step
    transferable energy is 1/resistance, so doubling the resistance halves
    the flow rate. resistance = 1 behaves like a rate-1 wire.

    Like Junction, a Resistor is the only actor on both of its links —
    neighbouring wires skip it — otherwise a downstream wire would pull at
    its own (unthrottled) rate and defeat the resistance.
    """

    def __init__(self, resistance=2, level=None, energy=0, name="resistor"):
        super().__init__(level=level, energy=energy, name=name)
        if resistance <= 0:
            raise CircuitException(f"In {name} resistance must be > 0, found {resistance}")
        self.resistance = resistance
        self.energy_in_rate = 1 / resistance
        self.energy_out_rate = 1 / resistance
        self.color = 'orange'
        self.self_managed_links = True

    def step(self):
        de = min([self.previous_comp.energy, self.energy_in_rate])
        if de > 0 and self.previous_comp.allow_output and self.energy + de <= self.max_energy:
            self.energy += de
            self.previous_comp.energy -= de

        de = min([self.energy, self.energy_out_rate])
        next_has_room = self.next_comp.energy + de < self.next_comp.max_energy
        if de > 0 and self.next_comp.allow_input and next_has_room \
                and not self.next_comp.self_managed_links:
            self.next_comp.energy += de
            self.energy -= de

    def plot(self, start_point=[0, 0], x_size=3, y_size=0.4, ax=None):
        if ax is None:
            ax = plt.gca()
        n_zigs = 3
        zig_x = np.linspace(
            start_point[0] + x_size / 3,
            start_point[0] + 2 * x_size / 3,
            2 * n_zigs + 1)
        zig_y = np.full_like(zig_x, float(start_point[1]))
        zig_y[1:-1:2] += y_size / 2
        zig_y[2:-1:2] -= y_size / 2
        xs = np.concatenate([[start_point[0]], zig_x, [start_point[0] + x_size]])
        ys = np.concatenate([[start_point[1]], zig_y, [start_point[1]]])
        ax.plot(xs, ys, color=self.color, ls="-")
        return ([start_point[0] + x_size, start_point[1]])
