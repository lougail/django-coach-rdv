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
]
