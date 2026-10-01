from .mock_provider import MockModelProviderAdapter
from .openai_provider import OpenAIProviderAdapter
from .anthropic_provider import AnthropicProviderAdapter

class ProviderRegistry:
    _adapters = {
        'mock': MockModelProviderAdapter,
        'openai': OpenAIProviderAdapter,
        'anthropic': AnthropicProviderAdapter,
    }

    @classmethod
    def register(cls, provider_type, adapter_class):
        cls._adapters[provider_type] = adapter_class

    @classmethod
    def get_adapter(cls, model_instance):
        provider_type = model_instance.provider.provider_type
        adapter_cls = cls._adapters.get(provider_type, MockModelProviderAdapter)
        return adapter_cls(model_instance)
