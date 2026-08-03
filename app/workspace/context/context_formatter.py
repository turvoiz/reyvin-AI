import json


class ContextFormatter:

    def format(
        self,
        context,
    ):

        callee_sources = []
        related_sources = []

        for item in context.get("related_sources", []):

            block = f"""==================================================
SYMBOL
==================================================

{item["symbol"]}

TYPE:
{item["type"]}

SOURCE:
{item["source"]}
"""

            if any(
                c["call"] == item["symbol"]
                for c in context.get("calls", [])
            ):
                callee_sources.append(block)

            else:
                related_sources.append(block)

        caller_names = "\n".join(
            caller["caller"]
            for caller in context.get("callers", [])
        )

        calls = "\n".join(
            call["call"]
            for call in context.get("calls", [])
        )

        dependencies = "\n".join(
            context.get("dependencies", [])
        )

        impact = context.get("impact", {})
        affected_symbols = "\n".join(
            impact.get("affected_symbols", [])
        )
        affected_files = "\n".join(
            impact.get("affected_files", [])
        )
        trace = json.dumps(context.get("trace", {}), indent=2)

        return f"""
==================================================
PRIMARY SYMBOL
==================================================

{context["symbol"]["name"]}

==================================================
CALLERS
==================================================

{caller_names}

==================================================
CALLEES
==================================================

{calls}

==================================================
DEPENDENCIES
==================================================

{dependencies}

==================================================
IMPACT
==================================================

RISK: {impact.get("risk", "")}

AFFECTED SYMBOLS:
{affected_symbols}

AFFECTED FILES:
{affected_files}

==================================================
TRACE
==================================================

{trace}

==================================================
SOURCE
==================================================

{context["source"]}

==================================================
RELATED SOURCE CODE (USE THIS AS EVIDENCE)
==================================================

==================================================
CALLEE SOURCE CODE (PRIMARY EVIDENCE)
==================================================

{''.join(callee_sources)}

==================================================
OTHER RELATED SOURCE CODE
==================================================

{''.join(related_sources)}

"""


context_formatter = ContextFormatter()
