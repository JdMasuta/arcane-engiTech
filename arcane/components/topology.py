"""Wire a nested circuit description into a steppable structure.

connect() turns nested component lists into linked previous_comp/
next_comp chains with auto-inserted wires and junction pairs;
check_level() and the get_* helpers walk the same nested shape.
"""
from arcane.components.component import component
from arcane.components.junction import Junction
from arcane.components.logic_gate import LogicGate
from arcane.components.wire import Wire
from arcane.exceptions import CircuitException


def connect(comp_list: list[component], depth=0, branch_idx=None, verbose=False):
    """Wire up previous_comp/next_comp links for a nested circuit description.

    Each element of comp_list is either a component or a list of parallel
    branches (a junction pair is created around those). Adjacent branch
    lists are allowed: the closing junction of one links straight into the
    opening junction of the next. At depth 0 the last element wraps back
    around to the first.
    """
    if depth > 100:
        raise RecursionError("Depth exceed maximum (100) in connect")
    if not isinstance(comp_list, list):
        comp_list = [comp_list]  # if we have single component inputs

    n_components = len(comp_list)
    wire_i = 0
    junc_i = 0

    # build a node per element: singles stay as-is, branch lists become
    # (opening junction, connected sub lists, closing junction)
    nodes = []
    consumed = set()
    for k, entry in enumerate(comp_list):
        if k in consumed:
            continue
        if isinstance(entry, list):
            junc_object_o = Junction(1, len(entry), name=f'junction {junc_i}_{depth}')
            # a multi-input gate right after a branch list acts as its closing junction
            follower = comp_list[k + 1] if k + 1 < n_components else None
            if isinstance(follower, LogicGate) and follower.n_inputs == len(entry):
                junc_object_c = follower
                consumed.add(k + 1)
            else:
                junc_object_c = Junction(len(entry), 1, name=f'junction -{junc_i}_{depth}')
            junc_object_o.junction_role = 'open'
            junc_object_c.junction_role = 'close'
            junc_i += 1

            sub_comp_lists = [
                connect(
                    cl,
                    depth=depth + 1,
                    branch_idx=bi,
                    verbose=verbose) for bi,
                cl in enumerate(entry)]

            # check each individual branch, then that all branches agree
            for scl in sub_comp_lists:
                check_level(scl)
            check_level([scl[-1] for scl in sub_comp_lists])

            junc_object_o.next_comp = [scl[0] for scl in sub_comp_lists]
            junc_object_c.previous_comp = [scl[-1] for scl in sub_comp_lists]
            for scl in sub_comp_lists:
                scl[0].previous_comp = junc_object_o
                scl[-1].next_comp = junc_object_c
            junc_object_c.level = junc_object_c.previous_comp[0].level
            nodes.append((junc_object_o, sub_comp_lists, junc_object_c))
        else:
            nodes.append(entry)

    def head(node):
        return (node[0] if isinstance(node, tuple) else node)

    def tail(node):
        return (node[2] if isinstance(node, tuple) else node)

    # link consecutive nodes; only a closed loop (depth 0) wraps around
    n_nodes = len(nodes)
    n_links = n_nodes if depth == 0 and n_nodes > 1 else n_nodes - 1
    link_wires = [None] * n_nodes
    for i in range(n_links):
        j = (i + 1) % n_nodes
        t, h = tail(nodes[i]), head(nodes[j])
        t_junc, h_junc = isinstance(t, Junction), isinstance(h, Junction)

        if not t_junc and not h_junc:
            if h.requires_input:
                if branch_idx is not None:
                    wire_name = f'wire {wire_i}_{depth}_{branch_idx}'
                else:
                    wire_name = f'wire {wire_i}_{depth}'
                wire_obj = Wire(None, 0, name=wire_name)
                wire_i += 1
                t.next_comp = wire_obj
                h.previous_comp = wire_obj
                wire_obj.previous_comp = t
                wire_obj.next_comp = h
                wire_obj.level = t.level
                if wire_obj.level != h.level:
                    raise CircuitException(
                        f"Wire object connecting {t.name} "
                        f"({t.__class__.__name__}) and {h.name} "
                        f"({h.__class__.__name__}) have different levels: "
                        f"{t.level} and {h.level}")
                link_wires[i] = wire_obj
            else:
                t.next_comp = None
        elif not t_junc and h_junc:
            t.next_comp = h
            h.previous_comp = [t]
            h.level = t.level
        elif t_junc and not h_junc:
            t.next_comp = [h]
            h.previous_comp = t
        else:
            # junction meets junction: downstream pulls, upstream skips
            t.next_comp = [h]
            h.previous_comp = [t]
            h.level = t.level

    # flatten into the same structure plot() expects
    new_comp_list = []
    for i, node in enumerate(nodes):
        if isinstance(node, tuple):
            new_comp_list.extend([node[0], node[1], node[2]])
        else:
            new_comp_list.append(node)
        if link_wires[i] is not None:
            new_comp_list.append(link_wires[i])
        if verbose:
            print(f"{''.join(['     ']*depth)}i: ", i, new_comp_list)
    return (new_comp_list)


def check_level(sub_comp_list):
    # a nested branch group leaves its raw list-of-branches as a plain list
    # entry (see connect()'s tuple-extend); it has no .level of its own and
    # its consistency was already checked recursively when it was built, so
    # skip it here rather than assuming every entry is a component
    levels = [sc.level for sc in sub_comp_list if not isinstance(sc, list)]
    assert all([levels[0] == x for x in levels])


def get_n_components(comp_list):
    count = 0
    for comp in comp_list:
        if isinstance(comp, list):
            count += get_n_components(comp)
        else:
            count += 1
    return (count)


def get_component_names(comp_list):
    names = []
    for comp in comp_list:
        if isinstance(comp, list):
            names += get_component_names(comp)
        else:
            names.append(comp.name)
    return (names)
