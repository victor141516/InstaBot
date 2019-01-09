from configuration import get_plain_credentials, get_target_nof_following, get_db, get_slowmo, get_show_html_if_error
import instaboting
import json
from loguru import logger
import signal
import sys
import time
import traceback

CONFIG_FILE = 'config.json'
global PEOPLE
PEOPLE = get_db()


def exit_handler(sig=None, frame=None):
    logger.info('Exiting...')
    instaboting.driver.get_driver().close()
    sys.exit(0)

signal.signal(signal.SIGINT, exit_handler)


def main_loop(nof_scrolls=0):
    global PEOPLE
    suggested_people = instaboting.auto.get_suggested_people(nof_scrolls=nof_scrolls)

    already_seen_people = 0
    for name in suggested_people:
        if name in PEOPLE:
            already_seen_people += 1
            logger.debug('{} already seen. Increase already_seen_people: {}'.format(name, str(already_seen_people)))
            suggested_people.remove(name)
        else:
            PEOPLE[name] = {'status': instaboting.constants.NOT_CHECKED}

    for name in PEOPLE:
        this_person = PEOPLE[name]
        this_person.update(instaboting.auto.check_person(name, PEOPLE))
        PEOPLE[name] = this_person
        if PEOPLE[name]['status'] == instaboting.constants.SHOULD_FOLLOW:
            PEOPLE[name]['status'] = instaboting.auto.follow_person_by_name(name)

    return already_seen_people / len(suggested_people)


def main():
    credentials = get_plain_credentials(CONFIG_FILE)
    instaboting.auth.login(credentials.username, credentials.password)

    target_nof_following = get_target_nof_following(CONFIG_FILE)
    current_following_number = instaboting.auto.get_current_following_number()
    next_nof_scrolls = 0
    while current_following_number < target_nof_following:
        logger.info('Current following number: {}'.format(current_following_number))
        try:
            current_seen_ratio = main_loop(next_nof_scrolls)
            logger.info('Current seen ratio: {}'.format(current_seen_ratio))
            if current_seen_ratio > 0.5:
                next_nof_scrolls += 1
                logger.info('####### Increasing nomber of scrolls: {} '.format(next_nof_scrolls))
        except instaboting.auto.UnestableScrapperException as e:
            if e.args[1] == instaboting.constants.ERROR_TIMEOUT_SUGGESTED:
                continue
            else:
                raise e
        current_following_number = instaboting.auto.get_current_following_number()
        time.sleep(get_slowmo())
    logger.info('Target following number ({}) reached: {}'.format(target_nof_following, current_following_number))


try:
    main()
except Exception as e:
    logger.critical('{} occurred, printing traceback and exiting'.format(str(type(e))))
    logger.critical(traceback.format_exc())
    driver = instaboting.driver.get_driver()
    logger.debug('HTML (saving to debug/page.html/png):')
    driver.save_screenshot('debug/page.png')
    html = driver.page_source
    with open('debug/page.html', 'w') as f:
        f.write(html)
    if get_show_html_if_error():
        logger.debug(html)
finally:
    exit_handler()
