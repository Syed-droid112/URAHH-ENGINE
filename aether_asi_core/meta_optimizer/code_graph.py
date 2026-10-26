import ast

class CodeGraph:
    def __init__(self, source: str):
        self.source = source
        self.tree = ast.parse(source)

    def to_source(self) -> str:
        return ast.unparse(self.tree)

    def node_count(self) -> int:
        return sum(1 for _ in ast.walk(self.tree))

    def __eq__(self, other):
        if not isinstance(other, CodeGraph):
            return NotImplemented
        return self.to_source() == other.to_source()

    def __hash__(self):
        return hash(self.to_source())

    def __repr__(self):
        return f"CodeGraph(nodes={self.node_count()})"
