from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from .models import Seance
from accounts.models import CreneauDisponible
from .forms import PriseRdvForm
from datetime import timedelta, datetime
from django.utils import timezone
from django.utils.dateparse import parse_date

def accueil(request):
    """
    Vue pour afficher la page d'accueil.
    Accessible à tous les visiteurs, présente le coach, ses services et horaires.
    """
    return render(request, 'rdv/accueil.html')

@login_required
def prise_rdv (request):
    """
    Vue pour la prise de rendez-vous.
    Connexion requise pour pouvoir y accéder.
    """
    if request.method == 'POST':
        form = PriseRdvForm(request.POST)
        if form.is_valid():
            # Créer la séance mais ne pas encore sauvegarder
            seance = form.save(commit=False)
            
            # Ajouter les informations manquantes
            seance.client = request.user # Client = utilisateur connecté
            
            # Convertir la chaîne en objet time
            heure_debut_str = form.cleaned_data['heure_début']
            heure_debut_obj = datetime.strptime(heure_debut_str, "%H:%M").time()
            seance.heure_début = heure_debut_obj
            
            # Ajouter 30 minutes pour calculer l'heure de fin
            debut_datetime = datetime.combine(datetime.today(), heure_debut_obj)
            fin_datetime = debut_datetime + timedelta(minutes=30)
            seance.heure_fin = fin_datetime.time()
            
            # Sauvegarder
            seance.save()
            messages.success(request, 'Votre rendez-vous a été réservé avec succès!')
            return redirect('accounts:dashboard')
    else:
        form = PriseRdvForm()
        
    today = timezone.now().date()
    nb_jours = 7
    coach = User.objects.filter(profil__role='coach').order_by('-id').first()
    grille = []

    if coach:
        for i in range(nb_jours):
            jour_date = today + timedelta(days=i)
            jour_semaine = jour_date.weekday()
            creneaux = CreneauDisponible.objects.filter(coach=coach, jour=jour_semaine, actif=True)
            ligne = []
            for creneau in creneaux:
                current_time = datetime.combine(jour_date, creneau.heure_début)
                end_time = datetime.combine(jour_date, creneau.heure_fin)
                while current_time + timedelta(minutes=30) <= end_time:
                    heure_debut = current_time.time()
                    heure_fin = (current_time + timedelta(minutes=30)).time()
                    # Vérifier si réservé
                    conflit = Seance.objects.filter(
                        date=jour_date,
                        heure_début__lt=heure_fin,
                        heure_fin__gt=heure_debut,
                        statut='reservee'
                    ).exists()
                    ligne.append({
                        'date': jour_date,
                        'heure': heure_debut.strftime('%H:%M'),
                        'reserve': conflit
                    })
                    current_time += timedelta(minutes=30)
            grille.append({'date': jour_date, 'creneaux': ligne})

    return render(request, 'rdv/prise_rdv.html', {'form': form, 'grille': grille})

def api_creneaux(request):
    # Récupérer la période demandée par FullCalendar (GET ?start=...&end=...)
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    def extract_date(date_str):
        if date_str:
            return parse_date(date_str[:10])
        return None
    start = extract_date(start_str)
    end = extract_date(end_str)
    if not start or not end:
        today = timezone.now().date()
        start = today
        end = today + timedelta(days=7)
    events = []
    coach = User.objects.filter(profil__role='coach').order_by('-id').first()
    if coach:
        nb_jours = (end - start).days
        for i in range(nb_jours):
            jour_date = start + timedelta(days=i)
            jour_semaine = jour_date.weekday()
            creneaux = CreneauDisponible.objects.filter(coach=coach, jour=jour_semaine, actif=True)
            for creneau in creneaux:
                current_time = datetime.combine(jour_date, creneau.heure_début)
                end_time = datetime.combine(jour_date, creneau.heure_fin)
                while current_time + timedelta(minutes=30) <= end_time:
                    heure_debut = current_time.time()
                    heure_fin = (current_time + timedelta(minutes=30)).time()
                    conflit = Seance.objects.filter(
                        date=jour_date,
                        heure_début__lt=heure_fin,
                        heure_fin__gt=heure_debut,
                        statut='reservee'
                    ).exists()
                    if not conflit:
                        events.append({
                            "title": "Disponible",
                            "start": f"{jour_date}T{heure_debut}",
                            "end": f"{jour_date}T{heure_fin}",
                            "color": "#6ee7b7"
                        })
                    current_time += timedelta(minutes=30)
    # Séances réservées (rouge)
    for seance in Seance.objects.filter(statut="reservee"):
        events.append({
            "title": "Réservé",
            "start": f"{seance.date}T{seance.heure_début}",
            "end": f"{seance.date}T{seance.heure_fin}",
            "color": "#f87171"
        })
    return JsonResponse(events, safe=False)