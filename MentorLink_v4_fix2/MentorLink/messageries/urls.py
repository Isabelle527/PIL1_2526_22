from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('fonctionnalites/', views.fonctionnalites, name='fonctionnalites'),
    path('ressources/', views.ressources, name='ressources'),
    path('mentors/', views.mentors, name='mentors'),
    path('contact/', views.contact, name='contact'),
    path('conversations/', views.conversations, name='conversations'),
    path('messagerie/', views.messagerie, name='messagerie'),
    path('messagerie/send/<int:conversation_id>/', views.send_in_messagerie, name='send_in_messagerie'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('chat/<int:user_id>/', views.start_chat, name='start_chat'),
]
