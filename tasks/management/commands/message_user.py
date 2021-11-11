import sys
from typing import Tuple

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand

from api.notifications import send_notification
from core.models import Profile


class Command(BaseCommand):
    help = 'Send a message to the user via OneSignal'

    def handle(self, **options):
        user, profile, message = self.parse_arguments(options)

        print()
        print(f'Sending message : {message}')
        print(f'User ID         : {user.username}')
        print(f'User name       : {user.first_name} {user.last_name}')
        print(f'OneSignal ID    : {profile.onesignal_id}')
        print(f'Sub ID          : {profile.sub_id}')
        print()

        send_notification(user.username, message)

    def add_arguments(self, parser):
        parser.add_argument('-m', '--message', nargs='+', type=str,
                            help="Message body for the user")
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-u', '--username', nargs='+', type=str,
                           help="Username of the user")
        group.add_argument('-o', '--onesignal', type=str,
                           help="The OneSignal ID of the user")
        group.add_argument('-s', '--sub', type=str,
                           help="Sub ID of the user")

    def parse_arguments(self, options) -> Tuple[User,  Profile, str]:
        message = ' '.join(options['message'])
        if options['username']:
            username = ' '.join(options['username'])
            try:
                user = User.objects.get(username=username)
            except ObjectDoesNotExist as _:
                print()
                print(f"Username does not exist : '{username}'")
                print()
                sys.exit(1)
            profile = user.profile
        elif options['onesignal']:
            try:
                profile = Profile.objects.get(onesignal_id=options['onesignal'])
            except ObjectDoesNotExist as _:
                print()
                print(f"OneSignal ID does not exist : '{options['onesignal']}'")
                print()
                sys.exit(1)
            user = profile.user
        elif options['sub']:
            try:
                profile = Profile.objects.get(sub_id=options['sub'])
            except ObjectDoesNotExist as _:
                print()
                print(f"Sub ID does not exist : '{options['sub']}'")
                print()
                sys.exit(1)
            user = profile.user
        else:
            print()
            print("This should not happen!")
            print("No username, OneSignal or Sub ID!")
            print()
            sys.exit(1)

        return user, profile, message
