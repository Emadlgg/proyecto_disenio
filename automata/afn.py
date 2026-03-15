class AFN:
    def __init__(self):
        self.states = set()
        self.initial_state = None
        self.final_states = set()
        self.transitions = {}
        self.token_map = {}
        self.priority = None  # estado_final → nombre_token

    def add_transition(self, from_state, symbol, to_state):
        if (from_state, symbol) not in self.transitions:
            self.transitions[(from_state, symbol)] = set()
        self.transitions[(from_state, symbol)].add(to_state)

    def __repr__(self):
        return (
            f"States: {self.states}\n"
            f"Initial: {self.initial_state}\n"
            f"Final: {self.final_states}\n"
            f"Transitions: {self.transitions}\n"
            f"Token Map: {self.token_map}"
        )
# ---------------------------------------------------
# Unificación de múltiples AFNs
# ---------------------------------------------------

def merge_afns(afns):
    merged = AFN()
    state_offset = 0
    new_initial = -1

    merged.states.add(new_initial)
    merged.initial_state = new_initial

    for afn in afns:
        state_mapping = {}

        # renumerar estados
        for state in afn.states:
            state_mapping[state] = state + state_offset

        # copiar estados
        for old_state, new_state in state_mapping.items():
            merged.states.add(new_state)

        # copiar transiciones
        for (state, symbol), targets in afn.transitions.items():
            new_state = state_mapping[state]
            for t in targets:
                merged.add_transition(new_state, symbol, state_mapping[t])

        # copiar finales
        for final_state in afn.final_states:
            merged.final_states.add(state_mapping[final_state])

        # copiar token_map
        for state, token_info in afn.token_map.items():
            merged.token_map[state_mapping[state]] = token_info

        # ε transición desde nuevo inicial
        merged.add_transition(new_initial, "ε", state_mapping[afn.initial_state])

        state_offset += max(afn.states) + 1

    return merged