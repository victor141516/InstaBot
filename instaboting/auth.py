import configuration
from instaboting.driver import get_driver, wait_for_element, find_element_by_text
from json.decoder import JSONDecodeError
from loguru import logger
import requests
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
import time

GETTT_ENDPOINT = 'https://gettt.viti.site/get?t={token}&q={term}'


class LoginFailedException(Exception):
    pass


def login(username, password):
    driver = get_driver()
    driver.get('https://www.instagram.com/accounts/login/')
    wait_for_element('input[name=username]')
    username_input = driver.find_element_by_name('username')
    password_input = driver.find_element_by_name('password')
    username_input.send_keys(username)
    password_input.send_keys(password)
    login_button = driver.find_element_by_css_selector('button[type=submit]')
    login_button.click()

    try:
        wait_for_element('//*[contains(text(), \'Send Security Code\')]', selector_type=By.XPATH)
        send_security_code_button = find_element_by_text('Send Security Code')
        prev_code = get_gettt_code()
        send_security_code_button.click()
        if prev_code is None:
            security_code = input('Check you email for security code: ')
        else:
            logger.debug('Getting security code using Gettt')
            iterations = 0
            while True:
                new_code = get_gettt_code()
                if new_code != prev_code:
                    security_code = new_code
                    logger.info('Security code: {}'.format(security_code))
                    break
                else:
                    if iterations == 60:
                        logger.warning('Could not retrieve security code using Gettt, please type it manually')
                        security_code = input('Check you email for security code: ')
                    time.sleep(5)
                    iterations += 1
        security_code_input = driver.find_element_by_name('security_code')
        security_code_input.send_keys(security_code)
        submit_button = driver.find_element_by_css_selector('form button')
        submit_button.click()
    except TimeoutException as e:
        pass

    try:
        wait_for_element('span[aria-label=Profile]')
    except TimeoutException as e:
        raise LoginFailedException('Could not log in correctly')


def get_gettt_code():
    token = configuration.get_gettt_token()
    if token is None:
        return None

    default_code = 'AAAAAA'
    url = GETTT_ENDPOINT.format(token=token, term='Instagram')
    result = requests.get(url)
    try:
        result = result.json()
    except JSONDecodeError:
        return default_code

    if len(result) == 0:
        return default_code

    result = result[0]['text/html']
    code = result.split('<font size="6">')[-1].split('</font>')[0]
    if len(code) != 6:
        return default_code

    return code
