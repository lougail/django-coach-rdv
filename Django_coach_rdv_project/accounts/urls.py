from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/client/', views.dashboard_client, name='dashboard_client'),
    path('dashboard/coach/', views.dashboard_coach, name='dashboard_coach'),
    path('client/<int:client_id>/', views.page_client, name='page_client'),
    path('coach/creneaux/', views.gerer_creneaux, name='gerer_creneaux'),
    path('coach/creneaux/supprimer/<int:creneau_id>/', views.supprimer_creneau, name='supprimer_creneau'),
    path('seance/annuler/<int:seance_id>/', views.annuler_seance, name='annuler_seance'),
]
