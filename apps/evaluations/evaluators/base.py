from abc import ABC, abstractmethod
from typing import Dict, Any, List

class EvaluationOutput:
    def __init__(
        self,
        score: float = 0.0,
        reasoning: str = "",
        evidences: List[Dict[str, Any]] = None,
        error_codes: List[str] = None,
        details: Dict[str, Any] = None
    ):
        self.score = score
        self.reasoning = reasoning
        self.evidences = evidences or []
        self.error_codes = error_codes or []
        self.details = details or {}

class BaseEvaluator(ABC):
    @abstractmethod
    def evaluate(
        self,
        question_text: str,
        expected_answer: str,
        response_text: str,
        reference_source: str = "",
        is_unanswerable: bool = False,
        **kwargs
    ) -> EvaluationOutput:
        pass
