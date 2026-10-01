import re
from .base import BaseEvaluator, EvaluationOutput

class ExactMatchEvaluator(BaseEvaluator):
    def _normalize(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        return " ".join(text.split())

    def evaluate(
        self,
        question_text: str,
        expected_answer: str,
        response_text: str,
        reference_source: str = "",
        is_unanswerable: bool = False,
        **kwargs
    ) -> EvaluationOutput:
        norm_expected = self._normalize(expected_answer)
        norm_response = self._normalize(response_text)

        if not norm_response:
            return EvaluationOutput(score=0.0, reasoning="Model response was empty.")

        if norm_expected == norm_response:
            score = 1.0
            reasoning = "Exact match verified: model output matches reference answer identically."
        elif norm_expected in norm_response or norm_response in norm_expected:
            score = 0.8
            reasoning = "Substantial exact substring match found between response and reference answer."
        else:
            score = 0.0
            reasoning = "No exact match between model response and reference answer."

        return EvaluationOutput(
            score=score,
            reasoning=reasoning,
            details={'norm_expected': norm_expected, 'norm_response': norm_response}
        )
