class ContextCompressor:

    def compress(
        self,
        context,
        intent="explain",
    ):

        base = {
            "symbol": context["symbol"],
            "source": context.get("source", "")[:4000],
        }

        if intent == "explain":
            base.update({
                "calls": context.get("calls", [])[:10],
                "related_sources": context.get(
                    "related_sources",
                    [],
                )[:10],
            })

        elif intent == "review":
            base.update({
                "calls": context.get("calls", [])[:5],
                "dependencies": context.get(
                    "dependencies",
                    [],
                )[:10],
                "impact": context.get(
                    "impact",
                    {},
                ),
                "related_sources": context.get(
                    "related_sources",
                    [],
                )[:5],
            })

        elif intent == "impact":
            base.update({
                "callers": context.get(
                    "callers",
                    [],
                )[:20],
                "impact": context.get(
                    "impact",
                    {},
                ),
                "related_sources": context.get(
                    "related_sources",
                    [],
                )[:10],
            })

        elif intent == "trace":
            base.update({
                "calls": context.get("calls", [])[:20],
                "trace": context.get("trace", {}),
                "related_sources": context.get(
                    "related_sources",
                    [],
                )[:10],
            })

        elif intent == "diagnose":
            related = []

            for item in context.get("related_sources", [])[:3]:
                copy = dict(item)
                copy["source"] = item.get("source", "")[:2500]
                related.append(copy)

            base.update({
                "related_sources": related,
            })

        else:
            base.update({
                "related_sources": context.get(
                    "related_sources",
                    [],
                )[:5],
            })

        return base


context_compressor = ContextCompressor()
