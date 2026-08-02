import ast
from pathlib import Path

from app.workspace.constants import IGNORE_DIRS, IGNORE_CALLS
from app.workspace.resolver import resolver_index
from app.workspace.symbols import build_symbol_index
from app.workspace.symbols import build_symbol_index


class CallVisitor(ast.NodeVisitor):

    def __init__(self, file, resolver, symbols):

        self.file = file

        self.resolver = resolver

        self.symbols = symbols

        self.current = None

        self.calls = {}

    def visit_ClassDef(self, node):

        previous = self.current

        self.current = node.name

        self.generic_visit(node)

        self.current = previous


    def visit_FunctionDef(self, node):

        previous = self.current

        if previous:

            self.current = f"{previous}.{node.name}"

        else:

            self.current = node.name

        self.generic_visit(node)

        self.current = previous

    def visit_Call(self, node):

        if self.current:

            target = None

            if isinstance(node.func, ast.Attribute):

                if isinstance(node.func.value, ast.Name):

                    instance = node.func.value.id

                    if instance == "self" and "." in self.current:

                        cls = self.current.split(".")[0]

                        target = f"{cls}.{node.func.attr}"

                    elif instance in self.resolver:

                        cls = self.resolver[instance]["class"]

                        target = f"{cls}.{node.func.attr}"

                    else:

                        target = None

                else:

                    target = None

            elif isinstance(node.func, ast.Name):

                target = node.func.id

            if (
                target
                and target not in IGNORE_CALLS
                and (
                    target in self.symbols
                )
            ):

                self.calls.setdefault(self.current, []).append({
                    "call": target,
                    "file": self.file,
                    "line": node.lineno,
                })

        self.generic_visit(node)


class CallGraph:

    def build(self, workspace):

        root = Path(workspace)

        graph = {}
        reverse = {}

        resolver = resolver_index.build(workspace)

        symbols = build_symbol_index(workspace)

        for file in root.rglob("*.py"):

            if any(part in IGNORE_DIRS for part in file.parts):
                continue

            relative = str(file.relative_to(root))

            source = file.read_text(encoding="utf-8")

            tree = ast.parse(source)

            visitor = CallVisitor(relative, resolver, symbols)

            visitor.visit(tree)

            graph.update(visitor.calls)

        for caller, callees in graph.items():

            for call in callees:

                reverse.setdefault(
                    call["call"],
                    []
                ).append({
                    "caller": caller,
                    "file": call["file"],
                    "line": call["line"],
                })

        return {
            "forward": graph,
            "reverse": reverse,
        }


call_graph = CallGraph()
