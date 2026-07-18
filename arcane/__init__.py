"""Arcane Engineering: simulate arcane circuits and render them.

Public API for scripting; the desktop app lives in arcane.gui.
"""
from arcane.components import (Battery, Wire, Resistor, Concentration, Switch,
                               Caster, Blank, Junction, LogicGate, AndGate,
                               OrGate, XorGate, NandGate, NotGate, component,
                               connect, plot, check_level, get_n_components,
                               get_component_names)
from arcane.exceptions import CircuitException
from arcane.util.simulation import (flatten, step_all, total_energy, simulate,
                                    plot_history)
from arcane.util.circuit_spec import build_circuit, load_circuit, COMPONENT_TYPES
from arcane.util.layout import trace_layout
from arcane.spellwave import SpellWave, SpellWave2D, waves_from_cast_log

__version__ = "1.2.0"

__all__ = [
    "Battery", "Wire", "Resistor", "Concentration", "Switch", "Caster",
    "Blank", "Junction", "LogicGate", "AndGate", "OrGate", "XorGate",
    "NandGate", "NotGate", "component", "connect", "plot", "check_level",
    "get_n_components",
    "get_component_names", "CircuitException", "flatten", "step_all",
    "total_energy", "simulate", "plot_history", "build_circuit",
    "load_circuit", "COMPONENT_TYPES", "trace_layout", "SpellWave",
    "SpellWave2D", "waves_from_cast_log", "make_circuit_scene",
    "make_spellwave_scene", "make_combined_scene", "render_circuit",
    "render_wave", "render_combined", "__version__",
]


def __getattr__(name):
    # Lazily expose the manim-backed helpers so importing arcane never
    # requires manim to be installed.
    if name == "make_circuit_scene":
        from arcane.manim.circuit import make_circuit_scene
        return make_circuit_scene
    if name == "make_spellwave_scene":
        from arcane.manim.wave import make_spellwave_scene
        return make_spellwave_scene
    if name == "make_combined_scene":
        from arcane.manim.circuit import make_combined_scene
        return make_combined_scene
    if name == "render_circuit":
        from arcane.manim.render import render_circuit
        return render_circuit
    if name == "render_wave":
        from arcane.manim.render import render_wave
        return render_wave
    if name == "render_combined":
        from arcane.manim.render import render_combined
        return render_combined
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
