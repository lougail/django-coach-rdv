from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from accounts.models import Profil


class Command(BaseCommand):
    help = 'Crée un compte coach avec les permissions appropriées'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='marie_coach', help='Nom d\'utilisateur du coach')
        parser.add_argument('--email', type=str, default='marie@coach-rdv.fr', help='Email du coach')
        parser.add_argument('--first-name', type=str, default='Marie', help='Prénom du coach')
        parser.add_argument('--last-name', type=str, default='Dupont', help='Nom de famille du coach')
        parser.add_argument('--password', type=str, default='coach123!', help='Mot de passe du coach')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        first_name = options['first_name']
        last_name = options['last_name']
        password = options['password']

        # Vérifier si l'utilisateur existe déjà
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'L\'utilisateur {username} existe déjà.')
            )
            return

        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True  # Permettre l'accès à l'admin
        )

        # Créer le profil coach
        Profil.objects.create(user=user, role='coach')

        # Ajouter au groupe Coach
        try:
            coach_group = Group.objects.get(name='Coach')
            user.groups.add(coach_group)
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('Le groupe Coach n\'existe pas. Exécutez les migrations d\'abord.')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Compte coach créé avec succès!\n'
                f'Username: {username}\n'
                f'Password: {password}\n'
                f'Email: {email}\n'
                f'Le coach peut maintenant se connecter et accéder à son dashboard.'
            )
        )
