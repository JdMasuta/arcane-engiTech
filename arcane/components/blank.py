"""Inert energy bucket, handy as a probe or placeholder."""
from arcane.components.component import component


class Blank(component):
    def __init__(self, level=1, energy=0, name="blank"):
        super().__init__(level=level, requires_input=True, energy=energy, name=name)
        self.max_energy = 10000

    def step(self):
        pass

    def plot(self, start_point=(0, 0), x_size=1, y_size=1.25, ax=None):
        return (start_point)
