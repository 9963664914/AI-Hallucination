from typing import Dict, Any, List
from .base import BaseEvaluator, EvaluationOutput
from .exact_match import ExactMatchEvaluator
from .semantic_similarity import SemanticSimilarityEvaluator
from .factuality import FactualityEvaluator
from .citation import CitationEvaluator

class CompositeEvaluator(BaseEvaluator):
    """
    Composite Evaluator that runs all evaluation signals:
    - Exact match
    - Semantic similarity
    - Factuality & abstention verification
    - Citation & source verification
    Calculates composite score, identifies hallucination flag, and collects error codes & evidence.
    """
    def __init__(self):
        self.exact_eval = ExactMatchEvaluator()
        self.similarity_eval = SemanticSimilarityEvaluator()
        self.factuality_eval = FactualityEvaluator()
        self.citation_eval = CitationEvaluator()

    def evaluate(
        self,
        question_text: str,
        expected_answer: str,
        response_text: str,
        reference_source: str = "",
        is_unanswerable: bool = False,
        **kwargs
    ) -> EvaluationOutput:
        exact_res = self.exact_eval.evaluate(question_text, expected_answer, response_text)
        sim_res = self.similarity_eval.evaluate(question_text, expected_answer, response_text)
        fact_res = self.factuality_eval.evaluate(question_text, expected_answer, response_text, reference_source, is_unanswerable)
        cite_res = self.citation_eval.evaluate(question_text, expected_answer, response_text, reference_source, is_unanswerable)

        # Weighted Composite Score
        if is_unanswerable:
            composite_score = fact_res.score
        else:
            composite_score = round(
                0.20 * exact_res.score +
                0.35 * sim_res.score +
                0.35 * fact_res.score +
                0.10 * cite_res.score,
                4
            )

        # Hallucination Threshold (< 0.60 composite score or flagged factuality error)
        is_hallucination = (composite_score < 0.60) or ('fabricated_fact' in fact_res.error_codes) or ('failure_to_abstain' in fact_res.error_codes)

        all_error_codes = list(set(fact_res.error_codes + cite_res.error_codes))
        all_evidences = fact_res.evidences + cite_res.evidences

        reasoning = (
            f"Composite Score: {composite_score:.2f} | "
            f"Factuality: {fact_res.score:.2f} | "
            f"Similarity: {sim_res.score:.2f} | "
            f"Exact Match: {exact_res.score:.2f} | "
            f"Citation: {cite_res.score:.2f}. "
            f"{fact_res.reasoning}"
        )

        return EvaluationOutput(
            score=composite_score,
            reasoning=reasoning,
            evidences=all_evidences,
            error_codes=all_error_codes,
            details={
                'exact_match_score': exact_res.score,
                'semantic_similarity_score': sim_res.score,
                'factuality_score': fact_res.score,
                'citation_score': cite_res.score,
                'composite_score': composite_score,
                'is_hallucination': is_hallucination,
                'is_abstained': ('failure_to_abstain' not in fact_res.error_codes and fact_res.score == 1.0 if is_unanswerable else False)
            }
        )
