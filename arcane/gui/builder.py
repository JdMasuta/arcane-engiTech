"""In-app circuit builder: compose a circuit without writing JSON.

A structured tree editor rather than a free-form canvas: top-level tree
items are the series chain, a "parallel group" item holds branch items,
and each branch holds its own series chain (groups nest, matching
connect()'s nesting rules). Build serializes the tree to the same spec
dict circuit_spec understands and validates it through build_circuit() +
connect(), surfacing any CircuitException inline, so the builder can
never produce a circuit the JSON loader would reject.
"""
import inspect

from PySide6 import QtCore, QtWidgets

from arcane.util.circuit_spec import COMPONENT_TYPES, build_circuit
from arcane.components import connect
from arcane.exceptions import CircuitException

ROLE_KIND = QtCore.Qt.UserRole
ROLE_SPEC = QtCore.Qt.UserRole + 1

KIND_COMPONENT = "component"
KIND_GROUP = "group"
KIND_BRANCH = "branch"


class ComponentDialog(QtWidgets.QDialog):
    """Pick a component type and fill in its constructor parameters.

    The form is generated from the constructor signature, so new component
    types (and new parameters like Caster's wave_range) appear here without
    builder changes. Only values changed from their defaults go into the
    spec entry, keeping produced specs minimal.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add component")
        self._fields = {}

        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(sorted(COMPONENT_TYPES))
        self.type_combo.currentTextChanged.connect(self._rebuild_form)

        self.form_host = QtWidgets.QWidget()
        self.form = QtWidgets.QFormLayout(self.form_host)
        self.form.setContentsMargins(0, 0, 0, 0)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Type"))
        layout.addWidget(self.type_combo)
        layout.addWidget(self.form_host)
        layout.addWidget(buttons)
        self._rebuild_form(self.type_combo.currentText())

    def _rebuild_form(self, type_name):
        while self.form.rowCount():
            self.form.removeRow(0)
        self._fields.clear()
        cls = COMPONENT_TYPES[type_name]
        params = list(inspect.signature(cls.__init__).parameters.items())[1:]
        for pname, param in params:
            default = param.default
            if default is inspect.Parameter.empty:
                widget = QtWidgets.QDoubleSpinBox()
                widget.setRange(-1e6, 1e6)
                widget.setValue(1)
            elif isinstance(default, bool):
                widget = QtWidgets.QCheckBox()
                widget.setChecked(default)
            elif isinstance(default, (int, float)):
                widget = QtWidgets.QDoubleSpinBox()
                widget.setRange(-1e6, 1e6)
                widget.setDecimals(3)
                widget.setValue(default)
            elif isinstance(default, str):
                widget = QtWidgets.QLineEdit(default)
            else:  # None or anything else: empty means "leave at default"
                widget = QtWidgets.QLineEdit()
                widget.setPlaceholderText("default")
            self.form.addRow(pname, widget)
            self._fields[pname] = (widget, default)

    def spec_entry(self):
        entry = {"type": self.type_combo.currentText()}
        for pname, (widget, default) in self._fields.items():
            if isinstance(widget, QtWidgets.QCheckBox):
                value = widget.isChecked()
                if value != default:
                    entry[pname] = value
            elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                value = widget.value()
                if default is inspect.Parameter.empty:
                    entry[pname] = _as_number(value)
                elif value != default:
                    entry[pname] = _as_number(value)
            else:
                text = widget.text().strip()
                if not text or text == default:
                    continue
                entry[pname] = _parse_text(text)
        return entry


def _as_number(value):
    return int(value) if float(value).is_integer() else float(value)


def _parse_text(text):
    lowered = text.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    try:
        return _as_number(float(text))
    except ValueError:
        return text


class CircuitBuilderDialog(QtWidgets.QDialog):
    """Tree-based circuit composer producing a validated spec dict."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Circuit builder")
        self.resize(560, 480)
        self.result_spec = None

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Structure", "Details"])
        self.tree.setColumnWidth(0, 260)

        toolbar = QtWidgets.QHBoxLayout()
        for label, slot in (
                ("Add component…", self._add_component),
                ("Add parallel group", self._add_group),
                ("Add branch", self._add_branch),
                ("Delete", self._delete_selected),
                ("Move up", lambda: self._move_selected(-1)),
                ("Move down", lambda: self._move_selected(+1))):
            button = QtWidgets.QPushButton(label)
            button.clicked.connect(slot)
            toolbar.addWidget(button)
        toolbar.addStretch(1)

        self.error_label = QtWidgets.QLabel("")
        self.error_label.setWordWrap(True)
        self.error_label.setObjectName("Subtitle")

        buttons = QtWidgets.QDialogButtonBox()
        self.build_button = buttons.addButton(
            "Build circuit", QtWidgets.QDialogButtonBox.AcceptRole)
        buttons.addButton(QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._try_build)
        buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(toolbar)
        layout.addWidget(self.tree, 1)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)

    # -- tree editing ----------------------------------------------------
    def _selected(self):
        items = self.tree.selectedItems()
        return items[0] if items else None

    def _insertion_parent(self):
        """Components/groups go into the series chain the selection sits in:
        the root list, or a branch's chain when a branch (or something
        inside one) is selected."""
        item = self._selected()
        while item is not None:
            if item.data(0, ROLE_KIND) == KIND_BRANCH:
                return item
            item = item.parent()
        return self.tree.invisibleRootItem()

    def _add_component(self):
        dialog = ComponentDialog(self)
        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return
        entry = dialog.spec_entry()
        item = QtWidgets.QTreeWidgetItem(
            [entry.get("name", entry["type"]), _describe_entry(entry)])
        item.setData(0, ROLE_KIND, KIND_COMPONENT)
        item.setData(0, ROLE_SPEC, entry)
        self._insertion_parent().addChild(item)
        self.tree.expandAll()

    def _add_group(self):
        group = QtWidgets.QTreeWidgetItem(["Parallel group", ""])
        group.setData(0, ROLE_KIND, KIND_GROUP)
        self._insertion_parent().addChild(group)
        for _ in range(2):  # a group only makes sense with 2+ branches
            self._append_branch(group)
        self.tree.expandAll()

    def _append_branch(self, group):
        branch = QtWidgets.QTreeWidgetItem(
            [f"Branch {group.childCount() + 1}", ""])
        branch.setData(0, ROLE_KIND, KIND_BRANCH)
        group.addChild(branch)
        return branch

    def _add_branch(self):
        item = self._selected()
        while item is not None and item.data(0, ROLE_KIND) != KIND_GROUP:
            item = item.parent()
        if item is None:
            self.error_label.setText("Select a parallel group (or something "
                                     "inside one) to add a branch to.")
            return
        self._append_branch(item)
        self.tree.expandAll()

    def _delete_selected(self):
        item = self._selected()
        if item is None:
            return
        parent = item.parent() or self.tree.invisibleRootItem()
        parent.removeChild(item)

    def _move_selected(self, delta):
        item = self._selected()
        if item is None:
            return
        parent = item.parent() or self.tree.invisibleRootItem()
        index = parent.indexOfChild(item)
        target = index + delta
        if 0 <= target < parent.childCount():
            parent.takeChild(index)
            parent.insertChild(target, item)
            self.tree.setCurrentItem(item)

    # -- building ----------------------------------------------------------
    def _serialize_children(self, parent):
        entries = []
        for i in range(parent.childCount()):
            child = parent.child(i)
            kind = child.data(0, ROLE_KIND)
            if kind == KIND_COMPONENT:
                entries.append(dict(child.data(0, ROLE_SPEC)))
            elif kind == KIND_GROUP:
                entries.append([self._serialize_children(child.child(b))
                                for b in range(child.childCount())])
        return entries

    def to_spec(self):
        return {"circuit": self._serialize_children(self.tree.invisibleRootItem())}

    def _try_build(self):
        spec = self.to_spec()
        if not spec["circuit"]:
            self.error_label.setText("Add at least one component first.")
            return
        try:
            raw, _registry = build_circuit(spec)
            connect(raw)
        except (CircuitException, AssertionError, RecursionError) as exc:
            self.error_label.setText(f"Cannot build: {exc}")
            return
        self.result_spec = spec
        self.accept()


def _describe_entry(entry):
    extras = {k: v for k, v in entry.items() if k not in ("type", "name")}
    if not extras:
        return entry["type"]
    detail = ", ".join(f"{k}={v}" for k, v in sorted(extras.items()))
    return f"{entry['type']} ({detail})"
