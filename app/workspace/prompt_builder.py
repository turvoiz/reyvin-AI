class PromptBuilder:

    def build(
        self,
        context,
        question,
    ):

        return f"""
You are a senior software architect.

Rules:
- Use ONLY the supplied workspace context.
- Never use outside knowledge.
- Never infer behavior.
- Never say "likely", "probably", "may", or "suggests".
- Every technical claim must have direct evidence from PRIMARY SOURCE or RELATED SOURCE CODE.
- If information is missing, say "Not shown in supplied context".

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
