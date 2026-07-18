"""Passes energy while any input is hot."""
from arcane.components.logic_gate import LogicGate


class OrGate(LogicGate):
    label = 'OR'

    def __init__(self, n_inputs=2, threshold=0.5, level=None, name="or gate"):
        super().__init__(n_inputs, threshold=threshold, level=level, name=name)

    def gate_open(self, active):
        return (any(active))
