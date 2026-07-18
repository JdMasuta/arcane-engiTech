"""Passes energy only while every input is hot."""
from arcane.components.logic_gate import LogicGate


class AndGate(LogicGate):
    label = 'AND'

    def __init__(self, n_inputs=2, threshold=0.5, level=None, name="and gate"):
        super().__init__(n_inputs, threshold=threshold, level=level, name=name)

    def gate_open(self, active):
        return (all(active))
