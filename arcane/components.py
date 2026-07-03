import inspect
import matplotlib.pyplot as plt
import numpy as np
from arcane.exceptions import CircuitException

class component():
    def __init__(self,requires_input = True, level = 1,energy = 0,name = 'placeholder_name'):
        self.requires_input = requires_input
        self.previous_comp = None #component before
        self.next_comp = None #component after
        self.energy = energy #amount of energy in the component
        self.level = level
        self.name = name
        self.allow_input = True
        self.allow_output = True
        self.max_energy = 2
        #a self-managed component is the sole actor on its links: wires must
        # not transfer across a link a self-managed neighbour already handles,
        # and when both ends of a link are self-managed the downstream one pulls
        self.self_managed_links = False
        #all components need a drawing function
        #   and also connecting points I think
        #   for now, let's just get them in one line
    def print_info(self):
        attributes = inspect.getmembers(self, lambda a:not(inspect.isroutine(a)))
        passed_atts = [a for a in attributes if not(a[0].startswith('__') and a[0].endswith('__'))]
        print(f"--------info about {self.name}----------")
        for pa in passed_atts:
            print(f'{pa[0]}: {pa[1]}')
        print("===================")

    def step(self):
        #a placeholder
        pass

class Battery(component):
    def __init__(self,level = 1,energy = 100,name = "battery"):
        super().__init__(level = level,energy = energy,name = name)
        if level == 0:
            self.requires_input = False
        self.max_energy = 1000

    def plot(self,start_point = (0,0),x_size = 0.25,y_size = 1,ax = None):
        if ax is None:
            ax = plt.gca()
        line1_x = [start_point[0],
                   start_point[0]]
        line1_y = [start_point[1] - y_size/2,
                   start_point[1] +y_size/2]
        line2_x = [start_point[0]+x_size,
                   start_point[0]+x_size]
        line2_y = [start_point[1] - y_size/4,
                   start_point[1] + y_size/4]
        ax.plot(line1_x,line1_y,color = 'k',ls = "-")
        ax.plot(line2_x,line2_y,color = 'k',ls = "-")
        end_point = [start_point[0] + x_size,start_point[1]]
        return(end_point)
    def step(self):
        pass

class Wire(component):
    def __init__(self,level = None,energy = 0,name = "wire"):
        super().__init__(level = level,energy = energy,name = name)
        self.energy_in_rate = 1
        self.energy_out_rate = np.inf #wires dump everything they hold each step
        self.color = 'r'
    def step(self):

        prev_energy = self.previous_comp.energy > 0
        prev_allow = self.previous_comp.allow_output
        self_thresh = self.energy < self.max_energy
        prev_passive = not self.previous_comp.self_managed_links

        if prev_energy and prev_allow and self_thresh and prev_passive :
            de = min([self.previous_comp.energy,self.energy_in_rate])
            self.energy += de
            self.previous_comp.energy -= de

        de = min([self.energy_out_rate,self.energy])

        self_energy = self.energy > 0
        next_allow = self.next_comp.allow_input
        next_thresh = self.next_comp.energy + de < self.next_comp.max_energy
        next_passive = not self.next_comp.self_managed_links

        if  self_energy and next_allow and next_thresh and next_passive:
            
            self.next_comp.energy += de
            self.energy -= de

    def plot(self,start_point = [0,0],x_size = 3,y_size = 0,ax = None):
        if ax is None:
            ax = plt.gca()
        line1 = np.array([[start_point[0],start_point[0] + x_size],
                          [start_point[1],start_point[1] + y_size]])
        ax.plot(line1[0,:],line1[1,:],color = self.color,ls = "-")
        return(line1[:,1])

class Resistor(Wire):
    """A Wire that throttles flow instead of passing everything through.

    Ohm's-law analogue for a discrete-step simulation: the per-step
    transferable energy is 1/resistance, so doubling the resistance halves
    the flow rate. resistance = 1 behaves like a rate-1 wire.

    Like Junction, a Resistor is the only actor on both of its links —
    neighbouring wires skip it — otherwise a downstream wire would pull at
    its own (unthrottled) rate and defeat the resistance.
    """
    def __init__(self,resistance = 2,level = None,energy = 0,name = "resistor"):
        super().__init__(level = level,energy = energy,name = name)
        if resistance <= 0:
            raise CircuitException(f"In {name} resistance must be > 0, found {resistance}")
        self.resistance = resistance
        self.energy_in_rate = 1/resistance
        self.energy_out_rate = 1/resistance
        self.color = 'orange'
        self.self_managed_links = True

    def step(self):
        de = min([self.previous_comp.energy,self.energy_in_rate])
        if de > 0 and self.previous_comp.allow_output and self.energy + de <= self.max_energy:
            self.energy += de
            self.previous_comp.energy -= de

        de = min([self.energy,self.energy_out_rate])
        if de > 0 and self.next_comp.allow_input and self.next_comp.energy + de < self.next_comp.max_energy \
                and not self.next_comp.self_managed_links:
            self.next_comp.energy += de
            self.energy -= de

    def plot(self,start_point = [0,0],x_size = 3,y_size = 0.4,ax = None):
        if ax is None:
            ax = plt.gca()
        n_zigs = 3
        zig_x = np.linspace(start_point[0] + x_size/3,start_point[0] + 2*x_size/3,2*n_zigs + 1)
        zig_y = np.full_like(zig_x,float(start_point[1]))
        zig_y[1:-1:2] += y_size/2
        zig_y[2:-1:2] -= y_size/2
        xs = np.concatenate([[start_point[0]],zig_x,[start_point[0] + x_size]])
        ys = np.concatenate([[start_point[1]],zig_y,[start_point[1]]])
        ax.plot(xs,ys,color = self.color,ls = "-")
        return([start_point[0] + x_size,start_point[1]])

class Concentration(component):
    """Capacitor/crystal analogue of the D&D concentration mechanic.

    Chosen semantics:
    - while *charging* it pulls up to charge_rate energy per step from the
      previous component and holds it, releasing nothing downstream
    - once the stored energy reaches capacity it starts *discharging*:
      each step it dumps as much held energy as the next component can
      accept, until empty, then goes back to charging
    - break_concentration() models a failed concentration save: whatever
      is held dissipates (leaves the circuit entirely, it is not passed
      on) and charging restarts from zero

    Like Resistor, it is the sole actor on both of its links.
    """
    def __init__(self,capacity = 50,charge_rate = 1,level = None,energy = 0,name = "concentration"):
        super().__init__(level = level,energy = energy,name = name)
        if capacity <= 0:
            raise CircuitException(f"In {name} capacity must be > 0, found {capacity}")
        self.capacity = capacity
        self.charge_rate = charge_rate
        self.max_energy = capacity
        self.discharging = False
        self.color = 'b'
        self.self_managed_links = True

    def step(self):
        if not self.discharging:
            de = min([self.previous_comp.energy,self.charge_rate,self.capacity - self.energy])
            if de > 0 and self.previous_comp.allow_output:
                self.energy += de
                self.previous_comp.energy -= de
            if self.energy >= self.capacity:
                self.discharging = True
        else:
            room = self.next_comp.max_energy - self.next_comp.energy
            de = min([self.energy,room])
            if de > 0 and self.next_comp.allow_input and not self.next_comp.self_managed_links:
                self.next_comp.energy += de
                self.energy -= de
            if self.energy <= 0:
                self.discharging = False
        self.allow_output = self.discharging

    def break_concentration(self):
        lost = self.energy
        self.energy = 0
        self.discharging = False
        self.allow_output = False
        return(lost)

    def plot(self,start_point = (0,0),x_size = 1,y_size = 1,ax = None):
        if ax is None:
            ax = plt.gca()
        gap = x_size/4
        mid = start_point[0] + x_size/2
        ax.plot([start_point[0],mid - gap/2],[start_point[1],start_point[1]],color = self.color,ls = "-")
        ax.plot([mid + gap/2,start_point[0] + x_size],[start_point[1],start_point[1]],color = self.color,ls = "-")
        ax.plot([mid - gap/2,mid - gap/2],[start_point[1] - y_size/2,start_point[1] + y_size/2],color = self.color,ls = "-")
        ax.plot([mid + gap/2,mid + gap/2],[start_point[1] - y_size/2,start_point[1] + y_size/2],color = self.color,ls = "-")
        return([start_point[0] + x_size,start_point[1]])

class Junction(component):
    def __init__(self,n_inputs,n_outputs,level = None,energy = 0,name = "junction"):
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs
        super().__init__(level = level,energy = energy,name = name)
        self.energy_in_rate = 1
        self.energy_out_rate = 1
        
        
        if self.n_inputs != 1 and self.n_outputs != 1:
            #check this for simplicity. In theory we can have a 3 input 2 output case work but for this code
            # I think demanding at least one be 1 works better
            raise CircuitException(f"In {self.name} either n_inputs or n_outputs must be 1. Instead found n_inputs = {self.n_inputs},n_outputs = {self.n_outputs}")
        self.color = 'purple'
        self.self_managed_links = True
        #'open'/'close' is stamped by connect(); 'inline' junction-like
        # components (1-in gates) are plotted as ordinary single components
        self.junction_role = None

    def step(self):
        #get energy from all possible inputs
        allowed_inputs = []
        
        for input_comp in range(self.n_inputs):
            #if self.name == "junction -0_0":
            #    print("i: ",self.previous_comp[input_comp].name,self.previous_comp[input_comp].energy,self.previous_comp[input_comp].allow_output)
            if self.previous_comp[input_comp].energy>0 and self.previous_comp[input_comp].allow_output:
                allowed_inputs.append(input_comp)
                #print(self.previous_comp[input_comp].energy)
        n_allowed_in = len(allowed_inputs)
        if n_allowed_in >1 :
            for i in allowed_inputs:
                if self.previous_comp[i].energy>0 and self.previous_comp[i].allow_output and self.energy < self.max_energy:
                    self.energy += min(self.previous_comp[i].energy,1)/n_allowed_in
                    self.previous_comp[i].energy -= min(self.previous_comp[i].energy,1)/n_allowed_in
        elif n_allowed_in ==1:
            i = allowed_inputs[0]
            if self.previous_comp[i].energy>0 and self.previous_comp[i].allow_output and self.energy < self.max_energy:
                self.energy += min([self.previous_comp[i].energy,1])
                self.previous_comp[i].energy -= min([self.previous_comp[i].energy,1])
        # if self.name == "junction -0_0":
        #     print("after in: ",self.energy, n_allowed_in, self.previous_comp[input_comp].energy)
        #     print(self.previous_comp[1].name)
        #only if we have energy to output

        e_before = self.energy

        if e_before > 0:
            allowed_outputs = []
            
            for output_comp in range(self.n_outputs):
                if self.next_comp[output_comp].allow_input and not self.next_comp[output_comp].self_managed_links:
                    allowed_outputs.append(output_comp)
            n_allowed_out = len(allowed_outputs)
            remaining_idx = []
            for i in allowed_outputs:
                if self.next_comp[i].energy + e_before/n_allowed_out < self.next_comp[i].max_energy:
                    self.next_comp[i].energy += e_before/n_allowed_out
                    self.energy -= e_before/n_allowed_out
                    remaining_idx.append(i)

            #if any don't meet that requirement we need to spread the remainder out
            remaining_energy = self.energy

            if remaining_idx and remaining_energy > 0:
                for i in remaining_idx:
                    self.next_comp[i].energy += remaining_energy/len(remaining_idx)
                    self.energy -= remaining_energy/len(remaining_idx)
            
    
    def plot(self,start_point = [[0,0]],x_size = 2,y_size = 2,ax = None,buffer = 0.1):
        if ax is None:
            ax = plt.gca()
        assert len(start_point) == self.n_inputs, f"Number of start_points differs from number of inputs to {self.name}"

        #make all start_points at same x
        
        max_x = start_point[0][0]
        for sp in start_point:
            if sp[0]>max_x:
                max_x = sp[0]
        mid_y = np.mean([sp[1] for sp in start_point])


        junction_line = np.array([[max_x+buffer+x_size/2,max_x+buffer+x_size/2],
                                 [mid_y + y_size/2,mid_y - y_size/2]])
        
        ax.plot(junction_line[0,:],junction_line[1,:],color = self.color)
        if self.n_inputs == 1:
            
            input_lines = np.array([[start_point[0][0],start_point[0][0] + x_size/2],
                                    [start_point[0][1],start_point[0][1]]])
            ax.plot(input_lines[0,:],input_lines[1,:],color = self.color)
        else:
            for i in range(self.n_inputs):
                input_x = [start_point[i][0],junction_line[0][0]]
                input_y = [start_point[i][1],start_point[i][1]]
                ax.plot(input_x,
                        input_y,
                        color = self.color)
        if self.n_outputs == 1:
            
            output_lines = np.array([[junction_line[0][0],max_x+buffer+x_size],
                                    [mid_y,mid_y]])
            end_points = [[max_x + buffer + x_size,mid_y]]
            ax.plot(output_lines[0,:],output_lines[1,:],color = self.color)
        else:
            
            end_points = []
            for i in range(self.n_outputs):
                output_y = np.linspace(mid_y + y_size/2,mid_y - y_size/2,self.n_outputs)
                output_x = [junction_line[0][0],max_x+buffer+x_size]
                ax.plot(output_x,
                        [output_y[i],output_y[i]],
                        color = self.color)
                end_points.append([output_x[-1],output_y[i]])
        return(end_points)
class LogicGate(Junction):
    """Base for gates: n inputs merged into 1 output, gated by a boolean rule.

    An input counts as *active* when it holds at least `threshold` energy
    and allows output. When gate_open(active) is True the gate pulls up to
    1 energy per step from each active input and pushes what it holds
    onward; when False nothing moves through it.

    Multi-input gates are placed directly after a branch list, where
    connect() uses them as that branch list's closing junction.
    """
    label = '?'
    def __init__(self,n_inputs,threshold = 0.5,level = None,energy = 0,name = "gate"):
        super().__init__(n_inputs,1,level = level,energy = energy,name = name)
        self.threshold = threshold
        self.color = 'g'
        self.junction_role = 'inline'

    def input_active(self):
        return([pc.energy >= self.threshold and pc.allow_output for pc in self.previous_comp])

    def gate_open(self,active):
        raise NotImplementedError

    def step(self):
        active = self.input_active()
        if self.gate_open(active):
            for i,a in enumerate(active):
                if a and self.energy < self.max_energy:
                    de = min([self.previous_comp[i].energy,1])
                    self.energy += de
                    self.previous_comp[i].energy -= de
        de = self.energy
        nxt = self.next_comp[0]
        if de > 0 and nxt.allow_input and not nxt.self_managed_links and nxt.energy + de < nxt.max_energy:
            nxt.energy += de
            self.energy -= de

    def plot(self,start_point = [[0,0]],x_size = 2,y_size = 2,ax = None,buffer = 0.1):
        if ax is None:
            ax = plt.gca()
        end_points = super().plot(start_point = start_point,x_size = x_size,y_size = y_size,ax = ax,buffer = buffer)
        mid_y = np.mean([sp[1] for sp in start_point]) if self.n_inputs > 1 else start_point[0][1]
        ax.text(end_points[0][0] - x_size/2,mid_y + y_size/2 + buffer,self.label,color = self.color,ha = 'center')
        return(end_points)

class AndGate(LogicGate):
    label = 'AND'
    def __init__(self,n_inputs = 2,threshold = 0.5,level = None,name = "and gate"):
        super().__init__(n_inputs,threshold = threshold,level = level,name = name)
    def gate_open(self,active):
        return(all(active))

class OrGate(LogicGate):
    label = 'OR'
    def __init__(self,n_inputs = 2,threshold = 0.5,level = None,name = "or gate"):
        super().__init__(n_inputs,threshold = threshold,level = level,name = name)
    def gate_open(self,active):
        return(any(active))

class NotGate(LogicGate):
    """Inverter: emits 1 energy per step from an internal reserve only while
    its input is quiet. The control signal is consumed either way (up to
    1/step): it refills the reserve when there is room, otherwise it
    dissipates — a NOT gate held open burns the energy used to hold it.
    """
    label = 'NOT'
    def __init__(self,supply = 100,threshold = 0.5,level = None,name = "not gate"):
        super().__init__(1,threshold = threshold,level = level,energy = supply,name = name)
        self.supply = supply
        self.max_energy = supply

    def gate_open(self,active):
        return(not active[0])

    def step(self):
        prev = self.previous_comp[0]
        was_active = self.input_active()[0]
        de = min([prev.energy,1])
        if de > 0 and prev.allow_output:
            prev.energy -= de
            self.energy = min([self.energy + de,self.max_energy])
        if not was_active:
            emit = min([self.energy,1])
            nxt = self.next_comp[0]
            if emit > 0 and nxt.allow_input and not nxt.self_managed_links and nxt.energy + emit < nxt.max_energy:
                nxt.energy += emit
                self.energy -= emit

    def plot(self,start_point = (0,0),x_size = 1.5,y_size = 1,ax = None):
        if ax is None:
            ax = plt.gca()
        tip_x = start_point[0] + x_size*0.8
        ax.plot([start_point[0],start_point[0],tip_x,start_point[0]],
                [start_point[1] - y_size/2,start_point[1] + y_size/2,start_point[1],start_point[1] - y_size/2],
                color = self.color,ls = "-")
        circle = plt.Circle((tip_x + x_size*0.1,start_point[1]),x_size*0.1,fill = False,color = self.color)
        ax.add_patch(circle)
        return([start_point[0] + x_size,start_point[1]])

class Caster(component):
    def __init__(self,level = 1,energy = 0,name = "caster"):
        super().__init__(level = level,requires_input=True,energy = energy,name = name)
        self.cast_threshold = 100
        self.allow_output=False
        self.max_energy = self.cast_threshold+1
    def cast(self):
        if self.energy>= self.cast_threshold:
            self.energy = 0
            return(True)
        else:
            return(False)
    
    def plot(self,start_point = (0,0),x_size = 1,y_size = 1.25,ax = None):
        if ax is None:
            ax = plt.gca()
        
        line1_x = [start_point[0],start_point[0] + x_size/2,start_point[0] + x_size]
        
        line1_y = [start_point[1],start_point[1] + y_size/2,start_point[1]]
        line2_y = [start_point[1],start_point[1] - y_size/2,start_point[1]]
        ax.plot(line1_x,line1_y,color = 'k',ls = "-")
        ax.plot(line1_x,line2_y,color = 'k',ls = "-")
        end_point = [start_point[0] + x_size,start_point[1]]

        return(end_point)
    
    def step(self):
        if self.energy >= self.cast_threshold:
            self.cast()
        else:
            pass

class Blank(component):
    def __init__(self,level = 1,energy = 0,name = "blank"):
        super().__init__(level = level,requires_input=True,energy = energy,name = name)
        self.max_energy = 10000
    def step(self):
        pass
    def plot(self,start_point = (0,0),x_size = 1,y_size = 1.25,ax = None):
        return(start_point)

class Switch(component):
    def __init__(self,level = None,energy = 0,name = "switch",start_on = False):
        super().__init__(level = level,requires_input=True,energy = energy,name = name)
        self.allow_input = start_on
        self.allow_output = start_on
        self.color = 'k'
    def step(self):
        if self.allow_input and self.previous_comp.energy > 0 and self.previous_comp.allow_output \
                and not self.previous_comp.self_managed_links:
            self.previous_comp.energy -=1
            self.energy += 1
        if self.energy > 0 and self.allow_output and self.next_comp.allow_input \
                and not self.next_comp.self_managed_links:
            self.next_comp.energy += 1
            self.energy -= 1
    def plot(self,start_point = (0,0),x_size = 2,y_size = 0.25,ax = None):
        if ax is None:
            ax = plt.gca()
        line1 = np.array([[start_point[0],start_point[0] + x_size*(1/3),start_point[0] + x_size*(2/3)],
                          [start_point[1],start_point[1],start_point[1] + y_size]])
        line2 = np.array([[start_point[0] + (2/3)*x_size,start_point[0] + x_size],[start_point[1],start_point[1]]])
        ax.plot(line1[0,:],line1[1,:],color = self.color,ls = "-")
        ax.plot(line2[0,:],line2[1,:],color = self.color,ls = "-")
        end_point = [start_point[0] + x_size,start_point[1] + 0]
        return(end_point)
    def toggle(self):
        self.allow_input = True
        self.allow_output = True

def connect(comp_list: list[component],depth = 0,branch_idx = None,verbose = False):
    """Wire up previous_comp/next_comp links for a nested circuit description.

    Each element of comp_list is either a component or a list of parallel
    branches (a junction pair is created around those). Adjacent branch
    lists are allowed: the closing junction of one links straight into the
    opening junction of the next. At depth 0 the last element wraps back
    around to the first.
    """
    if depth > 100:
        raise RecursionError("Depth exceed maximum (100) in connect")
    if not isinstance(comp_list,list):
        comp_list = [comp_list] #if we have single component inputs

    n_components = len(comp_list)
    wire_i = 0
    junc_i = 0

    #build a node per element: singles stay as-is, branch lists become
    # (opening junction, connected sub lists, closing junction)
    nodes = []
    consumed = set()
    for k,entry in enumerate(comp_list):
        if k in consumed:
            continue
        if isinstance(entry,list):
            junc_object_o = Junction(1,len(entry),name = f'junction {junc_i}_{depth}')
            #a multi-input gate right after a branch list acts as its closing junction
            follower = comp_list[k+1] if k+1 < n_components else None
            if isinstance(follower,LogicGate) and follower.n_inputs == len(entry):
                junc_object_c = follower
                consumed.add(k+1)
            else:
                junc_object_c = Junction(len(entry),1,name = f'junction -{junc_i}_{depth}')
            junc_object_o.junction_role = 'open'
            junc_object_c.junction_role = 'close'
            junc_i += 1

            sub_comp_lists = [connect(cl,depth = depth + 1,branch_idx = bi,verbose = verbose) for bi,cl in enumerate(entry)]

            #check each individual branch, then that all branches agree
            for scl in sub_comp_lists:
                check_level(scl)
            check_level([scl[-1] for scl in sub_comp_lists])

            junc_object_o.next_comp = [scl[0] for scl in sub_comp_lists]
            junc_object_c.previous_comp = [scl[-1] for scl in sub_comp_lists]
            for scl in sub_comp_lists:
                scl[0].previous_comp = junc_object_o
                scl[-1].next_comp = junc_object_c
            junc_object_c.level = junc_object_c.previous_comp[0].level
            nodes.append((junc_object_o,sub_comp_lists,junc_object_c))
        else:
            nodes.append(entry)

    def head(node):
        return(node[0] if isinstance(node,tuple) else node)
    def tail(node):
        return(node[2] if isinstance(node,tuple) else node)

    #link consecutive nodes; only a closed loop (depth 0) wraps around
    n_nodes = len(nodes)
    n_links = n_nodes if depth == 0 and n_nodes > 1 else n_nodes - 1
    link_wires = [None]*n_nodes
    for i in range(n_links):
        j = (i+1)%n_nodes
        t,h = tail(nodes[i]),head(nodes[j])
        t_junc,h_junc = isinstance(t,Junction),isinstance(h,Junction)

        if not t_junc and not h_junc:
            if h.requires_input:
                wire_obj = Wire(None,0,name = f'wire {wire_i}_{depth}_{branch_idx}' if branch_idx is not None else f'wire {wire_i}_{depth}')
                wire_i += 1
                t.next_comp = wire_obj
                h.previous_comp = wire_obj
                wire_obj.previous_comp = t
                wire_obj.next_comp = h
                wire_obj.level = t.level
                if wire_obj.level != h.level:
                    raise CircuitException(f"Wire object connecting {t.name} ({t.__class__.__name__}) and {h.name} ({h.__class__.__name__}) have different levels: {t.level} and {h.level}")
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
            #junction meets junction: downstream pulls, upstream skips
            t.next_comp = [h]
            h.previous_comp = [t]
            h.level = t.level

    #flatten into the same structure plot() expects
    new_comp_list = []
    for i,node in enumerate(nodes):
        if isinstance(node,tuple):
            new_comp_list.extend([node[0],node[1],node[2]])
        else:
            new_comp_list.append(node)
        if link_wires[i] is not None:
            new_comp_list.append(link_wires[i])
        if verbose:
            print(f"{''.join(['     ']*depth)}i: ",i,new_comp_list)
    return(new_comp_list)
def check_level(sub_comp_list):
    levels = [sc.level for sc in sub_comp_list]
    assert all([levels[0] == x for x in levels])

def wrap_around(end_point,wrap_to = [0,0],buffer = 3.,ax = None):
    if ax is None:
        ax = plt.gca()
    wire_line = np.array([[end_point[0],end_point[0] + buffer,end_point[0] + buffer,wrap_to[0] - buffer,wrap_to[0] - buffer,wrap_to[0]],
                          [end_point[1],end_point[1],end_point[1] - buffer,end_point[1] - buffer,end_point[1],end_point[1]]])
    ax.plot(wire_line[0],wire_line[1])

def plot(comp_list,buffer = 3.,start_point = [0,0],depth = 0,ax = None,record = None,show = True):
    """Draw the circuit; when record is a dict it also captures, per
    component, the xy line segments its symbol drew (used by the manim
    converter). Patch-based decorations (e.g. the NOT gate's circle) are
    not captured.
    """
    n_components = len(comp_list)
    start_point_init = start_point.copy()
    if ax is None:
        fig,ax = plt.subplots(1,1,figsize = (5,5))

    def capture(comp,plot_call):
        if record is None:
            return(plot_call())
        n0 = len(ax.lines)
        result = plot_call()
        record.setdefault(comp,[]).extend([np.array(l.get_data()) for l in ax.lines[n0:]])
        return(result)

    for i in range(n_components):
        comp = comp_list[i]
        role = getattr(comp,'junction_role',None)
        is_opening = isinstance(comp,Junction) and (role == 'open' or (role is None and "-" not in comp.name))
        is_closing = isinstance(comp,Junction) and (role == 'close' or (role is None and "-" in comp.name))
        if is_opening:
            end_points = capture(comp,lambda: comp.plot([start_point],ax = ax))
            #plot branches
            junction_close_points = []
            for k,scl in enumerate(comp_list[i+1]):
                sub_end_point = plot(scl,start_point = end_points[k],depth = depth + 1,ax = ax,record = record)
                junction_close_points.append(sub_end_point)
            #plot closing
            end_point = capture(comp_list[i+2],lambda: comp_list[i+2].plot(junction_close_points,ax = ax))[0]
            start_point = np.array(end_point)

        elif isinstance(comp,list) or is_closing:
            continue
        else:
            end_point = capture(comp,lambda: comp.plot(start_point,ax = ax))
            start_point = np.array(end_point)# + np.array([buffer,0])
    if depth == 0:
        if record is None:
            wrap_around(end_point,wrap_to = start_point_init,buffer = buffer,ax = ax)
        else:
            n0 = len(ax.lines)
            wrap_around(end_point,wrap_to = start_point_init,buffer = buffer,ax = ax)
            record.setdefault('__wrap__',[]).extend([np.array(l.get_data()) for l in ax.lines[n0:]])
        if show:
            plt.show()
        return(end_point)
    else:
        return(end_point)

def get_n_components(comp_list):
    count = 0
    for comp in comp_list:
        if isinstance(comp,list):
            count += get_n_components(comp)
        else:
            count += 1
    return(count)

def get_component_names(comp_list):
    names = []
    for comp in comp_list:
        if isinstance(comp,list):
            names += get_component_names(comp)
        else:
            names.append(comp.name)
    return(names)
if __name__ == "__main__":

    b_test = Battery(2,name = "Battery 1")
    b_test2 = Battery(2,name = "Battery 2")
    b_test3 = Battery(2,name = "Battery 3")
    b_test3.energy = 300
    s_test = Switch(2,name = "Switch")
    
    c_test = Caster(2,name = "Caster 1")
    w_test = Wire(2,name = "TestingElement")
    w_test.color = 'grey'
    c_test2 = Caster(2,name = "Caster 2")
    c_test3 = Caster(2,name = "Caster 3")
    blank_test = Blank(2)
    test_comp_list = [b_test,s_test,b_test2,b_test3,[c_test,c_test2,c_test3]]
    
    new_comp_list = connect(test_comp_list)

    print(new_comp_list)
    #--------simulation
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
            if isinstance(new_comp_list[i],list):
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
            if isinstance(comp,list):
                for scl in comp:
                    for c in scl:
                        c.step()
            else:
                comp.step()
        
    check_wires = False

    for i,cn in enumerate(comp_names):
        if check_wires:
            plt.plot(t,Es[cn],label = cn)
        elif check_wires is False and ("wire" not in cn and "junction" not in cn):
            plt.plot(t,Es[cn],label = cn)
    plt.plot(t,ET,color = 'k',ls = "--",label = "Total Energy")
    plt.legend()
    plt.ylabel("Energy")
    plt.xlabel("Time Step")
    plt.yscale('log')
    plt.show()


    