"""Blocks flow until toggled on."""
import matplotlib.pyplot as plt
import numpy as np

from arcane.components.component import component


class Switch(component):
    def __init__(self, level=None, energy=0, name="switch", start_on=False):
        super().__init__(level=level, requires_input=True, energy=energy, name=name)
        self.allow_input = start_on
        self.allow_output = start_on
        self.color = 'k'

    def step(self):
        if self.allow_input and self.previous_comp.energy > 0 and self.previous_comp.allow_output \
                and not self.previous_comp.self_managed_links:
            self.previous_comp.energy -= 1
            self.energy += 1
        if self.energy > 0 and self.allow_output and self.next_comp.allow_input \
                and not self.next_comp.self_managed_links:
            self.next_comp.energy += 1
            self.energy -= 1

    def plot(self, start_point=(0, 0), x_size=2, y_size=0.25, ax=None):
        if ax is None:
            ax = plt.gca()
        line1 = np.array([[start_point[0], start_point[0] + x_size * (1 / 3),
                           start_point[0] + x_size * (2 / 3)],
                          [start_point[1], start_point[1], start_point[1] + y_size]])
        line2 = np.array([[start_point[0] + (2 / 3) * x_size, start_point[0] +
                         x_size], [start_point[1], start_point[1]]])
        ax.plot(line1[0, :], line1[1, :], color=self.color, ls="-")
        ax.plot(line2[0, :], line2[1, :], color=self.color, ls="-")
        end_point = [start_point[0] + x_size, start_point[1] + 0]
        return (end_point)

    def toggle(self):
        self.allow_input = True
        self.allow_output = True
