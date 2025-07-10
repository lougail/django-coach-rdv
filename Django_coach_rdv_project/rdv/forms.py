from django import forms
from .models import Seance
from accounts.models import CreneauDisponible
from django.utils import timezone
from datetime import datetime, timedelta, date as date_module

class PriseRdvForm(forms.ModelForm):
    """
    Formulaire pour la prise de rendez-vous
    """
    
    # Champ personnalisé pour l'heure avec choix limité
    heure_début = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Générer les créneax horaires
        self.fields['heure_début'].choices = self.generer_creneaux()
        
    def generer_creneaux(self):
        """
        Génère les créneaux disponibles basés sur les créneaux définis par le coach
        Si aucun créneau défini, utilise les créneaux par défaut 9h-18h
        """
        creneaux = []
        
        # Récupérer les créneaux de disponibilité du coach
        # Pour l'instant, on prend le premier coach trouvé (amélioration future : passer le coach en paramètre)
        from django.contrib.auth.models import User
        coaches = User.objects.filter(profil__role='coach')
        
        if coaches.exists():
            coach = coaches.first()
            creneaux_coach = CreneauDisponible.objects.filter(
                coach=coach,
                actif=True
            ).order_by('jour', 'heure_début')
            
            if creneaux_coach.exists():
                # Utiliser les créneaux définis par le coach
                for creneau in creneaux_coach:
                    # Générer les créneaux de 30 minutes dans la plage horaire
                    debut = creneau.heure_début
                    fin = creneau.heure_fin
                    
                    current_time = datetime.combine(date_module.today(), debut)
                    end_time = datetime.combine(date_module.today(), fin)
                    
                    while current_time + timedelta(minutes=30) <= end_time:
                        heure_str = current_time.strftime("%H:%M")
                        jour_nom = dict(CreneauDisponible.JOURS_SEMAINES)[creneau.jour]
                        display_text = f"{heure_str} ({jour_nom})"
                        creneaux.append((heure_str, display_text))
                        current_time += timedelta(minutes=30)
            else:
                # Aucun créneau défini, utiliser les créneaux par défaut
                creneaux = self.generer_creneaux_defaut()
        else:
            # Pas de coach trouvé, utiliser les créneaux par défaut
            creneaux = self.generer_creneaux_defaut()
            
        return creneaux
    
    def generer_creneaux_defaut(self):
        """
        Génère les créneaux par défaut de 30 minutes entre 9h et 18h
        """
        creneaux = []
        
        # Créneaux de 9h00 à 17h30 (pour finir à 18h)
        heure = 9
        minute = 0
        
        while heure < 18:
            # Format : "09:00" pour l'affichage
            heure_str = f"{heure:02d}:{minute:02d}"
            creneaux.append((heure_str, heure_str))
            
            # Incrémenter de 30 minutes
            minute += 30
            if minute >= 60:
                minute = 0
                heure +=1
                
        return creneaux
    
    def clean(self):
        """
        Validation personnalisée pour vérifier les conflits d'horaires ET la correspondance avec les créneaux du coach
        """
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        heure_debut_str = cleaned_data.get('heure_début')

        if date and heure_debut_str:
            try:
                heure_debut = datetime.strptime(heure_debut_str, "%H:%M").time()
                debut_datetime = datetime.combine(date, heure_debut)
                fin_datetime = debut_datetime + timedelta(minutes=30)
                heure_fin = fin_datetime.time()

                # --- NOUVEAU : Vérifier que le créneau existe pour ce jour et cette heure ---
                from django.contrib.auth.models import User
                coach = User.objects.filter(profil__role='coach').first()
                if coach:
                    jour = date.weekday()  # 0=lundi
                    creneau_valide = CreneauDisponible.objects.filter(
                        coach=coach,
                        jour=jour,
                        actif=True,
                        heure_début__lte=heure_debut,
                        heure_fin__gte=heure_fin
                    ).exists()
                    if not creneau_valide:
                        raise forms.ValidationError(
                            "Le coach n'est pas disponible à ce jour et cette heure. Veuillez choisir un créneau valide."
                        )

                # Vérifier les conflits avec les séances existantes
                conflits = Seance.objects.filter(
                    date=date,  
                    heure_début__lt=heure_fin,
                    heure_fin__gt=heure_debut
                ).exclude(statut='annulee')
                if conflits.exists():
                    raise forms.ValidationError(
                        "Ce créneau horaire est déjà réservé. "
                        "Veuillez choisir un autre horaire."
                    )
            except ValueError:
                raise forms.ValidationError("Format d'heure invalide.")
        return cleaned_data
    
    class Meta:
        model = Seance
        fields = ['date', 'objet']  # Enlevé heure_début du Meta car c'est un champ personnalisé
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'objet': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
        }