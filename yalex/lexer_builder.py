from regex.regex_parser import RegexParser
from automata.thompson import Thompson
from automata.subset import SubsetConstruction
from automata.afn import merge_afns
from yalex.yalex_parser import YALexParser


# ---------------------------------------------------
# Tabla de palabras reservadas (si se usa)
# ---------------------------------------------------

RESERVED_WORDS = {
    "while": "WHILE",
    "if": "IF",
    "for": "FOR",
    "return": "RETURN",
    "true": "TRUE",
    "false": "FALSE",
    "break": "BREAK",
    "continue": "CONTINUE"
}


# ---------------------------------------------------
# Resolver referencias {TOKEN}
# ---------------------------------------------------

def resolve_references(regex, regex_map):
    result = ""
    i = 0

    while i < len(regex):
        if regex[i] == "{":
            j = i + 1
            name = ""

            while j < len(regex) and regex[j] != "}":
                name += regex[j]
                j += 1

            if j >= len(regex):
                raise Exception("Unclosed reference")

            if name not in regex_map:
                raise Exception(f"Undefined reference: {name}")

            result += "(" + regex_map[name] + ")"
            i = j + 1
        else:
            result += regex[i]
            i += 1

    return result


# ---------------------------------------------------
# Construcción del lexer desde especificación
# ---------------------------------------------------

def build_lexer_from_spec(spec_text):
    parser = YALexParser(spec_text)
    definitions, rules = parser.parse()

    regex_map = {name: regex for name, regex in definitions}

    # Detectar auxiliares (referenciados)
    referenced = set()

    for _, regex in definitions:
        i = 0
        while i < len(regex):
            if regex[i] == "{":
                j = i + 1
                name = ""
                while j < len(regex) and regex[j] != "}":
                    name += regex[j]
                    j += 1
                referenced.add(name)
                i = j
            i += 1

    # Si no hay rule, usar orden de let
    if not rules:
        rules = [name for name, _ in definitions]

    # Prioridad según rule
    priority_map = {name: i for i, name in enumerate(rules)}

    afns = []

    for token_name, regex in definitions:

        resolved_regex = resolve_references(regex, regex_map)
        tree = RegexParser(resolved_regex).parse()
        afn = Thompson().build(tree)

        # Caso 1: token definido en rule
        if token_name in priority_map:
            priority = priority_map[token_name]

        # Caso 2: token ignorado (_WS etc.)
        elif token_name.startswith("_"):
            priority = len(priority_map) + 1

        # Caso 3: auxiliar real → no genera token
        else:
            afns.append(afn)
            continue

        afn.priority = priority

        for s in afn.final_states:
            afn.token_map[s] = (token_name, priority)

        afns.append(afn)

    merged = merge_afns(afns)
    afd = SubsetConstruction(merged).build()

    return afd


# ---------------------------------------------------
# Tokenize completo
# ---------------------------------------------------

def tokenize(afd, input_string):
    tokens = []
    position = 0

    while position < len(input_string):
        result = afd.match(input_string[position:])

        if result is None:
            print("Error léxico en:", input_string[position:])
            break

        token, lexeme = result

        # Ignorar tokens que empiezan con "_"
        if token.startswith("_"):
            position += len(lexeme)
            continue

        # Convertir ID en palabra reservada
        if token == "ID" and lexeme in RESERVED_WORDS:
            tokens.append((RESERVED_WORDS[lexeme], lexeme))
        else:
            tokens.append((token, lexeme))

        position += len(lexeme)

    return tokens