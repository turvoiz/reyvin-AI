import json

from app.llm.interfaces.chat_provider import ChatProvider


class FakeProvider(ChatProvider):
    def chat(
        self,
        model: str,
        message: str,
        thinking: bool,
    ):

        if '"root_cause"' in message:
            return {
                "response": json.dumps(
                    {
                        "root_cause": "fake root cause",
                        "location": "greeter.ts:2:greet",
                        "explanation": "fake explanation",
                        "fixes": [
                            {
                                "description": "guard the input type",
                                "file": "greeter.ts",
                                "symbol": "greet",
                                "suggestion": "add a typeof guard before toUpperCase",
                            },
                        ],
                    }
                ),
                "elapsed_ms": 1,
            }

        if '"explanation"' in message:
            return {
                "response": json.dumps(
                    {
                        "explanation": "fake explanation",
                        "review": {
                            "summary": "fake summary",
                            "strengths": [],
                            "weaknesses": [],
                            "bugs": [],
                            "performance": [],
                            "security": [],
                            "refactor": [],
                        },
                    }
                ),
                "elapsed_ms": 1,
            }

        if "Return ONLY valid JSON" in message:
            return {
                "response": json.dumps(
                    {
                        "summary": "fake summary",
                        "strengths": ["fake strength"],
                        "weaknesses": [],
                        "bugs": [],
                        "performance": [],
                        "security": [],
                        "refactor": [],
                    }
                ),
                "elapsed_ms": 1,
            }

        return {
            "response": "FAKE RESPONSE",
            "elapsed_ms": 1,
        }


fake_provider = FakeProvider()
