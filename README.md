# Arcane Engineering

A discrete-time simulator for **arcane circuits** — magical analogues of
electrical circuits where batteries store spell energy, wires and junctions
route it, and casters discharge it as spells — plus a converter that turns a
simulated circuit into a [manim](https://docs.manim.community/) animation of
energy flowing through it.

The concept comes from
[GorillaOfDestiny](https://www.youtube.com/@GorillaOfDestiny)'s
[Arcane Engineering](https://www.drivethrurpg.com/en/product/495795/arcane-engineering)
D&D 5e supplement (part of the *Theory of Magic* project), which proposes
circuit components as an alternative to scrolls and spell slots. This repo
simulates that idea numerically; it does not reproduce the book's rules.
This is a fork of the original prototype at
[GorillaOfDestiny/arcane-engineering](https://github.com/GorillaOfDestiny/arcane-engineering).

## Setup

```bash
pip install -r requirements.txt      # numpy, matplotlib, pytest
pip install manim                    # optional, for animations
```

## Quick start

Run the built-in demo (three batteries feeding three parallel casters
through a switch):

```bash
cd scripts
python components.py
```

Or define a circuit as JSON and run it:

```bash
cd scripts
python circuit_spec.py ../examples/demo_circuit.json --steps 200
```

Render the demo animation (requires manim):

```bash
manim -pql scripts/manim_scene.py DemoScene
```

## Components

| Component | Circuit analogue | Behaviour |
|---|---|---|
| `Battery` | voltage source / spell slot | Stores energy for the circuit to drain. A level-0 battery needs no return path. |
| `Wire` | conductor | Pulls up to 1 energy/step from behind, dumps everything it holds forward. |
| `Resistor` | resistor | Throttles flow to 1/resistance energy per step. |
| `Concentration` | capacitor / focus crystal | Charges while releasing nothing; bursts downstream when full. `break_concentration()` dissipates whatever it holds (a failed concentration save). |
| `Junction` | node / splitter | Splits or merges parallel branches (one side must have exactly 1 port). Created automatically by `connect()`. |
| `Switch` | switch | Blocks flow until `toggle()`d on. |
| `AndGate` / `OrGate` | logic gates | Merge N inputs into 1 output; pass energy only while their boolean rule over the energised inputs holds. Place directly after a branch list. |
| `NotGate` | inverter | Emits from an internal reserve only while its input is quiet; the control signal that holds it shut is consumed. |
| `Caster` | load / wand | Accumulates energy and casts (drains to zero) at its threshold. |
| `Blank` | test point | Inert energy bucket, handy for probing. |

Every component carries a `level` (spell-level tier); `connect()` refuses to
wire components of different levels together.

## Building circuits

Describe a circuit as a list; nested lists are parallel branches. `connect()`
inserts wires and junction pairs and links everything up, wrapping the last
element back to the first:

```python
from components import *

battery = Battery(2, name="battery")
switch = Switch(2, name="switch")
casters = [Caster(2, name=f"caster {i}") for i in (1, 2, 3)]

circuit = connect([battery, switch, casters])
plot(circuit)                       # schematic diagram

from simulation import simulate, plot_history
t, Es, ET = simulate(circuit, 600, events={50: switch.toggle})
plot_history(t, Es, ET)
```

Two branch lists may sit adjacent — their junctions link directly. A
multi-input gate placed right after a branch list becomes that list's
closing junction:

```python
circuit = connect([battery, [sensor_a, sensor_b], AndGate(2, level=2), caster])
```

The same structures can be written as JSON — see
`examples/demo_circuit.json` and `scripts/circuit_spec.py`.

## Animation

`scripts/manim_scene.py` reuses the matplotlib schematic geometry: each
component's drawn segments become manim lines whose colour and thickness
track that component's simulated energy over time.

```python
from manim_scene import make_circuit_scene
MyScene = make_circuit_scene(circuit, Es, run_time=10, name="MyScene")
```

## Tests

```bash
python -m pytest
```
