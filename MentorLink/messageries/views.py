from django.shortcuts import render

def home(request):
    return render(request, 'index.html')
from django.shortcuts import render

# --- LES NOUVELLES VUES À AJOUTER ---

def fonctionnalites(request):
    return render(request, 'fonctionnalites.html')

def mentors(request):
    return render(request, 'mentors.html')

def contact(request):
    return render(request, 'contact.html')

# Create your views here.
