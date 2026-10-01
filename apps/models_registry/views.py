from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, permissions
from .models import ModelProvider, AIModel
from .serializers import ModelProviderSerializer, AIModelSerializer

# DRF ViewSets
class ModelProviderViewSet(viewsets.ModelViewSet):
    queryset = ModelProvider.objects.all()
    serializer_class = ModelProviderSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class AIModelViewSet(viewsets.ModelViewSet):
    queryset = AIModel.objects.all()
    serializer_class = AIModelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['provider', 'is_active']

# Web Views
def model_list_view(request):
    providers = ModelProvider.objects.prefetch_related('models').filter(is_active=True)
    models_list = AIModel.objects.select_related('provider').filter(is_active=True)
    return render(request, 'models_registry/list.html', {
        'providers': providers,
        'models_list': models_list
    })

@login_required
def model_create_view(request):
    if request.method == 'POST':
        provider_id = request.POST.get('provider')
        name = request.POST.get('name')
        model_identifier = request.POST.get('model_identifier')
        description = request.POST.get('description', '')
        temperature = float(request.POST.get('temperature', 0.0))
        max_tokens = int(request.POST.get('max_tokens', 1024))

        provider = get_object_or_404(ModelProvider, id=provider_id)
        
        AIModel.objects.create(
            provider=provider,
            name=name,
            model_identifier=model_identifier,
            description=description,
            temperature=temperature,
            max_tokens=max_tokens
        )
        messages.success(request, f"Model '{name}' configured successfully.")
        return redirect('models_registry:list')

    providers = ModelProvider.objects.filter(is_active=True)
    return render(request, 'models_registry/form.html', {'providers': providers})
