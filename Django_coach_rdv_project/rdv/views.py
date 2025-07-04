from django.shortcuts import render

def accueil(request):
    """
    Vue pour afficher la page d'accueil.
    Accessible à tous les visiteurs, présente le coach, ses services et horaires.
    """
    return render(request, 'rdv/accueil.html')

