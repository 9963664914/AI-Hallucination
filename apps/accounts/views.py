from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            organization = request.POST.get('organization', '')
            role = request.POST.get('role', 'researcher')
            
            profile = user.profile
            profile.organization = organization
            profile.role = role
            profile.save()
            
            login(request, user)
            messages.success(request, f"Welcome to HalluciBench, {user.username}! Account created successfully.")
            return redirect('dashboard:index')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                next_url = request.GET.get('next', 'dashboard:index')
                return redirect(next_url)
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('landing')

@login_required
def profile_view(request):
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', user.first_name)
        last_name = request.POST.get('last_name', user.last_name)
        email = request.POST.get('email', user.email)
        organization = request.POST.get('organization', profile.organization)
        role = request.POST.get('role', profile.role)
        bio = request.POST.get('bio', profile.bio)

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        profile.organization = organization
        profile.role = role
        profile.bio = bio
        profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('accounts:profile')

    recent_runs = user.benchmarkrun_set.select_related('dataset_version__dataset').order_by('-created_at')[:10]

    context = {
        'user_profile': profile,
        'recent_runs': recent_runs,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your password was successfully updated!")
            return redirect('accounts:profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/password_reset.html', {'form': form})
