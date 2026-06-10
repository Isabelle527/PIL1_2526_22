# Système de Matching Intelligent - Documentation

## Vue d'ensemble

Le système de matching intelligent de MentorLink analyse les mentors/annonces en fonction de 4 critères pondérés pour fournir des recommandations pertinentes avec des explications détaillées.

## Les 4 Critères de Compatibilité

### 1. **Compatibilité Technique (30%)**
- **Évaluation** : Points communs dans les compétences
- **Calcul** : min(30, 10 × nombre de skills partagées)
- **Explication** : "maitrise [skill1, skill2, skill3...]"
- **Exemple** : Si l'utilisateur et le mentor partagent 2 skills (Python, Django), le score est 20/30

### 2. **Compatibilité Humaine (30%)**
- **Évaluation** : Proximité académique + expérience de mentorat
- **Composants** :
  - **Filière** :
    - Même filière : +15 points
    - Filière proche (même groupe) : +8 points
  - **Expérience** : min(15, nb_mentees_accompagnees × 3)
- **Explication** : 
  - "appartient a la meme filiere (Informatique)"
  - "appartient a une filiere proche (Data Science)"
  - "a accompagne 3 etudiants"
- **Score max** : 30/30

### 3. **Compatibilité Logistique (25%)**
- **Évaluation** : Chevauchement des disponibilités
- **Calcul** : Basé sur parse_availability() - créneau commun + jours communs
- **Score max** : 30 points (mais pondéré à 25% dans le total)
- **Explication** :
  - "est disponible a des horaires compatibles"
  - "a des creneaux compatibles"
- **Exemple** : Mentor disponible "Lundi-Vendredi 14h-18h" + étudiant "Lundi-Mercredi 15h-17h" = match sur lundi et mardi

### 4. **Compatibilité de Motivation (15%)**
- **Évaluation** : Alignement du type de mentorat + rôle
- **Calcul** : 
  - Offre mentor + demande étudiant = +10 points
  - Demande mentor + offre étudiant = +10 points
- **Explication** : 
  - "propose exactement ce que vous cherchez"
  - "cherche ce que vous pouvez offrir"
- **Score max** : 10/10

## Calcul du Score Final

```
Score pondéré = (
  Technique × 0.30 +
  Humain × 0.30 +
  Logistique × 0.25 +
  Motivation × 0.15
)

Score normalisé sur 100 = (Score pondéré / Max possible) × 100
```

## Exemple Complet

**Utilisateur** : Alice, Bac+3 Informatique, cherche mentor
- Compétences : Python, Django, API REST
- Disponibilités : Lundi-Mercredi 15h-18h
- Filière : Informatique

**Mentor1** : Bob, Master 2 Informatique
- Compétences : Python, Django, Machine Learning
- Disponibilités : Lundi-Vendredi 14h-19h
- Filière : Data Science (groupe tech)
- Expérience : 3 etudiants mentorés

**Calcul du match Alice → Bob** :

1. Technique : Python + Django = 2 skills → 20/30
2. Humain : 
   - Filière proche (tech) : 8 pts
   - Expérience : min(15, 3×3) = 9 pts
   - Total : 17/30
3. Logistique : Lundi 15h-18h commun, Mardi 15h-18h commun → 25/30
4. Motivation : Offre (Bob) + Demande (Alice) → 10/10

**Score pondéré** = (20×0.30) + (17×0.30) + (25×0.25) + (10×0.15)
                   = 6 + 5.1 + 6.25 + 1.5 = 18.85

**Score sur 100** ≈ **75/100**

**Explication** : "Ce mentor vous correspond parce qu'il maitrise Python, Django, appartient a une filiere proche (Data Science), a accompagne 3 etudiants et est disponible a des horaires compatibles."

## Champs Mentoring Enrichis

### Profile Model
- `nb_mentees_accompagnees` : Nombre d'étudiants mentorés (utilisé pour scoring)
- `types_projets_mentores` : Type de projets accompagnés (Web, Data Science, etc.)

### Types de Mentorat
1. **Survie académique** : Support sur le cursus, UE difficiles
2. **Orientation** : Aide au choix de parcours, carrière
3. **Projet** : Accompagnement sur projets concrets
4. **Insertion professionnelle** : Préparation à l'emploi, CV, entretiens
5. **Leadership** : Vie étudiante, leadership, engagement

## Intégration dans l'Interface

### Pages affectées
- **Matching Posts** : Affiche score + détails + explication
- **Dashboard** : Recommandations d'annonces avec explications
- **Profile** : Historique de mentorat affiché

### Format d'affichage
```html
<div class='small text-primary'>
  {{ post.intelligent_match.explanation }}
</div>
<div class='small text-muted'>
  <div>Technique : 20/30</div>
  <div>Humain : 17/30</div>
  <div>Logistique : 25/30</div>
  <div>Motivation : 10/10</div>
</div>
```

## Avantages

✓ **Transparent** : Explications claires du pourquoi du match
✓ **Multi-critères** : Évaluation complète (technique, humain, pratique, volonté)
✓ **Pondéré** : Priorité à la compatibilité technique et humaine
✓ **Contextuel** : Prend en compte expérience et historique
✓ **Explicite** : Chaque critère contribue à la recommandation finale
