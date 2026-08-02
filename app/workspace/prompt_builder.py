class PromptBuilder:

    def build(self, knowledge, question):

        return f"""
You are an expert software engineer.

RULES

- Never guess.
- Never invent information.
- Use ONLY the workspace knowledge below.

==================================================
WORKSPACE KNOWLEDGE
==================================================

{knowledge}

==================================================
QUESTION
==================================================

{question}
"""


prompt_builder = PromptBuilder()
