from django.contrib import admin
from .models import Profile, MentoratPost

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'filiere', 'disponibilites', 'nb_mentees_accompagnees')
    search_fields = ('user__username', 'filiere', 'competences')
    fieldsets = (
        ('Utilisateur', {'fields': ('user', 'role')}),
        ('Academique', {'fields': ('filiere', 'niveau_etude', 'promotion', 'ue_fortes', 'ue_faibles', 'interets_academiques')}),
        ('Competences et disponibilites', {'fields': ('competences', 'disponibilites')}),
        ('Profil professionnel et mentorat', {'fields': ('identite_professionnelle', 'style_mentorat', 'motivation', 'nb_mentees_accompagnees', 'types_projets_mentores')}),
        ('Contact', {'fields': ('phone', 'bio')}),
    )


@admin.register(MentoratPost)
class MentoratPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'post_type', 'mentorat_type', 'filiere', 'created_at')
    list_filter = ('post_type', 'mentorat_type', 'filiere')
    search_fields = ('title', 'competences', 'description')
