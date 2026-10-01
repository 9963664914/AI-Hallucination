import time
from abc import ABC, abstractmethod

class GenerationResult:
    def __init__(self, response_text: str, latency_ms: float = 0.0, token_count: int = 0, is_error: bool = False, error_message: str = ""):
        self.response_text = response_text
        self.latency_ms = latency_ms
        self.token_count = token_count
        self.is_error = is_error
        self.error_message = error_message

    def to_dict(self):
        return {
            'response_text': self.response_text,
            'latency_ms': self.latency_ms,
            'token_count': self.token_count,
            'is_error': self.is_error,
            'error_message': self.error_message,
        }

class BaseModelProviderAdapter(ABC):
    def __init__(self, model_instance):
        self.model = model_instance
        self.provider = model_instance.provider

    @abstractmethod
    def generate(self, prompt: str, question_obj=None, **kwargs) -> GenerationResult:
        """
        Generate response for given prompt.
        Must return GenerationResult.
        """
        pass
