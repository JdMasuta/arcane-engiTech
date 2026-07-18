"""Branches-inside-branches: a parallel group where one branch itself
contains a further parallel group. This path was previously untested and
check_level() crashed on it (see test_check_level_handles_nested_branch_group
below) because a nested group leaves a raw list-of-branches entry in its
enclosing branch's flattened result, and check_level assumed every entry
was a component with a .level attribute.
"""
import matplotlib
import pytest

matplotlib.use('Agg')

from arcane.components import (Battery, Blank, Caster, connect,  # noqa: E402
                               get_component_names, plot)
from arcane.util.layout import trace_layout  # noqa: E402
from arcane.util.simulation import simulate, step_all, total_energy  # noqa: E402


def _nested_circuit():
    battery = Battery(1, name='battery')
    battery.energy = 500
    blank_a = Blank(1, name='blank_a')
    blank_b = Blank(1, name='blank_b')
    c1 = Caster(1, name='c1')
    c2 = Caster(1, name='c2')
    caster = Caster(1, name='caster')

    branch_a = [blank_a]
    branch_b = [blank_b, [[c1], [c2]]]  # nested parallel group inside branch_b
    circuit = connect([battery, [branch_a, branch_b], caster])
    return circuit, dict(battery=battery, blank_a=blank_a, blank_b=blank_b,
                         c1=c1, c2=c2, caster=caster)


def test_check_level_handles_nested_branch_group():
    # regression: used to raise AttributeError on the embedded list-of-lists
    circuit, comps = _nested_circuit()
    assert comps['battery'].next_comp is not None


def test_get_component_names_reaches_doubly_nested_components():
    circuit, comps = _nested_circuit()
    names = get_component_names(circuit)
    for expected in ('battery', 'blank_a', 'blank_b', 'c1', 'c2', 'caster'):
        assert expected in names


def test_trace_layout_records_doubly_nested_components():
    circuit, comps = _nested_circuit()
    record, bbox = trace_layout(circuit)
    recorded_names = {getattr(k, 'name', k) for k in record}
    assert set(get_component_names(circuit)) <= recorded_names
    assert all(seg.shape[0] == 2 for segs in record.values() for seg in segs)


def test_plot_renders_doubly_nested_circuit():
    circuit, comps = _nested_circuit()
    plot(circuit, show=False)  # must not raise


def test_simulation_splits_energy_across_the_nested_branch():
    circuit, comps = _nested_circuit()
    start = total_energy(circuit)
    for _ in range(150):
        step_all(circuit)
    # both nested casters are reachable and receive energy
    assert comps['c1'].energy > 0
    assert comps['c2'].energy > 0
    # conservation: nothing lost or duplicated by the nested topology
    end = total_energy(circuit)
    assert end == pytest.approx(start)


def test_simulate_helper_runs_end_to_end_on_nested_circuit():
    circuit, comps = _nested_circuit()
    t, Es, ET = simulate(circuit, 50)
    assert ET[0] == 500
    assert 'c1' in Es and 'c2' in Es
