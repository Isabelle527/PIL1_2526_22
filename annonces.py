import os
import MySQLdb.cursors
from flask import request, redirect, url_for, session, flash, render_template
from werkzeug.utils import secure_filename

# Configuration du dossier pour les images de profil
UPLOAD_FOLDER = 'static/uploads/profiles'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==============================================================================
# ENREGISTREMENT DES ROUTES DE LA PARTIE 2
# ==============================================================================
def init_routes_annonces(app, mysql):

    # 1. MODIFICATION DU PROFIL AVEC PHOTO
    @app.route('/profil/modifier', methods=['POST'])
    def modifier_profil_complet():
        if 'user_id' not in session:
            return redirect(url_for('login'))
            
        user_id = session['user_id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        telephone = request.form.get('telephone')
        filiere = request.form.get('filiere')
        niveau = request.form.get('niveau')
        bio = request.form.get('bio')
        
        file = request.files.get('photo')
        filename_db = None
        
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"user_{user_id}_{filename}"
            os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER), exist_ok=True)
            file.save(os.path.join(app.root_path, UPLOAD_FOLDER, unique_filename))
            filename_db = unique_filename

        if filename_db:
            cursor.execute("""
                UPDATE utilisateurs 
                SET nom=%s, prenom=%s, telephone=%s, filiere=%s, niveau=%s, bio=%s, photo=%s 
                WHERE id=%s
            """, (nom, prenom, telephone, filiere, niveau, bio, filename_db, user_id))
        else:
            cursor.execute("""
                UPDATE utilisateurs 
                SET nom=%s, prenom=%s, telephone=%s, filiere=%s, niveau=%s, bio=%s 
                WHERE id=%s
            """, (nom, prenom, telephone, filiere, niveau, bio, user_id))
            
        mysql.connection.commit()
        cursor.close()
        flash("Profil intégralement mis à jour !", "success")
        return redirect(url_for('profil'))

    # 2. CRUD : CRÉER ET LIRE LES ANNONCES
    @app.route('/annonces', methods=['GET', 'POST'])
    def gérer_annonces():
        if 'user_id' not in session:
            return redirect(url_for('login'))
            
        user_id = session['user_id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if request.method == 'POST':
            type_annonce = request.form.get('type_annonce')
            matiere = request.form.get('matiere')
            horaires = request.form.get('horaires')
            format_cours = request.form.get('format')
            description = request.form.get('description')
            
            cursor.execute("""
                INSERT INTO annonces (utilisateur_id, type_annonce, matiere, horaires, format, description)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, type_annonce, matiere, horaires, format_cours, description))
            mysql.connection.commit()
            flash("Votre annonce a été publiée !", "success")
            return redirect(url_for('gérer_annonces'))

        cursor.execute("""
            SELECT a.*, u.nom, u.prenom, u.photo, u.role, u.filiere 
            FROM annonces a
            JOIN utilisateurs u ON a.utilisateur_id = u.id
            ORDER BY a.date_publication DESC
        """)
        toutes_les_annonces = cursor.fetchall()
        cursor.close()
        return render_template('annonces.html', annonces=toutes_les_annonces)

    # 3. CRUD : SUPPRIMER UNE ANNONCE
    @app.route('/annonces/supprimer/<int:id_annonce>')
    def supprimer_annonce(id_annonce):
        if 'user_id' not in session:
            return redirect(url_for('login'))
            
        user_id = session['user_id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("DELETE FROM annonces WHERE id = %s AND utilisateur_id = %s", (id_annonce, user_id))
        mysql.connection.commit()
        cursor.close()
        flash("Annonce supprimée avec succès.", "info")
        return redirect(url_for('gérer_annonces'))

    # 4. MOTEUR DE RECHERCHE FILTRÉ
    @app.route('/annonces/recherche', methods=['GET'])
    def rechercher_annonces():
        if 'user_id' not in session:
            return redirect(url_for('login'))
            
        query = request.args.get('query', '').strip()
        type_filtre = request.args.get('type_annonce', '').strip()
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        sql = """
            SELECT a.*, u.nom, u.prenom, u.photo, u.role, u.competences 
            FROM annonces a
            JOIN utilisateurs u ON a.utilisateur_id = u.id
            WHERE 1=1
        """
        params = []
        
        if query:
            sql += " AND (a.matiere LIKE %s OR a.description LIKE %s OR u.competences LIKE %s)"
            like_query = f"%{query}%"
            params.extend([like_query, like_query, like_query])
            
        if type_filtre:
            sql += " AND a.type_annonce = %s"
            params.append(type_filtre)
            
        sql += " ORDER BY a.date_publication DESC"
        cursor.execute(sql, tuple(params))
        resultats = cursor.fetchall()
        cursor.close()
        return render_template('annonces.html', annonces=resultats, recherche_active=True, query=query)