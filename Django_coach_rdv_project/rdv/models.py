from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

class Seance(models.Model):
    """
    Modèle pour représenter une séance/rendez-vous
    """
    
    # Le client qui prend le rendez-vous
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seances')
    
    # Date de la séance
    date = models.DateField()
    
    # Heures de la séance
    heure_début = models.TimeField()
    heure_fin = models.TimeField()
    
    # Objet / Description de la séance
    objet = models.TextField(help_text="Décrivez l'objet de votre séance")
    
    # Notes privées du coach (visible seulement par le coach)
    notes_coach = models.TextField(blank=True, default="", help_text="Notes privées du coach (non visibles par le client)")
    
    # Statut de la séance
    STATUTS = [
        ('reservee', 'Réservée'),
        ('confirmee', 'Confirmée'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]
    statut = models.CharField(max_length=10, choices=STATUTS, default='reservee')
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.client.username} - {self.date} {self.heure_début}"
    
    class Meta:
        verbose_name = "Séance"
        verbose_name_plural = "Séances"
        ordering = ['date', 'heure_début']

    def clean(self):
        """Validations métier"""
        # Validation 1 : Heure début < Heure fin (seulement si les deux sont définies)
        if self.heure_début and self.heure_fin and self.heure_début >= self.heure_fin:
            raise ValidationError("L'heure de début doit être antérieure à l'heure de fin")
        
        # Validation 2 : Pas dans le passé
        if self.date and self.date < timezone.now().date():
            raise ValidationError("Impossible de réserver dans le passé")
        
        # Validation 3 : Horaires autorisés (9h-18h)
        if self.heure_début:
            heure_min = timezone.datetime.strptime("09:00", "%H:%M").time()
            heure_max = timezone.datetime.strptime("18:00", "%H:%M").time()
            if not (heure_min <= self.heure_début < heure_max):
                raise ValidationError("Les rendez-vous ne sont autorisés qu'entre 9h et 18h")
        
        # Validation 4 : Vérifier les chevauchements avec d'autres séances
        if self.date and self.heure_début and self.heure_fin:
            conflits = Seance.objects.filter(
                date=self.date,
                heure_début__lt=self.heure_fin,
                heure_fin__gt=self.heure_début
            ).exclude(statut='annulee')
            # Exclure la séance actuelle si on modifie une séance existante
            if self.pk:
                conflits = conflits.exclude(pk=self.pk)
            
            if conflits.exists():
                raise ValidationError("Ce créneau horaire est déjà réservé")

    def save(self, *args, **kwargs):
        """Surcharge du save pour calculer automatiquement l'heure de fin"""
        if self.heure_début and not self.heure_fin:
            # Calculer automatiquement l'heure de fin (séance de 30 minutes)
            debut_datetime = datetime.combine(datetime.today(), self.heure_début)
            fin_datetime = debut_datetime + timedelta(minutes=30)
            self.heure_fin = fin_datetime.time()
        
        super().save(*args, **kwargs)

    @property
    def est_passee(self):
        """Retourne True si la séance est passée"""
        return self.date < timezone.now().date()

    @property
    def duree_minutes(self):
        """Retourne la durée de la séance en minutes"""
        if self.heure_début and self.heure_fin:
            debut = timezone.datetime.combine(timezone.datetime.today(), self.heure_début)
            fin = timezone.datetime.combine(timezone.datetime.today(), self.heure_fin)
            return int((fin - debut).total_seconds() / 60)
        return 0

