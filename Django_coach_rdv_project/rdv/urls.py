from django.urls import path
from . import views

app_name = 'rdv'

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('prendre_rdv/', views.prise_rdv, name='prise_rdv'),
    path('api/creneaux/', views.api_creneaux, name='api_creneaux'),
]
