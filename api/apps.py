from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        from core.utils import is_extra_process
        if is_extra_process('api'):
            return

        from api.ping import setup
        setup()
