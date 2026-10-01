from .exact_match import ExactMatchEvaluator
from .semantic_similarity import SemanticSimilarityEvaluator
from .factuality import FactualityEvaluator
from .citation import CitationEvaluator
from .composite import CompositeEvaluator

class EvaluatorRegistry:
    _evaluators = {
        'exact_match': ExactMatchEvaluator,
        'semantic_similarity': SemanticSimilarityEvaluator,
        'factuality': FactualityEvaluator,
        'citation': CitationEvaluator,
        'composite': CompositeEvaluator,
    }

    @classmethod
    def register(cls, name, evaluator_class):
        cls._evaluators[name] = evaluator_class

    @classmethod
    def get_evaluator(cls, name='composite'):
        eval_cls = cls._evaluators.get(name, CompositeEvaluator)
        return eval_cls()
