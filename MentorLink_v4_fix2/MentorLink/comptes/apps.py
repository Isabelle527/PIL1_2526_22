from django.apps import AppConfig


class ComptesConfig(AppConfig):
    name = 'comptes'

    def ready(self):
        import comptes.models  # noqa: F401 — enregistre les signaux post_save
