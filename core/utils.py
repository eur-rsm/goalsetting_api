import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Union

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from pytz import timezone

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
ROTTERDAM = timezone('Europe/Amsterdam')


def date_string(dt: Union[int, datetime] = None) -> str:
    """ Standardize datetime to the Rotterdam timezone

        :param dt: Optionally a timestamp or datetime, otherwise use 'now'
        :return: a string with the formatted datetime
    """
    if type(dt) == int:
        dt = datetime.fromtimestamp(dt / 1000)
    if dt is None:
        dt = datetime.now()
    return dt.astimezone(ROTTERDAM).strftime(DATE_FORMAT)


def now_stamp() -> int:
    """ Get the timestamp of the current datetime

        :return: the current timestamp in miliseconds
    """
    return int(time.time() * 1000)


def is_extra_process(name: str) -> bool:
    """ Determine if this is not the main process, used in AppConfigs
        For Gunicorn : check via lock file

        :param name: name for the lock file
        :return: True if this is the main process, otherwise False
    """

    import os
    # Gunicorn doesn't use RUN_MAIN
    is_devserver = os.environ.get('SERVER_SOFTWARE') is None

    # Extra process started by dev server
    if is_devserver and not os.environ.get('RUN_MAIN'):
        return True

    if not is_devserver:
        # This might be a Gunicorn environment
        try:
            # Lock files will be removed by the bash script beforehand
            base_dir = Path(os.path.dirname(__file__)).parents[0]
            lock_dir = base_dir / '_data' / 'lock'
            os.makedirs(lock_dir, exist_ok=True)
            lock_file = os.path.join(lock_dir, name + '.lock')
            os.open(lock_file, os.O_CREAT | os.O_EXCL)
        except FileExistsError as _:
            return True

    return False


def log_chat(data: Union['Data', 'ChatMessage', Dict[str, Any]]):
    """ Uniform way to log the messages between user and bot
        Each room (i.e. user) gets its own file
        Not trivial to

        :param data: either Data or ChatMessage object,
            or a dictionary of the message attributes
    """

    from chat.models import ChatMessage
    from core.models import Data, JsonKey

    if type(data) == Data:
        chat_dict = data.__dict__
    elif type(data) == ChatMessage:
        chat_dict = data.as_dict
    else:
        chat_dict = data

    dt = None
    if JsonKey.timestamp in chat_dict.keys():
        dt = datetime.fromtimestamp(chat_dict[JsonKey.timestamp] / 1000)
    date_str = date_string(dt)

    file_path = settings.LOGGING['handlers']['chat']['filename']
    username = chat_dict[JsonKey.username]
    roomname = chat_dict.get(JsonKey.roomname) or username
    if roomname:
        file_path = file_path.replace('default.log', f'{roomname}.log')
        file_path = file_path.replace(' ', '_')

    with open(file_path, 'a') as f:
        for line in chat_dict[JsonKey.text].split("\n"):
            f.write("[{0}] [{1:<{2}}] {3}\n".format(
                date_str, username, len(roomname), line))
