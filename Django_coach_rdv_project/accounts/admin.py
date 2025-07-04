from django.contrib import admin
from .models import Profil

# Register your models here.

@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at']
