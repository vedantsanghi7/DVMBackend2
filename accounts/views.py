from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .forms import UserSignupForm, PassengerProfileForm


def signup_view(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save() 
            
            login(request, user)
            return redirect('metro_dashboard')  
    else:
        form = UserSignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('metro_dashboard')  
        else:
            error = "Invalid username or password"
            return render(request, 'accounts/login.html', {'error': error})

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('accounts_login')  


@login_required
def profile_edit_view(request):
    profile = request.user.profile  

    if request.method == 'POST':
        form = PassengerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('metro_dashboard')
    else:
        form = PassengerProfileForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form})
