import json
import logging
from typing import Dict, Union

import requests
from background_task import background
from django.conf import settings
from django.contrib.auth.models import User

from api.notifications import send_notification
from chat.models import ChatMessage
from core.config import Config, Color, LANGUAGES
from core.models import Data, JsonKey

logger_app = logging.getLogger('app')

HEADERS = {'Content-Type': 'application/json'}


def _get_params(user: User, data: Data) -> Dict[str, Union[str, int]]:
    return {
        'port': LANGUAGES[data.language]['port'],
        'username': user.username
    }


def converse_with_rasa(data: Data, add_ping: bool = True):
    """ This sends a message to the Rasa bot

        :param data: the Data object from the user input
        :param add_ping: whether or not to add a ping for the web clients
    """

    try:
        rasa_url = Config.get_rasa_url(data)
        payload = {'sender': data.username, 'message': data.text}
        r = requests.post(rasa_url, json=payload)
        response = json.loads(r.text)

        for utterance in response:
            new_data = Data({JsonKey.roomname: data.username,
                             JsonKey.username: settings.CHAT_MASTER,
                             JsonKey.text: utterance['text'],
                             JsonKey.buttons: utterance.get('buttons', [])})
            chat_message = ChatMessage.from_data(new_data, Color.OPTIONAL)
            chat_message.save()
        if response:
            # Send notifications to device
            send_notification(data.username, add_ping=add_ping)

    except Exception as e:
        logger_app.warning(e, extra={'origin': 'CONVERSE RASA'})
        logger_app.warning(data, extra={'origin': 'CONVERSE RASA'})


def set_rasa_names(user: User, data: Data):
    url = settings.RASA_API.format(**_get_params(user, data))
    payload = [{'event': 'slot', 'name': slot[0], 'value': slot[1]}
               for slot in (('first_name', user.first_name),
                            ('last_name', user.last_name),
                            ('full_name', user.profile.full_name))]
    r = requests.post(url, data=json.dumps(payload), headers=HEADERS)


def get_button_texts(data: Data, username: str) -> Dict[str, str]:
    institution = username.split('@')[-1].split('.')[0].lower()
    url = Config.get_action_url(data)
    payload = {"next_action": "action_buttons", "tracker": {},
               "domain": {'institution': institution}}
    r = requests.post(url, json=payload)
    results = json.loads(r.text)
    responses = results['responses']
    return responses[0]['custom']
