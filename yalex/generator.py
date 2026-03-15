def generate_lexer_file(afd, output_file="lexer.py"):
    """
    Genera un archivo lexer.py funcional a partir del AFD.

    Los estados del AFD son frozensets de enteros, lo que genera tablas
    enormes al serializar. Esta función los renumera a ints simples
    antes de escribir el archivo, resultando en un lexer compacto y rápido.
    """

    # ── Renumerar estados frozenset → int ────────────────────────
    state_list  = list(afd.states)
    s2i         = {s: i for i, s in enumerate(state_list)}

    initial     = s2i[afd.initial_state]
    final_set   = {s2i[s] for s in afd.final_states}
    token_map   = {s2i[s]: tok for s, tok in afd.token_map.items()}
    transitions = {(s2i[s], sym): s2i[t] for (s, sym), t in afd.transitions.items()}

    with open(output_file, "w", encoding="utf-8") as f:

        # ── Encabezado ───────────────────────────────────────────
        f.write("# =========================================\n")
        f.write("# LEXER AUTO-GENERADO POR YALEX\n")
        f.write("# =========================================\n\n")
        f.write("import sys\n\n")

        # ── Tablas del AFD ───────────────────────────────────────
        f.write(f"INITIAL_STATE = {initial}\n\n")
        f.write(f"FINAL_STATES  = {repr(final_set)}\n\n")
        f.write(f"TOKEN_MAP     = {repr(token_map)}\n\n")

        # Escribir transiciones línea por línea (evita líneas de megabytes)
        f.write("TRANSITIONS = {\n")
        for (state, symbol), target in sorted(transitions.items()):
            f.write(f"    ({state}, {repr(symbol)}): {target},\n")
        f.write("}\n\n")

        # ── match ─────────────────────────────────────────────────
        f.write('''\
def match(input_string):
    """Reconoce el token más largo desde el inicio. Retorna (token, lexeme) o None."""
    cur     = INITIAL_STATE
    last    = None
    lastpos = -1
    pos     = 0
    while pos < len(input_string):
        key = (cur, input_string[pos])
        if key not in TRANSITIONS:
            break
        cur = TRANSITIONS[key]
        pos += 1
        if cur in FINAL_STATES:
            last    = cur
            lastpos = pos
    if last is not None:
        return TOKEN_MAP[last], input_string[:lastpos]
    return None


''')

        # ── tokenize ──────────────────────────────────────────────
        f.write('''\
def tokenize(input_string):
    """
    Tokeniza input_string completo.
    Tokens con _ al inicio se ignoran (whitespace, comentarios).
    Retorna (lista_tokens, lista_errores).
    """
    tokens = []
    errors = []
    pos    = 0
    while pos < len(input_string):
        result = match(input_string[pos:])
        if result is None:
            errors.append(f"Error lexico en posicion {pos}: caracter inesperado {repr(input_string[pos])}")
            pos += 1
            continue
        token, lexeme = result
        if not token.startswith("_"):
            tokens.append((token, lexeme))
        pos += len(lexeme)
    return tokens, errors


''')

        # ── main ──────────────────────────────────────────────────
        f.write('''\
def main():
    if len(sys.argv) < 2:
        print("Uso: python lexer.py <archivo> [--verbose]")
        sys.exit(1)

    verbose = "--verbose" in sys.argv

    try:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Archivo no encontrado: {sys.argv[1]}")
        sys.exit(1)

    tokens, errors = tokenize(source)

    print(f"\\n{'='*55}")
    print(f"  TOKENS: {len(tokens)}")
    print(f"{'='*55}")
    for tok, lex in tokens:
        if verbose:
            print(f"  {tok:<25} {repr(lex)}")
        else:
            print(f"  ({tok}, {repr(lex)})")

    if errors:
        print(f"\\n{'='*55}")
        print(f"  ERRORES LEXICOS: {len(errors)}")
        print(f"{'='*55}")
        for err in errors:
            print(f"  {err}")
    else:
        print("\\n  Sin errores lexicos.")
    print(f"{'='*55}\\n")


if __name__ == "__main__":
    main()
''')

    print(f"Lexer generado: {output_file}")