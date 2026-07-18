"""Offscreen tests for the in-app circuit builder dialog."""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6 import QtWidgets  # noqa: E402

from arcane.gui.builder import (CircuitBuilderDialog, ComponentDialog,  # noqa: E402
                                ROLE_KIND, ROLE_SPEC, KIND_COMPONENT)
from arcane.gui.session import SimulationSession  # noqa: E402


@pytest.fixture(scope="module")
def app():
    instance = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield instance


def _component_item(entry):
    item = QtWidgets.QTreeWidgetItem([entry.get("name", entry["type"]), ""])
    item.setData(0, ROLE_KIND, KIND_COMPONENT)
    item.setData(0, ROLE_SPEC, entry)
    return item


def _build_tree(dialog):
    """battery -> [caster a | caster b] assembled programmatically, the
    same tree the toolbar buttons would produce interactively."""
    root = dialog.tree.invisibleRootItem()
    root.addChild(_component_item(
        {"type": "Battery", "name": "battery", "level": 1, "energy": 400}))
    dialog.tree.setCurrentItem(None)
    dialog._add_group()
    group = root.child(1)
    for branch_index, name in ((0, "caster a"), (1, "caster b")):
        group.child(branch_index).addChild(_component_item(
            {"type": "Caster", "name": name, "level": 1}))
    return dialog


def test_builder_serializes_and_builds_a_working_circuit(app):
    dialog = _build_tree(CircuitBuilderDialog())
    spec = dialog.to_spec()
    assert spec["circuit"][0]["name"] == "battery"
    assert isinstance(spec["circuit"][1], list)  # the parallel group
    assert len(spec["circuit"][1]) == 2

    dialog._try_build()
    assert dialog.result_spec is not None, dialog.error_label.text()

    session = SimulationSession.from_spec_dict(dialog.result_spec)
    session.run(200)
    assert max(session.Es["caster a"]) > 0
    assert max(session.Es["caster b"]) > 0


def test_builder_rejects_empty_and_invalid_trees(app):
    dialog = CircuitBuilderDialog()
    dialog._try_build()
    assert dialog.result_spec is None
    assert "Add at least one component" in dialog.error_label.text()

    # mismatched levels: connect() raises and the dialog stays open
    root = dialog.tree.invisibleRootItem()
    root.addChild(_component_item({"type": "Battery", "name": "b", "level": 1}))
    root.addChild(_component_item({"type": "Caster", "name": "c", "level": 3}))
    dialog._try_build()
    assert dialog.result_spec is None
    assert "Cannot build" in dialog.error_label.text()


def test_builder_group_editing_helpers(app):
    dialog = _build_tree(CircuitBuilderDialog())
    root = dialog.tree.invisibleRootItem()
    group = root.child(1)
    assert group.childCount() == 2

    # adding a branch requires a group selected
    dialog.tree.setCurrentItem(group)
    dialog._add_branch()
    assert group.childCount() == 3

    # move the battery below the group and back
    battery = root.child(0)
    dialog.tree.setCurrentItem(battery)
    dialog._move_selected(+1)
    assert root.child(1) is battery
    dialog._move_selected(-1)
    assert root.child(0) is battery

    # delete the extra branch
    dialog.tree.setCurrentItem(group.child(2))
    dialog._delete_selected()
    assert group.childCount() == 2


def test_component_dialog_generates_fields_and_minimal_entry(app):
    dialog = ComponentDialog()
    dialog.type_combo.setCurrentText("Caster")
    # constructor params appear as form fields, including the wave overrides
    assert {"level", "energy", "name", "wave_range", "wave_speed",
            "wave_width"} <= set(dialog._fields)

    # untouched fields stay out of the entry (minimal specs)
    entry = dialog.spec_entry()
    assert entry["type"] == "Caster"
    assert "wave_range" not in entry

    # setting a None-default field includes it, parsed as a number
    widget, _default = dialog._fields["wave_range"]
    widget.setText("42")
    entry = dialog.spec_entry()
    assert entry["wave_range"] == 42
