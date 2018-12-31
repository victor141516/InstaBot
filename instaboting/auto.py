from instaboting import constants
from instaboting.driver import get_driver, wait_for_element
from loguru import logger
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import time


class UnestableScrapperException(Exception):
    pass


def get_suggested_people():
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
                raise e
            logger.warning('Page failed to load, reloading ({}/{})'.format(x+1, retries))
            time.sleep(2*x)
            pass

    elements = driver.find_elements_by_css_selector('article > div > div > div > div')
    names = []
    for e in elements:
        e.click()
        name = wait_for_element('article > header a[title]').get_attribute('title')
        logger.info('Found {}'.format(name))
        names.append(name)
        driver.find_element_by_css_selector('body > div > div[role=dialog] > button').click()
    return list(set(names))


def check_person(name, all_people, min_following=100, max_following=10**6, min_followers=100, max_followers=5000, min_ratio=0.5, max_ratio=20):
    person = all_people.get(name, {})
    if person.get('status', constants.NOT_CHECKED) != constants.NOT_CHECKED:
        logger.info('{} has previously been seen, with status: {}. Skipping'.format(name, all_people[name]))
        return person

    driver = get_driver()
    driver.get('https://www.instagram.com/{}'.format(name))
    logger.info('{} has not previously been seen, checking'.format(name))
    followers_text = driver.find_element_by_css_selector('header > section > ul > li:nth-child(2)').text
    following_text = driver.find_element_by_css_selector('header > section > ul > li:nth-child(3)').text

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


def follow_person_by_name(name):
    driver = get_driver()
    logger.info('Following {}'.format(name))
    driver.get('https://www.instagram.com/{}'.format(name))
    follow_button_candidates = driver.find_elements_by_css_selector('header span button')
    for c in follow_button_candidates:
        if len(c.find_elements_by_css_selector('div')) == 0:
            follow_button = c
            break

    if c.text == 'Following':
        logger.info('Already followed')
        return constants.ALREADY_FOLLOWING

    c.click()
    try:
        wait_for_element(
            '//*[contains(text(), \'Following\')]',
            selector_type=By.XPATH,
            from_element=driver.find_element_by_css_selector(
                'header > section > div:nth-child(1) > span'
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
