from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os


class InstaDriver:
    class __Singleton:
        def __init__(self, arg):
            self.driver = arg

        def __str__(self):
            return repr(self) + self.driver

    instance = None

    def __init__(self, remote=False):
        if not InstaDriver.instance:
            if remote:
                options = webdriver.ChromeOptions()
                options.add_argument('--user-data-dir=/tmp/chrome')
                driver = webdriver.Remote(
                    'http://instabot_selenium:4444/wd/hub',
                    options.to_capabilities())
            else:
                driver = webdriver.Chrome()
            InstaDriver.instance = InstaDriver.__Singleton(driver)

    def __getattr__(self, name):
        return getattr(self.instance, name)


def get_driver():
    remote = os.environ.get('REMOTE_SELENIUM') in [True, 'true', 'True', '1']
    return InstaDriver(remote).instance.driver


def wait_for_element(selector, timeout=5, selector_type=By.CSS_SELECTOR, from_element=get_driver()):
    return WebDriverWait(from_element, timeout).until(EC.presence_of_element_located((selector_type, selector)))


def find_element_by_text(text):
    return find_elements_by_text(text)[0]


def find_elements_by_text(text, from_element=get_driver()):
    els = from_element.find_elements_by_xpath('//*[contains(text(), \'{}\')]'.format(text))
    if len(els) == 0:
        raise NoSuchElementException('No elements containing text: {}'.format(text))
    else:
        return els


def scroll_to_bottom():
    return get_driver().execute_script("window.scrollTo(0, document.body.scrollHeight);")


def save_debug(name, and_print=False):
    logger.debug('HTML (saving to debug/{}.[html/png]):'.format(name))
    driver = get_driver()
    driver.save_screenshot('debug/{}.png'.format(name))
    html = driver.page_source
    with open('debug/{}.html'.format(name), 'w') as f:
        f.write(html)
    if and_print:
        logger.debug(html)
