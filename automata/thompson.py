from automata.afn import AFN


class Thompson:
    def __init__(self):
        self.state_count = 0

    def new_state(self):
        state = self.state_count
        self.state_count += 1
        return state

    def build(self, node):
        if node.type == "SYMBOL":
            return self._build_symbol(node.value)

        elif node.type == "CONCAT":
            return self._build_concat(node)

        elif node.type == "OR":
            return self._build_or(node)

        elif node.type == "STAR":
            return self._build_star(node)
                
        elif node.type == "PLUS":
            return self._build_plus(node)

        elif node.type == "OPTIONAL":
            return self._build_optional(node)        

        else:
            raise Exception(f"Unsupported node type: {node.type}")

    # ----------------------------
    # SYMBOL
    # ----------------------------
    def _build_symbol(self, symbol):
        afn = AFN()

        s0 = self.new_state()
        s1 = self.new_state()

        afn.states.update({s0, s1})
        afn.initial_state = s0
        afn.final_states.add(s1)

        if symbol == "ε":
            afn.add_transition(s0, "ε", s1)
        else:
            afn.add_transition(s0, symbol, s1)

        return afn

    # ----------------------------
    # CONCAT
    # ----------------------------
    def _build_concat(self, node):
        left_afn = self.build(node.left)
        right_afn = self.build(node.right)

        # conectar finales del izquierdo al inicial del derecho con ε
        for final_state in left_afn.final_states:
            left_afn.add_transition(final_state, "ε", right_afn.initial_state)

        afn = AFN()
        afn.states = left_afn.states.union(right_afn.states)
        afn.initial_state = left_afn.initial_state
        afn.final_states = right_afn.final_states
        afn.transitions = {**left_afn.transitions}

        # agregar transiciones del derecho
        for key, value in right_afn.transitions.items():
            afn.transitions[key] = value

        return afn

    # ----------------------------
    # OR
    # ----------------------------
    def _build_or(self, node):
        left_afn = self.build(node.left)
        right_afn = self.build(node.right)

        afn = AFN()

        s0 = self.new_state()
        sf = self.new_state()

        afn.states = (
            left_afn.states
            .union(right_afn.states)
            .union({s0, sf})
        )

        afn.initial_state = s0
        afn.final_states = {sf}

        afn.transitions = {}

        # copiar transiciones existentes
        for key, value in left_afn.transitions.items():
            afn.transitions[key] = value

        for key, value in right_afn.transitions.items():
            afn.transitions[key] = value

        # ε transiciones
        afn.add_transition(s0, "ε", left_afn.initial_state)
        afn.add_transition(s0, "ε", right_afn.initial_state)

        for final_state in left_afn.final_states:
            afn.add_transition(final_state, "ε", sf)

        for final_state in right_afn.final_states:
            afn.add_transition(final_state, "ε", sf)

        return afn

    # ----------------------------
    # STAR
    # ----------------------------
    def _build_star(self, node):
        sub_afn = self.build(node.left)

        afn = AFN()

        s0 = self.new_state()
        sf = self.new_state()

        afn.states = sub_afn.states.union({s0, sf})
        afn.initial_state = s0
        afn.final_states = {sf}
        afn.transitions = sub_afn.transitions.copy()

        # ε transiciones
        afn.add_transition(s0, "ε", sub_afn.initial_state)
        afn.add_transition(s0, "ε", sf)

        for final_state in sub_afn.final_states:
            afn.add_transition(final_state, "ε", sub_afn.initial_state)
            afn.add_transition(final_state, "ε", sf)

        return afn

    # ----------------------------
    # PLUS
    # ----------------------------
    def _build_plus(self, node):
        # a+ = a CONCAT a*
        concat_node = type(node)(
            "CONCAT",
            left=node.left,
            right=type(node)("STAR", left=node.left)
        )
        return self.build(concat_node)

    # ----------------------------
    # OPTIONAL
    # ----------------------------
    def _build_optional(self, node):
        # a? = a | ε
        epsilon_node = type(node)("SYMBOL", value="ε")

        or_node = type(node)(
            "OR",
            left=node.left,
            right=epsilon_node
        )
        return self.build(or_node)