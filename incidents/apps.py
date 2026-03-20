import os
from django.apps import AppConfig


class IncidentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'incidents'

    def ready(self):
        if os.environ.get('RUN_MAIN') == 'true':
            from incidents.scheduler import start_scheduler
            start_scheduler()
