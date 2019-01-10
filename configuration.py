from dataclasses import dataclass
import json
from loguru import logger
import os
from redpie import Redpie


class NoCredentialsException(Exception):
    pass


@dataclass
class Credentials:
    username: str
    password: str


def request_credentials():
    username = input('Your Instagram username: ')
    password = input('Your Instagram password: ')
    return (username, password)


def get_plain_credentials(config_file):
    try:
        with open(config_file) as f:
            config = json.load(f)
            credentials = config.get('credentials', {})
            if not credentials.get('username') or not credentials.get('password'):
                raise NoCredentialsException
            else:
                username, password = credentials.get('username'), credentials.get('password')
    except FileNotFoundError as e:
        logger.info('Config file doesn\'t exists, creating...')
        f = open(config_file, 'w')
        logger.info('Provide your Instagram credentials')
        username, password = request_credentials()
        json.dump({'credentials': {'username': username, 'password': password}}, f)
    except json.decoder.JSONDecodeError as e:
        f = open(config_file, 'w')
        logger.info('Provide your Instagram credentials')
        username, password = request_credentials()
        json.dump({'credentials': {'username': username, 'password': password}}, f)
    except NoCredentialsException as e:
        f = open(config_file, 'w')
        logger.info('Provide your Instagram credentials')
        username, password = request_credentials()
        json.dump({'credentials': {'username': username, 'password': password}}, f)

    logger.info('Your username: {}'.format(username))
    logger.debug('Your password: {}'.format(password))

    return Credentials(username=username, password=password)


def get_target_nof_following(config_file=None, default=100):
    with open(config_file) as f:
        current_config = json.load(f)
    return current_config.get('target_following', default)


def get_db():
    use_redis = os.environ.get('USE_REDIS') in [True, 'true', 'True', '1']
    if use_redis:
        try:
            return Redpie(0, 'instabot_redis')
        except ConnectionError:
            return {}
    else:
        return {}


def get_slowmo():
    return int(os.environ.get('SLOW_TIME', 0))


def get_show_html_if_error():
    return os.environ.get('SHOW_HTML_IF_ERROR') in [True, 'true', 'True', '1']
