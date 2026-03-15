from regex.regex_node import RegexNode

# Caracteres imprimibles para wildcard _ (any)
# Excluimos ε que es solo interno
ALL_CHARS = [chr(c) for c in range(32, 127)]


class RegexParser:
    def __init__(self, pattern):
        self.pattern = pattern
        self.position = 0

    # -------------------------------------------------
    # Utilidades básicas
    # -------------------------------------------------

    def peek(self):
        if self.position < len(self.pattern):
            return self.pattern[self.position]
        return None

    def consume(self):
        char = self.peek()
        self.position += 1
        return char

    def expect(self, char):
        actual = self.consume()
        if actual != char:
            raise Exception(f"Expected '{char}', got '{actual}' at position {self.position}")

    # -------------------------------------------------
    # Entrada principal
    # -------------------------------------------------

    def parse(self):
        node = self.parse_expression()
        if self.peek() is not None:
            raise Exception(f"Unexpected character '{self.peek()}' at position {self.position}")
        return node

    # -------------------------------------------------
    # Nivel OR  (|)
    # -------------------------------------------------

    def parse_expression(self):
        node = self.parse_term()

        while self.peek() == "|":
            self.consume()
            right = self.parse_term()
            node = RegexNode("OR", left=node, right=right)

        return node

    # -------------------------------------------------
    # Nivel CONCAT (implícita)
    # -------------------------------------------------

    def parse_term(self):
        node = self.parse_factor()

        while True:
            next_char = self.peek()
            # estos caracteres NO pueden iniciar un factor
            if next_char is None or next_char in "|)":
                break
            right = self.parse_factor()
            node = RegexNode("CONCAT", left=node, right=right)

        return node

    # -------------------------------------------------
    # Nivel *, +, ?
    # -------------------------------------------------

    def parse_factor(self):
        node = self.parse_base()

        while True:
            next_char = self.peek()

            if next_char == "*":
                self.consume()
                node = RegexNode("STAR", left=node)

            elif next_char == "+":
                self.consume()
                node = RegexNode("PLUS", left=node)

            elif next_char == "?":
                self.consume()
                node = RegexNode("OPTIONAL", left=node)

            else:
                break

        return node

    # -------------------------------------------------
    # Base: símbolo, grupo, clase, literal, wildcard
    # -------------------------------------------------

    def parse_base(self):
        char = self.peek()

        if char is None:
            raise Exception("Unexpected end of pattern")

        # Grupo con paréntesis
        if char == "(":
            self.consume()
            node = self.parse_expression()
            self.expect(")")
            return node

        # Literal entre comillas simples 'c' o '\n'
        elif char == "'":
            return self.parse_single_char_literal()

        # Literal entre comillas dobles "string"
        elif char == '"':
            return self.parse_string_literal()

        # Clase tipo [abc] o [a-z] o [^a-z]
        elif char == "[":
            return self.parse_character_class()

        # Wildcard _ → cualquier carácter
        elif char == "_":
            self.consume()
            return self._chars_to_or(ALL_CHARS)

        # Palabra clave eof
        elif self.pattern[self.position:self.position + 3] == "eof":
            self.position += 3
            return RegexNode("SYMBOL", value="eof")

        # Símbolo simple (cualquier otro carácter)
        else:
            self.consume()
            return RegexNode("SYMBOL", value=char)

    # -------------------------------------------------
    # Literal de un solo carácter entre comillas simples
    # Soporta: 'a'  '\n'  '\t'  '\r'  '\\'  ' '
    # -------------------------------------------------

    def parse_single_char_literal(self):
        self.expect("'")

        char = self._read_escaped_char()

        # puede haber múltiples chars entre ' '  →  [' ' '\t']
        # eso ya lo maneja parse_character_class, aquí solo 'c'
        self.expect("'")

        return RegexNode("SYMBOL", value=char)

    # -------------------------------------------------
    # Leer un carácter, con soporte de escape \n \t \r \\
    # -------------------------------------------------

    def _read_escaped_char(self):
        char = self.consume()

        if char == "\\":
            escaped = self.consume()
            escape_map = {
                "n": "\n",
                "t": "\t",
                "r": "\r",
                "\\": "\\",
                "'": "'",
                '"': '"',
                "0": "\0",
            }
            if escaped in escape_map:
                return escape_map[escaped]
            else:
                # \x → solo x
                return escaped

        return char

    # -------------------------------------------------
    # Clase de caracteres:
    #   [abc]      → OR de a, b, c
    #   [a-z]      → OR de a..z
    #   [^abc]     → complemento
    #   [' '\t]    → espacio o tab (chars entre comillas simples)
    # -------------------------------------------------

    def parse_character_class(self):
        self.expect("[")

        # Complemento [^ ... ]
        negate = False
        if self.peek() == "^":
            self.consume()
            negate = True

        chars = []

        while self.peek() != "]":
            if self.peek() is None:
                raise Exception("Unclosed character class")

            # Char entre comillas simples dentro de clase: [' ' '\t']
            if self.peek() == "'":
                self.consume()  # abrir '
                c = self._read_escaped_char()
                self.expect("'")  # cerrar '
                chars.append(c)
                continue

            # Char entre comillas dobles dentro de clase: ["x"] → el char x
            # Esto permite escribir [^"'"] para "cualquier cosa excepto comilla simple"
            if self.peek() == '"':
                self.consume()  # abrir "
                c = self._read_escaped_char()
                self.expect('"')  # cerrar "
                chars.append(c)
                continue

            # Char normal o rango a-z
            start = self._read_escaped_char()

            if self.peek() == "-" and self.position + 1 < len(self.pattern) and self.pattern[self.position + 1] != "]":
                self.consume()  # consumir '-'
                end = self._read_escaped_char()
                for c in range(ord(start), ord(end) + 1):
                    chars.append(chr(c))
            else:
                chars.append(start)

        self.expect("]")

        if not chars and not negate:
            raise Exception("Empty character class")

        if negate:
            chars = [c for c in ALL_CHARS if c not in chars]

        if not chars:
            raise Exception("Negated character class matches nothing")

        return self._chars_to_or(chars)

    # -------------------------------------------------
    # Literal tipo "while" → concatenación de símbolos
    # -------------------------------------------------

    def parse_string_literal(self):
        self.expect('"')

        chars = []

        while self.peek() != '"':
            if self.peek() is None:
                raise Exception("Unclosed string literal")
            chars.append(self._read_escaped_char())

        self.expect('"')

        if not chars:
            raise Exception("Empty string literal")

        node = RegexNode("SYMBOL", value=chars[0])

        for c in chars[1:]:
            node = RegexNode(
                "CONCAT",
                left=node,
                right=RegexNode("SYMBOL", value=c)
            )

        return node

    # -------------------------------------------------
    # Helper: construir OR encadenado desde lista de chars
    # -------------------------------------------------

    def _chars_to_or(self, chars):
        if not chars:
            raise Exception("Cannot build OR from empty list")

        node = RegexNode("SYMBOL", value=chars[0])

        for c in chars[1:]:
            node = RegexNode(
                "OR",
                left=node,
                right=RegexNode("SYMBOL", value=c)
            )

        return node