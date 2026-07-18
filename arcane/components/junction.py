"""N-input/M-output splitter-merger for parallel branches."""
import matplotlib.pyplot as plt
import numpy as np

from arcane.components.component import component
from arcane.exceptions import CircuitException


class Junction(component):
    def __init__(self, n_inputs, n_outputs, level=None, energy=0, name="junction"):
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs
        super().__init__(level=level, energy=energy, name=name)
        self.energy_in_rate = 1
        self.energy_out_rate = 1

        if self.n_inputs != 1 and self.n_outputs != 1:
            # for simplicity we demand at least one side be 1; a 3-in/2-out
            # case could work in theory but this code assumes a single port
            raise CircuitException(
                f"In {self.name} either n_inputs or n_outputs must be 1. "
                f"Instead found n_inputs = {self.n_inputs},"
                f"n_outputs = {self.n_outputs}")
        self.color = 'purple'
        self.self_managed_links = True
        # 'open'/'close' is stamped by connect(); 'inline' junction-like
        # components (1-in gates) are plotted as ordinary single components
        self.junction_role = None

    def step(self):
        # get energy from all possible inputs
        allowed_inputs = []

        for input_comp in range(self.n_inputs):
            prev = self.previous_comp[input_comp]
            if prev.energy > 0 and prev.allow_output:
                allowed_inputs.append(input_comp)
        n_allowed_in = len(allowed_inputs)
        if n_allowed_in > 1:
            for i in allowed_inputs:
                prev = self.previous_comp[i]
                if prev.energy > 0 and prev.allow_output and self.energy < self.max_energy:
                    self.energy += min(prev.energy, 1) / n_allowed_in
                    prev.energy -= min(prev.energy, 1) / n_allowed_in
        elif n_allowed_in == 1:
            i = allowed_inputs[0]
            prev = self.previous_comp[i]
            if prev.energy > 0 and prev.allow_output and self.energy < self.max_energy:
                self.energy += min([prev.energy, 1])
                prev.energy -= min([prev.energy, 1])
        # only if we have energy to output

        e_before = self.energy

        if e_before > 0:
            active = [i for i in range(self.n_outputs)
                      if self.next_comp[i].allow_input
                      and not self.next_comp[i].self_managed_links]
            remaining_energy = e_before
            # water-fill: split the available energy evenly across whichever
            # outputs still have headroom. An output that hits its
            # max_energy is dropped and whatever it couldn't take is
            # redistributed across the rest on the next round, so no output
            # is ever pushed past capacity and no share is silently lost.
            while remaining_energy > 1e-12 and active:
                share = remaining_energy / len(active)
                next_active = []
                distributed = 0.0
                for i in active:
                    nxt = self.next_comp[i]
                    capacity = nxt.max_energy - nxt.energy
                    if capacity <= 1e-12:
                        continue
                    transfer = min(share, capacity)
                    nxt.energy += transfer
                    distributed += transfer
                    if transfer >= share - 1e-12:
                        next_active.append(i)
                if distributed <= 1e-12:
                    break
                self.energy -= distributed
                remaining_energy -= distributed
                active = next_active

    def plot(self, start_point=[[0, 0]], x_size=2, y_size=2, ax=None, buffer=0.1):
        if ax is None:
            ax = plt.gca()
        assert len(start_point) == self.n_inputs, \
            f"Number of start_points differs from number of inputs to {self.name}"

        # make all start_points at same x

        max_x = start_point[0][0]
        for sp in start_point:
            if sp[0] > max_x:
                max_x = sp[0]
        mid_y = np.mean([sp[1] for sp in start_point])

        junction_line = np.array([[max_x + buffer + x_size / 2, max_x + buffer + x_size / 2],
                                 [mid_y + y_size / 2, mid_y - y_size / 2]])

        ax.plot(junction_line[0, :], junction_line[1, :], color=self.color)
        if self.n_inputs == 1:

            input_lines = np.array([[start_point[0][0], start_point[0][0] + x_size / 2],
                                    [start_point[0][1], start_point[0][1]]])
            ax.plot(input_lines[0, :], input_lines[1, :], color=self.color)
        else:
            for i in range(self.n_inputs):
                input_x = [start_point[i][0], junction_line[0][0]]
                input_y = [start_point[i][1], start_point[i][1]]
                ax.plot(input_x,
                        input_y,
                        color=self.color)
        if self.n_outputs == 1:

            output_lines = np.array([[junction_line[0][0], max_x + buffer + x_size],
                                    [mid_y, mid_y]])
            end_points = [[max_x + buffer + x_size, mid_y]]
            ax.plot(output_lines[0, :], output_lines[1, :], color=self.color)
        else:

            end_points = []
            for i in range(self.n_outputs):
                output_y = np.linspace(mid_y + y_size / 2, mid_y - y_size / 2, self.n_outputs)
                output_x = [junction_line[0][0], max_x + buffer + x_size]
                ax.plot(output_x,
                        [output_y[i], output_y[i]],
                        color=self.color)
                end_points.append([output_x[-1], output_y[i]])
        return (end_points)
