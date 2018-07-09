from selenium import webdriver
from selenium.webdriver.common.by import By #1
from selenium.webdriver.support.ui import WebDriverWait #2
from selenium.webdriver.support import expected_conditions as EC #3
from pyvirtualdisplay import Display
#from seleniumrequests import Firefox
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

from lxml import html
import time

def get_driver():
    display = Display(visible=0, size=(800,600))
    display.start()
    chrome_options = Options()
    chrome_options.add_argument("--dns-prefetch-disable")
    chrome_options.add_argument('headless')
    chrome_options.add_argument('no-sandbox')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.set_page_load_timeout(15)
    return driver

def open_home_page(driver):
    cfg_lists = []
    for i in range(10):
        driver.get("https://booking2.airasia.com/AgentHome.aspx")
        driver.wait = WebDriverWait(driver, 5)
        time.sleep(5)
        try:
            usr = driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_TextBoxUserID")
        except:
            print 'Tried to locate an element to confirm page is loaded and failed'
            continue
        print 'Located element and cookie will be added to cfg file'
        cookies_dict = driver.get_cookie('i10c.bdddb')
        cookie = cookies_dict.get('value', '')
        if cookie:
            cfg_lists.append(cookie)
    with open('airasia_login_cookie.py', 'w') as f:
        f.write('airasia_login_cookie_list = %s' % cfg_lists)
    print 'config file updated with cookies'
    driver.quit()

def main():
    driver = get_driver()
    open_home_page(driver)


if __name__ == "__main__":
    main()
