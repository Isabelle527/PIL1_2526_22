import os
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash

# ==============================================================================
# 1. HACHAGE DES MOTS DE PASSE (Sécurisation des inscriptions & BDD)
# ==============================================================================
def hacher_mot_de_passe(mot_de_passe_brut):
    """
    Prend un mot de passe en texte clair et le transforme en empreinte (hash)
    sécurisée en utilisant l'algorithme PBKDF2 avec SHA256.
    À utiliser lors de l'inscription d'un nouvel utilisateur.
    """
    if not mot_de_passe_brut:
        return None
    return generate_password_hash(mot_de_passe_brut, method='pbkdf2:sha256')


def verifier_mot_de_passe(mot_de_passe_hache, mot_de_passe_brut):
    """
    Compare le mot de passe haché stocké dans la base de données avec le 
    mot de passe brut saisi par l'utilisateur dans le formulaire de connexion.
    Retourne True si ça correspond, False sinon.
    """
    if not mot_de_passe_hache or not mot_de_passe_brut:
        return False
    return check_password_hash(mot_de_passe_hache, mot_de_passe_brut)


# ==============================================================================
# 2. AUTHENTIFICATION & GESTION DES SESSIONS (Liaison Frontend / Backend)
# ==============================================================================
def connecter_utilisateur(session_obj, util_id, util_nom, util_prenom, util_role):
    """
    Initialise proprement les variables de session Flask après une authentification réussie.
    Permet au Frontend (profil.html, matching.html, messagerie.html) de savoir 
    qui est connecté et d'adapter les affichages dynamiquement.
    """
    session_obj.clear()  # Sécurité : Nettoyer toute ancienne session résiduelle
    session_obj['user_id'] = util_id
    session_obj['nom'] = util_nom
    session_obj['prenom'] = util_prenom
    session_obj['role'] = util_role       # Évite qu'un étudiant accède aux outils mentors (et vice-versa)
    session_obj.permanent = True          # Conserve la session selon la configuration de Flask


def verifier_acces_page(session_obj, role_requis=None):
    """
    Vérifie si l'utilisateur possède une session active et éventuellement le bon rôle.
    Retourne True si l'accès est autorisé, False si l'utilisateur doit être redirigé vers le login.
    """
    if 'user_id' not in session_obj:
        return False
    if role_requis and session_obj.get('role') != role_requis:
        return False
    return True


# ==============================================================================
# 3. PROTECTION CONTRE LES ERREURS ET ATTAQUES (Force Brute)
# ==============================================================================
def controler_tentatives_connexion(suivi_dict, email_saisi):
    """
    Enregistre et compte les échecs de connexion par adresse email.
    Aide à bloquer temporairement les tentatives malveillantes sur le formulaire.
    
    Retourne un tuple: (est_bloque, message_erreur)
    """
    tentatives = suivi_dict.get(email_saisi, 0) + 1
    suivi_dict[email_saisi] = tentatives
    
    if tentatives >= 5:
        return True, "Ce compte est temporairement bloqué après 5 tentatives infructueuses."
    
    restantes = 5 - tentatives
    return False, f"Identifiants incorrects. Il vous reste {restantes} tentatives avant le blocage."


# ==============================================================================
# 4. RÉINITIALISATION DU MOT DE PASSE (Sécurité des jetons d'oubli)
# ==============================================================================
def generer_token_reinitialisation():
    """
    Génère un jeton (token) cryptographique unique et hautement sécurisé de 64 caractères
    à insérer en BDD et à envoyer par mail pour l'option "Mot de passe oublié".
    """
    return os.urandom(32).hex()