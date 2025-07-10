from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import Profil, NoteClient, CreneauDisponible
from rdv.models import Seance


class Command(BaseCommand):
    """
    Commande pour configurer les permissions des groupes Coach et Client
    Usage: python manage.py setup_permissions
    """
    help = 'Configure les permissions pour les groupes Coach et Client'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Configuration des permissions...')

        try:
            # Récupérer ou créer les groupes
            coach_group, created = Group.objects.get_or_create(name='Coach')
            client_group, created = Group.objects.get_or_create(name='Client')

            if created:
                self.stdout.write(f'✅ Groupe créé: {coach_group.name}')
            
            # Récupérer les ContentTypes pour nos modèles
            seance_ct = ContentType.objects.get_for_model(Seance)
            profil_ct = ContentType.objects.get_for_model(Profil)
            note_ct = ContentType.objects.get_for_model(NoteClient)
            creneau_ct = ContentType.objects.get_for_model(CreneauDisponible)

            # === PERMISSIONS COACH ===
            coach_permissions = [
                # Séances - CRUD complet
                Permission.objects.get(codename='add_seance', content_type=seance_ct),
                Permission.objects.get(codename='change_seance', content_type=seance_ct),
                Permission.objects.get(codename='delete_seance', content_type=seance_ct),
                Permission.objects.get(codename='view_seance', content_type=seance_ct),
                
                # Profils - Lecture seule (pour voir les clients)
                Permission.objects.get(codename='view_profil', content_type=profil_ct),
                
                # Notes clients - CRUD complet
                Permission.objects.get(codename='add_noteclient', content_type=note_ct),
                Permission.objects.get(codename='change_noteclient', content_type=note_ct),
                Permission.objects.get(codename='delete_noteclient', content_type=note_ct),
                Permission.objects.get(codename='view_noteclient', content_type=note_ct),
                
                # Créneaux - CRUD complet
                Permission.objects.get(codename='add_creneaudisponible', content_type=creneau_ct),
                Permission.objects.get(codename='change_creneaudisponible', content_type=creneau_ct),
                Permission.objects.get(codename='delete_creneaudisponible', content_type=creneau_ct),
                Permission.objects.get(codename='view_creneaudisponible', content_type=creneau_ct),
            ]

            # === PERMISSIONS CLIENT ===
            client_permissions = [
                # Séances - Lecture et ajout uniquement (pas de suppression)
                Permission.objects.get(codename='add_seance', content_type=seance_ct),
                Permission.objects.get(codename='view_seance', content_type=seance_ct),
                # Note: le client peut modifier ses propres séances (annulation)
                Permission.objects.get(codename='change_seance', content_type=seance_ct),
                
                # Profils - Lecture de son propre profil
                Permission.objects.get(codename='view_profil', content_type=profil_ct),
                
                # Créneaux - Lecture seule (pour voir les disponibilités)
                Permission.objects.get(codename='view_creneaudisponible', content_type=creneau_ct),
            ]

            # Assigner les permissions aux groupes
            coach_group.permissions.set(coach_permissions)
            client_group.permissions.set(client_permissions)

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Permissions configurées:\n'
                    f'   - Coach: {len(coach_permissions)} permissions\n'
                    f'   - Client: {len(client_permissions)} permissions'
                )
            )

            # Afficher le détail des permissions
            self.stdout.write('\n📋 DÉTAIL DES PERMISSIONS:')
            
            self.stdout.write('\n🎯 COACH peut:')
            for perm in coach_permissions:
                self.stdout.write(f'   - {perm.name}')
            
            self.stdout.write('\n👤 CLIENT peut:')
            for perm in client_permissions:
                self.stdout.write(f'   - {perm.name}')

        except Permission.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Permission non trouvée: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur: {e}')
            )
