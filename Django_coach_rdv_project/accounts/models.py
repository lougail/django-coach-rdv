from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profil(models.Model):
    ROLE_CHOICES = [
        ('client', 'Client'),
        ('coach', 'Coach'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
    
    def is_coach(self):
        return self.role == 'coach'
    
    def is_client(self):
        return self.role == 'client'

class NoteClient(models.Model):
    coach = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="notes_donnees")
    client = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="notes_recues")
    contenu = models.TextField(help_text="Note privée du coach sur ce client")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Note sur client"
        verbose_name_plural = "Notes sur clients"
        
    def __str__(self):
        coach_name = self.coach.username if self.coach else "Coach supprimé"
        client_name = self.client.username if self.client else "Client supprimé"
        return f"Note de {coach_name} sur {client_name} ajoutée le ({self.created_at.strftime('%d/%m/%Y')})"
    
class CreneauDisponible(models.Model):
    JOURS_SEMAINES = [
        (0, 'Lundi'),
        (1, 'Mardi'),
        (2, 'Mercredi'),
        (3, 'Jeudi'),
        (4, 'Vendredi'),
        (5, 'Samedi'),
        (6, 'Dimanche'),
    ]
    
    coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name="creneaux_disponibles")
    jour = models.IntegerField(choices=JOURS_SEMAINES)
    heure_début = models.TimeField()
    heure_fin = models.TimeField()
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["jour", "heure_début"]
        unique_together = ['coach', 'jour', 'heure_début']
        verbose_name = "Créneau disponible"
        verbose_name_plural = "Créneaux disponibles"
        
    def __str__(self):
        return f"{self.coach.username} - {self.get_jour_display()} {self.heure_début}-{self.heure_fin}"