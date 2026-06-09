import jwt
import datetime
from functools import wraps
from flask import request, jsonify
# Werkzeug est la bibliothèque standard intégrée à Flask pour la sécurité
from werkzeug.security import generate_password_hash, check_password_hash

# Clé secrète essentielle pour signer tes jetons (Tokens)
SECRET_KEY = 'ifri_mentorlink_secret_key_2026'

# ==============================================================================
# 1. PILIER HACHAGE : Gestion sécurisée des mots de passe (Inscription / Connexion)
# ==============================================================================

def hacher_mot_de_passe(mot_de_pass_brut):
    """Prend un mot de passe en texte clair et le transforme en chaîne hachée non décryptable."""
    return generate_password_hash(mot_de_pass_brut, method='pbkdf2:sha256')

def verifier_mot_de_passe(mot_de_passe_hache, mot_de_passe_saisi):
    """Compare le mot de passe saisi par l'utilisateur avec la version hachée en BDD."""
    return check_password_hash(mot_de_passe_hache, mot_de_passe_saisi)


# ==============================================================================
# 2. PILIER AUTHENTIFICATION : Génération et Vérification des Tokens (JWT)
# ==============================================================================

def generer_token_utilisateur(id_utilisateur):
    """Génère un jeton d'accès unique valide pendant 24 heures après une connexion réussie."""
    payload = {
        'id_utilisateurs': id_utilisateur,
        'exp': datetime.datetime.utcnow() + datetime.datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def token_required(f):
    """
    Décorateur pour sécuriser les routes privées (ex: l'accueil ou le matching).
    Vérifie la présence et la validité du Token dans les en-têtes de la requête.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Le token est généralement envoyé dans l'en-tête 'Authorization' sous la forme : Bearer <token>
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if len(auth_header.split(" ")) > 1:
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({
                'status': 'error',
                'message': 'Accès refusé. Le jeton d\'accès (token) est manquant !'
            }), 401

        try:
            # Décodage du token avec notre clé secrète
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user_id = data['id_utilisateurs']
        except jwt.ExpiredSignatureError:
            return jsonify({
                'status': 'error',
                'message': 'Le jeton a expiré. Veuillez vous reconnecter.'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'status': 'error',
                'message': 'Jeton invalide ou altéré.'
            }), 401

        # On passe l'ID de l'utilisateur connecté à la fonction de la route Flask
        return f(current_user_id, *args, **kwargs)
        
    return decorated


# ==============================================================================
# 3. PILIER RÉINITIALISATION : Gestion de l'option oubli de mot de passe
# ==============================================================================

def generer_token_recuperation(email_utilisateur):
    """Génère un token éphémère (valide 15 minutes) dédié uniquement à la réinitialisation."""
    payload = {
        'reset_email': email_utilisateur,
        'exp': datetime.datetime.utcnow() + datetime.datetime.timedelta(minutes=15)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verifier_token_recuperation(token):
    """Vérifie le token de récupération et extrait l'email associé s'il est valide."""
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return data['reset_email']
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None