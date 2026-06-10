from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import MentoratPost, Profile, NoteMatiere, Disponibilite

MATIERES_IFRI = [
    "Logique Arithmétique et Application",
    "Algèbre Linéaire et Application",
    "Analyse et Application",
    "Probabilité",
    "Statistique Inférentielle",
    "Architecture et Topologie des Réseaux",
    "Outils de Base en Informatique",
    "Utilisation et Administration Windows et Linux",
    "Algorithmique",
    "Langage C",
    "Déontologie et Droit liés aux TIC",
    "TEEO",
    "Administration Réseau sous Windows et Linux",
    "Théorie des Graphes et Application",
    "Recherche Opérationnelle",
    "Développement Web",
    "Infographie",
    "Algèbre Relationnelle",
    "SGBD et Langage SQL",
    "Programmation Python",
    "Anglais",
]


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Adresse e-mail')
    first_name = forms.CharField(required=True, label='Prénom', max_length=150)
    last_name = forms.CharField(required=True, label='Nom', max_length=150)
    telephone = forms.CharField(required=True, label='Numéro de téléphone', max_length=40)
    filiere = forms.ChoiceField(required=True, label='Filière', choices=[
        ('', '-- Choisir --'),
        ('Génie Logiciel', 'Génie Logiciel'),
        ('Réseaux & Télécommunications', 'Réseaux & Télécommunications'),
        ('Systèmes Informatiques', 'Systèmes Informatiques'),
        ('Intelligence Artificielle', 'Intelligence Artificielle'),
    ])
    niveau = forms.ChoiceField(required=True, label='Niveau', choices=[
        ('', '-- Choisir --'),
        ('Licence 1', 'Licence 1'), ('Licence 2', 'Licence 2'),
        ('Licence 3', 'Licence 3'), ('Master 1', 'Master 1'), ('Master 2', 'Master 2'),
    ])
    date_naissance = forms.DateField(required=True, label='Date de naissance',
                                     widget=forms.DateInput(attrs={'type': 'date'}))
    bio = forms.CharField(required=False, label='Bio courte', widget=forms.Textarea(attrs={'rows': 3}))

    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'email', 'username', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.filiere = self.cleaned_data['filiere']
            profile.niveau_etude = self.cleaned_data['niveau']
            profile.date_naissance = self.cleaned_data['date_naissance']
            profile.phone = self.cleaned_data['telephone']
            profile.bio = self.cleaned_data.get('bio', '')
            profile.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'photo', 'role', 'filiere', 'niveau_etude', 'promotion',
            'ue_fortes', 'ue_faibles', 'interets_academiques',
            'competences', 'disponibilites', 'identite_professionnelle',
            'style_mentorat', 'motivation', 'nb_mentees_accompagnees',
            'types_projets_mentores', 'phone', 'bio'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'identite_professionnelle': forms.Textarea(attrs={'rows': 3}),
            'motivation': forms.Textarea(attrs={'rows': 3}),
            'competences': forms.TextInput(attrs={'placeholder': 'Python, Gestion, Communication'}),
            'interets_academiques': forms.TextInput(attrs={'placeholder': 'Developpement web, UI/UX, Data Science'}),
            'ue_fortes': forms.TextInput(attrs={'placeholder': 'Algorithmique, Systemes, Base de donnees'}),
            'ue_faibles': forms.TextInput(attrs={'placeholder': 'Reseaux, Mathematiques, Projet'}),
            'types_projets_mentores': forms.TextInput(attrs={'placeholder': 'Web, Data Science, Mobile, etc.'}),
        }


class MentoratPostForm(forms.ModelForm):
    class Meta:
        model = MentoratPost
        fields = ['post_type', 'mentorat_type', 'title', 'description', 'filiere', 'competences', 'disponibilites']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class DisponibiliteForm(forms.ModelForm):
    class Meta:
        model = Disponibilite
        fields = ['jour', 'creneau']
        widgets = {
            'creneau': forms.TimeInput(attrs={'type': 'time'}),
        }
