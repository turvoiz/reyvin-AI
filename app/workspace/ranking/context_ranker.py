class ContextRanker:

    def rank(
        self,
        primary,
        cache,
        symbols,
    ):

        primary_info = cache.get(primary)

        score = {}

        knowledge = cache.knowledge(primary)

        for symbol in symbols:

            info = cache.get(symbol)

            if not info:
                continue

            s = 0

            if symbol == primary:
                s += 1000

            if (
                primary_info
                and info.get("class")
                and info.get("class") == primary_info.get("class")
            ):
                s += 300

            if any(
                c["call"] == symbol
                for c in knowledge.get("calls", [])
            ):
                s += 200

            if any(
                c["caller"] == symbol
                for c in knowledge.get("callers", [])
            ):
                s += 150

            typ = info.get("type")

            if typ == "method":
                s += 80
            elif typ == "function":
                s += 60
            elif typ == "class":
                s += 20

            s -= symbol.count(".")

            score[symbol] = s

        ranked = sorted(
            score.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return [symbol for symbol, _ in ranked]


context_ranker = ContextRanker()
