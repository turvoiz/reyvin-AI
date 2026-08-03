import ast
import re
from pathlib import Path

JS_KEYWORDS = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "function",
    "return",
    "new",
    "typeof",
    "else",
    "do",
    "with",
    "case",
}


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


def parse_javascript_file(path: str):
    source = Path(path).read_text(encoding="utf-8", errors="ignore")
    lines = source.splitlines()

    classes = []
    functions = []
    units = []

    class_stack = []
    depth = 0

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()

        class_match = re.search(r"\bclass\s+(\w+)", line)

        if class_match:
            cls = {
                "name": class_match.group(1),
                "methods": [],
                "start_line": line_number,
                "end_line": None,
            }
            classes.append(cls)
            class_stack.append(
                {
                    "class": cls,
                    "open_depth": depth,
                }
            )

        current_class = class_stack[-1]["class"] if class_stack else None

        if current_class is not None:
            method_match = re.search(
                r"\b(?:async\s+|get\s+|set\s+)?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*[{=]",
                line,
            )

            if method_match and method_match.group(1) not in JS_KEYWORDS:
                method = {
                    "name": method_match.group(1),
                    "start_line": line_number,
                    "end_line": None,
                }
                current_class["methods"].append(method)
                units.append(method)

        else:
            function_match = re.search(
                r"\b(?:async\s+)?function\s+(\w+)\s*\(",
                line,
            )
            arrow_match = re.search(
                r"\b(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",
                line,
            )
            match = function_match or arrow_match

            if match:
                fn = {
                    "name": match.group(1),
                    "start_line": line_number,
                    "end_line": None,
                }
                functions.append(fn)
                units.append(fn)

        depth += line.count("{") - line.count("}")

        while class_stack and depth <= class_stack[-1]["open_depth"]:
            class_stack[-1]["class"]["end_line"] = line_number
            class_stack.pop()

    units.sort(key=lambda unit: unit["start_line"])

    for index, unit in enumerate(units):
        unit["end_line"] = (
            units[index + 1]["start_line"] - 1
            if index + 1 < len(units)
            else len(lines)
        )
        unit["end_line"] = max(unit["start_line"], unit["end_line"])

    for cls in classes:
        cls["end_line"] = cls["end_line"] or len(lines)

    imports = re.findall(
        r"(?:from\s+['\"]([^'\"]+)['\"]|require\(\s*['\"]([^'\"]+)['\"]\s*\))",
        source,
    )

    return {
        "classes": classes,
        "functions": functions,
        "imports": [first or second for first, second in imports],
    }


def parse_source_file(path: str):
    if Path(path).suffix.lower() == ".py":
        return parse_python_file(path)

    return parse_javascript_file(path)
