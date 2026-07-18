"""Passes energy only while exactly one input is hot."""
from arcane.components.logic_gate import LogicGate


class XorGate(LogicGate):
    label = 'XOR'

    def __init__(self, n_inputs=2, threshold=0.5, level=None, name="xor gate"):
        super().__init__(n_inputs, threshold=threshold, level=level, name=name)

    def gate_open(self, active):
        return (sum(active) == 1)
