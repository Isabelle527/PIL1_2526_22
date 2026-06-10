import json
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from messageries.models import Conversation
from .forms import MentoratPostForm, ProfileForm, UserRegisterForm, DisponibiliteForm
from .models import MentoratPost, Profile, NoteMatiere, Disponibilite, availability_matches_query

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


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Enregistrer les notes des matières
            for matiere in MATIERES_IFRI:
                field_key = f"note_{matiere}"
                note_val = request.POST.get(field_key)
                if note_val is not None:
                    try:
                        note_int = int(note_val)
                        if 1 <= note_int <= 10:
                            NoteMatiere.objects.update_or_create(
                                user=user, matiere=matiere,
                                defaults={'note': note_int}
                            )
                    except (ValueError, TypeError):
                        pass
            login(request, user)
            messages.success(request, 'Bienvenue ! Ton compte a été créé avec succès.')
            return redirect('profile')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form, 'matieres': MATIERES_IFRI})


def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    return render(request, 'login.html')


def logout_user(request):
    logout(request)
    messages.success(request, 'Tu es bien déconnecté.')
    return redirect('home')


@login_required
def profile(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    profile = get_object_or_404(Profile, user=user)
    posts = MentoratPost.objects.filter(author=user).order_by('-created_at')
    notes = NoteMatiere.objects.filter(user=user).order_by('matiere')
    disponibilites = Disponibilite.objects.filter(user=user).order_by('jour', 'creneau')

    matching_posts = []
    if user == request.user:
        other_posts = MentoratPost.objects.exclude(author=request.user).order_by('-created_at')
        matching_posts = list(other_posts)
        for post in matching_posts:
            post.match_score = post.match_score_for_profile(profile)
            post.match_details = post.match_details_for_profile(profile)
        matching_posts.sort(key=lambda post: post.match_score, reverse=True)

    return render(request, 'profile.html', {
        'profile': profile,
        'posts': posts,
        'matching_posts': matching_posts,
        'notes': notes,
        'disponibilites': disponibilites,
        'matieres': MATIERES_IFRI,
        'form': ProfileForm(instance=profile),
    })


@login_required
def dashboard(request):
    profile = get_object_or_404(Profile, user=request.user)
    posts = MentoratPost.objects.filter(author=request.user).order_by('-created_at')

    recommended_posts = list(MentoratPost.objects.exclude(author=request.user).order_by('-created_at'))
    for post in recommended_posts:
        post.match_score = post.match_score_for_profile(profile)
        post.match_details = post.match_details_for_profile(profile)
        post.intelligent_match = post.intelligent_match_for_profile(profile)
    recommended_posts.sort(key=lambda post: post.intelligent_match['score'], reverse=True)
    recommended_posts = recommended_posts[:4]

    mentors = list(Profile.objects.exclude(user=request.user).filter(role__in=['mentor', 'both']).order_by('-created_at'))
    for mentor in mentors:
        mentor.match_score = profile.compatibility_score_with(mentor)
        mentor.star_score = profile.complementarity_star_score(mentor)
        mentor.star_display = profile.complementarity_stars_display(mentor)
    recommended_mentors = sorted(mentors, key=lambda mentor: mentor.match_score, reverse=True)[:4]

    recent_posts = MentoratPost.objects.exclude(author=request.user).order_by('-created_at')[:4]
    for post in recent_posts:
        post.intelligent_match = post.intelligent_match_for_profile(profile)

    conversations = request.user.conversations.order_by('-updated_at')[:4]

    return render(request, 'dashboard.html', {
        'profile': profile,
        'posts': posts,
        'recommended_posts': recommended_posts,
        'recommended_mentors': recommended_mentors,
        'recent_posts': recent_posts,
        'conversations': conversations,
    })


@login_required
def matching_posts_search(request):
    profile = getattr(request.user, 'profile', None)
    query = request.GET.get('q', '')
    filiere = request.GET.get('filiere', '')
    availability = request.GET.get('availability', '')
    author_role = request.GET.get('author_role', 'all')
    post_type = request.GET.get('type', '')
    mentorat_type = request.GET.get('mentorat_type', '')

    posts = []
    if profile:
        posts_queryset = MentoratPost.objects.exclude(author=request.user).order_by('-created_at')
        if filiere:
            posts_queryset = posts_queryset.filter(filiere__icontains=filiere)
        if post_type in ['offre', 'demande']:
            posts_queryset = posts_queryset.filter(post_type=post_type)
        if mentorat_type:
            posts_queryset = posts_queryset.filter(mentorat_type=mentorat_type)
        if author_role == 'mentor':
            posts_queryset = posts_queryset.filter(author__profile__role__in=['mentor', 'both'])
        elif author_role == 'mentee':
            posts_queryset = posts_queryset.filter(author__profile__role__in=['mentee', 'both'])
        if query:
            posts_queryset = posts_queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(competences__icontains=query)
            )
        posts = list(posts_queryset)
        if availability:
            posts = [post for post in posts if availability_matches_query(post.disponibilites, availability)]
        for post in posts:
            post.match_score = post.match_score_for_profile(profile)
            post.match_details = post.match_details_for_profile(profile)
            post.intelligent_match = post.intelligent_match_for_profile(profile)
        posts.sort(key=lambda post: post.intelligent_match['score'], reverse=True)

    return render(request, 'matching_posts.html', {
        'posts': posts,
        'query': query,
        'filiere': filiere,
        'availability': availability,
        'author_role': author_role,
        'post_type': post_type,
        'mentorat_type': mentorat_type,
        'current_profile': profile,
    })


@login_required
def edit_profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        # Si c'est uniquement un changement de photo (formulaire avatar)
        if 'photo' in request.FILES and request.POST.get('photo_only') == '1':
            profile.photo = request.FILES['photo']
            profile.save(update_fields=['photo'])
            messages.success(request, 'Photo de profil mise à jour.')
            return redirect('profile')
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            saved_profile = form.save(commit=False)
            # Mettre à jour les champs User aussi
            user = request.user
            if request.POST.get('first_name'):
                user.first_name = request.POST['first_name']
            if request.POST.get('last_name'):
                user.last_name = request.POST['last_name']
            if request.POST.get('email'):
                user.email = request.POST['email']
            user.save()
            saved_profile.save()
            messages.success(request, 'Ton profil a été mis à jour.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    notes = NoteMatiere.objects.filter(user=request.user).order_by('matiere')
    disponibilites = Disponibilite.objects.filter(user=request.user).order_by('jour', 'creneau')
    return render(request, 'profile.html', {
        'form': form,
        'profile': profile,
        'editing': True,
        'notes': notes,
        'disponibilites': disponibilites,
        'matieres': MATIERES_IFRI,
    })


@login_required
def publier(request):
    if request.method == 'POST':
        form = MentoratPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Ton annonce a été publiée.')
            return redirect('profile')
    else:
        form = MentoratPostForm()
    profile = get_object_or_404(Profile, user=request.user)
    notes = NoteMatiere.objects.filter(user=request.user).order_by('matiere')
    disponibilites = Disponibilite.objects.filter(user=request.user).order_by('jour', 'creneau')
    return render(request, 'profile.html', {
        'form': ProfileForm(instance=profile),
        'publish': True,
        'profile': profile,
        'notes': notes,
        'disponibilites': disponibilites,
        'matieres': MATIERES_IFRI,
    })


def mentor_search(request):
    query = request.GET.get('q', '')
    filiere = request.GET.get('filiere', '')
    niveau = request.GET.get('niveau', '')
    availability = request.GET.get('availability', '')
    role = request.GET.get('role', 'mentor')

    mentors = []
    current_profile = None
    recommended_mentors = []
    error_message = None

    try:
        mentors_qs = Profile.objects.order_by('-created_at')

        if role == 'mentor':
            mentors_qs = mentors_qs.filter(role__in=['mentor', 'both'])
        elif role == 'mentee':
            mentors_qs = mentors_qs.filter(role__in=['mentee', 'both'])

        if filiere:
            mentors_qs = mentors_qs.filter(filiere__icontains=filiere)
        if niveau:
            mentors_qs = mentors_qs.filter(niveau_etude__icontains=niveau)
        if query:
            mentors_qs = mentors_qs.filter(
                Q(competences__icontains=query) |
                Q(user__username__icontains=query) |
                Q(bio__icontains=query)
            )

        if request.user.is_authenticated:
            try:
                current_profile = request.user.profile
            except Profile.DoesNotExist:
                current_profile = None

        if current_profile:
            mentors = list(mentors_qs)
            if availability:
                mentors = [m for m in mentors if availability_matches_query(m.disponibilites, availability)]
            for mentor in mentors:
                mentor.match_score = current_profile.compatibility_score_with(mentor)
                mentor.match_details = current_profile.compatibility_details_with(mentor)
                mentor.star_score = current_profile.complementarity_star_score(mentor)
                mentor.star_display = current_profile.complementarity_stars_display(mentor)
            mentors.sort(key=lambda p: p.match_score, reverse=True)
            recommended_mentors = mentors[:1]
        else:
            mentors = list(mentors_qs)

    except Exception:
        error_message = 'La base de données n\'est pas encore initialisée. Exécute : python manage.py migrate'
        mentors = []

    return render(request, 'mentors.html', {
        'mentors': mentors,
        'query': query,
        'filiere': filiere,
        'niveau': niveau,
        'availability': availability,
        'role': role,
        'current_profile': current_profile,
        'recommended_mentors': recommended_mentors,
        'error_message': error_message,
    })


@login_required
@require_POST
def save_notes(request):
    """Enregistre les notes sur 10 pour les matières"""
    try:
        data = json.loads(request.body)
        notes = data.get('notes', {})
        for matiere, note in notes.items():
            try:
                note_int = int(note)
                if 1 <= note_int <= 10:
                    NoteMatiere.objects.update_or_create(
                        user=request.user, matiere=matiere,
                        defaults={'note': note_int}
                    )
            except (ValueError, TypeError):
                pass
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def manage_disponibilites(request):
    """Gère les disponibilités via calendrier"""
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            form = DisponibiliteForm(request.POST)
            if form.is_valid():
                disp = form.save(commit=False)
                disp.user = request.user
                disp.save()
                return JsonResponse({'status': 'ok', 'id': disp.id, 'jour': disp.jour, 'creneau': str(disp.creneau)})
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
        elif action == 'delete':
            disp_id = request.POST.get('id')
            Disponibilite.objects.filter(id=disp_id, user=request.user).delete()
            return JsonResponse({'status': 'ok'})
    disps = list(Disponibilite.objects.filter(user=request.user).values('id', 'jour', 'creneau'))
    return JsonResponse({'disponibilites': disps})
