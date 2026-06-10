from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profil/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profil/<str:username>/', views.profile, name='user_profile'),
    path('modifier-profil/', views.edit_profile, name='edit_profile'),
    path('publier/', views.publier, name='publier'),
    path('recherche-mentors/', views.mentor_search, name='mentor_search'),
    path('mentors/', views.mentor_search, name='mentors'),
    path('annonces-compatibles/', views.matching_posts_search, name='matching_posts'),
    path('api/save-notes/', views.save_notes, name='save_notes'),
    path('api/disponibilites/', views.manage_disponibilites, name='manage_disponibilites'),
]
