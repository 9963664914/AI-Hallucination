import time
import requests
from .base import BaseModelProviderAdapter, GenerationResult
from .mock_provider import MockModelProviderAdapter

class OpenAIProviderAdapter(BaseModelProviderAdapter):
    def generate(self, prompt: str, question_obj=None, **kwargs) -> GenerationResult:
        api_key = self.provider.get_api_key()
        
        if not api_key:
            # Fallback to mock adapter if API key is not present in env
            mock_adapter = MockModelProviderAdapter(self.model)
            res = mock_adapter.generate(prompt, question_obj=question_obj, **kwargs)
            res.response_text = f"[OpenAI API key missing - Fallback Mock]: {res.response_text}"
            return res

        start_time = time.time()
        url = self.provider.base_url or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model.model_identifier,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant being evaluated on factual accuracy."},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.model.temperature,
            "max_tokens": self.model.max_tokens,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            latency_ms = round((time.time() - start_time) * 1000, 2)

            if resp.status_code == 200:
                data = resp.json()
                text = data['choices'][0]['message']['content']
                usage = data.get('usage', {})
                tokens = usage.get('total_tokens', len(text.split()))
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
                    error_message=f"OpenAI API HTTP {resp.status_code}: {resp.text}"
                )
        except Exception as e:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            return GenerationResult(
                response_text="",
                latency_ms=latency_ms,
                is_error=True,
                error_message=f"OpenAI connection error: {str(e)}"
            )
