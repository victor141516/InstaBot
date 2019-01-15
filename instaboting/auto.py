from datetime import datetime
from instaboting import constants
from instaboting.driver import get_driver, wait_for_element, scroll_to_bottom, save_debug
from loguru import logger
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.by import By
import time
import traceback


class UnestableScrapperException(Exception):
    pass


def get_suggested_people(nof_scrolls=0):
    def _fetch():
        current_nof_people_in_page = len(driver.find_elements_by_css_selector(PROFILES_SELECTOR))
        for x in range(0, 50):
            new_nof_people_in_page = len(driver.find_elements_by_css_selector(PROFILES_SELECTOR))
            if new_nof_people_in_page == current_nof_people_in_page:
                time.sleep(0.2)
            else:
                current_nof_people_in_page = new_nof_people_in_page
                break

        time.sleep(0.5)

        elements = driver.find_elements_by_css_selector(PROFILES_SELECTOR)
        for el in elements:
            try:
                el.location_once_scrolled_into_view
                el.click()
            except (StaleElementReferenceException, WebDriverException):
                logger.warning('Could not click profile')
                break

            try:
                name = wait_for_element('article > header a[title]').get_attribute('title')
            except TimeoutException as e:
                logger.warning('Error getting name after profile click')
                continue

            logger.info('Found {}'.format(name))
            names.append(name)
            driver.find_element_by_css_selector('body > div > div[role=dialog] > button').click()

    PROFILES_SELECTOR = 'article > div > div > div > div'
    retries = 10
    driver = get_driver()
    driver.get('https://www.instagram.com/explore/')
    logger.info('Exploring...')

    for x in range(0, retries):
        try:
            wait_for_element('article')  # This page fails sometimes
            break
        except TimeoutException as e:
            if x+1 == retries:
                raise UnestableScrapperException('Suggested page failed to load', constants.ERROR_TIMEOUT_SUGGESTED)
            logger.warning('Page failed to load, reloading ({}/{})'.format(x+1, retries))
            time.sleep(2*x)
            return get_suggested_people(nof_scrolls)

    names = []
    _fetch()
    for x in range(0, nof_scrolls):
        scroll_to_bottom()
        _fetch()

    return list(set(names))


def check_person(name, all_people, min_following=100, max_following=10**6, min_followers=100, max_followers=5000, min_ratio=0.5, max_ratio=20, _recursion=0):
    person = all_people.get(name, {})
    if person.get('status', constants.NOT_CHECKED) != constants.NOT_CHECKED:
        logger.debug('{} has previously been seen, with status: {}. Skipping'.format(name, all_people[name]))
        return person

    driver = get_driver()
    driver.get('https://www.instagram.com/{}'.format(name))
    logger.info('{} has not previously been seen, checking'.format(name))
    try:
        followers_text = driver.find_element_by_css_selector('header > section > ul > li:nth-child(2)').text
        following_text = driver.find_element_by_css_selector('header > section > ul > li:nth-child(3)').text
    except NoSuchElementException as e:
        h2s = driver.find_elements_by_css_selector('h2')
        if len(h2s) == 1 and 'Sorry, this page isn\'t available.' in h2s[0].text:
            if _recursion < 3:
                logger.debug('Error trying to check person, retry')
                return check_person(name, all_people, min_following, max_following, min_followers, max_followers, min_ratio, max_ratio, _recursion=_recursion+1)
            else:
                logger.warning('Multiple error trying to check person, skipping')
                return {'status': constants.SHOULD_NOT_FOLLOW}
        logger.warning('Cannot find followings or followers')
        logger.debug('Traceback:')
        logger.debug(traceback.format_exc())
        logger.debug('HTML of that section:')
        maybe_header = driver.find_elements_by_css_selector('header')
        if (len(maybe_header) == 0):
            save_debug(message='Header not found, saving screenshot')
        else:
            logger.debug(maybe_header[0]('header').source)
        return {'status': constants.NOT_CHECKED}

    if 'followers' not in followers_text or 'following' not in following_text:
        raise UnestableScrapperException('Could not find followes/following correctly')

    followers_text = followers_text.split(' followers')[0].replace(',', '')
    multiplier = 1
    if 'k' in followers_text:
        multiplier *= 1000
        followers_text = followers_text[:-1]
    if 'm' in followers_text:
        multiplier *= 1000000
        followers_text = followers_text[:-1]
    followers = int(float(followers_text) * multiplier)

    following_text = following_text.split(' following')[0].replace(',', '')
    multiplier = 1
    if 'k' in followers_text:
        multiplier *= 1000
        followers_text = followers_text[:-1]
    if 'm' in followers_text:
        multiplier *= 1000000
        followers_text = followers_text[:-1]
    following = int(float(following_text) * multiplier)

    follow_button = _get_follow_button()
    try:
        follow_button_text = follow_button.text
    except StaleElementReferenceException:
        logger.warning('Could not get follow button text')
        return {
            'status': constants.CANNOT_FOLLOW,
            'numbers': {
                'followers': followers,
                'following': following
            }
        }

    if follow_button:
        if follow_button_text == 'Follow Back':
            return {
                'status': constants.PREVIOUSLY_FOLLOWS_ME,
                'numbers': {
                    'followers': followers,
                    'following': following
                }
            }

        if follow_button_text in ['Following', 'Requested']:
            return {
                'status': constants.ALREADY_FOLLOWING,
                'numbers': {
                    'followers': followers,
                    'following': following
                }
            }

    result = min_following < following < max_following \
        and min_followers < followers < max_followers \
        and min_ratio < following/followers < max_ratio
    if result:
        logger.info('!!!!! Should follow {}'.format(name))
    else:
        logger.info('Should not follow {}'.format(name))
    return {
        'status': constants.SHOULD_FOLLOW if result else constants.SHOULD_NOT_FOLLOW,
        'numbers': {
            'followers': followers,
            'following': following
        }
    }


def _get_follow_button():
    driver = get_driver()
    follow_button_candidates = driver.find_elements_by_css_selector('header button')
    for c in follow_button_candidates:
        try:
            if c.text in ['Follow', 'Following']:
                return c
        except StaleElementReferenceException as e:
            logger.debug('Skipping exception while searching follow button:')
            logger.debug(e)
            pass


def follow_person_by_name(name):
    driver = get_driver()
    logger.info('Following {}'.format(name))
    driver.get('https://www.instagram.com/{}'.format(name))
    follow_button = _get_follow_button()

    if follow_button is None:
        save_debug(message='Could not find follow button')
        return constants.CANNOT_FOLLOW

    if follow_button.text == 'Following':
        logger.info('Already followed')
        return constants.ALREADY_FOLLOWING

    follow_button.click()
    try:
        wait_for_element(
            '//*[contains(text(), \'Following\')]',
            selector_type=By.XPATH,
            from_element=driver.find_element_by_css_selector(
                'header > section > div:nth-child(1)'
            )
        )
        logger.info('Followed!')
        return constants.NEW_FOLLOWING
    except TimeoutException as e:
        logger.error('Could not follow')
        return constants.CANNOT_FOLLOW


def get_current_following_number():
    driver = get_driver()
    profile_link = wait_for_element('span[aria-label=Profile]').find_element_by_xpath('..').get_attribute('href')
    driver.get(profile_link)
    return int(wait_for_element('header > section > ul > li:nth-child(3) > a > span').text)


def unfollow_everyone():
    driver = get_driver()
    driver.get('https://www.instagram.com/cacapedo__/')
    wait_for_element('section > main > div > header > section > ul > li:nth-child(3) > a').click()
    wait_for_element('div[role="dialog"] ul li button')
    first_person = driver.find_elements_by_css_selector('div[role="dialog"] ul li button')[0]
    first_person.location_once_scrolled_into_view
    following_classes = first_person.get_attribute('class').split(' ')
    first_person.click()
    wait_for_element('div[role=presentation] > div[role=dialog] > div > div > button:nth-child(1)').click()
    first_person = driver.find_elements_by_css_selector('div[role="dialog"] ul li button')[0]
    while True:
        not_following_classes = first_person.get_attribute('class').split(' ')
        following_class = list(set(following_classes).difference(set(not_following_classes)))
        if len(following_class) == 0:
            time.sleep(0.5)
            continue
        following_class = following_class[0]
        break

    following_people = driver.find_elements_by_css_selector('div[role="dialog"] ul li button.{}'.format(following_class))
    for person in following_people:
        try:
            person.location_once_scrolled_into_view
            person.click()
            wait_for_element('div[role=presentation] > div[role=dialog] > div > div > button:nth-child(1)').click()
        except (StaleElementReferenceException, TimeoutException):
            break
        while True:
            if len(person.find_elements_by_css_selector('svg')) > 0:
                time.sleep(0.5)
            else:
                break

    driver.get('https://www.instagram.com/cacapedo__/')
    if int(wait_for_element('section > main > div > header > section > ul > li:nth-child(3) > a > span').text) > 0:
        unfollow_everyone()
