from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Profil

# Create your views here.
def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username = username, password = password)

        if user is not None:
            login(request, user)
            # Redirection conditionnelle selon le rôle
            try:
                profil = user.profil
                if profil.is_coach():
                    return redirect("accounts:dashboard_coach")
                else:
                    return redirect("accounts:dashboard_client")
            except Profil.DoesNotExist:
                # Si pas de profil, créer un profil client par défaut
                Profil.objects.create(user=user, role='client')
                return redirect("accounts:dashboard_client")
        else:
            messages.info(request, "Identifiant ou mot de passe incorrect")
            
    form = AuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})

def logout_user(request):
    logout(request)
    return redirect("rdv:accueil")

def register_user(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        role = request.POST.get('role', 'client')  # Récupérer le rôle sélectionné
        
        if form.is_valid():
            user = form.save()
            # Créer le profil avec le rôle sélectionné
            profil = Profil.objects.create(user=user, role=role)
            
            # AJOUTER CES LIGNES : Connecter automatiquement l'utilisateur
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Rediriger selon le rôle
                if profil.is_coach():
                    return redirect('accounts:dashboard_coach')
                else:
                    return redirect('accounts:dashboard_client')
            
            # Si l'authentification échoue (cas rare), rediriger vers login
            messages.success(request, f'Compte créé pour {username}! Vous pouvez maintenant vous connecter.')
            return redirect('accounts:login')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def dashboard_client(request):
    """Dashboard pour les clients"""
    context = {
        'user': request.user,
        'profil': request.user.profil
    }
    return render(request, 'accounts/dashboard_client.html', context)

@login_required
def dashboard_coach(request):
    """Dashboard pour les coachs"""
    context = {
        'user': request.user,
        'profil': request.user.profil
    }
    return render(request, 'accounts/dashboard_coach.html', context)

@login_required
def dashboard(request):
    """Vue générale qui redirige vers le bon dashboard selon le rôle"""
    try:
        profil = request.user.profil
        if profil.is_coach():
            return redirect("accounts:dashboard_coach")
        else:
            return redirect("accounts:dashboard_client")
    except Profil.DoesNotExist:
        # Si pas de profil, créer un profil client par défaut
        Profil.objects.create(user=request.user, role='client')
        return redirect("accounts:dashboard_client")