class RegexNode:
    def __init__(self, node_type, value=None, left=None, right=None):
        self.type = node_type
        self.value = value
        self.left = left
        self.right = right

    def __repr__(self):
        if self.type == "SYMBOL":
            return f"SYMBOL({self.value})"
        elif self.type in ["STAR", "PLUS", "OPTIONAL"]:
            return f"{self.type}({self.left})"
        else:
            return f"{self.type}({self.left}, {self.right})"