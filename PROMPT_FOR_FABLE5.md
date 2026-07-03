# Prompt for Claude Fable 5: Complete the Arcane Engineering Simulator

> Copy everything below the line into a Claude Fable 5 session/agent invocation.
> It is self-contained: domain background, current code state, known bugs, and a
> prioritized build list are all inline so the agent doesn't need working web
> access to succeed. Reference links are included for optional further reading.

---

## Who you are helping and why

You are completing a small, early-stage Python prototype called **Arcane
Engineering**. It is a fan-made simulation tool inspired by a Dungeons &
Dragons 5e homebrew supplement of the same name, written by the tabletop
creator **GorillaOfDestiny** (a.k.a. "The Gorilla of Destiny", who holds a
Master's in Astrophysics and publishes D&D-meets-real-science content under
the banner "The Theory of Magic"). The original tabletop supplement proposes
that wizards can build **arcane circuits** out of magical analogues of real
electrical components — batteries, wires, resistors, inductors, capacitors
("crystals"), switches, and junctions — to store, shape, and discharge
magical energy instead of using scrolls or spell slots directly. This
repository is a code prototype that simulates those circuits numerically and
draws simple schematic diagrams of them.

Reference material (for context/citation only — do not fetch these if you
lack browsing tools, everything you need is summarized below):
- Original upstream repo this project forked from: https://github.com/GorillaOfDestiny/arcane-engineering
- The published tabletop supplement: https://www.drivethrurpg.com/en/product/495795/arcane-engineering
- Creator's site: https://www.gorillaofdestiny.com/
- Creator's YouTube channel: https://www.youtube.com/@GorillaOfDestiny
- The short that inspired this fork: https://youtube.com/shorts/KaTegZBmYRI
- Manim Community docs (for the animation task below): https://docs.manim.community/

## The simulation model already in place

The repo represents a circuit as a **linked list of component objects**
(with branches as nested lists for parallel paths). Each component has a
`step()` method that moves discrete "energy" between `previous_comp` and
`next_comp` each simulated time tick, plus a `plot()` method that draws its
schematic symbol with matplotlib. A `level` attribute tags each component
with a "power tier"; connected components must share a level
(`check_level()`), which stands in for spell level compatibility.

Existing components in `scripts/components.py`:

- **`component`** — abstract base: energy, level, `allow_input`/`allow_output`
  flags, `max_energy` cap, `step()`/`plot()` stubs.
- **`Battery`** — an energy source (models a spell slot / stored charge).
- **`Wire`** — a plain conductor that moves energy at a fixed rate between
  two non-junction neighbors.
- **`Junction`** — an N-input/M-output splitter/merger for parallel or series
  branches (one side must have exactly 1 port).
- **`Switch`** — gates energy flow on/off (`toggle()` turns it on).
- **`Caster`** — the "load": accumulates energy and, once it reaches
  `cast_threshold`, "casts" (drains to 0 and returns `True`) — this is the
  payoff event of a circuit, analogous to a capacitor discharge or a wand
  firing off a spell.
- **`Blank`** — a no-op placeholder component.
- **`connect(comp_list)`** — takes a nested list describing a circuit
  topology and wires up `previous_comp`/`next_comp` links, inserting `Wire`
  and `Junction` objects as needed.
- **`plot(comp_list)`** — walks a connected circuit and draws it end-to-end
  with matplotlib, wrapping the last component back to the first.
- **`get_n_components`/`get_component_names`** — helpers for iterating the
  (possibly nested) circuit list.
- The `__main__` block in `components.py` builds a small demo circuit
  (batteries → switch → three parallel casters), steps it 600 times, and
  plots energy-over-time per component.

`scripts/exceptions.py` currently defines only `CircuitException(Exception)`.

The README states the long-term goal plainly: *"make arcane circuit
simulations and then a converter to manim."* Manim is the Python animation
engine (originally built by 3Blue1Brown, now maintained as Manim Community)
used to produce math/science animation videos — the intent is to turn the
existing static matplotlib circuit diagrams (and the energy-over-time
simulation) into an animated video showing energy flowing through the
circuit over time.

The `TODO` file lists, verbatim:
```
[ ] Add functionality to allow two junctions to meet
[ ] Add resistors
[ ] Add Concentration Components
[ ] Logic Gates
```

## Known bugs to fix first (found by reading the current code closely)

Fix correctness issues before adding features — a "complete" simulator must
first be a *correct* one:

1. **`Junction.__init__` never raises its validation error.** It does
   `CircuitException(f"...")` as a bare expression instead of `raise
   CircuitException(...)`, so an invalid junction (neither side has exactly
   1 port) silently passes validation.
2. **`connect()` has an unbound-variable bug.** In the 1-input/1-output
   branch, `wire_obj` is only assigned inside `if comp_list[j].requires_input:`.
   When that condition is `False`, the very next line,
   `new_comp_list.append(wire_obj)`, raises `UnboundLocalError` because
   `wire_obj` was never defined on that path.
3. **Typo: `next_component` vs `next_comp`.** In the junction branch of
   `connect()`, `comp_list[i].next_component = junc_object_o` sets an
   attribute nothing else reads — every other component uses `next_comp`.
   This silently breaks the link from a component into an opening junction.
4. **Possible division by zero in `Junction.step()`.** The "spread remaining
   energy across `remaining_idx`" loop divides by `len(remaining_idx)`
   without checking it isn't empty.
5. Leftover debug `print()` statements inside `connect()` should be removed
   or converted to an opt-in `verbose`/logging flag.

## What "complete" means for this project (as assumed by Claude Sonnet 5) — build list, in priority order

1. **Fix the bugs above.**
2. **Resistor component** — throttles energy flow rate rather than passing
   it 1:1 like `Wire`. Model it as an Ohm's-law-style analogue: give it a
   `resistance` value and derive its effective `energy_in_rate`/
   `energy_out_rate` (or per-step transferable delta) as inversely
   proportional to resistance, so higher resistance = slower energy transfer
   per step. It should otherwise behave like `Wire` (single previous/next
   neighbor) and reuse as much of `Wire`'s logic as is sensible (consider
   whether `Resistor` should subclass `Wire`).
3. **Concentration component** (the "capacitor"/"crystal" from the TODO) —
   models D&D's *concentration* mechanic: it holds accumulated energy across
   many steps (rather than passing it straight through like a `Wire`) and
   only releases it under some condition — e.g. once full, or via an
   explicit `break_concentration()` call that dumps/loses the stored energy
   (mirroring a failed concentration check). Design the exact
   charge/hold/release semantics yourself, but document the model you chose
   in a docstring since this is the least self-evident component.
4. **Junction-to-junction connections** (TODO item #1). Currently
   `Wire.step()` explicitly refuses to move energy when either neighbor is a
   `Junction` (see the `prev_junction`/`next_not_junction` checks), and
   `connect()` doesn't appear to build a topology where two junctions sit
   adjacent with no component between them. Extend both so two junctions can
   be connected directly (with or without a `Wire` between them — pick one
   and be consistent), and add a small test circuit exercising it.
5. **Logic gates** — add at least AND, OR, and NOT gate components that take
   multiple inputs (reuse the `Junction` multi-port pattern) and only pass
   energy onward based on a boolean-style rule over their inputs' energized
   state (e.g. AND gate passes energy only when all inputs currently hold
   energy above some threshold). Keep the semantics simple and explicit.
6. **Manim converter** — add a new module (e.g. `scripts/manim_scene.py`)
   that takes an already-`connect()`-ed circuit and the per-step energy
   history (the `Es`/`ET` data already computed in the `__main__` demo) and
   produces a Manim `Scene` animating energy flowing through the circuit
   over time — reusing the existing `plot()` layout geometry (component
   endpoints/positions) rather than inventing a new layout system. It's fine
   if this only supports simple (non-nested-branch) circuits for a first
   pass, as long as it's clearly noted.
7. **A way to define circuits without hand-writing nested Python lists** —
   e.g. a small builder API or a JSON/YAML circuit description that
   `connect()` (or a thin wrapper around it) can consume. Keep it minimal;
   don't build a general-purpose DSL.
8. **Automated tests** (pytest) covering: each component's `step()` behavior
   in isolation, energy conservation across a stepped simulation for a small
   circuit, `connect()`/`check_level()` correctness (including the level-
   mismatch error path and the junction-arity error path), and regression
   tests for the 5 bugs listed above.
9. **Packaging and ergonomics** — add a `requirements.txt` or
   `pyproject.toml` (numpy, matplotlib, manim, pytest), turn `scripts/` into
   an importable package if that's the cleanest path, and add a minimal CLI
   or `if __name__ == "__main__"` example per new component so the project
   is runnable without reading source first.
10. **Docs** — expand `README.md` with: a short explanation of the concept
    and credit/link to GorillaOfDestiny's original Arcane Engineering
    supplement as the conceptual basis, a component reference (one line per
    component type and what real-circuit concept it models), and
    instructions for running the simulation and generating a manim
    animation. Update `TODO` to reflect what's now done vs. still open.

## Constraints

- Keep the existing discrete-time-step, float-energy simulation model —
  don't rewrite the simulation approach wholesale.
- Don't break the existing working components (`Battery`, `Wire`, `Junction`,
  `Switch`, `Caster`, `Blank`) or the existing matplotlib `plot()` path;
  additive changes and targeted bug fixes only, unless a redesign is clearly
  required by a TODO item (e.g. junction-to-junction linking necessarily
  touches `Wire`/`connect()`), or you think it would be a great boon to the project as a whole (simpler and/or more effective/holistic solutions).
- Favor small, focused classes/functions consistent with the existing style
  over new abstractions/frameworks.
- No comments explaining *what* code does; only comment non-obvious *why*
  (the concentration-component semantics you choose are a good candidate).
- Commit incrementally with clear messages as you complete each numbered
  item above, rather than one giant commit (conventional commits).
