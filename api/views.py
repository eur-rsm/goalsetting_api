from datetime import datetime
import json
import logging

from background_task.models import Task, TaskManager
from django.conf import settings
from django.contrib.auth.models import User
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from pytz import timezone
from rest_framework.decorators import api_view
from rest_framework.request import Request

from api.notifications import send_notification
from api.ping import has_web_ping
from chat.chat import handle_user_message
from core.rasa import get_button_texts
from chat.conversation import start_conversation
from chat.models import ChatMessage
from core.utils import now_stamp, log_chat
from core.models import Data, JsonKey

logger_debug = logging.getLogger('debug')
logger_app = logging.getLogger('app')


@api_view(['POST'])
def log(request: Request) -> HttpResponse:
    """ For development only

        :param request: the request with the log message in JSON
        :return: Simple acknowledgement
    """
    chat_dict = {
        JsonKey.timestamp: now_stamp(),
        JsonKey.roomname: 'log.log',
        JsonKey.username: request.user.username,
        JsonKey.text: request.data.get(JsonKey.text, 'No message')
    }

    log_chat(chat_dict)

    return HttpResponse('OK')


@api_view(['POST'])
def ping(request: Request) -> JsonResponse:
    """ Lightweight endpoint for the web interface to emulate the notifications
        functionality (no DB calls).

        :param request: The request from the app, should contain the token
        :return: True or False based on the existence of new messages.
    """

    username = request.user.username
    return JsonResponse({JsonKey.messages: has_web_ping(username)})


@api_view(['POST'])
def config(request: Request) -> JsonResponse:
    """ Endpoint for getting data to the client

        :param request: The request from the app, should contain the token
        :return: :return: Dict of config items.
    """

    username = request.user.username
    info = get_button_texts(Data(request.data), username)
    return JsonResponse({JsonKey.config: info})


@api_view(['POST'])
def sync_messages(request: Request) -> JsonResponse:
    """ The main endpoint for the app :
            - Ingest a message if present
            - Return all messages for the user after from_stamp

        :param request: The request from the app, should contain the token
        :return:
            A list of messages to display, both from the user as the bot(s)
            A list of buttons for the user to choose from
            A list of configs the user needs to fill
    """

    extra = {'origin': 'API VIEWS SYNC'}
    logger_debug.info(f"{request.user.username} : {request.data}", extra=extra)

    # Ensure / clean data
    request.data[JsonKey.text] = request.data.get(JsonKey.text, '').strip()
    request.data[JsonKey.username] = request.user.username
    request.data[JsonKey.roomname] = request.data[JsonKey.username]
    request.data[JsonKey.fromstamp] = request.data.get(JsonKey.fromstamp, 0)

    # Users shouldn't be allowed to directly trigger actions via intents
    if request.data[JsonKey.text].startswith('/restart') or \
            request.data[JsonKey.text].startswith('EXTERNAL: '):
        logger_app.warning(
            f"{request.user.username} : {request.data[JsonKey.text]}",
            extra={'origin': 'API VIEWS SYNC'})
        request.data[JsonKey.text] = ''

    return handle_user_message(Data(request.data))


@require_POST
@csrf_exempt
def ingress(request: WSGIRequest) -> HttpResponse:
    """ Ingress point for chats from Rasa outside of a conversation call
        Usually the response from Rasa is via 'converse with Rasa' interaction
        But sometimes Rasa wants to interact (action via intent)

        :param request: The request from the bot, encoded as a message
        :return: A simple acknowledgement if the ingress succeeded
            or a denial if there is no valid authentication
    """

    request_data = json.loads(request.body)
    if request_data.get('backend_secret') != settings.BACKEND_SECRET:
        return HttpResponse('Nope')

    extra = {'origin': 'INGRESS CHAT'}
    logger_debug.info(request_data, extra=extra)

    request_data[JsonKey.timestamp] = now_stamp()
    request_data[JsonKey.username] = settings.CHAT_MASTER
    chat_message = ChatMessage.from_data(Data(request_data))
    chat_message.save()

    # Send notifications to device
    send_notification(chat_message.roomname)

    return HttpResponse('OK')


@require_POST
@csrf_exempt
def ingress_task(request: WSGIRequest) -> HttpResponse:
    """ Ingress point for tasks from Rasa
        This could be a delayed survey request

        :param request: The request from the bot
        :return: A simple acknowledgement if the ingress succeeded
            or a denial if there is no valid authentication
    """

    request_data = json.loads(request.body)
    if request_data.get('backend_secret') != settings.BACKEND_SECRET:
        return HttpResponse('Nope')

    if request_data.get('cancel'):
        params = json.dumps(
            [[request_data['task'], request_data['username']], {}])
        for task in Task.objects.filter(task_name=start_conversation.name,
                                        task_params=params):
            task.delete()
    else:
        date_time = datetime.fromtimestamp(request_data['timestamp'])
        request_data[date_time] = date_time.replace(tzinfo=timezone('UTC'))

        task = TaskManager().new_task(start_conversation.name,
                                      args=(request_data['task'],
                                            request_data['username']),
                                      run_at=request_data[date_time],
                                      remove_existing_tasks=False)
        task.save()

    extra = {'origin': 'INGRESS TASK'}
    logger_debug.info(request_data, extra=extra)

    return HttpResponse('OK')


@require_POST
@csrf_exempt
def get_names(request: WSGIRequest) -> JsonResponse:
    """ Endpoint for Rasa to get missing names

        :param request: The request from the bot
        :return: A dict with the names
            or nothing if there is no valid authentication
    """
    request_data = json.loads(request.body)
    if request_data.get('backend_secret') != settings.BACKEND_SECRET:
        return JsonResponse({})

    user = User.objects.get(username=request_data[JsonKey.username])
    if not user:
        return JsonResponse({})

    return JsonResponse({
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.profile.full_name,
    })
