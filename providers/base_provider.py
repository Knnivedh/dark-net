from abc import ABC, abstractmethod

class BaseProvider(ABC):
    def __init__(self, api_key):
        self.api_key = api_key
        self.name = "base"

    @abstractmethod
    def chat(self, messages):
        pass
