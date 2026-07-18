"""Non-Qt simulation state shared across the GUI widgets.

Keeping the circuit, its history, and the scheduled switch events in one
plain object means the widgets stay thin and the logic stays unit-testable
without a running Qt application.
"""
from arcane.components import Caster, Switch, connect, get_component_names
from arcane.util.circuit_spec import build_circuit, load_circuit
from arcane.util.simulation import simulate, flatten
from arcane.spellwave import (DEFAULT_MAX_RANGE, DEFAULT_SPEED, DEFAULT_WIDTH,
                              SpellWave2D, waves_from_cast_log)


class SimulationSession:
    """Owns one circuit, its scheduled events, and the last simulated run."""

    def __init__(self, comp_list, registry=None, source=None):
        self.comp_list = comp_list
        self.registry = registry or {}
        self.source = source
        self.switch_events = {}          # switch name -> step index to toggle at
        self.wave_settings = {"max_range": DEFAULT_MAX_RANGE,
                              "speed": DEFAULT_SPEED, "width": DEFAULT_WIDTH}
        self.wave_2d = False              # SpellWave (1D) vs SpellWave2D per run
        self.t = []
        self.Es = {}
        self.ET = []
        self.cast_log = []
        self.waves = []

    # -- construction helpers ------------------------------------------------
    @classmethod
    def from_spec_file(cls, path):
        comp_list, registry = load_circuit(path, do_connect=True)
        return cls(comp_list, registry, source=str(path))

    @classmethod
    def from_spec_dict(cls, spec, source=None):
        raw, registry = build_circuit(spec)
        return cls(connect(raw), registry, source=source)

    @classmethod
    def demo(cls):
        """A self-contained example circuit so the GUI has something to show
        without needing a spec file on disk."""
        from arcane.components import Battery, Switch, Resistor, Concentration, Caster

        battery = Battery(2, name="battery")
        battery.energy = 400
        switch = Switch(2, name="switch")
        crystal = Concentration(capacity=25, level=2, name="focus crystal")
        caster_a = Caster(2, name="caster 1")
        resistor = Resistor(resistance=3, level=2, name="resistor")
        caster_b = Caster(2, name="caster 2")
        registry = {c.name: c for c in
                    (battery, switch, crystal, caster_a, resistor, caster_b)}
        raw = [battery, switch, crystal, [[caster_a], [resistor, caster_b]]]
        session = cls(connect(raw), registry, source="demo circuit")
        session.switch_events = {"switch": 20}
        return session

    # -- introspection -------------------------------------------------------
    def switches(self):
        return [c for c in flatten(self.comp_list) if isinstance(c, Switch)]

    def component_names(self, include_plumbing=False):
        names = get_component_names(self.comp_list)
        if include_plumbing:
            return names
        return [n for n in names if "wire" not in n and "junction" not in n]

    @property
    def n_steps(self):
        return len(self.t)

    def has_run(self):
        return self.n_steps > 0

    # -- running -------------------------------------------------------------
    def build_events(self):
        events = {}
        by_name = {s.name: s for s in self.switches()}
        for name, step in self.switch_events.items():
            switch = by_name.get(name)
            if switch is not None and step is not None:
                events.setdefault(step, []).append(switch.toggle)
        return {step: _chain(calls) for step, calls in events.items()}

    def caster_wave_overrides(self):
        """Per-caster wave-parameter overrides sourced from each Caster's
        own wave_range/wave_speed/wave_width (e.g. set via a JSON spec),
        keyed by caster name for waves_from_cast_log."""
        overrides = {}
        for caster in (c for c in flatten(self.comp_list) if isinstance(c, Caster)):
            entry = {}
            if caster.wave_range is not None:
                entry["max_range"] = caster.wave_range
            if caster.wave_speed is not None:
                entry["speed"] = caster.wave_speed
            if caster.wave_width is not None:
                entry["width"] = caster.wave_width
            if entry:
                overrides[caster.name] = entry
        return overrides

    def run(self, n_steps):
        self.reset_energy()
        self.cast_log = []
        self.t, self.Es, self.ET = simulate(self.comp_list, n_steps,
                                            events=self.build_events(),
                                            cast_log=self.cast_log)
        self.waves = waves_from_cast_log(
            self.cast_log, n_steps,
            overrides_by_caster=self.caster_wave_overrides(),
            wave_cls=SpellWave2D if self.wave_2d else None,
            **self.wave_settings)
        return self.t, self.Es, self.ET

    def reset_energy(self):
        """Restore every component to the energy it had before the last run so
        repeated runs from the GUI are reproducible."""
        for comp in flatten(self.comp_list):
            if hasattr(comp, "_initial_energy"):
                comp.energy = comp._initial_energy
            else:
                comp._initial_energy = comp.energy
        for switch in self.switches():
            if hasattr(switch, "_initial_switch_state"):
                switch.allow_input, switch.allow_output = switch._initial_switch_state
            else:
                switch._initial_switch_state = (switch.allow_input, switch.allow_output)


def _chain(calls):
    def run_all():
        for call in calls:
            call()
    return run_all
