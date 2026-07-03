"""Arcane Engineering: simulate arcane circuits and render them.

Public API for scripting; the desktop app lives in arcane.gui.
"""
from arcane.components import (Battery, Wire, Resistor, Concentration, Switch,
                               Caster, Blank, Junction, LogicGate, AndGate,
                               OrGate, NotGate, component, connect, plot,
                               check_level, get_n_components,
                               get_component_names)
from arcane.exceptions import CircuitException
from arcane.simulation import (flatten, step_all, total_energy, simulate,
                               plot_history)
from arcane.circuit_spec import build_circuit, load_circuit, COMPONENT_TYPES
from arcane.layout import trace_layout

__version__ = "1.0.0"

__all__ = [
    "Battery", "Wire", "Resistor", "Concentration", "Switch", "Caster",
    "Blank", "Junction", "LogicGate", "AndGate", "OrGate", "NotGate",
    "component", "connect", "plot", "check_level", "get_n_components",
    "get_component_names", "CircuitException", "flatten", "step_all",
    "total_energy", "simulate", "plot_history", "build_circuit",
    "load_circuit", "COMPONENT_TYPES", "trace_layout", "make_circuit_scene",
    "render_circuit", "__version__",
]


def __getattr__(name):
    # Lazily expose the manim-backed helpers so importing arcane never
    # requires manim to be installed.
    if name == "make_circuit_scene":
        from arcane.manim_scene import make_circuit_scene
        return make_circuit_scene
    if name == "render_circuit":
        from arcane.render import render_circuit
        return render_circuit
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
