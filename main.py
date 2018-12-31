from configuration import get_plain_credentials, add_people_to_config, get_people_from_config, get_target_nof_following
import instaboting
import json
from loguru import logger
import signal
import sys

CONFIG_FILE = 'config.json'
global PEOPLE


def exit_handler(sig=None, frame=None):
    global PEOPLE
    logger.info('Exiting...')
    instaboting.driver.get_driver().close()
    add_people_to_config(PEOPLE, CONFIG_FILE)
    sys.exit(0)

signal.signal(signal.SIGINT, exit_handler)


def main_loop():
    global PEOPLE
    PEOPLE = get_people_from_config(CONFIG_FILE)
    suggested_people = instaboting.auto.get_suggested_people()
    for name in suggested_people:
        PEOPLE[name] = {'status': instaboting.constants.NOT_CHECKED}

    for name in PEOPLE:
        PEOPLE[name].update(instaboting.auto.check_person(name, PEOPLE))
        if PEOPLE[name]['status'] == instaboting.constants.SHOULD_FOLLOW:
            PEOPLE[name]['status'] = instaboting.auto.follow_person_by_name(name)


def main():
    global PEOPLE
    credentials = get_plain_credentials(CONFIG_FILE)
    instaboting.auth.login(credentials.username, credentials.password)

    target_nof_following = get_target_nof_following(CONFIG_FILE)
    current_following_number = instaboting.auto.get_current_following_number()
    while current_following_number < target_nof_following:
        logger.info('Current following number: {}'.format(current_following_number))
        try:
            main_loop()
        except instaboting.auto.UnestableScrapperException as e:
            if e.args[1] == instaboting.constants.ERROR_TIMEOUT_SUGGESTED:
                continue
            else:
                raise e
        current_following_number = instaboting.auto.get_current_following_number()
    logger.info('Target following number ({}) reached: {}'.format(target_nof_following, current_following_number))


try:
    main()
except Exception as e:
    logger.critical('{} occurred, printing traceback and exiting'.format(str(type(e))))
    logger.critical(e)
finally:
    exit_handler()
