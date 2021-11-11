import sys
from typing import List

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from core.rasa import set_rasa_names
from core.config import ENGLISH
from core.models import Data, JsonKey

CONVERSATIONS = ['/restart',]


class Command(BaseCommand):
    help = 'Push all names from API to RASA'

    def handle(self, **options):
        users = self.parse_arguments(options)
        if len(users) == 1:
            print()
            print(f'Set names for : {users[0].username}')
            print()
        else:
            print()
            print(f'Set names for : all')
            print()

        deny = input('Is this correct [Y/n]? ')
        if deny.lower() in ('n', 'no', 'nein', 'njet', 'nee', 'no fucking way'):
            return

        for user in users:
            lang = user.profile.config.get(JsonKey.language, ENGLISH)
            data = Data({'language': lang})
            set_rasa_names(user, data)

    def add_arguments(self, parser):
        parser.add_argument('-u', '--username', type=str,
                            help="Username of the user")

    def parse_arguments(self, options) -> List[User]:
        username = options['username']
        if username:
            try:
                users = [User.objects.get(username=username)]
            except ObjectDoesNotExist as _:
                print()
                print(f"Username does not exist : '{username}'")
                print()
                sys.exit(1)
        else:
            users = list(User.objects.all())

        return users
