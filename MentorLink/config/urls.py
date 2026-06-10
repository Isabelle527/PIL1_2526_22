"""
URL configuration for config project.
"""
from django.urls import path
from messageries import views


urlpatterns = [
    # Ta route vers l'accueil actuelle
    path('', views.home, name='home'), 
    
    # --- LES NOUVELLES ROUTES À AJOUTER ---
    path('fonctionnalites/', views.fonctionnalites, name='fonctionnalites'),
    path('mentors/', views.mentors, name='mentors'),
    path('contact/', views.contact, name='contact'),
]