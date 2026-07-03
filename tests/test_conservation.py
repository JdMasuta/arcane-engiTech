import pytest

from arcane.components import Battery, Blank, Caster, Switch, Resistor, connect
from arcane.simulation import flatten, step_all, total_energy


def casts_accounted_total(circuit, n_steps):
    """Total energy plus everything consumed by cast() firing, which is the
    one intentional energy sink in a gate-free circuit."""
    consumed = []
    for caster in [c for c in flatten(circuit) if isinstance(c, Caster)]:
        def counting_cast(c=caster, orig=None):
            if c.energy >= c.cast_threshold:
                consumed.append(c.energy)
            return Caster.cast(c)
        caster.cast = counting_cast
    for _ in range(n_steps):
        step_all(circuit)
    return total_energy(circuit) + sum(consumed)


def test_series_chain_conserves_energy():
    b, s, c = Battery(1, name='b'), Switch(1, name='s', start_on=True), Caster(1, name='c')
    circuit = connect([b, s, c])
    start = total_energy(circuit)
    assert casts_accounted_total(circuit, 300) == pytest.approx(start)


def test_branched_circuit_conserves_energy():
    b = Battery(1, name='b')
    b.energy = 500
    c1, c2, c3 = (Caster(1, name=f'c{i}') for i in (1, 2, 3))
    circuit = connect([b, [c1, c2, c3]])
    start = total_energy(circuit)
    assert casts_accounted_total(circuit, 400) == pytest.approx(start)


def test_junction_to_junction_circuit_conserves_energy():
    b = Battery(1, name='b')
    b.energy = 800
    d1, d2 = Blank(1, name='d1'), Blank(1, name='d2')
    e1, e2 = Caster(1, name='e1'), Caster(1, name='e2')
    circuit = connect([b, [d1, d2], [e1, e2]])
    start = total_energy(circuit)
    assert casts_accounted_total(circuit, 400) == pytest.approx(start)


def test_resistor_circuit_conserves_energy():
    b = Battery(1, name='b')
    r = Resistor(resistance=3, level=1, name='r')
    sink = Blank(1, name='sink')
    circuit = connect([b, r, sink])
    start = total_energy(circuit)
    for _ in range(200):
        step_all(circuit)
    assert total_energy(circuit) == pytest.approx(start)
