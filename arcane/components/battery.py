"""Energy source: a spell slot / stored charge."""
import matplotlib.pyplot as plt

from arcane.components.component import component


class Battery(component):
    def __init__(self, level=1, energy=100, name="battery"):
        super().__init__(level=level, energy=energy, name=name)
        if level == 0:
            self.requires_input = False
        self.max_energy = 1000

    def plot(self, start_point=(0, 0), x_size=0.25, y_size=1, ax=None):
        if ax is None:
            ax = plt.gca()
        line1_x = [start_point[0],
                   start_point[0]]
        line1_y = [start_point[1] - y_size / 2,
                   start_point[1] + y_size / 2]
        line2_x = [start_point[0] + x_size,
                   start_point[0] + x_size]
        line2_y = [start_point[1] - y_size / 4,
                   start_point[1] + y_size / 4]
        ax.plot(line1_x, line1_y, color='k', ls="-")
        ax.plot(line2_x, line2_y, color='k', ls="-")
        end_point = [start_point[0] + x_size, start_point[1]]
        return (end_point)

    def step(self):
        pass
