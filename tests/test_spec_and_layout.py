import os

import pytest

from arcane.util.circuit_spec import build_circuit, load_circuit
from arcane.exceptions import CircuitException
from arcane.manim.circuit import MANIM_AVAILABLE, make_circuit_scene
from arcane.util.layout import trace_layout
from arcane.util.simulation import simulate

EXAMPLE = os.path.join(os.path.dirname(__file__), os.pardir, 'examples', 'demo_circuit.json')


def test_load_example_spec_and_simulate():
    circuit, registry = load_circuit(EXAMPLE)
    expected = {'battery', 'switch', 'focus crystal', 'caster 1', 'resistor', 'caster 2'}
    assert expected <= set(registry)
    t, Es, ET = simulate(circuit, 50)
    assert ET[0] == 500
    assert max(Es['focus crystal']) > 0  # energy actually flowed


@pytest.mark.parametrize('bad_spec', [
    [{'type': 'Vortex'}],
    [{'name': 'missing type'}],
    [{'type': 'Battery', 'name': 'dup'}, {'type': 'Battery', 'name': 'dup'}],
    [{'type': 'Resistor', 'frobnicate': 1}],
])
def test_bad_specs_raise_circuit_exception(bad_spec):
    with pytest.raises(CircuitException):
        build_circuit(bad_spec)


def test_trace_layout_records_every_component():
    from arcane.components import Battery, Switch, Caster, connect, get_component_names
    b = Battery(2, name='battery')
    s = Switch(2, name='switch')
    c1, c2 = Caster(2, name='caster 1'), Caster(2, name='caster 2')
    circuit = connect([b, s, [c1, c2]])
    record, bbox = trace_layout(circuit)
    recorded_names = {getattr(k, 'name', k) for k in record}
    assert set(get_component_names(circuit)) <= recorded_names
    assert '__wrap__' in recorded_names
    xmin, xmax, ymin, ymax = bbox
    assert xmax > xmin and ymax > ymin
    assert all(seg.shape[0] == 2 for segs in record.values() for seg in segs)


@pytest.mark.skipif(MANIM_AVAILABLE, reason='manim installed; guard not applicable')
def test_make_circuit_scene_raises_without_manim():
    from arcane.components import Battery, Caster, connect
    circuit = connect([Battery(1, name='b'), Caster(1, name='c')])
    with pytest.raises(ImportError):
        make_circuit_scene(circuit, {})
