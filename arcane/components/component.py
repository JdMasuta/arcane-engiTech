"""Base class every circuit component derives from."""
import inspect


class component():
    def __init__(self, requires_input=True, level=1, energy=0, name='placeholder_name'):
        self.requires_input = requires_input
        self.previous_comp = None  # component before
        self.next_comp = None  # component after
        self.energy = energy  # amount of energy in the component
        self.level = level
        self.name = name
        self.allow_input = True
        self.allow_output = True
        self.max_energy = 2
        # a self-managed component is the sole actor on its links: wires must
        # not transfer across a link a self-managed neighbour already handles,
        # and when both ends of a link are self-managed the downstream one pulls
        self.self_managed_links = False
        # all components need a drawing function
        #   and also connecting points I think
        #   for now, let's just get them in one line

    def print_info(self):
        attributes = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        passed_atts = [a for a in attributes if not (a[0].startswith('__') and a[0].endswith('__'))]
        print(f"--------info about {self.name}----------")
        for pa in passed_atts:
            print(f'{pa[0]}: {pa[1]}')
        print("===================")

    def step(self):
        # a placeholder
        pass
