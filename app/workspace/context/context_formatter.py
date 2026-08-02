class ContextFormatter:

    def format(
        self,
        context,
    ):

        callees = []
        callers = []

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
                callees.append(block)

            else:
                callers.append(block)

        callers = "\n".join(
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

        return f"""
==================================================
PRIMARY SYMBOL
==================================================

{context["symbol"]["name"]}

==================================================
CALLERS
==================================================

{callers}

==================================================
CALLEES
==================================================

{calls}

==================================================
DEPENDENCIES
==================================================

{dependencies}

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

{''.join(callees)}

==================================================
OTHER RELATED SOURCE CODE
==================================================

{''.join(callers)}

"""


context_formatter = ContextFormatter()
