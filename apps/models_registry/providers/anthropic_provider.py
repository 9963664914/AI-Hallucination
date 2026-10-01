import time
import requests
from .base import BaseModelProviderAdapter, GenerationResult
from .mock_provider import MockModelProviderAdapter

class AnthropicProviderAdapter(BaseModelProviderAdapter):
    def generate(self, prompt: str, question_obj=None, **kwargs) -> GenerationResult:
        api_key = self.provider.get_api_key()

        if not api_key:
            mock_adapter = MockModelProviderAdapter(self.model)
            res = mock_adapter.generate(prompt, question_obj=question_obj, **kwargs)
            res.response_text = f"[Anthropic API key missing - Fallback Mock]: {res.response_text}"
            return res

        start_time = time.time()
        url = self.provider.base_url or "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model.model_identifier,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.model.max_tokens,
            "temperature": self.model.temperature,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            latency_ms = round((time.time() - start_time) * 1000, 2)

            if resp.status_code == 200:
                data = resp.json()
                text = data['content'][0]['text']
                tokens = data.get('usage', {}).get('input_tokens', 0) + data.get('usage', {}).get('output_tokens', 0)
                return GenerationResult(
                    response_text=text,
                    latency_ms=latency_ms,
                    token_count=tokens,
                    is_error=False
                )
            else:
                return GenerationResult(
                    response_text="",
                    latency_ms=latency_ms,
                    is_error=True,
                    error_message=f"Anthropic API HTTP {resp.status_code}: {resp.text}"
                )
        except Exception as e:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            return GenerationResult(
                response_text="",
                latency_ms=latency_ms,
                is_error=True,
                error_message=f"Anthropic connection error: {str(e)}"
            )
