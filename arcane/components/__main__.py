"""The original author's demo circuit: python -m arcane.components"""
import matplotlib.pyplot as plt

from arcane.components import (Battery, Blank, Caster, Switch, Wire,
                               connect, get_component_names, plot)


if __name__ == "__main__":

    b_test = Battery(2, name="Battery 1")
    b_test2 = Battery(2, name="Battery 2")
    b_test3 = Battery(2, name="Battery 3")
    b_test3.energy = 300
    s_test = Switch(2, name="Switch")

    c_test = Caster(2, name="Caster 1")
    w_test = Wire(2, name="TestingElement")
    w_test.color = 'grey'
    c_test2 = Caster(2, name="Caster 2")
    c_test3 = Caster(2, name="Caster 3")
    blank_test = Blank(2)
    test_comp_list = [b_test, s_test, b_test2, b_test3, [c_test, c_test2, c_test3]]

    new_comp_list = connect(test_comp_list)

    print(new_comp_list)
    # --------simulation
    plot(new_comp_list)
    t = []
    n_t_steps = 600
    comp_names = get_component_names(new_comp_list)
    print(comp_names)
    Es = {}

    for cn in comp_names:
        Es[cn] = []
    ET = []
    for t_step in range(n_t_steps):
        et = 0
        for i in range(len(new_comp_list)):
            if isinstance(new_comp_list[i], list):
                for scl in new_comp_list[i]:
                    for c in scl:
                        Es[c.name].append(c.energy)
                        et += c.energy
            else:
                c = new_comp_list[i]
                Es[c.name].append(c.energy)
                et += c.energy
        ET.append(et)
        if t_step == 50:

            s_test.toggle()
        t.append(t_step)
        for comp in new_comp_list:
            if isinstance(comp, list):
                for scl in comp:
                    for c in scl:
                        c.step()
            else:
                comp.step()

    check_wires = False

    for i, cn in enumerate(comp_names):
        if check_wires:
            plt.plot(t, Es[cn], label=cn)
        elif check_wires is False and ("wire" not in cn and "junction" not in cn):
            plt.plot(t, Es[cn], label=cn)
    plt.plot(t, ET, color='k', ls="--", label="Total Energy")
    plt.legend()
    plt.ylabel("Energy")
    plt.xlabel("Time Step")
    plt.yscale('log')
    plt.show()
