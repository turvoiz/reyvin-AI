from abc import ABC, abstractmethod


class ChatProvider(ABC):

    @abstractmethod
    def chat(
        self,
        model: str,
        message: str,
        thinking: bool,
    ):
        pass
