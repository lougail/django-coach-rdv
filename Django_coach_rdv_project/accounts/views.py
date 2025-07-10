from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
from .models import Profil, User, NoteClient, CreneauDisponible
from rdv.models import Seance

# Utilitaires pour les permissions
def is_coach(user):
    """Vérifie si l'utilisateur est un coach"""
    return user.is_authenticated and hasattr(user, 'profil') and user.profil.is_coach()

def is_client(user):
    """Vérifie si l'utilisateur est un client"""
    return user.is_authenticated and hasattr(user, 'profil') and user.profil.is_client()

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
        
        if form.is_valid():
            user = form.save()
            # Créer le profil avec le rôle client par défaut (plus de choix)
            profil = Profil.objects.create(user=user, role='client')
            
            # Assigner l'utilisateur au groupe Client
            client_group = Group.objects.get(name='Client')
            user.groups.add(client_group)
            
            # Connecter automatiquement l'utilisateur
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Rediriger vers le dashboard client
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
    # Récupérer toutes les séances (de l'utilisateur connecté)
    seances_a_venir = Seance.objects.filter(client=request.user, date__gte=timezone.now().date()).exclude(statut="annulee").order_by('date', 'heure_début')
    seances_passees = Seance.objects.filter(client=request.user, date__lt=timezone.now().date()).order_by('-date', '-heure_début')
    
    context = {
        'user': request.user,
        'profil': request.user.profil,
        'seances_a_venir': seances_a_venir,
        'seances_passees': seances_passees,
    }
    return render(request, 'accounts/dashboard_client.html', context)

@login_required
@user_passes_test(is_coach, login_url='/accounts/login/')
@permission_required('accounts.view_noteclient', raise_exception=True)
def dashboard_coach(request):
    """Dashboard pour les coachs - accès sécurisé"""
    # Vérifier que l'utilisateur est coach ou admin
    try:
        profil = request.user.profil
        if not profil.is_coach() and not request.user.is_superuser:
            messages.error(request, "Accès refusé : cette page est réservée aux coachs.")
            return redirect('accounts:dashboard_client')
    except Profil.DoesNotExist:
        messages.error(request, "Accès refusé : profil non trouvé.")
        return redirect('accounts:dashboard_client')
    
    # Date d'aujourd'hui
    aujourd_hui = timezone.now().date()
    
    # Récupérer les séances
    seances_aujourd_hui = Seance.objects.filter(date=aujourd_hui).exclude(statut="annulee").order_by('heure_début')
    seances_a_venir = Seance.objects.filter(date__gte=aujourd_hui).exclude(statut="annulee").order_by('date', 'heure_début')
    seances_passees = Seance.objects.filter(date__lt=aujourd_hui).exclude(statut="annulee").order_by('-date', '-heure_début')
    
    # Séances récemment annulées (7 derniers jours)
    date_limite = aujourd_hui - timedelta(days=7)
    seances_annulees_recentes = Seance.objects.filter(
        statut='annulee',
        updated_at__gte=timezone.make_aware(datetime.combine(date_limite, datetime.min.time()))
    ).order_by('-updated_at')[:5]
    
    # Statistiques pour le coach
    total_seances_donnees = seances_passees.count()
    clients_uniques = seances_a_venir.values('client').distinct().count() + seances_passees.values('client').distinct().count()
    
    # Liste des clients ayant pris au moins un RDV
    clients_avec_rdv = []
    for client in User.objects.filter(seances__isnull=False).distinct():
        # Récupérer toutes les séances de ce client
        seances_client = Seance.objects.filter(client=client)
        
        # Calculer les statistiques pour ce client
        nombre_total_seances = seances_client.count()
        
        # Dernière séance (la plus récente dans le passé)
        derniere_seance = seances_client.filter(date__lt=aujourd_hui).order_by('-date', '-heure_début').first()
        
        # Prochaine séance (la plus proche dans le futur ou aujourd'hui, hors annulée)
        prochaine_seance = seances_client.filter(date__gte=aujourd_hui).exclude(statut="annulee").order_by('date', 'heure_début').first()
        
        # Ajouter les informations du client à la liste
        clients_avec_rdv.append({
            'client': client,
            'nombre_total_seances': nombre_total_seances,
            'derniere_seance': derniere_seance,
            'prochaine_seance': prochaine_seance,
        })
    
    context = {
        'user': request.user,
        'profil': request.user.profil,
        'seances_aujourd_hui': seances_aujourd_hui,
        'seances_a_venir': seances_a_venir,
        'seances_passees': seances_passees,
        'seances_annulees_recentes': seances_annulees_recentes,
        'total_seances_donnees': total_seances_donnees,
        'clients_uniques': clients_uniques,
        'clients_avec_rdv': clients_avec_rdv,
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
        # Avertir l'utilisateur et proposer un lien vers l'inscription/connexion
        messages.warning(request, "Vous devez être connecté pour accéder à votre tableau de bord. Veuillez vous inscrire ou vous connecter.")
        return redirect("accounts:login")

@login_required
def page_client(request, client_id):
    """Page complète d'un client - historique, notes, etc. - réservé aux coachs"""
    # Vérifier que l'utilisateur est coach ou admin
    try:
        profil = request.user.profil
        if not profil.is_coach() and not request.user.is_superuser:
            messages.error(request, "Accès refusé : cette page est réservée aux coachs.")
            return redirect('accounts:dashboard_client')
    except Profil.DoesNotExist:
        messages.error(request, "Accès refusé : profil non trouvé.")
        return redirect('accounts:dashboard_client')
    
    # Récupérer le client
    try:
        client = User.objects.get(id=client_id)
    except User.DoesNotExist:
        messages.error(request, "Client non trouvé.")
        return redirect('accounts:dashboard_coach')
    
    # Traitement du formulaire d'ajout de note
    if request.method == 'POST' and request.POST.get('action') == 'ajouter_note':
        nouvelle_note = request.POST.get('nouvelle_note', '').strip()
        
        if nouvelle_note:
            # Créer la note
            NoteClient.objects.create(
                coach=request.user,
                client=client,
                contenu=nouvelle_note
            )
            messages.success(request, 'Note ajoutée avec succès !')
        else:
            messages.error(request, 'Veuillez saisir une note.')
        
        # Redirection pour éviter la re-soumission
        return redirect('accounts:page_client', client_id=client.id)
    
    # Récupérer toutes les séances de ce client
    seances_passees = Seance.objects.filter(
        client=client, 
        date__lt=timezone.now().date()
    ).order_by('-date', '-heure_début')
    
    seances_a_venir = Seance.objects.filter(
        client=client, 
        date__gte=timezone.now().date()
    ).order_by('date', 'heure_début')
    
    # Récupérer les notes du coach pour ce client
    notes_client = NoteClient.objects.filter(
        client=client,
        coach=request.user
    ).order_by('-created_at')
    
    # Statistiques du client
    total_seances = seances_passees.count() + seances_a_venir.count()
    
    context = {
        'client': client,
        'seances_passees': seances_passees,
        'seances_a_venir': seances_a_venir,
        'notes_client': notes_client,
        'total_seances': total_seances,
    }
    
    return render(request, 'accounts/page_client.html', context)

    
@login_required
def gerer_creneaux(request):
    """
    Permet au coach de gérer ses créneaux de disponibilité - reservé au coach
    """
    # Vérifier que l'utilisateur est un coach
    try:
        profil = request.user.profil
        if not profil.is_coach():
            messages.error(request, "Accès refusé : cette page est réservée aux coachs.")
            return redirect('accounts:dashboard_client')
    except Profil.DoesNotExist:
        messages.error(request, "Accès refusé : profil non trouvé.")
        return redirect('accounts:dashboard_client')
    
    try:
        # Récupérer les créneaux existants
        creneaux_existants = CreneauDisponible.objects.filter(
            coach = request.user,
            actif = True
        ).order_by('jour', 'heure_début')
        
        # Si c'est une requête POST (ajout d'un créneau)
        if request.method == 'POST':
            jour = request.POST.get('jour')
            heure_debut = request.POST.get('heure_debut')
            heure_fin = request.POST.get('heure_fin')
            
            # Validation des champs obligatoires
            if not jour or not heure_debut or not heure_fin:
                messages.error(request, "Tous les champs sont obligatoires")
            else:
                # Validation du jour (doit être entre 0 et 6)
                try:
                    jour = int(jour)
                    if jour < 0 or jour > 6:
                        messages.error(request, "Jour invalide")
                    else:
                        # Validation des heures
                        try:
                            debut = datetime.strptime(heure_debut, "%H:%M").time()
                            fin = datetime.strptime(heure_fin, "%H:%M").time()
                            
                            if debut >= fin:
                                messages.error(request, "L'heure de début doit être avant l'heure de fin")
                            else:
                                # Vérifier les conflits
                                creneaux_meme_jour = CreneauDisponible.objects.filter(
                                    coach=request.user,
                                    jour=jour,
                                    actif=True
                                )
                                conflit = False
                                for creneau_existant in creneaux_meme_jour:
                                    if (debut < creneau_existant.heure_fin and fin > creneau_existant.heure_début):
                                        conflit = True
                                        messages.error(request, "Ce créneau chevauche un créneau déjà existant")
                                        break
                                if not conflit:
                                # Créer le nouveau créneau
                                    CreneauDisponible.objects.create(
                                        coach=request.user,
                                        jour=jour,
                                        heure_début=debut,
                                        heure_fin=fin,
                                        actif=True
                                    )
                                    messages.success(request, "Créneau ajouté avec succès !")
                                    return redirect('accounts:gerer_creneaux')
                        
                        except ValueError:
                            messages.error(request, "Format d'heure invalide (utilisez HH:MM)")
                except ValueError:
                    messages.error(request, "Jour invalide")
        
        # Préparer les données pour le template
        jours_semaine = CreneauDisponible.JOURS_SEMAINES
        
        context = {
            'creneaux_existants': creneaux_existants,
            'jours_semaine': jours_semaine,
        }
        
        return render(request, 'accounts/gerer_creneaux.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur : {str(e)}")
        return redirect('accounts:dashboard_coach')
    
@login_required
def supprimer_creneau(request, creneau_id):
    """
    Supprimer un creneau de disponibilité - réservé au coach
    """
    # Vérifier que l'utilisateur est un coach
    try:
        profil = request.user.profil
        if not profil.is_coach():
            messages.error(request, "Accès refusée : cette action est réservée au coach.")
            return redirect('accounts:dashboard_client')
    except Profil.DoesNotExist:
        messages.error(request, 'Accès refusé : profil non trouvé')
        return redirect('accounts:dashboard_client')
    
    if request.method == 'POST':
        try:
            # Récupérer le créneau à supprimer
            creneau = CreneauDisponible.objects.get(
                id = creneau_id,
                coach = request.user,
                actif = True
            )
            creneau.delete()
            messages.success(request, "Le créneau a été supprimé avec succès")
            
        except CreneauDisponible.DoesNotExist:
            messages.error(request, "Créneau non trouvé, ou vous n'avez pas les droits pour le supprimer")
        
    # Rediriger vers la page de gestion des créneaux
    return redirect('accounts:gerer_creneaux')

@login_required
def annuler_seance(request, seance_id):
    """
    Permet à un client d'annuler une séance
    """
    if request.method == 'POST':
        try:
            # Récupérer la séance
            seance = Seance.objects.get(id=seance_id, client=request.user)
            
            if seance.statut == 'reservee':
                seance.statut = 'annulee'
                seance.save()
                messages.success(request, "Séance annulée avec succès")
            else:
                messages.error(request, "Cette séance ne peut pas être annulée")
                
        except Seance.DoesNotExist:
            messages.error(request, "Séance non trouvée.")
            
    return redirect('accounts:dashboard_client')