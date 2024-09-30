from django.apps import AppConfig
from django.db.models.signals import pre_delete, pre_save


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        from api import signals
        from api.models import Comment, Volunteer

        for model in [Comment, Volunteer]:
            pre_delete.connect(signals.delete_media, sender=model)
            pre_save.connect(signals.update_media, sender=model)
