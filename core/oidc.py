import json
from typing import Any, Dict, Tuple, List, Union

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import requests
from rest_framework.request import Request

from core.models import Profile


def get_user_by_sub(request: Request, id_token: Dict[str, Any]) -> User:
    """ Get the user from the 'sub' parameter as we get it from SurfConext
        If the user doesn't exists locally, create it and its profile
        The user fields come from the UserInfo endpoint

        :param request: from this we get the access token fromt he header
        :param id_token: the idToken from SurfConext, provides the sub id
        :return: a user from the local DB
    """

    try:
        user = Profile.objects.get(sub_id=id_token['sub']).user
    except ObjectDoesNotExist as _:
        access_token = request.META['HTTP_ACCESS_TOKEN']
        user = _create_save_user(id_token['sub'], access_token)

    return user


def _get_user_info(access_token: str) -> Dict[str, Any]:
    """ Get the claims from the UserInfo endpoint

        :param access_token: the access token as provided by SurfConext
        :return: a dictionary containing the claims
    """
    url = f"{settings.OIDC_AUTH['OIDC_ENDPOINT']}/oidc/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(url, headers=headers)
    return json.loads(r.text)


def _create_save_user(sub: str, access_token: str) -> User:
    """ Create a user and its profile from the claims
        The profile contains the sub id, and later the OneSignal ID

        :param sub:
        :param access_token:
        :return: the just created user
    """
    user_dict = _get_user_info(access_token)
    erna_id, email = _get_identifiers(user_dict)
    full_name, first_name, last_name = _get_names(user_dict)

    return Profile.save_user_and_profile(erna_id, sub,
                                         first_name, last_name, email)


def _get_identifiers(user_dict: Dict[str, Any]) -> Tuple[str, str]:
    erna_id = user_dict.get('uids', [''])[0]
    email = user_dict['email']
    # HR doesn't use an institution identifier
    if '@' not in erna_id:
        erna_id += email[email.index('@'):]

    return erna_id, email


def _get_names(user_dict: Dict[str, Any]) -> Tuple[str, str, str]:
    full_name: str = user_dict['preferred_username']

    # If format 'last, first' (HR)
    if ',' in full_name:
        first_name = ', '.join([s.strip() for s in full_name.split(',')[1:]])
        last_name = full_name.split(',')[0].strip()
    # EUR uses 'first last'
    else:
        first_name = full_name.split(' ')[0]
        last_name = ' '.join(full_name.split(' ')[1:])

    return full_name, first_name, last_name
