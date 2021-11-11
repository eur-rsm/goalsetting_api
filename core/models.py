import json
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Union

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.utils import now_stamp


class JsonKey:
    """ Names to be used in JSON objects,
        tightly coupled with the fields of the Data class """
    text = 'text'
    username = 'username'
    roomname = 'roomname'
    fromstamp = 'fromstamp'
    timestamp = 'timestamp'
    messages = 'messages'
    buttons = 'buttons'

    # Config keys
    language = 'language'
    config = 'config'


@dataclass
class Data:
    text: str = ''
    username: str = None
    roomname: str = None
    fromstamp: int = 0
    timestamp: int = -1
    messages: List = None
    buttons: List = None

    # Config params
    language: str = None

    def __init__(self, data_dict: Dict[str, Union[str, int]]):
        if not data_dict:
            return
        allowed_keys = [key for key in dir(JsonKey) if not key.startswith('_')]
        for key, value in data_dict.items():
            if key in allowed_keys:
                setattr(self, key, value)
        if self.timestamp == -1:
            self.timestamp = now_stamp()

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def config(self):
        return {k: v for k, v in asdict(self).items()
                if k in [JsonKey.language]}

    def __repr__(self):
        return str(asdict(self))


class Profile(models.Model):
    class Meta:
        app_label = 'auth'

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sub_id = models.TextField(max_length=40, blank=False)
    onesignal_id = models.TextField(max_length=40, blank=True)
    config_str = models.TextField()

    @property
    def config(self) -> Dict[str, Any]:
        return json.loads(self.config_str or "{}")

    @staticmethod
    def save_user_and_profile(username: str, sub_id: str,
                              first_name: str, last_name: str,
                              email: str) -> User:
        """ Create a user (if needed) and its profile

            :param username: unique id of the user (ERNA or HRO equivalent)
            :param sub_id: SurfConext ID
            :param first_name: first name of the the user
            :param last_name: last name of the the user
            :param email: email of the user, if exists
            :return: the just created user
        """
        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist as _:
            user = User(username=username, email=email,
                        first_name=first_name, last_name=last_name)
            user.save()
        user.profile.sub_id = sub_id
        user.profile.save()

        return user

    @property
    def full_name(self) -> str:
        full_name = f'{self.user.first_name} {self.user.last_name}'
        if '@' in self.user.last_name:
            # Use ip@instituion for demo users
            full_name = full_name.replace(' ', '')
        return full_name


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

