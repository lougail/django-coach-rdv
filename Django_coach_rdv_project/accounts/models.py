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
