from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class Singleton:
    class __Singleton:
        def __init__(self, arg):
            self.driver = arg

        def __str__(self):
            return repr(self) + self.driver

    instance = None

    def __init__(self, arg):
        if not Singleton.instance:
            Singleton.instance = Singleton.__Singleton(arg())

    def __getattr__(self, name):
        return getattr(self.instance, name)


class InstaDriver(Singleton):
    def __init__(self):
        super().__init__(webdriver.Chrome)


def get_driver():
    return InstaDriver().instance.driver


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
