from app.workspace.reader import read_file


class ContextBuilder:
    def build(self, symbol: dict):

        source = read_file(symbol["file"])

        lines = source["content"].splitlines()

        start = symbol["start_line"] - 1
        end = symbol["end_line"]

        return "\n".join(lines[start:end])


context_builder = ContextBuilder()
