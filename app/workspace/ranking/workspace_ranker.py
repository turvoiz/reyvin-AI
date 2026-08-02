class WorkspaceRanker:
    def rank(
        self,
        context,
    ):

        score = {}

        def add(name, value):

            if not name:
                return

            score[name] = score.get(name, 0) + value

        symbol = context["symbol"]["name"]

        add(symbol, 100)

        for call in context.get("calls", []):
            add(call["call"], 30)

        for caller in context.get("callers", []):
            add(caller["caller"], 30)

        for dep in context.get("dependencies", []):
            add(dep, 20)

        print("\n=== REFERENCES ===")
        print(context.get("references"))

        for ref in context.get("references", []):
            print(type(ref), ref)
            add(ref.get("symbol"), 10)

        ranked = sorted(
            score.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return ranked

    def top(
        self,
        context,
        limit=8,
    ):

        return [symbol for symbol, _ in self.rank(context)[:limit]]


workspace_ranker = WorkspaceRanker()
