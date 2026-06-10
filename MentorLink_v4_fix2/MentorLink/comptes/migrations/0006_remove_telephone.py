from django.db import migrations


class Migration(migrations.Migration):
    """
    Supprime la colonne 'telephone' en doublon.
    Le champ 'phone' (migration 0001) remplit ce rôle.
    """

    dependencies = [
        ('comptes', '0005_profile_photo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='telephone',
        ),
    ]
