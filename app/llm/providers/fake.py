import json

from app.llm.interfaces.chat_provider import ChatProvider


class FakeProvider(ChatProvider):

    def chat(
        self,
        model: str,
        message: str,
        thinking: bool,
    ):

        
        if '"explanation"' in message:

            return {
                "response": json.dumps({
                    "explanation": "fake explanation",
                    "review": {
                        "summary": "fake summary",
                        "strengths": [],
                        "weaknesses": [],
                        "bugs": [],
                        "performance": [],
                        "security": [],
                        "refactor": []
                    }
                }),
                "elapsed_ms": 1,
            }

        if "Return ONLY valid JSON" in message:

            return {
                "response": json.dumps({
                    "summary": "fake summary",
                    "strengths": ["fake strength"],
                    "weaknesses": [],
                    "bugs": [],
                    "performance": [],
                    "security": [],
                    "refactor": [],
                }),
                "elapsed_ms": 1,
            }

        return {
            "response": "FAKE RESPONSE",
            "elapsed_ms": 1,
        }


fake_provider = FakeProvider()
