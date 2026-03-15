class YALexParser:
    def __init__(self, text):
        self.text = text

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

    def parse(self):
        text = self.remove_comments(self.text)
        lines = text.splitlines()

        definitions = []
        rules = []
        in_rule = False
        in_block = False  # para header/trailer

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # Detectar inicio o fin de bloque header/trailer
            if line == "{":
                in_block = True
                continue

            if line == "}":
                in_block = False
                continue

            if in_block:
                continue

            # let definitions
            if line.startswith("let"):
                parts = line.split("=", 1)
                if len(parts) != 2:
                    raise Exception(f"Invalid definition: {line}")

                left = parts[0].strip()
                right = parts[1].strip()

                token_name = left.replace("let", "").strip()
                regex = right.strip()

                definitions.append((token_name, regex))

            # rule section
            elif line.startswith("rule"):
                in_rule = True

            elif in_rule:
                if line.startswith("|"):
                    line = line[1:].strip()

                if line.startswith("{"):
                    end = line.find("}")
                    if end == -1:
                        raise Exception(f"Invalid rule line: {line}")

                    token_name = line[1:end].strip()
                    rules.append(token_name)

        return definitions, rules