import re
from .base import BaseEvaluator, EvaluationOutput

ABSTAIN_PHRASES = [
    'insufficient information', 'cannot answer', 'do not have enough context',
    'not mentioned', 'unknown', 'no data available', 'unclear from context',
    'cannot be determined', 'insufficient evidence'
]

OVERCONFIDENT_PHRASES = [
    'definitively', 'without a doubt', '100%', 'absolutely certain',
    'it is a proven fact', 'undeniably'
]

class FactualityEvaluator(BaseEvaluator):
    def evaluate(
        self,
        question_text: str,
        expected_answer: str,
        response_text: str,
        reference_source: str = "",
        is_unanswerable: bool = False,
        **kwargs
    ) -> EvaluationOutput:
        response_lower = response_text.lower()
        evidences = []
        error_codes = []

        # 1. Unanswerable / Abstention evaluation
        if is_unanswerable:
            has_abstained = any(phrase in response_lower for phrase in ABSTAIN_PHRASES)
            if has_abstained:
                score = 1.0
                reasoning = "Model correctly identified unanswerable question and abstained with insufficient information notice."
                evidences.append({
                    'claim_text': "Abstention on unanswerable query",
                    'status': 'supported',
                    'reasoning': "Model stated that context/data was insufficient.",
                    'confidence': 1.0
                })
            else:
                score = 0.0
                reasoning = "Model failed to abstain on an unanswerable question and hallucinated a response."
                error_codes.append('failure_to_abstain')
                error_codes.append('fabricated_fact')
                evidences.append({
                    'claim_text': response_text[:120],
                    'status': 'unsupported',
                    'reasoning': "Question was designed to test abstention; model generated fabricated factual details.",
                    'confidence': 0.95
                })
            return EvaluationOutput(score=score, reasoning=reasoning, evidences=evidences, error_codes=error_codes)

        # 2. Factual numerical & entity overlap check
        expected_numbers = set(re.findall(r'\b\d{1,4}\b', expected_answer))
        response_numbers = set(re.findall(r'\b\d{1,4}\b', response_text))

        if expected_numbers:
            missing_numbers = expected_numbers - response_numbers
            wrong_numbers = response_numbers - expected_numbers
            if wrong_numbers and missing_numbers:
                error_codes.append('incorrect_fact')
                if any(k in question_text.lower() for k in ['calculate', 'math', 'sum', 'product', 'total']):
                    error_codes.append('wrong_calculation')
                evidences.append({
                    'claim_text': f"Numeric discrepancy: expected {expected_numbers}, found {response_numbers}",
                    'status': 'contradicted',
                    'reasoning': f"Model produced mismatched numbers ({wrong_numbers}) instead of expected ({expected_numbers}).",
                    'confidence': 0.9
                })

        # 3. Check for overconfident framing with hallucinated claim
        is_overconfident = any(phrase in response_lower for phrase in OVERCONFIDENT_PHRASES)

        # Basic factual alignment score
        exp_words = set(re.findall(r'\w+', expected_answer.lower()))
        resp_words = set(re.findall(r'\w+', response_lower))
        overlap = len(exp_words.intersection(resp_words)) / len(exp_words) if exp_words else 1.0

        if overlap >= 0.7:
            score = round(min(1.0, overlap + 0.1), 2)
            reasoning = f"High factual consistency with reference answer (overlap: {overlap:.2f})."
            evidences.append({
                'claim_text': "Core response claims",
                'status': 'supported',
                'reasoning': "Key concepts and entities align with ground truth reference.",
                'confidence': score
            })
        elif overlap >= 0.3:
            score = 0.5
            reasoning = f"Partial factual alignment (overlap: {overlap:.2f}). Contains unsupported or unverified details."
            error_codes.append('partially_correct')
            error_codes.append('unsupported_claim')
            evidences.append({
                'claim_text': response_text[:120],
                'status': 'unsupported',
                'reasoning': "Response contains partially accurate info mixed with unsupported assertions.",
                'confidence': 0.7
            })
        else:
            score = 0.1
            reasoning = f"Low factual consistency with reference answer (overlap: {overlap:.2f}). High probability of hallucination."
            error_codes.append('incorrect_fact')
            error_codes.append('contradiction')
            if is_overconfident:
                error_codes.append('overconfident_answer')
            evidences.append({
                'claim_text': response_text[:120],
                'status': 'contradicted',
                'reasoning': "Response contradicts ground truth answer provided in benchmark dataset.",
                'confidence': 0.9
            })

        return EvaluationOutput(score=score, reasoning=reasoning, evidences=evidences, error_codes=error_codes)
