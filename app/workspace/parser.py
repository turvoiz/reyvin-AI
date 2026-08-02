import ast


class PythonParser(ast.NodeVisitor):
    def __init__(self):
        self.classes = []
        self.functions = []
        self.imports = []

    def visit_ClassDef(self, node):

        methods = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(
                    {
                        "name": item.name,
                        "start_line": item.lineno,
                        "end_line": item.end_lineno,
                    }
                )

        self.classes.append(
            {
                "name": node.name,
                "methods": methods,
                "start_line": node.lineno,
                "end_line": node.end_lineno,
            }
        )

        self.generic_visit(node)

    def visit_FunctionDef(self, node):

        if isinstance(getattr(node, "parent", None), ast.Module):
            self.functions.append(
                {
                    "name": node.name,
                    "start_line": node.lineno,
                    "end_line": node.end_lineno,
                }
            )

        self.generic_visit(node)

    def visit_Import(self, node):

        for alias in node.names:
            self.imports.append(alias.name)

    def visit_ImportFrom(self, node):

        if node.module:
            self.imports.append(node.module)


def parse_python_file(path: str):

    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node

    parser = PythonParser()

    parser.visit(tree)

    return {
        "classes": parser.classes,
        "functions": parser.functions,
        "imports": parser.imports,
    }
