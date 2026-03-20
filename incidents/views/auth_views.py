import logging
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.db import transaction

User = get_user_model()
logger = logging.getLogger(__name__)

VALID_CONCERNS = {'physical', 'digital', 'weather'}


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('feed')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm  = request.POST.get('confirm_password', '')
        name     = request.POST.get('name', '').strip()
        location = request.POST.get('location', '').strip()
        concerns = request.POST.getlist('concerns')

        # validation
        errors = []
        if not username:
            errors.append("Username is required.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if not name:
            errors.append("Name is required.")
        if not location:
            errors.append("Location is required.")
        if User.objects.filter(username=username).exists():
            errors.append("Username already taken.")
        invalid_concerns = set(concerns) - VALID_CONCERNS
        if invalid_concerns:
            errors.append(f"Invalid concerns: {invalid_concerns}")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'signup.html', {
                'form_data': request.POST,
                'selected_concerns': concerns,
            })

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    name=name,
                    location=location,
                    concerns=concerns,
                )
            login(request, user)
            messages.success(request, f"Welcome, {name}! Your account is ready.")
            return redirect('feed')

        except Exception as e:
            logger.error(f"Signup error: {e}")
            messages.error(request, "Something went wrong. Please try again.")

    return render(request, 'signup.html', {
        'form_data': {},
        'selected_concerns': [],
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('feed')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', reverse('feed'))
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'login.html', {
        'form_data': request.POST if request.method == 'POST' else {},
    })


def logout_view(request):
    logout(request)
    return redirect('/login/')
