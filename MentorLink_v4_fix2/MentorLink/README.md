# IFRI MentorLink

Plateforme de mentorat académique et professionnel pour les étudiants et alumni de l'IFRI.

## Prérequis

- Python 3.10+
- pip

## Installation

```bash
# 1. Cloner le dépôt
git clone <url-du-depot>
cd MentorLink

# 2. Créer et activer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Appliquer les migrations et lancer
python migrate_and_run.py
```

L'application sera disponible sur http://127.0.0.1:8000

## Structure du projet

```
MentorLink/
├── config/          # Paramètres Django (settings, urls, wsgi, asgi)
├── comptes/         # App utilisateurs, profils, matching
├── messageries/     # App messagerie/conversations
├── templates/       # Templates HTML
├── static/          # CSS, images
├── sql/             # Scripts SQL de référence
├── manage.py        # Point d'entrée Django
└── migrate_and_run.py  # Script de démarrage rapide
```

## Fonctionnalités

- Inscription / Connexion
- Profils mentors et étudiants
- Matching intelligent par matière et disponibilité
- Messagerie en temps réel
- Tableau de bord personnalisé
- Ressources et conseils
