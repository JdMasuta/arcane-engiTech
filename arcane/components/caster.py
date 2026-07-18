"""The load: accumulates energy and casts at its threshold."""
import matplotlib.pyplot as plt

from arcane.components.component import component


class Caster(component):
    def __init__(self, level=1, energy=0, name="caster", wave_range=None,
                 wave_speed=None, wave_width=None):
        super().__init__(level=level, requires_input=True, energy=energy, name=name)
        self.cast_threshold = 100
        self.allow_output = False
        self.max_energy = self.cast_threshold + 1
        # per-caster overrides for the spell wave this caster spawns on
        # firing; None means "use whatever default the caller supplies"
        # (see spellwave.waves_from_cast_log's overrides_by_caster)
        self.wave_range = wave_range
        self.wave_speed = wave_speed
        self.wave_width = wave_width

    def cast(self):
        if self.energy >= self.cast_threshold:
            self.energy = 0
            return (True)
        else:
            return (False)

    def plot(self, start_point=(0, 0), x_size=1, y_size=1.25, ax=None):
        if ax is None:
            ax = plt.gca()

        line1_x = [start_point[0], start_point[0] + x_size / 2, start_point[0] + x_size]

        line1_y = [start_point[1], start_point[1] + y_size / 2, start_point[1]]
        line2_y = [start_point[1], start_point[1] - y_size / 2, start_point[1]]
        ax.plot(line1_x, line1_y, color='k', ls="-")
        ax.plot(line1_x, line2_y, color='k', ls="-")
        end_point = [start_point[0] + x_size, start_point[1]]

        return (end_point)

    def step(self):
        if self.energy >= self.cast_threshold:
            self.cast()
        else:
            pass
