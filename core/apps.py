from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from core.utils import is_extra_process
        if is_extra_process('core'):
            return

        from core.config import Config
        Config.setup()
