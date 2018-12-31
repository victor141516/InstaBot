from dataclasses import dataclass
import json
from loguru import logger


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


def get_people_from_config(config_file):
    with open(config_file) as f:
        current_config = json.load(f)
    return current_config.get('people', {})


def add_people_to_config(people, config_file):
    if people is None:
        logger.error('Empty people structure')
        return

    with open(config_file) as f:
        current_config = json.load(f)
    with open(config_file, 'w') as f:
        current_config['people'] = current_config.get('people', {})
        current_config['people'].update(people)
        logger.info('Adding people...')
        logger.info(json.dumps(current_config['people']))
        json.dump(current_config, f)


def get_target_nof_following(config_file=None, default=100):
    with open(config_file) as f:
        current_config = json.load(f)
    return current_config.get('target_following', default)
