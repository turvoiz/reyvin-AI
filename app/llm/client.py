from ollama import Client

client = Client(host="http://localhost:11434")


def chat(model: str, message: str) -> str:
    response = client.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": message,
            }
        ],
    )

    return response["message"]["content"]
