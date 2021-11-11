from enum import Enum
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from django.conf import settings
from django.contrib.auth.models import User

from core.models import Profile, Data, JsonKey

ENGLISH = 'EN'  # This will be used as default
DUTCH = 'NL'

LANGUAGES = {
    ENGLISH: {
        'title': 'English',
        'port': 5005,
        'action_port': 5055,
    },

    DUTCH: {
        'title': 'Nederlands',
        'port': 5006,
        'action_port': 5056,
    },
}

INSTITUTIONS = {
    'EUR': {'postfix': '@eur.nl'},
    'HR': {'postfix': '@hr.nl'},
}


class Color(Enum):
    # Sync with Rasa
    OPTIONAL = 'blue'
    # Should not be needed in API, Rasa should provide these
    REQUIRED = 'darkgreen'
    SYSTEM = 'black'


class LanguageError(Exception):
    pass


class Config:
    """ This is config stuff
        Do we need to make this configurable?
    """

    @staticmethod
    def _config_dir():
        base_dir = Path(os.path.dirname(__file__)).parents[0]
        return base_dir / '_data' / 'config'

    @staticmethod
    def setup():
        # Make sure dir exists, clear old files
        base_dir = Path(os.path.dirname(__file__)).parents[0]
        Config.__CONF_DIR = base_dir / '_data' / 'config'
        os.makedirs(Config.__CONF_DIR, exist_ok=True)
        for file in Config.__CONF_DIR.glob('*'):
            file.unlink()

        # Fill from DB
        for profile in Profile.objects.all():
            if profile.config:
                (Config.__CONF_DIR / profile.user.username).touch(exist_ok=True)

    @staticmethod
    def get_rasa_url(data: Data) -> str:
        params = {'port': LANGUAGES[data.language]['port']}
        return settings.RASA_URL.format(**params)

    @staticmethod
    def get_action_url(data: Data) -> str:
        params = {'port': LANGUAGES[data.language]['action_port']}
        return settings.ACTION_URL.format(**params)

    @classmethod
    def get_config(cls, data: Data) -> List[Dict[str, Any]]:
        # User already provided all and didn't delete client side
        file_path = cls._config_dir() / data.username
        if file_path.is_file() and data.language is not None:
            with open(file_path, 'r') as f:
                if json.loads(f.read() or '[]') == data.config():
                    return []

        # User provided all needed config : save to DB and file
        if None not in data.config().values():
            users = User.objects.filter(username=data.username)
            if users:
                user = users[0]
                profile = Profile.objects.get(user=user)
                profile.config_str = json.dumps(data.config())
                profile.save()

                with open(file_path, 'w') as f:
                    json.dump(data.config(), f)

                return []

        # Force user to answer config questions
        choices = [{'value': key, 'title': value['title']}
                   for key, value in LANGUAGES.items()]
        language = {'name': JsonKey.language,
                    'title': 'Choose the language of your study',
                    'choices': choices}

        return [language]
