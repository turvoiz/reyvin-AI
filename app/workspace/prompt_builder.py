class PromptBuilder:

    def build(
        self,
        context,
        question,
        external=False,
    ):

        if external:
            rules = (
                "- Use the supplied WORKSPACE CONTEXT as the primary evidence.\n"
                "- You may use the supplied WEB EVIDENCE for library versions, "
                "policies, deprecation notices, and current best practices.\n"
                "- Do not invent facts that are not present in the supplied "
                "context or web evidence.\n"
                "- Never say \"likely\", \"probably\", \"may\", or \"suggests\" "
                "without evidence.\n"
                "- If information is missing, say \"Not shown in supplied context\"."
            )
        else:
            rules = (
                "- Use ONLY the supplied workspace context.\n"
                "- Never use outside knowledge.\n"
                "- Never infer behavior.\n"
                "- Never say \"likely\", \"probably\", \"may\", or \"suggests\".\n"
                "- Every technical claim must have direct evidence from PRIMARY SOURCE or RELATED SOURCE CODE.\n"
                "- If information is missing, say \"Not shown in supplied context\"."
            )

        return f"""
You are a senior software architect.

Rules:
{rules}

Answer the question using concrete identifiers.

==================================================
WORKSPACE CONTEXT
==================================================

{context}

==================================================
QUESTION
==================================================

{question}
"""


prompt_builder = PromptBuilder()
