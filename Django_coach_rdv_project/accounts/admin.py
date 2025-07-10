from django.contrib import admin
from .models import Profil, CreneauDisponible, NoteClient

# Register your models here.

@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at']

@admin.register(CreneauDisponible)
class CreneauDisponibleAdmin(admin.ModelAdmin):
    list_display = ['coach', 'jour', 'heure_début', 'heure_fin', 'actif']
    list_filter = ['coach', 'jour', 'actif']
    search_fields = ['coach__username']
    
@admin.register(NoteClient)
class NoteClientAdmin(admin.ModelAdmin):
    list_display = ['coach', 'client', 'contenu_court', 'created_at']
    list_filter = ['coach', 'client']
    search_fields = ['coach__username', 'client__username', 'contenu']
    readonly_fields = ['created_at', 'updated_at']

    def contenu_court(self, obj):
        return obj.contenu[:40] + '...' if len(obj.contenu) > 40 else obj.contenu
    contenu_court.short_description = 'Contenu'