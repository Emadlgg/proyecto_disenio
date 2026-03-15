from automata import afd
from automata.afd import AFD


class SubsetConstruction:
    def __init__(self, afn):
        self.afn = afn

    # ----------------------------
    # ε-closure
    # ----------------------------
    def epsilon_closure(self, states):
        stack = list(states)
        closure = set(states)

        while stack:
            state = stack.pop()

            if (state, "ε") in self.afn.transitions:
                for next_state in self.afn.transitions[(state, "ε")]:
                    if next_state not in closure:
                        closure.add(next_state)
                        stack.append(next_state)

        return closure

    # ----------------------------
    # move
    # ----------------------------
    def move(self, states, symbol):
        result = set()

        for state in states:
            if (state, symbol) in self.afn.transitions:
                result.update(self.afn.transitions[(state, symbol)])

        return result

    # ----------------------------
    # Construcción principal
    # ----------------------------
    def build(self):
        afd = AFD()

        # estado inicial del AFD
        initial_closure = frozenset(
            self.epsilon_closure({self.afn.initial_state})
        )

        afd.initial_state = initial_closure
        afd.states.add(initial_closure)

        unmarked_states = [initial_closure]

        while unmarked_states:
            current = unmarked_states.pop()

            # obtener símbolos del AFN (sin ε)
            symbols = {
                symbol
                for (state, symbol) in self.afn.transitions
                if symbol != "ε"
            }

            for symbol in symbols:
                move_result = self.move(current, symbol)
                if not move_result:
                    continue

                closure = frozenset(self.epsilon_closure(move_result))

                if closure not in afd.states:
                    afd.states.add(closure)
                    unmarked_states.append(closure)

                afd.transitions[(current, symbol)] = closure

        # determinar estados finales
        for state in afd.states:
            matching_tokens = []

            for afn_state in state:
                if afn_state in self.afn.token_map:
                    token, priority = self.afn.token_map[afn_state]
                    matching_tokens.append((token, priority))

            if matching_tokens:
                afd.final_states.add(state)

                # escoger token con menor prioridad
                best_token = sorted(matching_tokens, key=lambda x: x[1])[0]
                afd.token_map[state] = best_token[0]
        
        return afd