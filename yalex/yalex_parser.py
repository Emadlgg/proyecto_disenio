class YALexParser:
    def __init__(self, text):
        self.text = text

    # --------------------------------------------------
    # Eliminar comentarios (* ... *)
    # --------------------------------------------------
    def remove_comments(self, text):
        result = ""
        i = 0
        while i < len(text):
            if text[i:i+2] == "(*":
                end = text.find("*)", i)
                if end == -1:
                    raise Exception("Unclosed comment")
                i = end + 2
            else:
                result += text[i]
                i += 1
        return result

    # --------------------------------------------------
    # Extraer bloques { ... } de header/trailer
    # --------------------------------------------------
    def remove_code_blocks(self, text):
        """
        Elimina bloques { ... } de header y trailer.
        Estos bloques están al inicio y al final del archivo,
        NO son las acciones { return X } de las rules.
        Los reconocemos porque están solos en su línea.
        """
        lines = text.splitlines()
        result = []
        in_block = False

        for line in lines:
            stripped = line.strip()

            if stripped == "{":
                in_block = True
                continue

            if stripped == "}" and in_block:
                in_block = False
                continue

            if in_block:
                continue

            result.append(line)

        return "\n".join(result)

    # --------------------------------------------------
    # Parsear una línea de rule:
    #   regex { return TOKEN }
    #   regex { TOKEN }
    # Retorna (regex_str, token_name) o None
    # --------------------------------------------------
    def parse_rule_line(self, line):
        # Buscar la acción { ... }
        brace_open = line.rfind("{")
        brace_close = line.rfind("}")

        if brace_open == -1 or brace_close == -1:
            return None

        action = line[brace_open + 1 : brace_close].strip()
        regex_part = line[:brace_open].strip()

        # Quitar | del inicio si viene de alternancia
        if regex_part.startswith("|"):
            regex_part = regex_part[1:].strip()

        # Extraer token name de "return TOKEN" o solo "TOKEN"
        if action.startswith("return"):
            token_name = action[len("return"):].strip()
        else:
            token_name = action.strip()

        if not token_name or not regex_part:
            return None

        return (regex_part, token_name)

    # --------------------------------------------------
    # Parser principal
    # --------------------------------------------------
    def parse(self):
        """
        Retorna:
          definitions: lista de (name, regex_str)  ← los 'let'
          rules:       lista de (regex_str, token_name) en orden ← las rules
        """
        text = self.remove_comments(self.text)
        text = self.remove_code_blocks(text)

        definitions = []   # (name, regex)
        rules = []         # (regex_str, token_name)

        in_rule = False

        # Unir líneas que son continuación de una rule
        # (líneas que empiezan con | son parte de la rule anterior)
        lines = text.splitlines()
        merged_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            merged_lines.append(stripped)

        i = 0
        while i < len(merged_lines):
            line = merged_lines[i]

            # --- let definition ---
            if line.startswith("let "):
                # formato: let NAME = regex
                rest = line[4:].strip()  # quitar "let "
                eq_idx = rest.find("=")

                if eq_idx == -1:
                    raise Exception(f"Invalid let definition: {line}")

                name = rest[:eq_idx].strip()
                regex = rest[eq_idx + 1:].strip()

                definitions.append((name, regex))
                in_rule = False

            # --- rule entrypoint ---
            elif line.startswith("rule "):
                in_rule = True
                # La primera alternativa puede estar en la misma línea
                # rule gettoken = regex { action }
                # o en la siguiente línea
                eq_idx = line.find("=")
                if eq_idx != -1:
                    rest = line[eq_idx + 1:].strip()
                    if rest and "{" in rest:
                        parsed = self.parse_rule_line(rest)
                        if parsed:
                            rules.append(parsed)

            # --- alternativas de rule ---
            elif in_rule:
                if line.startswith("|") or "{" in line:
                    parsed = self.parse_rule_line(line)
                    if parsed:
                        rules.append(parsed)
                else:
                    # Si la línea no tiene { ni | probablemente salimos de la rule
                    in_rule = False

            i += 1

        return definitions, rules