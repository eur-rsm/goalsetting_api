from datetime import datetime, timedelta

from background_task import background
from background_task.models import TaskManager
from django.contrib.auth.models import User
from pytz import timezone

from core.rasa import converse_with_rasa, set_rasa_names
from core.models import Data, JsonKey
from core.utils import log_chat


@background
def schedule_conversation(conversation_name: str, username: str = None):
    """ This schedules the conversation for a particular user or all users

    Args:
        conversation_name: the name of the conversation to be scheduled
        username: the name of the user for which to schedule the conversation
            if no username is given, schedule for all users 1 minute apart

    """
    def is_mobile_user(user):
        return user.profile and user.profile.onesignal_id

    now = datetime.now().replace(tzinfo=timezone('UTC'))
    users = User.objects.filter(username=username)
    if not users:
        users = [user for user in User.objects.all()]

    delta = 0
    for user in users:
        # Only schedule mobile users, unless it's restart
        if not is_mobile_user(user) and conversation_name != '/restart':
            continue

        # Spread the conversations, unless it's a restart
        if conversation_name != '/restart':
            delta += 10

        date_time = now + timedelta(seconds=delta)
        task = TaskManager().new_task(start_conversation.name,
                                      args=(conversation_name, user.username),
                                      run_at=date_time,
                                      remove_existing_tasks=False)
        task.save()


@background
def start_conversation(conversation_name: str, username: str):
    """ Start a conversation with the user
        The conversation name should be handled as an action form on Rasa
        The trigger doesn't show up in the database,
        either as ChatMessage or in the Rasa tracker

    Args:
        conversation_name: the name of the conversation to be started
        username: the name of the user for which to start the conversation

    """
    user = User.objects.get(username=username)
    profile = user.profile
    config = profile.config

    # The user didn't complete the config, don't interact
    if not config:
        return

    data = Data({
        JsonKey.username: username,
        JsonKey.text: conversation_name,
        JsonKey.language: config[JsonKey.language]
    })

    # Make sure the names are set
    if conversation_name != '/restart':
        set_rasa_names(user, data)

    # Log the conversation
    chat_dict = data.__dict__
    chat_dict[JsonKey.roomname] = username
    log_chat(chat_dict)

    converse_with_rasa(data)
