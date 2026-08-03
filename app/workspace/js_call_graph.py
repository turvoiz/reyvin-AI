import re
from pathlib import Path

from app.workspace.constants import IGNORE_DIRS

JS_SUFFIXES = {".js", ".jsx", ".ts", ".tsx"}

IDENTIFIER_CALL = re.compile(r"\b([A-Za-z_$][\w$]*)\s*\(")
THIS_METHOD_CALL = re.compile(r"\bthis\.([A-Za-z_$][\w$]*)\s*\(")

SKIP_KEYWORDS = {
    "new",
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "return",
    "typeof",
    "instanceof",
    "function",
    "class",
    "extends",
    "import",
    "export",
}


class JSCallGraph:
    def build(
        self,
        workspace,
        symbols,
    ):

        root = Path(workspace)

        forward = {}
        reverse = {}

        for file in root.rglob("*"):
            if (
                not file.is_file()
                or file.suffix.lower() not in JS_SUFFIXES
            ):
                continue

            if any(part in IGNORE_DIRS for part in file.parts):
                continue

            relative = str(file.relative_to(root))

            source = file.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            file_calls = self._file_calls(
                source,
                relative,
                symbols,
            )

            if not file_calls:
                continue

            forward.update(file_calls)

            for caller, callees in file_calls.items():
                for call in callees:
                    reverse.setdefault(
                        call["call"],
                        [],
                    ).append(
                        {
                            "caller": caller,
                            "file": call["file"],
                            "line": call["line"],
                        }
                    )

        return {
            "forward": forward,
            "reverse": reverse,
        }

    def _file_calls(
        self,
        source,
        relative,
        symbols,
    ):

        lines = source.splitlines()

        file_symbols = [
            info
            for info in symbols.values()
            if info["file"] == relative
        ]

        calls = {}

        for info in file_symbols:

            start = max(info.get("start_line", 1) - 1, 0)
            end = min(info.get("end_line", len(lines)), len(lines))

            body = lines[start:end]

            extracted = self._extract(
                body,
                info,
                symbols,
            )

            if extracted:
                calls[info["name"]] = extracted

        return calls

    def _extract(
        self,
        body,
        info,
        symbols,
    ):

        found = []
        seen = set()

        class_name = info.get("class")

        for offset, line in enumerate(body, start=1):
            lineno = info.get("start_line", 1) + offset - 1

            for match in THIS_METHOD_CALL.finditer(line):
                method = match.group(1)

                if class_name:
                    target = f"{class_name}.{method}"
                else:
                    target = method

                if target == info["name"]:
                    continue

                if target in symbols and target not in seen:
                    seen.add(target)
                    found.append(
                        {
                            "call": target,
                            "file": info["file"],
                            "line": lineno,
                        }
                    )

            for match in IDENTIFIER_CALL.finditer(line):
                name = match.group(1)

                if name in SKIP_KEYWORDS or name == info["name"]:
                    continue

                target = name

                if target in symbols and target not in seen:
                    seen.add(target)
                    found.append(
                        {
                            "call": target,
                            "file": info["file"],
                            "line": lineno,
                        }
                    )

        return found


js_call_graph = JSCallGraph()
