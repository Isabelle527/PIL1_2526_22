import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector # Le nouveau connecteur officiel
# Importation de tes modules séparés
from security import verifier_mot_de_passe, connecter_utilisateur, hacher_mot_de_passe
from annonces import init_routes_annonces

app = Flask(__name__)
app.secret_key = 'ifri_mentorlink_secret_key_2026'

# --------------------------------------------------------
# NOUVELLE FONCTION DE CONNEXION À LA BASE DE DONNÉES
# --------------------------------------------------------
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='ifri_mentorlink'
    )

# --------------------------------------------------------
# ROUTE 1 : PAGE DE CONNEXION (LOGIN)
# --------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password_saisi = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nom, prenom, mot_de_passe, role FROM utilisateurs WHERE email = %s", (email,))
        utilisateur = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if utilisateur:
            if verifier_mot_de_passe(utilisateur['mot_de_passe'], password_saisi):
                connecter_utilisateur(session, utilisateur['id'], utilisateur['nom'], utilisateur['prenom'], utilisateur['role'])
                flash("Connexion réussie !", "success")
                return redirect(url_for('profil'))
            
        flash("Adresse email ou mot de passe incorrect.", "danger")
        
    return render_template('login.html')

# --------------------------------------------------------
# ROUTE 2 : PAGE DE PROFIL
# --------------------------------------------------------
@app.route('/profil', methods=['GET'])
def profil():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT nom, prenom, email, telephone, filiere, niveau, competences, bio FROM utilisateurs WHERE id = %s", (user_id,))
    infos_user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return render_template('profil.html', user=infos_user)

# --------------------------------------------------------
# ROUTE 3 : ALGORITHME DE MATCHING
# --------------------------------------------------------
@app.route('/matching')
def matching():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    user_role = session.get('role')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id, filiere, competences FROM utilisateurs WHERE id = %s", (user_id,))
    moi = cursor.fetchone()
    
    cible_role = 'mentor' if user_role == 'etudiant' else 'etudiant'
    
    cursor.execute("SELECT id, nom, prenom, email, filiere, niveau, competences, bio FROM utilisateurs WHERE role = %s", (cible_role,))
    utilisateurs_cibles = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    suggestions = []
    
    for cible in utilisateurs_cibles:
        score = 0
        if moi['filiere'] and cible['filiere']:
            if moi['filiere'].strip().lower() == cible['filiere'].strip().lower():
                score += 50
                
        if moi['competences'] and cible['competences']:
            mes_comp = set([c.strip().lower() for c in moi['competences'].split(',') if c.strip()])
            ses_comp = set([c.strip().lower() for c in cible['competences'].split(',') if c.strip()])
            communes = mes_comp.intersection(ses_comp)
            score += len(communes) * 10
            
        if score > 0:
            cible['score_match'] = score
            suggestions.append(cible)
            
    suggestions.sort(key=lambda x: x['score_match'], reverse=True)
    
    return render_template('matching.html', suggestions=suggestions)

# --------------------------------------------------------
# ROUTE 4 : MESSAGERIE
# --------------------------------------------------------
@app.route('/messagerie', methods=['GET', 'POST'])
@app.route('/messagerie/<int:destinataire_id>', methods=['GET', 'POST'])
def messagerie(destinataire_id=None):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST' and destinataire_id:
        contenu = request.form.get('message')
        if contenu and contenu.strip() != "":
            cursor.execute("""
                INSERT INTO messages (expediteur_id, destinataire_id, contenu) 
                VALUES (%s, %s, %s)
            """, (user_id, destinataire_id, contenu.strip()))
            conn.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                cursor.close()
                conn.close()
                return jsonify({"status": "sent", "message": contenu})
                
            cursor.close()
            conn.close()
            return redirect(url_for('messagerie', destinataire_id=destinataire_id))

    cursor.execute("""
        SELECT DISTINCT id, nom, prenom, role 
        FROM utilisateurs 
        WHERE id != %s
    """, (user_id,))
    contacts = cursor.fetchall()
    
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
    conn.close()
    return render_template('messagerie.html', contacts=contacts, conversations=conversations, contact_actuel=contact_actuel)

# --------------------------------------------------------
# ROUTE 5 : DÉCONNEXION
# --------------------------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --------------------------------------------------------
# INITIALISATION DES AUTRES MODULES
# --------------------------------------------------------
# On transmet l'application et la fonction de connexion à la base de données
init_routes_annonces(app, get_db_connection)

if __name__ == '__main__':
    app.run(debug=True, port=5000)