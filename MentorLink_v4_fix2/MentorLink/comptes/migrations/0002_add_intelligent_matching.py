# Generated migration for adding intelligent matching fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mentoratpost',
            name='mentorat_type',
            field=models.CharField(
                choices=[
                    ('survie', 'Mentorat de service de survie academique'),
                    ('orientation', "Mentorat d'orientation"),
                    ('projet', 'Mentorat projet'),
                    ('insertion', 'Mentorat insertion professionnelle'),
                    ('leadership', 'Mentorat leadership / vie etudiante'),
                ],
                default='orientation',
                max_length=30
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='nb_mentees_accompagnees',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Nombre d etudiants mentores'
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='types_projets_mentores',
            field=models.CharField(
                blank=True,
                help_text='Types de projets accompagnes (separes par des virgules)',
                max_length=300
            ),
        ),
    ]
