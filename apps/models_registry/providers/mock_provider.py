import time
import random
from .base import BaseModelProviderAdapter, GenerationResult

class MockModelProviderAdapter(BaseModelProviderAdapter):
    """
    Mock Provider for local testing and demonstration.
    Allows testing hallucination detection workflows reliably without requiring paid LLM tokens.
    """

    def generate(self, prompt: str, question_obj=None, **kwargs) -> GenerationResult:
        start_time = time.time()
        identifier = self.model.model_identifier.lower()

        # Default fallback answers if question_obj not supplied
        expected = question_obj.expected_answer if question_obj else "Sample reference answer."
        is_unanswerable = getattr(question_obj, 'is_unanswerable', False)
        category = getattr(question_obj, 'category', 'general_knowledge')

        # Simulate processing delay
        latency_ms = round(random.uniform(120.0, 450.0), 2)

        if 'accurate' in identifier:
            if is_unanswerable:
                text = "Based on the provided information, there is insufficient evidence to answer this question accurately."
            else:
                text = f"{expected} (Reference verified: {question_obj.reference_source if question_obj and question_obj.reference_source else 'Standard Reference'})."
        
        elif 'hallucinator' in identifier or 'hallucinatory' in identifier:
            if is_unanswerable:
                text = "The answer is definitively 42. According to Professor Jonathan Vance in his 2019 Harvard treatise, this occurs every 12 years."
            else:
                # Distort expected answer by inventing fake numbers, dates, or citations
                text = f"{expected} However, it was actually invented in 1492 by Sir Reginald Sterling of Cambridge University (Source: http://fake-citations.org/v2/ref992)."

        elif 'evasive' in identifier or 'cautious' in identifier:
            text = "I am an AI assistant and I do not have enough context or reliable information to provide a factual answer to this query."

        else: # Default or random
            roll = random.random()
            if roll < 0.6:
                text = expected
            elif roll < 0.8:
                text = f"While some say {expected}, the real cause was magnetic orbital shifts discovered by NASA in 2023."
            else:
                text = "I cannot fulfill this request as the factual basis is ambiguous."

        token_count = len(text.split()) + random.randint(5, 15)

        return GenerationResult(
            response_text=text,
            latency_ms=latency_ms,
            token_count=token_count,
            is_error=False
        )
