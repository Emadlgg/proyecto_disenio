class AFD:
    def __init__(self):
        self.states = set()
        self.initial_state = None
        self.final_states = set()
        self.transitions = {}
        self.token_map = {}  # estado_AFD (frozenset) → token

    # ----------------------------
    # Simulación booleana
    # ----------------------------
    def simulate(self, input_string):
        current_state = self.initial_state

        for symbol in input_string:
            key = (current_state, symbol)

            if key not in self.transitions:
                return False

            current_state = self.transitions[key]

        return current_state in self.final_states

    # ----------------------------
    # Simulación con token
    # ----------------------------
    def simulate_token(self, input_string):
        current_state = self.initial_state

        for symbol in input_string:
            key = (current_state, symbol)

            if key not in self.transitions:
                return None

            current_state = self.transitions[key]

        if current_state in self.final_states:
            return self.token_map.get(current_state, None)

        return None

    def __repr__(self):
        return (
            f"States: {self.states}\n"
            f"Initial: {self.initial_state}\n"
            f"Final: {self.final_states}\n"
            f"Transitions: {self.transitions}\n"
            f"Token Map: {self.token_map}"
        )
    
        # ----------------------------
    # Longest Match (Lexer real)
    # ----------------------------
    def match(self, input_string):
        current_state = self.initial_state
        last_final_state = None
        last_final_position = -1

        position = 0

        while position < len(input_string):
            symbol = input_string[position]
            key = (current_state, symbol)

            if key not in self.transitions:
                break

            current_state = self.transitions[key]
            position += 1

            if current_state in self.final_states:
                last_final_state = current_state
                last_final_position = position

        if last_final_state is not None:
            token = self.token_map[last_final_state]
            lexeme = input_string[:last_final_position]
            return token, lexeme

        return None