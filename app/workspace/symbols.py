from pathlib import Path

from app.workspace.languages import iter_source_files
from app.workspace.parser import parse_source_file


def build_symbol_index(workspace: str):

    root = Path(workspace)

    symbols = {}

    for file in iter_source_files(workspace):

        data = parse_source_file(str(file))

        relative = str(file.relative_to(root))

        for cls in data["classes"]:
            symbols[cls["name"]] = {
                "name": cls["name"],
                "type": "class",
                "file": relative,
                "methods": [m["name"] for m in cls["methods"]],
                "start_line": cls["start_line"],
                "end_line": cls["end_line"],
            }

            for method in cls["methods"]:
                fq_name = f"{cls['name']}.{method['name']}"

                symbols[fq_name] = {
                    "name": fq_name,
                    "type": "method",
                    "class": cls["name"],
                    "file": relative,
                    "start_line": method["start_line"],
                    "end_line": method["end_line"],
                }

        for fn in data["functions"]:
            symbols[fn["name"]] = {
                "name": fn["name"],
                "type": "function",
                "file": relative,
                "start_line": fn["start_line"],
                "end_line": fn["end_line"],
            }

    return symbols


def build_file_symbols(path: str, workspace="."):

    root = Path(workspace)

    file = Path(path)

    if not file.is_absolute():
        file = root / file

    data = parse_source_file(str(file))

    relative = str(file.relative_to(root))

    symbols = {}

    for cls in data["classes"]:
        symbols[cls["name"]] = {
            "name": cls["name"],
            "type": "class",
            "file": relative,
            "methods": [m["name"] for m in cls["methods"]],
            "start_line": cls["start_line"],
            "end_line": cls["end_line"],
        }

        for method in cls["methods"]:
            fq = f"{cls['name']}.{method['name']}"

            symbols[fq] = {
                "name": fq,
                "type": "method",
                "class": cls["name"],
                "file": relative,
                "start_line": method["start_line"],
                "end_line": method["end_line"],
            }

    for fn in data["functions"]:
        symbols[fn["name"]] = {
            "name": fn["name"],
            "type": "function",
            "file": relative,
            "start_line": fn["start_line"],
            "end_line": fn["end_line"],
        }

    return symbols
