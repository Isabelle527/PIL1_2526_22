import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
# Importation des fonctions de sécurité exclusives
from security import verifier_mot_de_passe, connecter_utilisateur, hacher_mot_de_passe
from annonces import init_routes_annonces

init_routes_annonces(app, mysql)

app = Flask(__name__)

# Clé secrète pour la gestion sécurisée des sessions Flask
app.secret_key = 'ifri_mentorlink_secret_key_2026'

# --------------------------------------------------------
# CONFIGURATION BASE DE DONNÉES (ifri_mentorlink)
# --------------------------------------------------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'ifri_mentorlink'

mysql = MySQL(app)

# --------------------------------------------------------
# ROUTE 1 : PAGE DE CONNEXION (LOGIN)
# --------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password_saisi = request.form.get('password')
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id, nom, prenom, mot_de_passe, role FROM utilisateurs WHERE email = %s", (email,))
        utilisateur = cursor.fetchone()
        cursor.close()
        
        if utilisateur:
            if verifier_mot_de_passe(utilisateur['mot_de_passe'], password_saisi):
                connecter_utilisateur(
                    session, 
                    utilisateur['id'], 
                    utilisateur['nom'], 
                    utilisateur['prenom'], 
                    utilisateur['role']
                )
                flash("Connexion réussie !", "success")
                return redirect(url_for('profil'))
            
        flash("Adresse email ou mot de passe incorrect.", "danger")
        
    return render_template('login.html')

# -------------------------------------------------------
# ROUTE 2 : PAGE DE PROFIL (MON PROFIL)
# --------------------------------------------------------
@app.route('/profil', methods=['GET', 'POST'])
def profil():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        telephone = request.form.get('telephone')
        filiere = request.form.get('filiere') # Ex: Génie Logiciel, Internet des Objets...
        niveau = request.form.get('niveau')
        competences = request.form.get('competences') # Séparées par des virgules
        bio = request.form.get('bio')
        
        cursor.execute("""
            UPDATE utilisateurs 
            SET nom = %s, prenom = %s, telephone = %s, filiere = %s, niveau = %s, competences = %s, bio = %s
            WHERE id = %s
        """, (nom, prenom, telephone, filiere, niveau, competences, bio, user_id))
        
        mysql.connection.commit()
        session['prenom'] = prenom
        flash("Votre profil a été mis à jour avec succès !", "success")

    cursor.execute("SELECT nom, prenom, email, telephone, filiere, niveau, competences, bio FROM utilisateurs WHERE id = %s", (user_id,))
    infos_user = cursor.fetchone()
    cursor.close()
    
    return render_template('profil.html', user=infos_user)

# --------------------------------------------------------
# ROUTE 3 : ALGORITHME DE MATCHING (MENTORS / ÉTUDIANTS)
# --------------------------------------------------------
@app.route('/matching')
def matching():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    user_role = session.get('role')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # 1. Récupérer les filières et compétences de l'utilisateur connecté
    cursor.execute("SELECT id, filiere, competences FROM utilisateurs WHERE id = %s", (user_id,))
    moi = cursor.fetchone()
    
    # 2. Déterminer le rôle ciblé pour le matching
    # Si je suis étudiant, je cherche un mentor. Si je suis mentor, je cherche des étudiants.
    cible_role = 'mentor' if user_role == 'etudiant' else 'etudiant'
    
    cursor.execute("SELECT id, nom, prenom, email, filiere, niveau, competences, bio FROM utilisateurs WHERE role = %s", (cible_role,))
    utilisateurs_cibles = cursor.fetchall()
    cursor.close()
    
    suggestions = []
    
    # 3. Calcul du score de matching
    for cible in utilisateurs_cibles:
        score = 0
        
        # Comparaison de la filière (Poids fort : 50 points)
        if moi['filiere'] and cible['filiere']:
            if moi['filiere'].strip().lower() == cible['filiere'].strip().lower():
                score += 50
                
        # Comparaison des compétences textuelles (Poids dynamique : 10 points par mot-clé commun)
        if moi['competences'] and cible['competences']:
            mes_comp = set([c.strip().lower() for c in moi['competences'].split(',') if c.strip()])
            ses_comp = set([c.strip().lower() for c in cible['competences'].split(',') if c.strip()])
            communes = mes_comp.intersection(ses_comp)
            score += len(communes) * 10
            
        # On n'ajoute que si un intérêt ou point commun minimal existe
        if score > 0:
            cible['score_match'] = score
            suggestions.append(cible)
            
    # Trier du score le plus fort au plus faible
    suggestions.sort(key=lambda x: x['score_match'], reverse=True)
    
    return render_template('matching.html', suggestions=suggestions)

# --------------------------------------------------------
# ROUTE 4 : SYSTÈME DE MESSAGERIE (DISCUSSIONS)
# --------------------------------------------------------
@app.route('/messagerie', methods=['GET', 'POST'])
@app.route('/messagerie/<int:destinataire_id>', methods=['GET', 'POST'])
def messagerie(destinataire_id=None):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Traitement de l'envoi d'un message (Frontend par formulaire ou AJAX)
    if request.method == 'POST' and destinataire_id:
        contenu = request.form.get('message')
        if contenu and contenu.strip() != "":
            cursor.execute("""
                INSERT INTO messages (expediteur_id, destinataire_id, contenu) 
                VALUES (%s, %s, %s)
            """, (user_id, destinataire_id, contenu.strip()))
            mysql.connection.commit()
            
            # Si c'est une requête AJAX, renvoyer du JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"status": "sent", "message": contenu})
                
            return redirect(url_for('messagerie', destinataire_id=destinataire_id))

    # 1. Récupérer la liste des utilisateurs avec qui on a discuté ou peut discuter
    cursor.execute("""
        SELECT DISTINCT id, nom, prenom, role 
        FROM utilisateurs 
        WHERE id != %s
    """, (user_id,))
    contacts = cursor.fetchall()
    
    # 2. Récupérer l'historique des messages si un contact est sélectionné
    conversations = []
    contact_actuel = None
    if destinataire_id:
        cursor.execute("SELECT id, nom, prenom FROM utilisateurs WHERE id = %s", (destinataire_id,))
        contact_actuel = cursor.fetchone()
        
        cursor.execute("""
            SELECT expediteur_id, destinataire_id, contenu, date_envoi 
            FROM messages 
            WHERE (expediteur_id = %s AND destinataire_id = %s) 
               OR (expediteur_id = %s AND destinataire_id = %s)
            ORDER BY date_envoi ASC
        """, (user_id, destinataire_id, destinataire_id, user_id))
        conversations = cursor.fetchall()
        
    cursor.close()
    return render_template('messagerie.html', contacts=contacts, conversations=conversations, contact_actuel=contact_actuel)

# --------------------------------------------------------
# ROUTE 5 : INTERFACE D'API POUR LES DISPONIBILITÉS DU CALENDRIER
# --------------------------------------------------------
@app.route('/api/disponibilites', methods=['GET', 'POST'])
def gerer_disponibilites():
    if 'user_id' not in session:
        return jsonify({"error": "Non autorisé"}), 401
        
    user_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if request.method == 'POST':
        donnees_dispo = request.get_json()
        cursor.execute("DELETE FROM disponibilites WHERE utilisateur_id = %s", (user_id,))
        
        for date_jour, tranches in donnees_dispo.items():
            for tranche in tranches:
                cursor.execute("""
                    INSERT INTO disponibilites (utilisateur_id, date_jour, tranche_horaire)
                    VALUES (%s, %s, %s)
                """, (user_id, date_jour, tranche))
                
        mysql.connection.commit()
        cursor.close()
        return jsonify({"status": "success", "message": "Disponibilités synchronisées !"})

    cursor.execute("SELECT date_jour, tranche_horaire FROM disponibilites WHERE utilisateur_id = %s", (user_id,))
    lignes = cursor.fetchall()
    cursor.close()
    
    structure_json = {}
    for ligne in lignes:
        date_str = str(ligne['date_jour'])
        if date_str not in structure_json:
            structure_json[date_str] = []
        structure_json[date_str].append(ligne['tranche_horaire'])
        
    return jsonify(structure_json)

# --------------------------------------------------------
# ROUTE 6 : DÉCONNEXION
# --------------------------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)