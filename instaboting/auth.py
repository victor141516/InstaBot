from instaboting.driver import get_driver, wait_for_element, find_element_by_text
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By


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
        send_security_code_button.click()
        security_code = input('Check you email for security code: ')
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
