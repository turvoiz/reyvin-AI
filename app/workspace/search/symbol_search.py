from difflib import SequenceMatcher


class SymbolSearch:

    def search(
        self,
        cache,
        query: str,
        limit: int = 20,
    ):

        query = query.lower()

        results = []

        for name, info in cache.symbols().items():

            score = SequenceMatcher(
                None,
                query,
                name.lower(),
            ).ratio()

            if query in name.lower():
                score += 1

            if score > 0.3:
                results.append({
                    "symbol": name,
                    "score": round(score, 3),
                    "file": info["file"],
                    "type": info["type"],
                })

        results.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        return results[:limit]


symbol_search = SymbolSearch()
