from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0004_notematiere_disponibilite'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='profile_photos/', help_text='Photo de profil'),
        ),
    ]
