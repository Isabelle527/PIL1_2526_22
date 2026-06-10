from django.contrib.auth.models import User
from django.db import models


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    updated_at = models.DateTimeField(auto_now=True)
    # État du flux de la conversation / relation
    STATUS_CHOICES = [
        ('initiated', 'Initiée'),
        ('scheduled', 'Planifiée'),
        ('in_progress', 'En cours de suivi'),
        ('completed', 'Terminée'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    # Stocke des créneaux proposés automatiquement (liste de dicts {day, start, end, note})
    suggested_slots = models.JSONField(blank=True, null=True)
    # Objectif initial proposé/fixé avant la première séance
    initial_goal = models.TextField(blank=True)
    # Indique si le mini-formulaire "ce que j'attends" a été soumis
    initiation_form = models.TextField(blank=True)

    def __str__(self):
        names = ', '.join(user.username for user in self.participants.all())
        return f'Conversation: {names}'


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    # Type de message pour différencier proposition de créneaux, formulaire, system, etc.
    TYPE_CHOICES = [
        ('text', 'Texte'),
        ('slot_suggestion', 'Proposition de créneaux'),
        ('goal_proposal', 'Proposition d\'objectif'),
        ('form_submission', 'Formulaire soumis'),
        ('system', 'Système'),
    ]
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='text')
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message from {self.sender.username} at {self.timestamp:%Y-%m-%d %H:%M}'


class ContactMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='contact_messages')
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=180)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Contact from {self.name} - {self.subject}'
