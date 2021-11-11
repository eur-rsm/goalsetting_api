import sys
from typing import Tuple

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from chat.conversation import start_conversation

# These come from ../rasa/config/domain-base.yml
CONVERSATIONS = [
    '/request_diary_01',
    '/request_diary_10_12',
    '/request_feedback',
    '/request_tam',
    '/request_well_being',
    '/request_phq_depression',
    '/request_gad_anxiety',
    '/request_test_anxiety',
    '/request_efficacy',
    '/request_exam_prep',
    '/request_update',
    '/request_check_in',
    '/request_covid',
    '/request_cbt',
    '/request_welcome',
    '/request_farewell1'
    '/request_farewell2'
    '/restart',
]


class Command(BaseCommand):
    help = 'Start a conversation with a user'

    def handle(self, **options):
        user, conversation_name = self.parse_arguments(options)
        print()
        print(f'Username        : {user.username}')
        print(f'Conversation    : {conversation_name}')
        print()

        deny = input('Is this correct [Y/n]? ')
        if deny.lower() in ('n', 'no', 'nein', 'njet', 'nee', 'no fucking way'):
            return

        start_conversation(conversation_name, user.username)

    def add_arguments(self, parser):
        parser.add_argument('-c', '--conversation', type=str,
                            help="Name of the conversation")
        parser.add_argument('-u', '--username', nargs='+', type=str,
                            help="Username of the user")

    def parse_arguments(self, options) -> Tuple[User, str]:
        if len(sys.argv) < 4:
            self.print_help(*sys.argv)
            sys.exit(1)

        conversation = options['conversation']
        if not conversation:
            print()
            print("You need to name a conversation")
            print()
            sys.exit(1)
        elif not conversation.startswith('/'):
            conversation_name = f'/{conversation}'
        else:
            conversation_name = conversation
        if conversation_name not in CONVERSATIONS:
            print()
            print(f"Not a valid conversation : '{conversation}'")
            print()
            sys.exit(1)

        username = ' '.join(options['username'])
        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist as _:
            print()
            print(f"Username does not exist : '{username}'")
            print()
            sys.exit(1)

        return user, conversation_name
