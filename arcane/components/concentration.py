"""Capacitor/crystal analogue of the D&D concentration mechanic."""
import matplotlib.pyplot as plt

from arcane.components.component import component
from arcane.exceptions import CircuitException


class Concentration(component):
    """Capacitor/crystal analogue of the D&D concentration mechanic.

    Chosen semantics:
    - while *charging* it pulls up to charge_rate energy per step from the
      previous component and holds it, releasing nothing downstream
    - once the stored energy reaches capacity it starts *discharging*:
      each step it dumps as much held energy as the next component can
      accept, until empty, then goes back to charging
    - break_concentration() models a failed concentration save: whatever
      is held dissipates (leaves the circuit entirely, it is not passed
      on) and charging restarts from zero

    Like Resistor, it is the sole actor on both of its links.
    """

    def __init__(self, capacity=50, charge_rate=1, level=None, energy=0, name="concentration"):
        super().__init__(level=level, energy=energy, name=name)
        if capacity <= 0:
            raise CircuitException(f"In {name} capacity must be > 0, found {capacity}")
        self.capacity = capacity
        self.charge_rate = charge_rate
        self.max_energy = capacity
        self.discharging = False
        self.color = 'b'
        self.self_managed_links = True

    def step(self):
        if not self.discharging:
            de = min([self.previous_comp.energy, self.charge_rate, self.capacity - self.energy])
            if de > 0 and self.previous_comp.allow_output:
                self.energy += de
                self.previous_comp.energy -= de
            if self.energy >= self.capacity:
                self.discharging = True
        else:
            room = self.next_comp.max_energy - self.next_comp.energy
            de = min([self.energy, room])
            if de > 0 and self.next_comp.allow_input and not self.next_comp.self_managed_links:
                self.next_comp.energy += de
                self.energy -= de
            if self.energy <= 0:
                self.discharging = False
        self.allow_output = self.discharging

    def break_concentration(self):
        lost = self.energy
        self.energy = 0
        self.discharging = False
        self.allow_output = False
        return (lost)

    def plot(self, start_point=(0, 0), x_size=1, y_size=1, ax=None):
        if ax is None:
            ax = plt.gca()
        gap = x_size / 4
        mid = start_point[0] + x_size / 2
        ax.plot([start_point[0], mid - gap / 2],
                [start_point[1], start_point[1]], color=self.color, ls="-")
        ax.plot([mid + gap / 2, start_point[0] + x_size],
                [start_point[1], start_point[1]], color=self.color, ls="-")
        ax.plot([mid - gap / 2, mid - gap / 2], [start_point[1] - y_size /
                2, start_point[1] + y_size / 2], color=self.color, ls="-")
        ax.plot([mid + gap / 2, mid + gap / 2], [start_point[1] - y_size /
                2, start_point[1] + y_size / 2], color=self.color, ls="-")
        return ([start_point[0] + x_size, start_point[1]])
