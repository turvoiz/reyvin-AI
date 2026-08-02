from app.workspace.indexers.call_indexer import call_indexer
from app.workspace.indexers.symbol_indexer import symbol_indexer


class IncrementalRebuilder:

    def rebuild(
        self,
        cache,
        changed_files,
    ):

        rebuilt = []

        print(
            f"[Incremental] {len(changed_files)} changed file(s)"
        )


        for file in changed_files:

            symbol_indexer.update(
                cache,
                file,
            )


            call_indexer.update(
                cache,
                cache.workspace,
            )

            print(
                "[Symbol]",
                file,
            )

            rebuilt.append(file)

        print("[Incremental] done")

        return {
            "rebuilt": rebuilt,
            "symbols": len(cache.symbols()),
        }


incremental_rebuilder = IncrementalRebuilder()
