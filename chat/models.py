import json
from dataclasses import dataclass
from typing import Dict, Union, List

from django.db import models

from core.utils import date_string, log_chat
from core.models import Data, JsonKey
from core.config import Color


@dataclass
class Button:
    title: str = ''
    payload: str = ''


class ChatMessage(models.Model):
    # Unique ID of the user (ERNA or HR equivalent)
    roomname = models.CharField(max_length=200)
    # Name of the originator, either roomname or 'bot'
    username = models.CharField(max_length=200)
    # Text of the message
    text = models.TextField()
    # Optionally the list of buttons
    buttons_str = models.TextField()
    # Time of sending, miliseconds
    timestamp = models.BigIntegerField()

    """ TODO Where to put this?
        Buttons allows a last item with payload = 'Type out your own message...'
        Defined in rasa/cli/utils.py
        This makes the client show the input (otherwise closed) 
    """

    def __str__(self) -> str:
        date = date_string(self.timestamp)
        line = "%s -> %s [%s] %s" % (
            self.username, self.roomname, date, self.text[:35])
        if self.buttons:
            buttons = ' - '.join([button['title'] for button in self.buttons])
            skip = ' ' * len(self.username + ' -> ')
            button_line = "\n%s%s" % (skip, buttons)
        else:
            button_line = ''
        return "%s%s" % (line, button_line)

    @property
    def buttons(self) -> List[Dict[str, str]]:
        if not self.buttons_str:
            return []
        return json.loads(self.buttons_str) or []

    @property
    def as_dict(self) -> Dict[str, Union[int, str, List[Button]]]:
        return {JsonKey.username: self.username,
                JsonKey.text: self.text,
                JsonKey.buttons: self.buttons,
                JsonKey.timestamp: self.timestamp}

    @property
    def as_dict_log(self) -> Dict[str, Union[int, str, List[Button]]]:
        return {JsonKey.username: self.username,
                JsonKey.roomname: self.roomname,
                JsonKey.text: self.text,
                JsonKey.timestamp: self.timestamp}

    @staticmethod
    def from_data(data: Data, color: Color = None) -> 'ChatMessage':
        # Add color to utterances if needed
        if color and '<span style=' not in data['text']:
            data['text'] = f"<span style='color: {color.value};'>" \
                           f"{data['text']}</span>"

        chat = ChatMessage(roomname=data.roomname,
                           username=data.username,
                           text=data.text,
                           timestamp=data.timestamp,
                           buttons_str=json.dumps(data.buttons or []))

        # Log the message
        log_chat(chat.as_dict_log)

        return chat

    @classmethod
    def get_room_messages(cls, data: Data) -> List['ChatMessage']:
        """ Get all the (new) messages for a room """
        return cls.objects \
            .filter(roomname=data.roomname, timestamp__gt=data.fromstamp) \
            .order_by('timestamp')
