"""Helpers for stepping a connected circuit and recording its energy history.

These reproduce what the components.py __main__ demo does inline, so other
modules (tests, the manim converter, demo scripts) can reuse them.
"""


def flatten(comp_list):
    flat = []
    for comp in comp_list:
        if isinstance(comp, list):
            for sub in comp:
                flat.extend(flatten(sub) if isinstance(sub, list) else [sub])
        else:
            flat.append(comp)
    return flat


def step_all(comp_list):
    for comp in flatten(comp_list):
        comp.step()


def total_energy(comp_list):
    return sum(comp.energy for comp in flatten(comp_list))


def simulate(comp_list, n_steps, events=None):
    """Step the circuit n_steps times, recording per-component energy.

    events maps a step index to a callable fired before that step runs
    (e.g. {50: switch.toggle}). Returns (t, Es, ET) where Es maps component
    name to its energy series and ET is the total energy series.
    """
    events = events or {}
    comps = flatten(comp_list)
    t = []
    Es = {comp.name: [] for comp in comps}
    ET = []
    for step_i in range(n_steps):
        if step_i in events:
            events[step_i]()
        for comp in comps:
            Es[comp.name].append(comp.energy)
        ET.append(sum(comp.energy for comp in comps))
        t.append(step_i)
        for comp in comps:
            comp.step()
    return t, Es, ET


def plot_history(t, Es, ET, check_wires=False, log_scale=True, ax=None):
    import matplotlib.pyplot as plt

    if ax is None:
        ax = plt.gca()
    for name, series in Es.items():
        if check_wires or ("wire" not in name and "junction" not in name):
            ax.plot(t, series, label=name)
    ax.plot(t, ET, color='k', ls="--", label="Total Energy")
    ax.legend()
    ax.set_ylabel("Energy")
    ax.set_xlabel("Time Step")
    if log_scale:
        ax.set_yscale('log')
    return ax
