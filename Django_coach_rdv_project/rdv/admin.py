from django.contrib import admin
from .models import Seance

@admin.register(Seance)
class SeanceAdmin(admin.ModelAdmin):
    list_display = ['client', 'date', 'heure_début', 'heure_fin', 'statut']
    list_filter = ['statut', 'date', 'client']
    search_fields = ['client_username', 'objet']
    ordering = ['-date', '-heure_début']