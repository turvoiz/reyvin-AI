class ContextCompressor:

    def compress(
        self,
        context,
    ):

        impact = context.get("impact", [])

        if isinstance(impact, dict):
            impact = list(impact.items())

        elif not isinstance(impact, list):
            impact = []

        return {
            "symbol": context["symbol"],
            "top_symbols": context.get("top_symbols", []),
            "callers": context.get("callers", [])[:10],
            "calls": context.get("calls", [])[:10],
            "dependencies": context.get("dependencies", [])[:10],
            "impact": impact[:10],
            "source": context.get("source", "")[:3000],
        }


context_compressor = ContextCompressor()
