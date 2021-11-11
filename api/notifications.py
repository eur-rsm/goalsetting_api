import json
import logging
import re
import time
from typing import Any, Dict, List

from background_task import background
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from onesignal import Client, Notification

from api.ping import add_web_ping
from core.models import Profile

logger_debug = logging.getLogger('debug')
logger_app = logging.getLogger('app')


class NotificationError(Exception):
    pass


def _get_client() -> Client:
    """ Connect to OneSignal """
    return Client(user_auth_key=settings.USER_AUTH_KEY,
                  app_auth_key=settings.APP_AUTH_KEY,
                  app_id=settings.APP_ID)


def _get_all_players() -> List[Dict[str, Any]]:
    """ Get all devices for this app """
    client = _get_client()
    players = []
    request_query = {'offset': 0}
    while True:
        devices = json.loads(client.view_devices(request_query).text)
        players.extend(devices['players'])
        request_query['offset'] += 300
        if request_query['offset'] > devices['total_count']:
            break
        time.sleep(1)

    # Filter out non-app users
    players = [p for p in players if p['external_user_id']]
    # Sort by last active (overwrites older usages if user has multiple devices)
    players.sort(key=lambda p: p['last_active'])

    return players


@background
def retrieve_onesignal_ids():
    """ Get all the devices from OneSignal, store in user profile
    """
    try:
        players = _get_all_players()
    except:
        print("\nError getting OneSignal data\n")
        return

    # Create or update profile if needed
    extra = {'origin': 'ONESIGNAL IDS'}
    profiles_dict = {p.sub_id: p for p in Profile.objects.all()}
    for player in players:
        sub_id = player['external_user_id']
        profile = profiles_dict.get(sub_id)
        if profile is None:
            logger_app.warning(
                f"Player {sub_id} doesn't have a profile yet", extra=extra)
        elif profile.onesignal_id != player['id']:
            profile.onesignal_id = player['id']
            profile.save()


@background(schedule=0)
def send_notification(username: str, message: str = 'New message',
                      add_ping: bool = True):
    """ Send a notification to the user, if it's OneSignal ID is present
        Also make sure the web client receives a 'ping'

        :param username: name of the user
        :param message: message send to the user
        :param add_ping: whether to add a ping for web interfaces
    """

    # For web clients: add a 'ping' for out-of-conversation bot messages
    if add_ping:
        add_web_ping(username)

    # Get the User profile from DB to get the OneSignal ID
    try:
        user = User.objects.get(username=username)
        onesignal_id = user.profile.onesignal_id
    except ObjectDoesNotExist as _:
        # The demo version uses the IP address as username, no notifications
        if re.sub('[\d, \.]', '', username) == '':
            return
        raise NotificationError(f"Client '{username}' not known")
    if not onesignal_id:
        logger_app.warning(f"Client '{username}' has no OneSignal ID",
                           extra={'origin': 'SEND NOTIFICATION'})
        return

    new_notification = Notification(post_body={
        'headings': {'en': '<TODO>'},
        'contents': {'en': message},
        'include_player_ids': [onesignal_id],
        'collapse_id': '<TODO>',
    })
    client = _get_client()
    client.send_notification(new_notification)
