from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('messageries', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='status',
            field=models.CharField(choices=[('initiated', 'Initiée'), ('scheduled', 'Planifiée'), ('in_progress', 'En cours de suivi'), ('completed', 'Terminée')], default='initiated', max_length=20),
        ),
        migrations.AddField(
            model_name='conversation',
            name='suggested_slots',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='initial_goal',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='initiation_form',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='message',
            name='type',
            field=models.CharField(choices=[('text', 'Texte'), ('slot_suggestion', 'Proposition de créneaux'), ('goal_proposal', "Proposition d'objectif"), ('form_submission', 'Formulaire soumis'), ('system', 'Système')], default='text', max_length=30),
        ),
    ]
