class SymbolExpander:
    def expand(
        self,
        cache,
        symbol,
    ):

        knowledge = cache.knowledge(symbol)

        related = []

        for call in knowledge.get("calls", []):
            related.append(call["call"])

        for caller in knowledge.get("callers", []):
            related.append(caller["caller"])

        seen = set()

        ordered = []

        for item in [symbol] + related:
            if item not in seen:
                seen.add(item)
                ordered.append(item)

        return ordered


symbol_expander = SymbolExpander()
