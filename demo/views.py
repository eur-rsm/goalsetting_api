import logging

from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.request import Request

from api.ping import has_web_ping
from chat.chat import handle_user_message
from core.rasa import get_button_texts
from core.config import INSTITUTIONS
from core.models import Data, JsonKey, Profile

logger_debug = logging.getLogger('debug')


def get_ip_as_username(request: Request) -> str:
    """ The demo version doesn't have authentication, and therefore no username
        The identify the user the IP address from the request is used

        :param request: the request
        :return: the extracted IP as string
    """
    remote_address = request.META.get('HTTP_X_FORWARDED_FOR')
    if not remote_address:
        remote_address = request.META.get('REMOTE_ADDR', request.user.username)

    # This is a demo-only key
    institution = request.data.pop('institution', 'EUR').strip()
    return f"{remote_address}{INSTITUTIONS[institution]['postfix']}"


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def ping(request: Request) -> JsonResponse:
    """ Lightweight endpoint for the web interface to emulate the notifications
        functionality (no DB calls).

        :param request: The request from the app, should contain the token
        :return: True or False based on the existence of new messages.
    """

    username = get_ip_as_username(request)
    return JsonResponse({JsonKey.messages: has_web_ping(username)})


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def config(request: Request) -> JsonResponse:
    """ Endpoint for getting data to the client

        :param request: The request from the app
        :return: Dict of config items.
    """

    username = get_ip_as_username(request)
    info = get_button_texts(Data(request.data), username)
    return JsonResponse({JsonKey.config: info})


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def sync_messages(request: Request) -> JsonResponse:
    """ The main endpoint for the demo client :
            - Ingest a message if present
            - Return all messages for the user after from_stamp

        :param request: the request with
        :return:
            A list of new messages
            A list of buttons for the user to choose from
            A List of needed config items
    """

    # Ensure / clean data, add @institution to IP for username
    username = get_ip_as_username(request)
    request.data[JsonKey.text] = request.data.get(JsonKey.text, '').strip()
    request.data[JsonKey.username] = username
    request.data[JsonKey.roomname] = request.data[JsonKey.username]
    request.data[JsonKey.fromstamp] = request.data.get(JsonKey.fromstamp, 0)

    if request.data[JsonKey.text]:
        extra = {'origin': 'DEMO VIEWS SYNC'}
        logger_debug.info(
            f"{request.data[JsonKey.username]} : {request.data}", extra=extra)

    # Create user for demo site
    first_name = username[:username.index('@')]
    last_name = username[username.index('@'):]
    Profile.save_user_and_profile(username, '',
                                  first_name, last_name, username)

    return handle_user_message(Data(request.data))
