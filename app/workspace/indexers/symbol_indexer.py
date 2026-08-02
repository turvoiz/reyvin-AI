from app.workspace.symbols import (
    build_symbol_index,
    build_file_symbols,
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
            name
            for name, info in cache._symbols.items()
            if info["file"] == relative
        ]

        for name in old:
            cache._symbols.pop(name, None)

        cache._symbols.update(
            build_file_symbols(
                file,
                cache.workspace,
            )
        )


symbol_indexer = SymbolIndexer()
