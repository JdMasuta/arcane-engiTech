"""Define circuits as JSON instead of hand-written nested Python lists.

Spec format: an object with a "circuit" array. Each entry is either a
component object -- {"type": "Battery", "level": 2, "name": "b1", ...} with
the remaining keys passed to that component's constructor -- or an array of
branches, where each branch is itself an array of entries (nesting works
the same way connect() nesting does).

    {"circuit": [
        {"type": "Battery", "level": 2, "name": "battery", "energy": 300},
        {"type": "Switch", "level": 2, "name": "switch", "start_on": true},
        [
            [{"type": "Caster", "level": 2, "name": "caster 1"}],
            [{"type": "Resistor", "level": 2, "name": "r1", "resistance": 3},
             {"type": "Caster", "level": 2, "name": "caster 2"}]
        ]
    ]}

Run a spec directly:  python circuit_spec.py path/to/spec.json --steps 200
"""
import json

from arcane.components import (Battery, Wire, Resistor, Concentration, Switch,
                               Caster, Blank, Junction, AndGate, OrGate,
                               XorGate, NandGate, NotGate, connect, plot)
from arcane.exceptions import CircuitException

COMPONENT_TYPES = {cls.__name__: cls for cls in
                   (Battery, Wire, Resistor, Concentration, Switch, Caster,
                    Blank, Junction, AndGate, OrGate, XorGate, NandGate,
                    NotGate)}


def build_circuit(spec, registry=None):
    """Turn a spec's "circuit" array into the nested component list connect()
    consumes. Returns (comp_list, registry) with registry mapping component
    names to instances."""
    if registry is None:
        registry = {}
    if isinstance(spec, dict) and "circuit" in spec:
        spec = spec["circuit"]

    def build_entry(entry):
        if isinstance(entry, list):
            return [build_entry(sub) for sub in entry]
        if not isinstance(entry, dict) or "type" not in entry:
            raise CircuitException(
                f"Spec entries must be arrays or objects with a 'type' key, got: {entry!r}")
        kwargs = dict(entry)
        type_name = kwargs.pop("type")
        if type_name not in COMPONENT_TYPES:
            raise CircuitException(
                f"Unknown component type {type_name!r}; known types: {sorted(COMPONENT_TYPES)}")
        try:
            comp = COMPONENT_TYPES[type_name](**kwargs)
        except TypeError as err:
            raise CircuitException(f"Bad arguments for {type_name}: {err}") from err
        if comp.name in registry:
            raise CircuitException(f"Duplicate component name {comp.name!r} in spec")
        registry[comp.name] = comp
        return comp

    return [build_entry(entry) for entry in spec], registry


def load_circuit(path, do_connect=True, verbose=False):
    """Load a JSON spec file; returns (comp_list, registry). With do_connect
    the list is already wired up and ready to step."""
    with open(path) as fh:
        spec = json.load(fh)
    comp_list, registry = build_circuit(spec)
    if do_connect:
        comp_list = connect(comp_list, verbose=verbose)
    return comp_list, registry


def main(argv=None):
    import argparse
    import matplotlib.pyplot as plt
    from arcane.util.simulation import simulate, plot_history

    parser = argparse.ArgumentParser(description="Load, draw, and simulate a JSON circuit spec")
    parser.add_argument("spec", help="path to the JSON spec file")
    parser.add_argument("--steps", type=int, default=0,
                        help="also simulate this many steps and plot the energy history")
    args = parser.parse_args(argv)

    circuit, registry = load_circuit(args.spec)
    print("components:", ", ".join(registry))
    plot(circuit)
    if args.steps:
        t, Es, ET = simulate(circuit, args.steps)
        plot_history(t, Es, ET)
        plt.show()


if __name__ == "__main__":
    main()
