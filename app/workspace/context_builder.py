from pathlib import Path

from app.workspace.reader import read_file


class ContextBuilder:
    def build(self, symbol: dict, workspace="."):

        source = read_file(Path(workspace) / symbol["file"])

        lines = source["content"].splitlines()

        start = symbol["start_line"] - 1
        end = symbol["end_line"]

        return "\n".join(lines[start:end])


context_builder = ContextBuilder()
