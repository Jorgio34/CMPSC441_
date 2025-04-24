from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def respond(self, input_text: str, context: dict) -> str:
        pass
