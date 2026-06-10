import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.contrib.auth.models import User
from comptes.models import Profile, MentoratPost
from messageries.models import Conversation, Message, ContactMessage

# Supprime les données existantes si nécessaire
print('Cleaning existing demo users and contact messages...')
User.objects.filter(username__in=['mentor1', 'mentor2', 'mentee1', 'mentee2', 'admin']).delete()
ContactMessage.objects.all().delete()
Conversation.objects.all().delete()

# Crée des utilisateurs
print('Creating demo users...')
users = {
    'mentor1': {'email': 'mentor1@ifri.com', 'password': 'Mentor123!', 'role': 'mentor', 'filiere': 'Informatique', 'competences': 'Python, Django, IA', 'disponibilites': 'Lundi-Vendredi 14h-18h', 'bio': 'Mentor en développement web et IA.'},
    'mentor2': {'email': 'mentor2@ifri.com', 'password': 'Mentor123!', 'role': 'both', 'filiere': 'Data Science', 'competences': 'Data Mining, Machine Learning, SQL', 'disponibilites': 'Mardi-Jeudi 10h-16h', 'bio': 'Expert data science prêt à accompagner.'},
    'mentee1': {'email': 'mentee1@ifri.com', 'password': 'Mentee123!', 'role': 'mentee', 'filiere': 'Informatique', 'competences': 'Java, C++, Réseaux', 'disponibilites': 'Lundi-Mercredi 9h-12h', 'bio': 'Étudiant cherche coach technique.'},
    'mentee2': {'email': 'mentee2@ifri.com', 'password': 'Mentee123!', 'role': 'both', 'filiere': 'Marketing', 'competences': 'SEO, Réseaux sociaux, Communication', 'disponibilites': 'Mercredi-Vendredi 14h-18h', 'bio': 'Je souhaite construire un projet commun.'},
    'admin': {'email': 'admin@ifri.com', 'password': 'Admin123!', 'role': 'both', 'filiere': 'Management', 'competences': 'Leadership, Projet, Stratégie', 'disponibilites': 'Lundi-Vendredi 9h-17h', 'bio': 'Administrateur de test.'},
}

for username, data in users.items():
    user = User.objects.create_user(username=username, email=data['email'], password=data['password'])
    profile = user.profile
    profile.role = data['role']
    profile.filiere = data['filiere']
    profile.competences = data['competences']
    profile.disponibilites = data['disponibilites']
    profile.bio = data['bio']
    
    # Add mentoring experience for mentors
    if username == 'mentor1':
        profile.nb_mentees_accompagnees = 3
        profile.types_projets_mentores = 'Web, API, Database'
    elif username == 'mentor2':
        profile.nb_mentees_accompagnees = 5
        profile.types_projets_mentores = 'Data Analysis, Machine Learning, SQL'
    
    profile.save()

# Crée des annonces de mentorat
print('Creating demo posts...')
posts = [
    {
        'author': User.objects.get(username='mentor1'),
        'post_type': 'offre',
        'mentorat_type': 'projet',
        'title': 'Mentorat Python et Django',
        'description': 'Je propose un accompagnement en développement web avec Python/Django.',
        'filiere': 'Informatique',
        'competences': 'Python, Django, HTML, CSS',
        'disponibilites': 'Lundi 14h-18h, Mercredi 14h-18h',
    },
    {
        'author': User.objects.get(username='mentor2'),
        'post_type': 'offre',
        'mentorat_type': 'insertion',
        'title': 'Mentorat en Data Science',
        'description': 'Assistance en machine learning et SQL.',
        'filiere': 'Data Science',
        'competences': 'Data Science, ML, SQL',
        'disponibilites': 'Mardi 10h-16h, Jeudi 10h-16h',
    },
    {
        'author': User.objects.get(username='mentee1'),
        'post_type': 'demande',
        'mentorat_type': 'survie',
        'title': 'Recherche mentor technique',
        'description': 'Je souhaite être guidé sur mes projets en informatique.',
        'filiere': 'Informatique',
        'competences': 'Java, C++, Réseaux',
        'disponibilites': 'Lundi-Mercredi 9h-12h',
    },
    {
        'author': User.objects.get(username='mentee2'),
        'post_type': 'demande',
        'mentorat_type': 'orientation',
        'title': 'Recherche mentor en marketing digital',
        'description': 'Besoin de mentor pour stratégie réseaux sociaux et SEO.',
        'filiere': 'Marketing',
        'competences': 'SEO, Social Media, Communication',
        'disponibilites': 'Mercredi-Vendredi 14h-18h',
    }
]
for post_data in posts:
    MentoratPost.objects.create(**post_data)

# Crée quelques conversations et messages
print('Creating demo conversations...')
conv = Conversation.objects.create()
conv.participants.add(User.objects.get(username='mentor1'), User.objects.get(username='mentee1'))
Message.objects.create(conversation=conv, sender=User.objects.get(username='mentor1'), body='Bonjour ! Ravi de te rencontrer, comment puis-je t’aider ?')
Message.objects.create(conversation=conv, sender=User.objects.get(username='mentee1'), body='Bonjour, je cherche du soutien sur un projet Python.')

# Crée quelques messages de contact
print('Creating demo contact messages...')
ContactMessage.objects.create(name='Étudiant IFRI', email='etudiant@ifri.com', subject='Question sur le mentorat', message='Comment fonctionne le matching des mentors ?')
ContactMessage.objects.create(name='Professionnel', email='pro@ifri.com', subject='Proposition de partenariat', message='J’aimerais proposer un partenariat pour des sessions de mentorat.')

print('Demo data created successfully.')
