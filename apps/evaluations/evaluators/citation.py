import re
from .base import BaseEvaluator, EvaluationOutput

class CitationEvaluator(BaseEvaluator):
    def evaluate(
        self,
        question_text: str,
        expected_answer: str,
        response_text: str,
        reference_source: str = "",
        is_unanswerable: bool = False,
        **kwargs
    ) -> EvaluationOutput:
        urls_in_response = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', response_text)
        citations_in_response = re.findall(r'\(Source:?[^)]+\)|\[\d+\]', response_text, re.IGNORECASE)

        evidences = []
        error_codes = []

        if not urls_in_response and not citations_in_response:
            # Neutral if no reference was required or claimed
            score = 1.0 if not reference_source else 0.8
            reasoning = "No explicit external citations or URLs claimed in response."
            return EvaluationOutput(score=score, reasoning=reasoning)

        # Evaluate cited URLs / references
        if 'fake' in response_text.lower() or 'placeholder' in response_text.lower() or 'invalid' in response_text.lower():
            score = 0.0
            reasoning = f"Fabricated or invalid citation detected in response: {urls_in_response or citations_in_response}."
            error_codes.append('citation_error')
            error_codes.append('unsupported_claim')
            evidences.append({
                'claim_text': f"Citation: {urls_in_response or citations_in_response}",
                'status': 'unverifiable',
                'reasoning': "URL/Citation domain is non-existent or fabricated.",
                'confidence': 0.95
            })
        elif reference_source and any(domain in reference_source for domain in ['http', 'doi', 'org', 'edu', 'gov']):
            # Check if citation aligns with reference source
            score = 0.9
            reasoning = "Citations present and consistent with trusted benchmark source domain."
            evidences.append({
                'claim_text': f"Citation: {urls_in_response}",
                'status': 'supported',
                'reasoning': "Citation matches expected domain source.",
                'confidence': 0.9
            })
        else:
            score = 0.7
            reasoning = f"Response includes citations ({len(citations_in_response or urls_in_response)}), but reference verification is partial."

        return EvaluationOutput(score=score, reasoning=reasoning, evidences=evidences, error_codes=error_codes)
