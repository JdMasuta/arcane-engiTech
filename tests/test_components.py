import pytest

from arcane.components import (Battery, Wire, Resistor, Concentration, Switch,
                               Caster, Blank, Junction, AndGate, OrGate,
                               NotGate, connect)
from arcane.exceptions import CircuitException
from arcane.simulation import step_all, total_energy


def run(circuit, n_steps, events=None):
    events = events or {}
    for i in range(n_steps):
        if i in events:
            events[i]()
        step_all(circuit)


def test_wire_moves_energy_from_battery_to_caster():
    b, w, c = Battery(1, name='b'), Wire(1, name='w'), Caster(1, name='c')
    circuit = connect([b, w, c])
    run(circuit, 10)
    assert c.energy == 10
    assert b.energy == 90


def test_resistor_throttles_at_one_over_resistance():
    b, r, c = Battery(1, name='b'), Resistor(resistance=4, level=1, name='r'), Caster(1, name='c')
    circuit = connect([b, r, c])
    run(circuit, 100)
    assert c.energy == pytest.approx(25.0)


def test_resistance_one_matches_plain_wire_rate():
    b, r, c = Battery(1, name='b'), Resistor(resistance=1, level=1, name='r'), Caster(1, name='c')
    circuit = connect([b, r, c])
    run(circuit, 50)
    assert c.energy == pytest.approx(50.0)


def test_resistor_rejects_nonpositive_resistance():
    with pytest.raises(CircuitException):
        Resistor(resistance=0)


def test_concentration_holds_then_bursts():
    b = Battery(1, name='b')
    k = Concentration(capacity=10, level=1, name='k')
    c = Caster(1, name='c')
    circuit = connect([b, k, c])
    run(circuit, 10)
    assert c.energy == 0  # still charging, nothing released
    run(circuit, 15)
    assert c.energy > 0


def test_break_concentration_dissipates_held_energy():
    b = Battery(1, name='b')
    k = Concentration(capacity=50, level=1, name='k')
    c = Caster(1, name='c')
    circuit = connect([b, k, c])
    run(circuit, 20)
    held = k.energy
    assert held > 0
    lost = k.break_concentration()
    assert lost == held
    assert k.energy == 0
    assert not k.discharging
    assert total_energy(circuit) == pytest.approx(100 - lost)


def test_switch_blocks_until_toggled():
    b, s, c = Battery(1, name='b'), Switch(1, name='s', start_on=False), Caster(1, name='c')
    circuit = connect([b, s, c])
    run(circuit, 20)
    assert c.energy == 0
    s.toggle()
    run(circuit, 20)
    assert c.energy > 0


def test_caster_casts_at_threshold():
    c = Caster(1, name='c')
    c.energy = c.cast_threshold
    assert c.cast() is True
    assert c.energy == 0
    c.energy = c.cast_threshold - 1
    assert c.cast() is False


def test_and_gate_requires_all_inputs():
    b = Battery(1, name='b')
    quiet = Switch(1, name='quiet', start_on=False)
    live = Blank(1, name='live')
    g = AndGate(2, level=1, name='g')
    c = Caster(1, name='c')
    circuit = connect([b, [live, quiet], g, c])
    run(circuit, 40)
    assert c.energy == 0
    quiet.toggle()
    run(circuit, 40)
    assert c.energy > 0


def test_or_gate_passes_any_input():
    b = Battery(1, name='b')
    quiet = Switch(1, name='quiet', start_on=False)
    live = Blank(1, name='live')
    g = OrGate(2, level=1, name='g')
    c = Caster(1, name='c')
    circuit = connect([b, [live, quiet], g, c])
    run(circuit, 40)
    assert c.energy > 0


def test_not_gate_emits_only_while_input_quiet():
    b = Battery(1, name='b')
    s = Switch(1, name='s', start_on=False)
    g = NotGate(supply=100, level=1, name='g')
    c = Caster(1, name='c')
    circuit = connect([b, s, g, c])
    run(circuit, 30)
    quiet_level = c.energy
    assert quiet_level > 0
    s.toggle()
    run(circuit, 30)
    assert c.energy == quiet_level
