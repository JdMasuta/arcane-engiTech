"""Plain conductor: pulls up to 1 energy/step, dumps everything on."""
import matplotlib.pyplot as plt
import numpy as np

from arcane.components.component import component


class Wire(component):
    def __init__(self, level=None, energy=0, name="wire"):
        super().__init__(level=level, energy=energy, name=name)
        self.energy_in_rate = 1
        self.energy_out_rate = np.inf  # wires dump everything they hold each step
        self.color = 'r'

    def step(self):

        prev_energy = self.previous_comp.energy > 0
        prev_allow = self.previous_comp.allow_output
        self_thresh = self.energy < self.max_energy
        prev_passive = not self.previous_comp.self_managed_links

        if prev_energy and prev_allow and self_thresh and prev_passive:
            de = min([self.previous_comp.energy, self.energy_in_rate])
            self.energy += de
            self.previous_comp.energy -= de

        de = min([self.energy_out_rate, self.energy])

        self_energy = self.energy > 0
        next_allow = self.next_comp.allow_input
        next_thresh = self.next_comp.energy + de < self.next_comp.max_energy
        next_passive = not self.next_comp.self_managed_links

        if self_energy and next_allow and next_thresh and next_passive:

            self.next_comp.energy += de
            self.energy -= de

    def plot(self, start_point=[0, 0], x_size=3, y_size=0, ax=None):
        if ax is None:
            ax = plt.gca()
        line1 = np.array([[start_point[0], start_point[0] + x_size],
                          [start_point[1], start_point[1] + y_size]])
        ax.plot(line1[0, :], line1[1, :], color=self.color, ls="-")
        return (line1[:, 1])
