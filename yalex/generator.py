def generate_lexer_file(afd, output_file="lexer.py"):
    """
    Genera un archivo lexer.py funcional a partir del AFD.
    """

    # Convertir estructuras para serialización
    transitions = {}
    for (state, symbol), target in afd.transitions.items():
        transitions[(tuple(state), symbol)] = tuple(target)

    final_states = [tuple(s) for s in afd.final_states]
    token_map = {tuple(state): token for state, token in afd.token_map.items()}
    initial_state = tuple(afd.initial_state)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# =========================================\n")
        f.write("# AUTO-GENERATED LEXER\n")
        f.write("# =========================================\n\n")

        f.write(f"INITIAL_STATE = {repr(initial_state)}\n\n")
        f.write(f"TRANSITIONS = {repr(transitions)}\n\n")
        f.write(f"FINAL_STATES = {repr(final_states)}\n\n")
        f.write(f"TOKEN_MAP = {repr(token_map)}\n\n")

        f.write("""
def match(input_string):
    current_state = INITIAL_STATE
    last_final_state = None
    last_final_position = -1

    position = 0

    while position < len(input_string):
        symbol = input_string[position]
        key = (current_state, symbol)

        if key not in TRANSITIONS:
            break

        current_state = TRANSITIONS[key]
        position += 1

        if current_state in FINAL_STATES:
            last_final_state = current_state
            last_final_position = position

    if last_final_state is not None:
        token = TOKEN_MAP[last_final_state]
        lexeme = input_string[:last_final_position]
        return token, lexeme

    return None


def tokenize(input_string):
    tokens = []
    position = 0

    while position < len(input_string):
        result = match(input_string[position:])

        if result is None:
            print("Lexical error at:", input_string[position:])
            break

        token, lexeme = result

        # Ignorar tokens que empiezan con "_"
        if not token.startswith("_"):
            tokens.append((token, lexeme))

        position += len(lexeme)

    return tokens
""")

    print(f"Lexer generated successfully: {output_file}")