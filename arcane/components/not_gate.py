"""Inverter: emits from an internal reserve while its input is quiet."""
import matplotlib.pyplot as plt

from arcane.components.logic_gate import LogicGate


class NotGate(LogicGate):
    """Inverter: emits 1 energy per step from an internal reserve only while
    its input is quiet. The control signal is consumed either way (up to
    1/step): it refills the reserve when there is room, otherwise it
    dissipates — a NOT gate held open burns the energy used to hold it.
    """
    label = 'NOT'

    def __init__(self, supply=100, threshold=0.5, level=None, name="not gate"):
        super().__init__(1, threshold=threshold, level=level, energy=supply, name=name)
        self.supply = supply
        self.max_energy = supply

    def gate_open(self, active):
        return (not active[0])

    def step(self):
        prev = self.previous_comp[0]
        was_active = self.input_active()[0]
        de = min([prev.energy, 1])
        if de > 0 and prev.allow_output:
            prev.energy -= de
            self.energy = min([self.energy + de, self.max_energy])
        if not was_active:
            emit = min([self.energy, 1])
            nxt = self.next_comp[0]
            nxt_has_room = nxt.energy + emit < nxt.max_energy
            if emit > 0 and nxt.allow_input and not nxt.self_managed_links and nxt_has_room:
                nxt.energy += emit
                self.energy -= emit

    def plot(self, start_point=(0, 0), x_size=1.5, y_size=1, ax=None):
        if ax is None:
            ax = plt.gca()
        tip_x = start_point[0] + x_size * 0.8
        ax.plot([start_point[0], start_point[0], tip_x, start_point[0]],
                [start_point[1] - y_size / 2, start_point[1] + y_size /
                    2, start_point[1], start_point[1] - y_size / 2],
                color=self.color, ls="-")
        circle = plt.Circle(
            (tip_x + x_size * 0.1,
             start_point[1]),
            x_size * 0.1,
            fill=False,
            color=self.color)
        ax.add_patch(circle)
        return ([start_point[0] + x_size, start_point[1]])
