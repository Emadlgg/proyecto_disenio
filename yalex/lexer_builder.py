from regex.regex_parser import RegexParser
from automata.thompson import Thompson
from automata.subset import SubsetConstruction
from automata.afn import merge_afns
from yalex.yalex_parser import YALexParser


# --------------------------------------------------
# Resolver referencias {IDENT} dentro de un regex
# Resuelve recursivamente para soportar definiciones
# que referencian a otras: NUM = {DIGIT}+
# --------------------------------------------------
def resolve_references(regex, regex_map, visited=None):
    if visited is None:
        visited = set()

    result = ""
    i = 0

    while i < len(regex):
        ch = regex[i]

        # Saltar strings entre comillas dobles "..." sin tocarlos
        if ch == '"':
            result += ch
            i += 1
            while i < len(regex) and regex[i] != '"':
                result += regex[i]
                i += 1
            if i < len(regex):
                result += regex[i]  # comilla de cierre
                i += 1
            continue

        # Saltar chars entre comillas simples '...' sin tocarlos
        if ch == "'":
            result += ch
            i += 1
            while i < len(regex) and regex[i] != "'":
                result += regex[i]
                i += 1
            if i < len(regex):
                result += regex[i]  # comilla de cierre
                i += 1
            continue

        # Referencia {IDENT} — solo si el contenido es un identificador válido
        if ch == "{":
            j = i + 1
            name = ""

            while j < len(regex) and regex[j] != "}":
                name += regex[j]
                j += 1

            if j >= len(regex):
                raise Exception(f"Unclosed reference in: {regex}")

            # Validar que es un identificador (letras, dígitos, _)
            is_ident = name.replace("_", "").replace("$", "").isalnum() and len(name) > 0

            if is_ident and name in regex_map:
                if name in visited:
                    raise Exception(f"Circular reference detected: {name}")
                inner = resolve_references(regex_map[name], regex_map, visited | {name})
                result += "(" + inner + ")"
                i = j + 1
            elif is_ident and name not in regex_map:
                raise Exception(f"Undefined reference: {name}")
            else:
                # No es un identificador → dejar el { tal cual (e.g. literal)
                result += ch
                i += 1
            continue

        result += ch
        i += 1

    return result


# --------------------------------------------------
# Construcción del AFD desde la especificación .yal
# --------------------------------------------------
def build_lexer_from_spec(spec_text):
    parser = YALexParser(spec_text)
    definitions, rules = parser.parse()

    # Mapa de nombre → regex para resolver referencias
    # Ej: {"DIGIT": "[0-9]", "LETTER": "[a-zA-Z]", ...}
    regex_map = {name: regex for name, regex in definitions}

    afns = []

    # Las rules vienen en orden → eso define la prioridad
    # rules = [(regex_str, token_name), ...]
    for priority, (regex_str, token_name) in enumerate(rules):

        # Resolver referencias {IDENT} en el regex
        try:
            resolved = resolve_references(regex_str, regex_map)
        except Exception as e:
            print(f"[Warning] Skipping rule '{token_name}': {e}")
            continue

        # Parsear el regex resuelto → árbol
        try:
            tree = RegexParser(resolved).parse()
        except Exception as e:
            print(f"[Warning] Skipping rule '{token_name}' (parse error): {e}")
            continue

        # Construir AFN con Thompson
        afn = Thompson().build(tree)
        afn.priority = priority

        # Marcar estados finales con el token
        for s in afn.final_states:
            afn.token_map[s] = (token_name, priority)

        afns.append(afn)

    if not afns:
        raise Exception("No valid rules found in the .yal file")

    # Unificar todos los AFNs en uno solo
    merged = merge_afns(afns)

    # Convertir AFN → AFD
    afd = SubsetConstruction(merged).build()

    return afd


# --------------------------------------------------
# Tokenizar una cadena con el AFD construido
# --------------------------------------------------
def tokenize(afd, input_string):
    tokens = []
    position = 0

    while position < len(input_string):
        result = afd.match(input_string[position:])

        if result is None:
            char = input_string[position]
            print(f"Error léxico en posición {position}: '{char}'")
            position += 1  # saltar el carácter inválido y continuar
            continue

        token, lexeme = result

        # Tokens que empiezan con _ se ignoran (ej: _WS, _COMMENT)
        if not token.startswith("_"):
            tokens.append((token, lexeme))

        position += len(lexeme)

    return tokens