from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0003_profile_identite_professionnelle_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NoteMatiere',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('matiere', models.CharField(max_length=100)),
                ('note', models.IntegerField(help_text='Note de 1 à 10')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes_matieres', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'matiere')},
            },
        ),
        migrations.CreateModel(
            name='Disponibilite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jour', models.CharField(choices=[('Lundi', 'Lundi'), ('Mardi', 'Mardi'), ('Mercredi', 'Mercredi'), ('Jeudi', 'Jeudi'), ('Vendredi', 'Vendredi'), ('Samedi', 'Samedi')], max_length=20)),
                ('creneau', models.TimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='disponibilites_cal', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='profile',
            name='telephone',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='profile',
            name='date_naissance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='nb_mentees_accompagnees',
            field=models.PositiveIntegerField(default=0, help_text="Nombre d'etudiants mentores"),
        ),
        migrations.AddField(
            model_name='profile',
            name='types_projets_mentores',
            field=models.CharField(blank=True, help_text='Types de projets accompagnes (separes par des virgules)', max_length=300),
        ),
    ]

# Patch: ajout du champ photo au modèle Profile (ajouté manuellement)
