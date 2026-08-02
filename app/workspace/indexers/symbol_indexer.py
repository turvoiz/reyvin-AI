from app.workspace.symbols import (
    build_file_symbols,
    build_symbol_index,
)


class SymbolIndexer:
    def build(self, workspace):

        return build_symbol_index(workspace)

    def update(
        self,
        cache,
        file,
    ):

        relative = file

        old = [
            name for name, info in cache._symbols.items() if info["file"] == relative
        ]

        for name in old:
            cache._symbols.pop(name, None)

        cache.invalidate(old)

        new_symbols = build_file_symbols(
            file,
            cache.workspace,
        )

        cache._symbols.update(new_symbols)

        cache.invalidate(new_symbols.keys())


symbol_indexer = SymbolIndexer()
