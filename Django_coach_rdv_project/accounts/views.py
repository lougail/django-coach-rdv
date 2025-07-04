from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect

# Create your views here.
def login_user(request):
    if request.method == POST:
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username = username, password = password)

        if user is not None:
            login(request, user)
            return redirect("rdv:accueil")
        else:
            messages.info(request, "Identifiant ou mot de passe incorrect")
            
    form = AuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})

def logout_user(request):
    logout(request)
    return redirect("rdv:accueil")

def register_user(request):
    pass