import logging
from typing import Dict, List, Union

from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse

from api.notifications import send_notification
from core.config import Config
from chat.models import ChatMessage, Button
from core.rasa import send_to_factsbot, converse_with_rasa, set_rasa_names
from core.utils import now_stamp
from core.models import Data, JsonKey

logger_app = logging.getLogger('app')


def handle_user_message(data: Data) -> JsonResponse:
    """ Handle the message from the user, either from the API
        (authenticated clients, app or web) or the demo web client

        :param data: the Data object from the user input
        :return:
            A list of new messages
            A List of needed config items
    """

    # The user just wants to test, reply with a (not stored) test message
    if data.text == 'TEST':
        return handle_test_message(data)

    # Save message and send to bot-backend
    if data.text:
        handle_message(data)

    # Get any new messages, this might include replies from the bot-backend
    messages = get_messages(data)

    # Get the questions the user need to answer
    config = Config.get_config(data)

    # Apparently this is the first interaction from the user, show 'welcome'
    if not config and not messages and data.fromstamp == 0:
        messages = get_welcome_message(data)

    response = JsonResponse({
        JsonKey.messages: messages,
        JsonKey.config: config,
    })

    # Make sure the names are re-set after a restart
    if data.text.startswith('/restart'):
        users = User.objects.filter(username=data.username)
        if users:
            user = users[0]
            set_rasa_names(user, data)

    return response


def handle_test_message(data: Data) -> JsonResponse:
    """ The user wants to test the client, reply with a test message.
        Also send a notification
        But don't store anything in the DB.

        :param data: the Data object from the user input
        :return: list of the user message and a default bot message
    """
    send_notification(data.username)

    msg1 = {JsonKey.text: data.text,
            JsonKey.username: data.username,
            JsonKey.timestamp: now_stamp()}
    msg2 = {JsonKey.text: "THIS IS JUST A TEST",
            JsonKey.username: settings.CHAT_MASTER,
            JsonKey.timestamp: now_stamp()}
    return JsonResponse({JsonKey.messages: [msg1, msg2]})


def get_welcome_message(data: Data) \
        -> List[Dict[str, Union[int, str, List[Button]]]]:
    # Send names to Rasa to be used by the surveys / responses
    users = User.objects.filter(username=data.username)
    if users:
        user = users[0]
        set_rasa_names(user, data)

    data.text = '/request_welcome'
    converse_with_rasa(data)
    return get_messages(data)


def handle_message(data: Data):
    """ Handle a 'normal' message by sending it to the bat-backend
        Either the test-bot (echo bot) or the Rasa bot, depending on the setting
        Replies are stored in the DB, will be retrieved by handle_user_message

        :param data: the Data object from the user input
    """

    # Save message from user
    chat_message = ChatMessage.from_data(data)
    chat_message.save()

    # Send to backend or Rasa
    converse_with_rasa(data, False)


def get_messages(data: Data) -> List[Dict[str, Union[int, str, List[Button]]]]:
    """ Get the messages (as dicts) from a room

        :param data: the Data object from the user input
        :return: A list of messages
    """

    return [message.as_dict for message in
            ChatMessage.get_room_messages(data)]
