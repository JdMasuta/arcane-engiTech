import pytest

from arcane.components import (Battery, Wire, Blank, Caster, Junction, AndGate,
                               connect, check_level, get_component_names, plot)
from arcane.exceptions import CircuitException
from arcane.simulation import step_all


def test_junction_rejects_multi_in_multi_out():
    # regression: this used to build the exception and throw it away
    with pytest.raises(CircuitException):
        Junction(2, 3)
    Junction(1, 3)
    Junction(3, 1)
    Junction(1, 1)


def test_connect_handles_component_not_requiring_input():
    # regression: appending an unbound wire_obj crashed this path
    sink = Blank(0, name='sink')
    source = Battery(0, name='source')  # level-0 battery requires no input
    circuit = connect([sink, source])
    assert sink.next_comp is None
    names = get_component_names(circuit)
    assert 'sink' in names and 'source' in names


def test_connect_links_component_into_opening_junction():
    # regression: next_component typo left next_comp unset
    b = Battery(1, name='b')
    c1, c2 = Caster(1, name='c1'), Caster(1, name='c2')
    circuit = connect([b, [c1, c2]])
    assert isinstance(b.next_comp, Junction)
    assert b.next_comp.previous_comp == [b]


def test_junction_step_with_all_outputs_full_does_not_divide_by_zero():
    # regression: spreading remainder energy divided by len([]) == 0
    j = Junction(1, 2, name='j')
    src = Battery(1, name='src')
    full_a, full_b = Blank(1, name='a'), Blank(1, name='b')
    full_a.energy = full_a.max_energy
    full_b.energy = full_b.max_energy
    j.previous_comp = [src]
    j.next_comp = [full_a, full_b]
    j.energy = 1
    j.step()  # must not raise


def test_connect_is_silent_by_default(capsys):
    b, c = Battery(1, name='b'), Caster(1, name='c')
    connect([b, c])
    assert capsys.readouterr().out == ''


def test_wire_level_mismatch_raises():
    b = Battery(1, name='b')
    c = Caster(2, name='c')
    with pytest.raises(CircuitException):
        connect([b, c])


def test_check_level_rejects_mixed_levels():
    with pytest.raises(AssertionError):
        check_level([Battery(1), Caster(2)])


def test_junction_to_junction_topology_and_flow():
    b = Battery(1, name='b')
    b.energy = 1000
    d1, d2 = Blank(1, name='d1'), Blank(1, name='d2')
    e1, e2, e3 = (Caster(1, name=f'e{i}') for i in (1, 2, 3))
    circuit = connect([b, [d1, d2], [e1, e2, e3]])

    closers = [c for c in circuit if isinstance(c, Junction) and c.junction_role == 'close']
    openers = [c for c in circuit if isinstance(c, Junction) and c.junction_role == 'open']
    assert len(closers) == 2 and len(openers) == 2
    # the first closing junction feeds the second opening junction directly
    assert closers[0].next_comp == [openers[1]]
    assert openers[1].previous_comp == [closers[0]]

    for _ in range(200):
        step_all(circuit)
    assert e1.energy > 0 and e2.energy > 0 and e3.energy > 0


def test_multi_input_gate_adopted_as_closing_junction():
    b = Battery(1, name='b')
    d1, d2 = Blank(1, name='d1'), Blank(1, name='d2')
    g = AndGate(2, level=1, name='g')
    c = Caster(1, name='c')
    circuit = connect([b, [d1, d2], g, c])
    assert g.junction_role == 'close'
    assert g.previous_comp == [d1, d2]
    assert g in circuit
    # the gate is not duplicated as a standalone node
    assert sum(1 for comp in circuit if comp is g) == 1


def test_plot_junction_to_junction_circuit(tmp_path):
    import matplotlib.pyplot as plt
    b = Battery(1, name='b')
    d1, d2 = Blank(1, name='d1'), Blank(1, name='d2')
    e1, e2 = Caster(1, name='e1'), Caster(1, name='e2')
    circuit = connect([b, [d1, d2], [e1, e2]])
    plot(circuit, show=False)
    plt.close('all')
