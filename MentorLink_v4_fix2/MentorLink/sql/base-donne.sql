DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS conversations;
DROP TABLE IF EXISTS matchs;
DROP TABLE IF EXISTS offres;
DROP TABLE IF EXISTS disponibilites;
DROP TABLE IF EXISTS notes_matieres;
DROP TABLE IF EXISTS profils;
DROP TABLE IF EXISTS utilisateurs;

CREATE TABLE IF NOT EXISTS utilisateurs(
    id_user         SERIAL PRIMARY KEY,
    nom             VARCHAR(150) NOT NULL,
    prenom          VARCHAR(150) NOT NULL,
    email           VARCHAR(100) UNIQUE NOT NULL,
    telephone       VARCHAR(40) UNIQUE NOT NULL,
    mot_de_passe    VARCHAR(255) NOT NULL,
    date_naissance  DATE,
    date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profils (
    id_prf      SERIAL PRIMARY KEY,
    id_user     INT REFERENCES utilisateurs(id_user) ON DELETE CASCADE,
    pseudo      VARCHAR(100),
    photo       VARCHAR(255),
    filiere     VARCHAR(100),
    niveau      VARCHAR(20),
    bio         TEXT,
    role        VARCHAR(20) DEFAULT 'both' CHECK (role IN ('mentor','mentee','both')),
    competences TEXT,
    disponibilites TEXT,
    identite_professionnelle TEXT,
    style_mentorat VARCHAR(200),
    motivation TEXT,
    nb_mentees_accompagnees INTEGER DEFAULT 0,
    types_projets_mentores TEXT
);

CREATE TABLE IF NOT EXISTS notes_matieres (
    id_user     INTEGER REFERENCES utilisateurs(id_user) ON DELETE CASCADE,
    matiere     VARCHAR(100) NOT NULL,
    note        INTEGER CHECK (note >= 1 AND note <= 10),
    PRIMARY KEY (id_user, matiere)
);

CREATE TABLE IF NOT EXISTS disponibilites (
    id_disp     SERIAL PRIMARY KEY,
    id_user     INTEGER REFERENCES utilisateurs(id_user) ON DELETE CASCADE,
    jour        VARCHAR(20) CHECK (jour IN ('Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi')),
    creneau     TIME
);

CREATE TABLE IF NOT EXISTS offres (
    id_of       SERIAL PRIMARY KEY,
    id_user     INTEGER REFERENCES utilisateurs(id_user) ON DELETE CASCADE,
    type        VARCHAR(20) CHECK (type IN ('offre','demande')),
    matiere     VARCHAR(100) NOT NULL,
    format      VARCHAR(20) CHECK (format IN ('presentiel','enligne','les deux')),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS matchs (
    id_ma       SERIAL PRIMARY KEY,
    id_mentor   INTEGER REFERENCES utilisateurs(id_user) ON DELETE CASCADE,
    id_mentore  INTEGER REFERENCES utilisateurs(id_user) ON DELETE CASCADE,
    score       NUMERIC(5,2),
    statut      VARCHAR(20) DEFAULT 'en attente' CHECK (statut IN ('en attente','accepte','refuse')),
    date_match  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    id_conv     SERIAL PRIMARY KEY,
    id_user1    INTEGER REFERENCES utilisateurs(id_user) ON DELETE CASCADE,
    id_user2    INTEGER REFERENCES utilisateurs(id_user) ON DELETE CASCADE,
    statut      VARCHAR(20) DEFAULT 'initiated' CHECK (statut IN ('initiated','scheduled','in_progress','completed')),
    objectif_initial TEXT,
    formulaire_initiation TEXT,
    creneaux_suggeres JSONB,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_maj    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id_mes      SERIAL PRIMARY KEY,
    id_conv     INTEGER REFERENCES conversations(id_conv) ON DELETE CASCADE,
    expediteur_id INTEGER REFERENCES utilisateurs(id_user) ON DELETE CASCADE,
    type        VARCHAR(30) DEFAULT 'text' CHECK (type IN ('text','slot_suggestion','goal_proposal','form_submission','system')),
    contenu     TEXT NOT NULL,
    date_envoi  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lu          BOOLEAN DEFAULT FALSE
);
