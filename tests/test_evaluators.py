from django.test import TestCase
from apps.evaluations.evaluators import EvaluatorRegistry
from apps.evaluations.evaluators.exact_match import ExactMatchEvaluator
from apps.evaluations.evaluators.semantic_similarity import SemanticSimilarityEvaluator
from apps.evaluations.evaluators.factuality import FactualityEvaluator
from apps.evaluations.evaluators.citation import CitationEvaluator
from apps.evaluations.evaluators.composite import CompositeEvaluator

class EvaluatorsTestCase(TestCase):
    def test_exact_match_evaluator(self):
        evaluator = ExactMatchEvaluator()
        res_exact = evaluator.evaluate("What is 2+2?", "4", "4")
        self.assertEqual(res_exact.score, 1.0)

        res_diff = evaluator.evaluate("What is 2+2?", "4", "5")
        self.assertEqual(res_diff.score, 0.0)

    def test_semantic_similarity_evaluator(self):
        evaluator = SemanticSimilarityEvaluator()
        res = evaluator.evaluate("Question", "The capital of France is Paris.", "Paris is the capital city of France.")
        self.assertGreater(res.score, 0.6)

    def test_factuality_evaluator_unanswerable_success(self):
        evaluator = FactualityEvaluator()
        res = evaluator.evaluate(
            "What will happen in 2099?",
            "Unanswerable",
            "There is insufficient information to answer this question.",
            is_unanswerable=True
        )
        self.assertEqual(res.score, 1.0)
        self.assertNotIn('failure_to_abstain', res.error_codes)

    def test_factuality_evaluator_unanswerable_failure(self):
        evaluator = FactualityEvaluator()
        res = evaluator.evaluate(
            "What will happen in 2099?",
            "Unanswerable",
            "In 2099, Earth will undergo a global magnetic shift.",
            is_unanswerable=True
        )
        self.assertEqual(res.score, 0.0)
        self.assertIn('failure_to_abstain', res.error_codes)

    def test_composite_evaluator(self):
        evaluator = CompositeEvaluator()
        output = evaluator.evaluate("Who discovered gravity?", "Isaac Newton", "Sir Isaac Newton in 1687.")
        self.assertGreater(output.score, 0.7)
        self.assertFalse(output.details['is_hallucination'])
