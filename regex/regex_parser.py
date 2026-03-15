from regex.regex_node import RegexNode


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

    # -------------------------------------------------
    # Entrada principal
    # -------------------------------------------------

    def parse(self):
        node = self.parse_expression()
        return node

    # -------------------------------------------------
    # Nivel OR (|)
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

            if next_char and next_char not in "|)":
                right = self.parse_factor()
                node = RegexNode("CONCAT", left=node, right=right)
            else:
                break

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
    # Base: símbolo, grupo, clase o literal
    # -------------------------------------------------

    def parse_base(self):
        char = self.peek()

        # Grupo con paréntesis
        if char == "(":
            self.consume()
            node = self.parse_expression()

            if self.peek() != ")":
                raise Exception("Missing closing parenthesis")

            self.consume()
            return node

        # Literal entre comillas "..."
        elif char == '"':
            return self.parse_literal()

        # Clase tipo [ ... ]
        elif char == "[":
            return self.parse_character_class()

        # Símbolo simple
        elif char:
            self.consume()
            return RegexNode("SYMBOL", value=char)

        else:
            raise Exception("Unexpected end of pattern")

    # -------------------------------------------------
    # Clase de caracteres [a-z] o [abc]
    # -------------------------------------------------

    def parse_character_class(self):
        self.consume()  # consumir '['

        chars = []

        while self.peek() != "]":
            if self.peek() is None:
                raise Exception("Unclosed character class")

            start = self.consume()

            # Rango tipo a-z
            if self.peek() == "-":
                self.consume()  # consumir '-'
                end = self.consume()

                for c in range(ord(start), ord(end) + 1):
                    chars.append(chr(c))
            else:
                chars.append(start)

        self.consume()  # consumir ']'

        if not chars:
            raise Exception("Empty character class")

        # Construir OR encadenado
        node = RegexNode("SYMBOL", value=chars[0])

        for c in chars[1:]:
            node = RegexNode(
                "OR",
                left=node,
                right=RegexNode("SYMBOL", value=c)
            )

        return node

    # -------------------------------------------------
    # Literal tipo "while"
    # -------------------------------------------------

    def parse_literal(self):
        self.consume()  # consumir comilla inicial

        chars = []

        while self.peek() != '"':
            if self.peek() is None:
                raise Exception("Unclosed string literal")

            chars.append(self.consume())

        self.consume()  # consumir comilla final

        if not chars:
            raise Exception("Empty string literal")

        # Construir concatenación
        node = RegexNode("SYMBOL", value=chars[0])

        for c in chars[1:]:
            node = RegexNode(
                "CONCAT",
                left=node,
                right=RegexNode("SYMBOL", value=c)
            )

        return node