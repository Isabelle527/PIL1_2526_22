from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

# --- Configuration de la base de données ---
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  
    'database': 'ifri_mentorlink'  
}

# =====================================================================
# --- 1. MOTEUR DE MATCHING HYBRIDE  ---
# =====================================================================

@app.route('/api/matching/<int:id_utilisateur>', methods=['GET'])
def executer_matching(id_utilisateur):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Récupérer les lacunes du demandeur
        cursor.execute("""
            SELECT c.nom_de_competence 
            FROM POSSEDER p
            JOIN COMPETENCE c ON p.id_Competence = c.Id_competence
            WHERE p.Id_Utilisateurs = %s AND p.type_relation = 'Mentore'
        """, (id_utilisateur,))
        lacunes = [row['nom_de_competence'].lower() for row in cursor.fetchall()]
        
        if not lacunes:
            cursor.close()
            conn.close()
            return jsonify({"message": "Aucune lacune enregistrée pour cet utilisateur."}), 404
            
        # Trouver tous les mentors possédant ces matières
        cursor.execute("""
            SELECT u.Id_Utilisateurs as mentor_id, u.nom, u.prenom, u.email, u.filiere,
                   c.nom_de_competence, p.note
            FROM POSSEDER p
            JOIN UTILISATEUR u ON p.Id_Utilisateurs = u.Id_Utilisateurs
            JOIN COMPETENCE c ON p.id_Competence = c.Id_competence
            WHERE p.Id_Utilisateurs != %s AND p.type_relation = 'Mentor'
        """, (id_utilisateur,))
        toutes_offres = cursor.fetchall()
        
        profils_mentors = {}
        for offre in toutes_offres:
            m_id = offre['mentor_id']
            if m_id not in profils_mentors:
                profils_mentors[m_id] = {
                    "mentor_id": m_id, "nom": offre['nom'], "prenom": offre['prenom'],
                    "email": offre['email'], "filiere": offre['filiere'], "competences": {}
                }
            profils_mentors[m_id]["competences"][offre['nom_de_competence'].lower()] = offre['note']
            
        liste_suggestions = []
        for m_id, mentor in profils_mentors.items():
            matieres_communes = [lacune for lacune in lacunes if lacune in mentor["competences"]]
            
            if matieres_communes:
                total_notes = sum(mentor["competences"][mat] for mat in matieres_communes)
                taux_couverture = len(matieres_communes) / len(lacunes)
                moyenne_note = total_notes / len(matieres_communes)
                
                score_final = round(taux_couverture * (moyenne_note / 10) * 100, 2)
                
                liste_suggestions.append({
                    "mentor_id": mentor["mentor_id"],
                    "nom": mentor["nom"],
                    "prenom": mentor["prenom"],
                    "email": mentor["email"],
                    "filiere": mentor["filiere"],
                    "matieres_partagees": ", ".join(matieres_communes),
                    "score": f"{score_final}%"
                })
                
        liste_suggestions = sorted(liste_suggestions, key=lambda x: float(x['score'].replace('%', '')), reverse=True)
        
        cursor.close()
        conn.close()
        return jsonify({"suggestions_mentors": liste_suggestions}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur technique : {str(e)}"}), 500


# =====================================================================
# --- 2. AUTHENTIFICATION & COMPTE  ---
# =====================================================================

@app.route('/api/auth/register', methods=['POST'])
def inscription():
    data = request.json
    nom = data.get('nom')
    prenom = data.get('prenom')
    email = data.get('email')
    mot_de_passe = data.get('mot_de_passe')
    telephone = data.get('telephone')
    filiere = data.get('filiere')
    statut_mentorat = data.get('statut_mentorat', 'Les deux')

    if not all([nom, prenom, email, mot_de_passe, telephone, filiere]):
        return jsonify({"error": "Champs obligatoires manquants"}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT Id_Utilisateurs FROM UTILISATEUR WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "Cet email existe déjà"}), 400

        requete = """
            INSERT INTO UTILISATEUR (nom, prenom, email, mot_de_passe, telephone, filiere, statut_mentorat)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(requete, (nom, prenom, email, mot_de_passe, telephone, filiere, statut_mentorat))
        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({"message": "Utilisateur créé avec succès !"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
# --- 3. GESTION DES SLIDERS / CONFIGURATION DE PROFIL ---
# =====================================================================

@app.route('/api/profil/<int:id_utilisateur>/competences', methods=['POST'])
def attribuer_note_competence(id_utilisateur):
    data = request.json
    id_competence = data.get('id_competence')
    type_relation = data.get('type_relation')
    note = data.get('note', 5)

    if not id_competence or not type_relation:
        return jsonify({"error": "id_competence et type_relation requis"}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        requete = """
            INSERT INTO POSSEDER (Id_Utilisateurs, id_Competence, type_relation, note)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE type_relation = VALUES(type_relation), note = VALUES(note)
        """
        cursor.execute(requete, (id_utilisateur, id_competence, type_relation, note))
        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({"message": "Configuration du curseur sauvegardée !"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
# --- 4. MESSAGERIE CONFORME AUX TABLES DE LIAISON  ---
# =====================================================================

@app.route('/api/messages/send', methods=['POST'])
def envoyer_message():
    data = request.json
    id_expediteur = data.get('id_expediteur')
    id_destinataire = data.get('id_destinataire')
    contenu = data.get('contenu')

    if not all([id_expediteur, id_destinataire, contenu]):
        return jsonify({"error": "Données de message incomplètes"}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 1. Insertion dans la table MESSAGE
        cursor.execute("INSERT INTO MESSAGE (contenu) VALUES (%s)", (contenu,))
        id_message = cursor.lastrowid

        # 2. Liaisons dans les tables pivots ENVOYER et RECEVOIR 
        cursor.execute("INSERT INTO ENVOYER (Id_Utilisateurs, Id_message) VALUES (%s, %s)", (id_expediteur, id_message))
        cursor.execute("INSERT INTO RECEVOIR (Id_Utilisateurs, Id_message) VALUES (%s, %s)", (id_destinataire, id_message))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Message envoyé avec succès !"}), 201
    except Exception as e:
        return jsonify({"error": f"Erreur de messagerie : {str(e)}"}), 500


@app.route('/api/messages/history', methods=['GET'])
def historique_messages():
    user1 = request.args.get('user1')
    user2 = request.args.get('user2')

    if not user1 or not user2:
        return jsonify({"error": "Paramètres user1 et user2 manquants"}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Extraction via jointures des tables pivots ENVOYER (e) et RECEVOIR (r)
        requete = """
            SELECT m.Id_message, m.contenu, m.date_envoi, e.Id_Utilisateurs as expediteur_id
            FROM MESSAGE m
            JOIN ENVOYER e ON m.Id_message = e.Id_message
            JOIN RECEVOIR r ON m.Id_message = r.Id_message
            WHERE (e.Id_Utilisateurs = %s AND r.Id_Utilisateurs = %s)
               OR (e.Id_Utilisateurs = %s AND r.Id_Utilisateurs = %s)
            ORDER BY m.date_envoi ASC
        """
        cursor.execute(requete, (user1, user2, user2, user1))
        historique = cursor.fetchall()

        cursor.close()
        conn.close()
        return jsonify({"historique": historique}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur d'historique : {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)