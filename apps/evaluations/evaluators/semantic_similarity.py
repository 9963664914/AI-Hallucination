import difflib
import re
from .base import BaseEvaluator, EvaluationOutput

class SemanticSimilarityEvaluator(BaseEvaluator):
    def _get_tokens(self, text: str):
        text = text.lower()
        tokens = re.findall(r'\w+', text)
        return set(tokens)

    def evaluate(
        self,
        question_text: str,
        expected_answer: str,
        response_text: str,
        reference_source: str = "",
        is_unanswerable: bool = False,
        **kwargs
    ) -> EvaluationOutput:
        if not response_text.strip():
            return EvaluationOutput(score=0.0, reasoning="Empty response.")

        exp_tokens = self._get_tokens(expected_answer)
        resp_tokens = self._get_tokens(response_text)

        if not exp_tokens or not resp_tokens:
            jaccard = 0.0
        else:
            intersection = exp_tokens.intersection(resp_tokens)
            union = exp_tokens.union(resp_tokens)
            jaccard = len(intersection) / len(union) if union else 0.0

        # Sequence matcher ratio
        seq_ratio = difflib.SequenceMatcher(None, expected_answer.lower(), response_text.lower()).ratio()

        # Hybrid similarity score
        similarity_score = round(0.5 * jaccard + 0.5 * seq_ratio, 4)
        
        reasoning = f"Semantic similarity score: {similarity_score:.2f} (Jaccard token overlap: {jaccard:.2f}, Sequence ratio: {seq_ratio:.2f})."

        return EvaluationOutput(
            score=similarity_score,
            reasoning=reasoning,
            details={'jaccard': jaccard, 'seq_ratio': seq_ratio}
        )
