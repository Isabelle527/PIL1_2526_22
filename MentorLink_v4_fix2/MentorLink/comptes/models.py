import re

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

DAY_ORDER = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
DAY_RANGE_RE = re.compile(
    r'(?P<start>lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\s*(?:[-–—]|au|à|a)\s*(?P<end>lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)'
)
DAY_RE = re.compile(r'\b(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\b')
TIME_RANGE_RE = re.compile(r'(\d{1,2})(?:h|:)?(\d{2})?\s*[-–—]\s*(\d{1,2})(?:h|:)?(\d{2})?')
ALL_DAY_RE = re.compile(r'\b(journée|journee|toute la journée|toute la journee|all day|journée entière|journee entiere)\b')


def normalize_text(text):
    return re.sub(r'[^a-z0-9\s]', ' ', text.lower()).strip()


def parse_time_token(token):
    token = token.strip()
    match = re.match(r'^(\d{1,2})(?:h|:)?(\d{2})?$', token)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    return max(0, min(23, hour)) * 60 + max(0, min(59, minute))


def expand_day_range(start, end):
    start = start.lower()
    end = end.lower()
    if start not in DAY_ORDER or end not in DAY_ORDER:
        return []
    start_index = DAY_ORDER.index(start)
    end_index = DAY_ORDER.index(end)
    if start_index <= end_index:
        return DAY_ORDER[start_index:end_index + 1]
    return DAY_ORDER[start_index:] + DAY_ORDER[:end_index + 1]


def parse_availability(text):
    if not text:
        return []

    cleaned = normalize_text(text)
    cleaned = cleaned.replace(',', ' | ').replace(';', ' | ').replace('/', ' | ').replace('\\', ' | ')
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    parts = [part.strip() for part in cleaned.split('|') if part.strip()]

    slots = []
    for part in parts:
        days = []
        for day_range in DAY_RANGE_RE.finditer(part):
            days.extend(expand_day_range(day_range.group('start'), day_range.group('end')))

        if not days:
            days = [match.group(1) for match in DAY_RE.finditer(part)]

        times = []
        for match in TIME_RANGE_RE.finditer(part):
            start = parse_time_token(match.group(1) + (match.group(2) or ''))
            end = parse_time_token(match.group(3) + (match.group(4) or ''))
            if start is not None and end is not None:
                if end <= start:
                    end = min(start + 60, 23 * 60 + 59)
                times.append((start, end))

        if not days and ALL_DAY_RE.search(part):
            days = DAY_ORDER.copy()

        if not days and times:
            days = DAY_ORDER.copy()

        if days and not times:
            for day in days:
                slots.append({'day': day, 'start': 0, 'end': 24 * 60})
            continue

        for day in days:
            for start, end in times:
                slots.append({'day': day, 'start': start, 'end': end})

    return slots


def availability_overlap_score(slots_a, slots_b):
    if not slots_a or not slots_b:
        return 0

    days_a = {slot['day'] for slot in slots_a}
    days_b = {slot['day'] for slot in slots_b}
    common_days = days_a & days_b
    day_score = min(10, 5 * len(common_days))

    time_score = 0
    for slot_a in slots_a:
        for slot_b in slots_b:
            if slot_a['day'] != slot_b['day']:
                continue
            overlap = min(slot_a['end'], slot_b['end']) - max(slot_a['start'], slot_b['start'])
            if overlap > 0:
                time_score = 20
                break
        if time_score:
            break

    return day_score + time_score


def availability_matches_query(subject_text, query_text):
    if not query_text:
        return True
    if not subject_text:
        return False

    normalized_query = normalize_text(query_text)
    normalized_subject = normalize_text(subject_text)
    if normalized_query in normalized_subject:
        return True

    query_slots = parse_availability(query_text)
    subject_slots = parse_availability(subject_text)
    return availability_overlap_score(query_slots, subject_slots) > 0


class Profile(models.Model):
    ROLE_CHOICES = [
        ('mentor', 'Mentor'),
        ('mentee', 'Mentoré'),
        ('both', 'Mentor/Bénéficiaire'),
    ]

    FILIERE_CHOICES = [
        ('Informatique', 'Informatique'),
        ('Data Science', 'Data Science'),
        ('Finance', 'Finance'),
        ('Management', 'Management'),
        ('Marketing', 'Marketing'),
        ('Design', 'Design'),
        ('Cybersécurité', 'Cybersécurité'),
    ]

    FILIERE_GROUPS = {
        'Informatique': 'tech',
        'Data Science': 'tech',
        'Cybersécurité': 'tech',
        'Finance': 'business',
        'Management': 'business',
        'Marketing': 'business',
        'Design': 'creative',
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='both')
    filiere = models.CharField(max_length=120, choices=FILIERE_CHOICES, default='Informatique')
    niveau_etude = models.CharField(max_length=120, blank=True, help_text='Ex: Bac+3, Master 1, année 2')
    promotion = models.CharField(max_length=120, blank=True, help_text='Ex: Promo 2026, Promo 2027')
    ue_fortes = models.CharField(max_length=300, blank=True, help_text='Unités d’enseignement fortes, séparées par des virgules')
    ue_faibles = models.CharField(max_length=300, blank=True, help_text='Unités d’enseignement à renforcer, séparées par des virgules')
    interets_academiques = models.CharField(max_length=300, blank=True, help_text='Ex: développement web, UI/UX, data science, algorithmique')
    competences = models.CharField(max_length=300, blank=True, help_text='Sépare les compétences par des virgules')
    disponibilites = models.CharField(max_length=120, blank=True, default='Lundi-Vendredi')
    identite_professionnelle = models.TextField(blank=True, help_text='Raconte ton identité professionnelle ou tes objectifs de carrière')
    style_mentorat = models.CharField(max_length=200, blank=True, help_text='Décris ton style de mentorat ou d’accompagnement')
    motivation = models.TextField(blank=True, help_text='Pourquoi tu veux participer au mentorat et quels objectifs tu vises')
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True, help_text='Photo de profil')
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    nb_mentees_accompagnees = models.PositiveIntegerField(default=0, help_text="Nombre d'etudiants mentores")
    types_projets_mentores = models.CharField(max_length=300, blank=True, help_text="Types de projets accompagnes (separes par des virgules)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

    def skills_list(self):
        return [skill.strip().lower() for skill in self.competences.split(',') if skill.strip()]

    def filiere_group(self):
        return self.FILIERE_GROUPS.get(self.filiere, 'autre')

    def filiere_score(self, other):
        if self.filiere == other.filiere:
            return 40
        if self.filiere_group() == other.filiere_group():
            return 20
        return 0

    def availability_score(self, other):
        my_slots = parse_availability(self.disponibilites)
        other_slots = parse_availability(other.disponibilites)
        return availability_overlap_score(my_slots, other_slots)

    def skills_score(self, other):
        shared = set(self.skills_list()) & set(other.skills_list())
        return min(30, 10 * len(shared))

    def compatibility_score_with(self, other):
        score = 0
        score += self.filiere_score(other)
        score += self.skills_score(other)
        score += self.availability_score(other)
        return score

    def complementarity_star_score(self, other):
        """
        Score de complémentarité mentor↔mentoré sur 5 étoiles.
        Logique : plus le mentor est fort là où le mentoré est faible (et vice versa),
        plus le score est élevé. La disponibilité commune booste également le score.

        Retourne un float entre 0.0 et 5.0.
        """
        # 1. Notes matières : récupérer les notes des deux utilisateurs
        notes_self = {n.matiere: n.note for n in NoteMatiere.objects.filter(user=self.user)}
        notes_other = {n.matiere: n.note for n in NoteMatiere.objects.filter(user=other.user)}

        # 2. Score de complémentarité académique (max 60 pts)
        #    Pour chaque matière commune : |note_mentor - note_mentoré| normalisé
        #    Un mentor fort (8-10) vs mentoré faible (1-4) => score élevé
        matieres_communes = set(notes_self.keys()) & set(notes_other.keys())
        complementarity_score = 0
        if matieres_communes:
            total_diff = 0
            for matiere in matieres_communes:
                note_a = notes_self[matiere]
                note_b = notes_other[matiere]
                # La complémentarité est maximale quand l'un est fort et l'autre faible
                diff = abs(note_a - note_b)
                total_diff += diff
            # Moyenne des différences normalisée sur 9 (écart max = 10-1)
            avg_diff = total_diff / len(matieres_communes)
            complementarity_score = (avg_diff / 9) * 60
        elif not notes_self and not notes_other:
            # Si aucune note renseignée, score neutre
            complementarity_score = 20

        # 3. Score de disponibilité (max 40 pts)
        my_slots = parse_availability(self.disponibilites)
        other_slots = parse_availability(other.disponibilites)
        avail_raw = availability_overlap_score(my_slots, other_slots)  # 0-30
        avail_score = (avail_raw / 30) * 40

        # 4. Total normalisé sur 5 étoiles
        total = complementarity_score + avail_score  # max 100
        stars = round((total / 100) * 5, 1)
        return max(0.0, min(5.0, stars))

    def complementarity_stars_display(self, other):
        """Retourne le score sous forme d'entier d'étoiles (1 à 5)."""
        score = self.complementarity_star_score(other)
        return max(1, round(score))

    def compatibility_details_with(self, other):
        return {
            'filiere': self.filiere_score(other),
            'skills': self.skills_score(other),
            'availability': self.availability_score(other),
            'total': self.compatibility_score_with(other),
        }

    def get_absolute_url(self):
        return reverse('user_profile', kwargs={'username': self.user.username})


class MentoratPost(models.Model):
    TYPE_CHOICES = [
        ('offre', 'Offre de mentorat'),
        ('demande', 'Demande de mentorat'),
    ]

    MENTORAT_TYPE_CHOICES = [
        ('survie', 'Mentorat de service de survie académique'),
        ('orientation', 'Mentorat d’orientation'),
        ('projet', 'Mentorat projet'),
        ('insertion', 'Mentorat insertion professionnelle'),
        ('leadership', 'Mentorat leadership / vie étudiante'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    post_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='offre')
    mentorat_type = models.CharField(max_length=30, choices=MENTORAT_TYPE_CHOICES, default='orientation')
    title = models.CharField(max_length=140)
    description = models.TextField()
    filiere = models.CharField(max_length=120, choices=Profile.FILIERE_CHOICES, default='Informatique')
    competences = models.CharField(max_length=250, help_text='Sépare les compétences par des virgules')
    disponibilites = models.CharField(max_length=120, blank=True, default='Lundi-Vendredi')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_post_type_display()} - {self.title}"

    def competences_list(self):
        return [skill.strip().lower() for skill in self.competences.split(',') if skill.strip()]

    def post_role_score(self, profile):
        if self.post_type == 'offre' and profile.role in ['mentee', 'both']:
            return 20
        if self.post_type == 'demande' and profile.role in ['mentor', 'both']:
            return 20
        return 0

    def filiere_score(self, profile):
        if self.filiere == profile.filiere:
            return 30
        if profile.filiere_group() == Profile.FILIERE_GROUPS.get(self.filiere):
            return 10
        return 0

    def skills_score(self, profile):
        shared = set(self.competences_list()) & set(profile.skills_list())
        return min(30, 10 * len(shared))

    def availability_score(self, profile):
        post_slots = parse_availability(self.disponibilites)
        profile_slots = parse_availability(profile.disponibilites)
        return availability_overlap_score(post_slots, profile_slots)

    def match_score_for_profile(self, profile):
        score = 0
        score += self.post_role_score(profile)
        score += self.filiere_score(profile)
        score += self.skills_score(profile)
        score += self.availability_score(profile)
        return score

    def match_details_for_profile(self, profile):
        return {
            'role': self.post_role_score(profile),
            'filiere': self.filiere_score(profile),
            'skills': self.skills_score(profile),
            'availability': self.availability_score(profile),
            'total': self.match_score_for_profile(profile),
        }

    def intelligent_match_for_profile(self, profile):
        """Scoring intelligent avec 4 criteres et explications"""
        mentor_profile = self.author.profile
        
        # 1. COMPATIBILITE TECHNIQUE (30%)
        shared_skills = set(self.competences_list()) & set(profile.skills_list())
        nb_shared_skills = len(shared_skills)
        tech_score = min(30, 10 * nb_shared_skills)
        tech_weight = 0.30
        
        tech_reasons = []
        if nb_shared_skills > 0:
            skills_str = ', '.join(list(shared_skills)[:3])
            if nb_shared_skills > 3:
                skills_str += ' (+' + str(nb_shared_skills-3) + ' autres)'
            tech_reasons.append('maitrise ' + skills_str)
        
        # 2. COMPATIBILITE HUMAINE (30%)
        human_score = 0
        human_reasons = []
        
        if self.filiere == profile.filiere:
            human_score += 15
            human_reasons.append('appartient a la meme filiere (' + self.filiere + ')')
        elif mentor_profile.filiere_group() == Profile.FILIERE_GROUPS.get(self.filiere):
            human_score += 8
            human_reasons.append('appartient a une filiere proche (' + mentor_profile.filiere + ')')
        
        # Experience de mentorat
        if mentor_profile.nb_mentees_accompagnees > 0:
            exp_score = min(15, mentor_profile.nb_mentees_accompagnees * 3)
            human_score += exp_score
            plural = 's' if mentor_profile.nb_mentees_accompagnees > 1 else ''
            human_reasons.append('a accompagne ' + str(mentor_profile.nb_mentees_accompagnees) + ' etudiant' + plural)
        
        human_weight = 0.30
        
        # 3. COMPATIBILITE LOGISTIQUE (25%)
        avail_score = self.availability_score(profile)
        logistic_weight = 0.25
        
        logistic_reasons = []
        if avail_score >= 20:
            logistic_reasons.append('est disponible a des horaires compatibles')
        elif avail_score >= 10:
            logistic_reasons.append('a des creneaux compatibles')
        
        # 4. COMPATIBILITE DE MOTIVATION (15%)
        motivation_score = 0
        motivation_weight = 0.15
        motivation_reasons = []
        
        if self.post_type == 'offre' and profile.role in ['mentee', 'both']:
            motivation_score += 10
            motivation_reasons.append('propose exactement ce que vous cherchez')
        elif self.post_type == 'demande' and profile.role in ['mentor', 'both']:
            motivation_score += 10
            motivation_reasons.append('cherche ce que vous pouvez offrir')
        
        # Scoring pondere final
        weighted_total = (tech_score * tech_weight +
                         human_score * human_weight +
                         avail_score * logistic_weight +
                         motivation_score * motivation_weight)
        
        # Normaliser le score sur 100
        max_possible = (30 * tech_weight +
                       30 * human_weight +
                       30 * logistic_weight +
                       10 * motivation_weight)
        normalized_score = int((weighted_total / max_possible) * 100) if max_possible > 0 else 0
        
        all_reasons = tech_reasons + human_reasons + logistic_reasons + motivation_reasons
        
        return {
            'score': normalized_score,
            'details': {
                'technique': {'score': tech_score, 'weight': tech_weight, 'reasons': tech_reasons},
                'humain': {'score': human_score, 'weight': human_weight, 'reasons': human_reasons},
                'logistique': {'score': avail_score, 'weight': logistic_weight, 'reasons': logistic_reasons},
                'motivation': {'score': motivation_score, 'weight': motivation_weight, 'reasons': motivation_reasons},
            },
            'explanation': self._build_explanation(all_reasons),
            'all_reasons': all_reasons,
        }
    
    def _build_explanation(self, reasons):
        """Construit une phrase explicative"""
        if not reasons:
            return "Ce mentor pourrait etre un bon match."
        
        if len(reasons) == 1:
            return "Ce mentor vous correspond parce qu'il " + reasons[0] + "."
        elif len(reasons) == 2:
            return "Ce mentor vous correspond parce qu'il " + reasons[0] + " et " + reasons[1] + "."
        else:
            reasons_text = ", ".join(reasons[:-1])
            return "Ce mentor vous correspond parce qu'il " + reasons_text + " et " + reasons[-1] + "."


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class NoteMatiere(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes_matieres')
    matiere = models.CharField(max_length=100)
    note = models.IntegerField(help_text='Note de 1 à 10')

    class Meta:
        unique_together = ('user', 'matiere')

    def __str__(self):
        return f"{self.user.username} - {self.matiere}: {self.note}/10"


class Disponibilite(models.Model):
    JOUR_CHOICES = [
        ('Lundi', 'Lundi'), ('Mardi', 'Mardi'), ('Mercredi', 'Mercredi'),
        ('Jeudi', 'Jeudi'), ('Vendredi', 'Vendredi'), ('Samedi', 'Samedi'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disponibilites_cal')
    jour = models.CharField(max_length=20, choices=JOUR_CHOICES)
    creneau = models.TimeField()

    def __str__(self):
        return f"{self.user.username} - {self.jour} {self.creneau}"
