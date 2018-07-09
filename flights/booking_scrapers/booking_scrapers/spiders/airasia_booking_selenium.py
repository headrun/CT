import re
import time
import json
import md5
import random
import smtplib
import MySQLdb
import datetime
from random import randint
import smtplib
import ssl
from email import encoders
from airasia_xpaths import *
from ast import literal_eval
from scrapy import signals
from booking_scrapers.utils import *
from scrapy.spider import Spider
from collections import OrderedDict
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from scrapy.http import FormRequest, Request
from email.mime.multipart import MIMEMultipart
from scrapy.selector import Selector
from ConfigParser import SafeConfigParser
from scrapy.xlib.pydispatch import dispatcher
from airasia_utils import *

from scrapy.conf import settings

from indigo_utils import IndigoUtils

import sys
sys.path.append(settings['ROOT_PATH'])
from airasia_login_cookie import airasia_login_cookie_list

_cfg = SafeConfigParser()
_cfg.read(settings['BOOK_PCC_PATH'])
counter = 0
from scrapy.utils.response import open_in_browser
from selenium.webdriver.firefox.options import Options

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
import unittest, time, re


class AirAsiaBookingBrowse(Spider, AirAsiaUtils, IndigoUtils):
    name = "airasia_booking_selenium"
    start_urls = ["https://booking2.airasia.com/AgentHome.aspx"]
    handle_httpstatus_list = [404, 500, 400, 403]

    def __init__(self, *args, **kwargs):
        super(AirAsiaBookingBrowse, self).__init__(*args, **kwargs)
        self.price_patt = re.compile('\d+')
        self.log = create_logger_obj('airasia_booking')
        self.booking_dict = kwargs.get('jsons', {})
        self.ow_input_flight = self.rt_input_flight = {}
        self.ow_fullinput_dict = self.rt_fullinput_dict = {}
        self.proceed_to_book = 0
        self.tolerance_amount = 0
        self.book_using = ''
        self.multiple_pcc = False
        self.pnrs_tobe_checked = []
        self.pnrs_checked = []
        self.auto_book_dict = {}
        self.queue = ''
        self.pcc_name = ''
        self.garbage_retry = 0
        self.logout_view_state = ''
        self.logout_cookies = {}
        self.air_insert_query = 'insert into airasia_booking_report (sk, airline, pnr, flight_number, from_location, to_location, triptype, cleartrip_price, airasia_price, status_message, tolerance_amount, oneway_date, return_date, error_message, paxdetails, price_details, created_at, modified_at) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(), now()) on duplicate key update modified_at=now(), sk=%s, airline=%s, pnr=%s, flight_number=%s, from_location=%s, to_location=%s, triptype=%s, cleartrip_price=%s, airasia_price=%s, status_message=%s, tolerance_amount=%s, oneway_date=%s, return_date=%s, error_message=%s, paxdetails=%s, price_details=%s'
        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('booking', 'IP')
        passwd = db_cfg.get('booking', 'PASSWD')
        user = db_cfg.get('booking', 'USER')
        db_name = db_cfg.get('booking', 'DBNAME')
        self.conn = MySQLdb.connect(
            host=host, user=user, passwd=passwd, db=db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()
        self.headers = {
            'pragma': 'no-cache',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-GB,en-US;q=0.8,en;q=0.6',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'cache-control': 'no-cache',
            'authority': 'booking2.airasia.com',
        }
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()
        self.driver.quit()
        import requests
        data = [
            ('__EVENTTARGET', 'MemberLoginAgentHomeView$LinkButtonLogOut'),
            ('__EVENTARGUMENT', ''),
            ('__VIEWSTATE', self.logout_view_state),
            ('pageToken', ''),
            ('__VIEWSTATEGENERATOR', '05F9A2B0'),
        ]
        response = requests.post('https://booking2.airasia.com/AgentHome.aspx',
                                 headers=self.headers, cookies=self.logout_cookies, data=data)

    def insert_into_db(self, book_dict, error):
        flight_ids = str(book_dict.get('flights', str([])))
        pricing_details = book_dict.get('price_details', json.dumps({}))
        if isinstance(pricing_details, dict):
            pricing_details = json.dumps(pricing_details)
        status_message = book_dict.get('status_message', "Booking Failed")
        airasia_price = book_dict.get('airasia_price', '')
        pnr = book_dict.get('pnr', '')
        tolerance_value = book_dict.get('tolerance_value', '')
        ctprice = book_dict.get('ctprice', '')
        tripid = book_dict.get('tripid', '')
        origin = book_dict.get('origin', '')
        if not origin:
            origin = book_dict.get('origin_code', '')
        destination = book_dict.get('destination', '')
        if not destination:
            destination = book_dict.get('destination_code', '')
        oneway_date = ''
        return_date = ''
        if book_dict.get('triptype', ''):
            trip_type = '%s_%s_%s' % (book_dict.get(
                'triptype', ''), self.queue, self.book_using)
        else:
            trip_type = ''
        try:
            book_dict['garbage_retry'] = self.garbage_retry
        except:
            pass
        if not tripid:
            tripid = book_dict.get('trip_ref', '')
        vals = (tripid, 'AirAsia', pnr, flight_ids, origin, destination, trip_type, ctprice,
                airasia_price, status_message, tolerance_value, oneway_date,
                return_date, error, json.dumps(book_dict), pricing_details,
                tripid, 'AirAsia', pnr, flight_ids, origin, destination, trip_type, ctprice,
                airasia_price, status_message, tolerance_value, oneway_date,
                return_date, error, json.dumps(book_dict), pricing_details,
                )
        self.cur.execute(self.air_insert_query, vals)

    def date_picker(self, driver, book_dict):
        try:
            ow_date = book_dict.get('onewaydate', '')
            print ow_date
            day, month, year, month_name = self.date_month_year(ow_date)
            print day, month, year
	    driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchViewdate_picker_display_id_1").click()
            for i in range(10):
                try:
                    sel = Selector(text=driver.page_source)
                    year_text = ''.join(sel.xpath('//select[@class="datepicker_newYear"]/option[@selected="selected"]//text()').extract())
                    month_text = ''.join(sel.xpath('//select[@class="datepicker_newMonth"]/option[@selected="selected"]//text()').extract())
                    if month_name == month_text and str(year) == year_text:
                        driver.find_element_by_link_text("%s"%day).click()
                        time.sleep(1)
                        driver.find_element_by_id("flightSearchContainer").click()
                        break
                    time.sleep(2)
                    driver.find_element_by_link_text(">>").click()
                except:
                    pass
                    #driver.find_element_by_link_text(">>").click()
            rt_date = book_dict.get('returndate', '')
            print rt_date
            if rt_date:
                re_day, re_month, re_year, re_month_name = self.date_month_year(rt_date)
                for i in range(10):
                    try:
                        time.sleep(2)
                        driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchViewdate_picker_display_id_2").click()
                        if month == re_month:
                            driver.find_element_by_link_text("%s"%re_day).click()
                            time.sleep(1)
                            driver.find_element_by_id("flightSearchContainer").click()
                            break
                        else:
                            sel = Selector(text=driver.page_source)
                            re_year_text = ''.join(sel.xpath('//select[@class="datepicker_newYear"]/option[@selected="selected"]//text()').extract())
                            re_month_text = ''.join(sel.xpath('//select[@class="datepicker_newMonth"]/option[@selected="selected"]//text()').extract())
                            if re_month_name == re_month_text and re_year_text == str(re_year):
                                driver.find_element_by_link_text("%s"%re_day).click()
                                time.sleep(1)
                                driver.find_element_by_id("flightSearchContainer").click()
                                break
                            driver.find_element_by_link_text(">>").click()
                            time.sleep(2)
                            break
                    except:
                        pass
            return (driver, "")
        except:
            return (driver, "Failed to select date")

    def select_pax(self, driver, book_dict):
        try:
            no_of_adults = self.booking_dict.get('no_of_adults', 0)
            if no_of_adults == 1 or no_of_adults == '1':
                adult_text = 'Adult'
            else:
                adult_text = 'Adults'
            no_of_child = self.booking_dict.get('no_of_children', 0)
            if no_of_child == '1' or no_of_child == 1:
                child_text = 'Child'
            else:
                child_text = 'Children'
            no_of_child = self.booking_dict.get('no_of_children', 0)
            driver.implicitly_wait(50)
            Select(driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_DropDownListPassengerType_ADT")).select_by_visible_text("%s %s"%(no_of_adults, adult_text))
            driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_DropDownListPassengerType_ADT").click()
	    driver.implicitly_wait(100)    
            Select(driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_DropDownListPassengerType_CHD")).select_by_visible_text("%s %s"%(no_of_child, child_text))
            driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_DropDownListPassengerType_CHD").click()
	    driver.implicitly_wait(100)
            driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_DropDownListPassengerType_INFANT").click()
            driver.find_element_by_id("ControlGroupSearchView_ButtonSubmit").click()
            return (driver, "")
        except:
            return (driver, "Failed to fetch Pax")

    def date_month_year(self, date_):
        date = datetime.datetime.strptime(date_, '%Y-%m-%d')
        month_name = date.strftime('%Y-%B-%d')
        month_name = month_name.split('-')[1]
        return (str(date.day), str(date.month).lstrip('0'), str(date.year), month_name)

    def flight_search(self, driver, book_dict):
        try:
            temp = False
            origin = self.booking_dict.get('origin_code', '')
            dest = self.booking_dict.get('destination_code', '')
            if self.booking_dict.get('trip_type') == 'OW':
                driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_OneWay").click()
            elif self.booking_dict.get('trip_type') == 'RT':
                driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_RoundTrip").click()
            driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchVieworiginStationMultiColumn1_1").click()
            driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchVieworiginStationMultiColumn1_1").clear()
            driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchVieworiginStationMultiColumn1_1").send_keys(origin)
	    #driver.find_element_by_id("SkySales").submit()
            #ori_id.send_keys(origin)
            #ori_id.send_keys(Keys.RETURN)
            #ori_id.send_keys(Keys.ENTER)
            #site_ori = driver.find_element_by_xpath("//p[@id='originStationContainer1']/div/div[2]/div/div[2]/ul/li[2]/a/b").text
            #if site_ori == origin:
            driver.find_element_by_xpath("//p[@id='originStationContainer1']/div/div[2]/div/div[2]/ul/li[2]/a/b").click()
            time.sleep(2)
            #else:
            driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchViewdestinationStationMultiColumn1_1").click()
            driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchViewdestinationStationMultiColumn1_1").clear()
            driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchViewdestinationStationMultiColumn1_1").send_keys(dest)
            #dest_id.send_keys(dest)
	    #driver.find_element_by_id("SkySales").submit()
            #dest_id.send_keys(Keys.RETURN)
            #dest_id.send_keys(Keys.ENTER)
            #site_dest = driver.find_element_by_xpath("//p[@id='destinationStationContainer1']/div/div[2]/div/div[2]/ul/li[2]/a/b").text
            driver.find_element_by_xpath("//p[@id='destinationStationContainer1']/div/div[2]/div/div[2]/ul/li[2]/a/b").click()
            print dest
	    time.sleep(1)
	    #driver.find_element_by_id("flightSearchContainer").click()
            #return (driver, 'Failed to load segments')
            driver, error_ = self.date_picker(driver, book_dict)
            driver, error = self.select_pax(driver, book_dict)
            return (driver, error, error_)
        except:
            return (driver, "Failed to load segments", '')

    def start_driver(self):
        #self.driver = webdriver.Firefox()
        options = Options()
        options.add_argument('--headless')
        self.fp  = webdriver.FirefoxProfile()
        self.driver= webdriver.Firefox(firefox_profile=self.fp, firefox_options=options)
        #self.driver = webdriver.PhantomJS()

    def check_login_status(self, driver):
        sel = Selector(text=driver.page_source)
        login_failed = ''.join(sel.xpath('//div[@id="errorSectionContent"]//text()').extract())
        if 'user/agent ID you entered is not valid' in login_failed:
            status = True
        else: status = False
        return status

    def go_with_selenium(self):
        self.pcc_name, book_dict = self.get_pcc_name()

        if book_dict.get('queue', '') == 'coupon':
            self.pcc_name = 'airasia_coupon_default'
        try:
            logging.debug('Booking using: %s' %
                          _cfg.get(self.pcc_name, 'username'))
        except:
            pass
        if self.multiple_pcc:
            logging.debug('Multiple PCC booking')
            self.insert_into_db(book_dict, "Multiple PCC booking")
            return
        else:
            try:
                user_name = _cfg.get(self.pcc_name, 'username')
                user_psswd = _cfg.get(self.pcc_name, 'password')
                self.book_using = user_name
            except:
                self.insert_into_db(book_dict, "PCC credentials not found")
                return
        try:
            book_dict = self.process_input()
        except Exception as e:
            logging.debug(e.message)
            self.insert_into_db(book_dict, e.message)
            #self.send_mail('AirAsia Booking Faild', e.message)
            return
        self.start_driver()
        driver = self.driver
        #*****************login**********************************************
        driver.get("https://booking2.airasia.com/AgentHome.aspx")
	driver.implicitly_wait(100)
	time.sleep(20)
	driver.implicitly_wait(100)
        driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_TextBoxUserID").click()
        driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_TextBoxUserID").clear()
        driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_TextBoxUserID").send_keys(user_name)
        driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_PasswordFieldPassword").click()
        driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_PasswordFieldPassword").clear()
        driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_PasswordFieldPassword").send_keys(user_psswd)
        driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_LinkButtonLogIn").click()
        #***********************book my flight ********************************
        driver.implicitly_wait(100)
	time.sleep(20)
	driver.implicitly_wait(100)
        try:driver.find_element_by_xpath('//a[@id="Search"]').click()
        except:
            logging.debug("I5 search buttom not found %s"%book_dict.get('tripid', ''))
	    self.insert_into_db(book_dict, "Failed to click book my flight")
	    driver.save_screenshot("%s_book_my_flight.png"%book_dict.get('tripid', ''))
        #***********************search page **********************************
        driver.implicitly_wait(100)
	time.sleep(20)
        login_status = self.check_login_status(driver)
        if login_status:
            logging.debug("I5 Login Failed %s"%book_dict.get('tripid', ''))
            self.insert_into_db(book_dict, "Login Failed")
            return
        driver, error, date_picker_error = self.flight_search(driver, book_dict)#flight search
        driver, ow_flt_id, rt_flt_id, search_status = self.select_flight(driver, book_dict)#select flights
        if not search_status:
            driver, ow_flt_id, rt_flt_id, search_status = self.select_flight(driver, book_dict)#select flights
        if not search_status:
            logging.debug("I5 Failed to seasrch flights %s"%book_dict.get('tripid', ''))
            driver.save_screenshot("%s_search_flight.png"%book_dict.get('tripid', ''))
            self.insert_into_db(book_dict, "Failed to search flights")
            return
        if date_picker_error:
            logging.debug("I5 date not loaded %s"%book_dict.get('tripid', ''))
            driver.save_screenshot("%s_search_flight.png"%book_dict.get('tripid', ''))
            self.insert_into_db(book_dict, error)
            return
        if self.booking_dict.get('trip_type') == 'OW':
            if ow_flt_id:
                driver.find_element_by_id(ow_flt_id).click()
                driver.find_element_by_id("ControlGroupSelectView_ButtonSubmit").click()
            else:
                driver.save_screenshot("%s_flight.png"%book_dict.get('tripid', ''))
                logging.debug("I5 Flightsresponse not loaded %s"%book_dict.get('tripid', ''))
		print error, book_dict.get('tripid', '')
		logging.debug("I5 %s %s"%(book_dict.get('tripid', ''), error))
                self.insert_into_db(book_dict, "Failed to load flights response")
                return
        else:
            if rt_flt_id:
                driver.find_element_by_id(ow_flt_id).click()
                driver.find_element_by_id("ControlGroupSelectView_ButtonSubmit").click()
            else:
                logging.debug("I5 Flights not found %s"%book_dict.get('tripid', ''))
                print "Flights not found"
		logging.debug("I5 %s %s"%(book_dict.get('tripid', ''), error))
		print error, book_dict.get('tripid', '')
                self.insert_into_db(book_dict, "Flights not found")
		driver.save_screenshot("%s_flight_notfound.png"%book_dict.get('tripid', ''))
                return
        driver, error = self.form_filling(driver, book_dict)
        if error:
            print error
            logging.debug("I5 flights not found %s"%book_dict.get('tripid', ''))
	    logging.debug("I5 %s %s"%(book_dict.get('tripid', ''), error))
            self.insert_into_db(book_dict, "Failed to fill the pax details")
	    driver.save_screenshot("%s_pax_page.png"%book_dict.get('tripid', ''))
            return
        driver, book_dict, tolerence_status, error = self.tolerance_check(driver, book_dict)
        if not error:
            if tolerence_status == 1 or tolerence_status == '1':
                try:
                    time.sleep(10)
                    driver.implicitly_wait(100)
		    driver.implicitly_wait(200)
                    driver.find_element_by_id("CONTROLGROUPADDONSFLIGHTVIEW_ButtonSubmit").click()#addon
                except:
                    self.insert_into_db(book_dict, "Add on page not loaded")
                    logging.debug("I5 Add on page not loaded  %s"%book_dict.get('tripid', ''))
		    driver.save_screenshot("%s_addon_page.png"%book_dict.get('tripid', ''))
                    return
            else:
                logging.debug("I5 Fare increased by airline  %s"%book_dict.get('tripid', ''))
                self.insert_into_db(book_dict, "Fare increased by airline")
                return
        else:
            logging.debug("I5 %s  %s"%(error, book_dict.get('tripid', '')))
            self.insert_into_db(book_dict, error)
            return
        if not error:
            try:
                time.sleep(10)
                driver.implicitly_wait(100)
		driver.implicitly_wait(200)
                driver.find_element_by_id("ControlGroupUnitMapView_UnitMapViewControl_LinkButtonAssignUnit").click()#unitmap
            except:
                self.insert_into_db(book_dict, "Failed to load payment page")
                logging.debug("I5 Failed to load payment page %s"%book_dict.get('tripid', ''))
		driver.save_screenshot("%s_payment_page.png"%book_dict.get('tripid', ''))
                return
        else:
            self.insert_into_db(book_dict, error)
            return
        try:
	    time.sleep(10)
	    time.sleep(20)
	    driver.implicitly_wait(200)
	    driver.implicitly_wait(100)
            driver.find_element_by_id("AgencyAccount").click()#agency ac
        except:
            self.insert_into_db(book_dict, "Failed to load AgencyAccount")
            logging.debug("I5 Failed to load AgencyAccount %s"%book_dict.get('tripid', ''))
	    driver.save_screenshot("%s_agency_account.png"%book_dict.get('tripid', ''))
            return
        driver, book_dict = self.get_response_details(driver, book_dict)
        if int(self.proceed_to_book) == 1:
            print "Go to payment"
            try:
                driver.save_screenshot("%s_payment_flight.png"%book_dict.get('tripid', ''))
                driver.implicitly_wait(100)
                driver.find_element_by_id("ButtonSubmitProxy").click()
		time.sleep(20)
		driver.implicitly_wait(100)
                driver.save_screenshot("%s_post_payment_flight.png"%book_dict.get('tripid', ''))
                driver, book_dict, status = self.get_pnr_resposne(driver, book_dict)
                time.sleep(10)
                if status == "Unknown":
                    driver, book_dict, status = self.get_pnr_resposne(driver, book_dict)
                if status == "Unknown":
                    self.insert_into_db(book_dict, 'Payment failed whereas payment is successful')
                else:
                    self.insert_into_db(book_dict, '')
                driver.save_screenshot("%s_post_payment_flight.png"%book_dict.get('tripid', ''))
            except:
                logging.debug("I5 Payment failed whereas payment is successful %s"%book_dict.get('tripid', ''))
                self.insert_into_db(book_dict, 'Payment failed whereas payment is successful')
        else:
            driver.save_screenshot("%s_payment_flight.png"%book_dict.get('tripid', ''))
            flt_no = book_dict.get('ow_flt', '').replace('<>', ' ').strip()
            rt_flt_no = book_dict.get('rt_flt', '').replace('<>', ' ').strip()
            flt = [flt_no, rt_flt_no]
            pnr_no, conform, pax_details = '100', 'Mock is Successful', ''
            book_dict['pnr'] = pnr_no
            trip_type_ = '%s_%s_%s' % (book_dict.get(
                'triptype', ''), self.queue, self.book_using)
            self.insert_into_db(book_dict, 'Mock is Successful')
            print "test booking"

    def form_filling(self, driver, book_dict):
        try:
            error = ''
            time.sleep(20)
	    time.sleep(40)
            driver.implicitly_wait(100)
	    driver.implicitly_wait(200)
            contact_mobile = self.booking_dict.get('contact_mobile', '').strip()
            Select(driver.find_element_by_id("CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ContactInputTravelerView_DropDownListOtherPhoneIDC")).select_by_visible_text("India(+91)")
            driver.find_element_by_id("CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ContactInputTravelerView_DropDownListOtherPhoneIDC").click()
            driver.find_element_by_id("CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ContactInputTravelerView_TextBoxOtherPhone").click()
            driver.find_element_by_id("CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ContactInputTravelerView_TextBoxOtherPhone").clear()
            driver.find_element_by_id("CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ContactInputTravelerView_TextBoxOtherPhone").send_keys(contact_mobile)
            driver.find_element_by_id("NextButton").click()
            driver.implicitly_wait(30)
            guestdetails = book_dict.get('guestdetails', [])
            guestdetails.extend(book_dict.get('childdetails', []))
            for idx, details in enumerate(guestdetails):
                birth_date = details.get('dob', '')
                bo_day, bo_month, bo_year = ['']*3
                if birth_date:
                    birth_date = datetime.datetime.strptime(birth_date, '%Y-%m-%d')
                    b_date = birth_date.strftime('%Y-%b-%d')
                    bo_day, bo_month, bo_year = birth_date.day, birth_date.month, birth_date.year
                    bo_month = b_date.split('-')[1]
                gender = details.get('gender', '')
                if gender == 'Male' or gender == 'M':
                    gender_val = 1
                else:
                    gender_val = 2
                if details:
                    pax_de = [gender, details, bo_day, bo_month, bo_year]

                    driver, error = self.pax_details_filling(driver, book_dict, pax_de, idx)
                    time.sleep(2)
                    driver.implicitly_wait(30)
            return (driver, error)
        except:
            return (driver, "Failed to load Traveler page1")

    def pax_details_filling(self, driver, book_dict, pax_de, idx):
        try:
            time.sleep(20)
            driver.implicitly_wait(100)
            error = ''
            gender, details, bo_day, bo_month, bo_year = pax_de
            bo_day = str(bo_day).lstrip('0')
            name = details.get('firstname', '')
            lname = details.get('lastname', '')
            key = 'CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER'
            driver.implicitly_wait(100)
            Select(driver.find_element_by_id("%s_PassengerInputTravelerView_DropDownListTitle_%s"%(key, idx))).select_by_visible_text(gender)
            #driver.find_element_by_id("CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_PassengerInputTravelerView_DropDownListTitle_0").click()
            driver.find_element_by_id("%s_PassengerInputTravelerView_TextBoxFirstName_%s"%(key, idx)).click()
            driver.find_element_by_id("%s_PassengerInputTravelerView_TextBoxFirstName_%s"%(key, idx)).clear()
            driver.find_element_by_id("%s_PassengerInputTravelerView_TextBoxFirstName_%s"%(key, idx)).send_keys(name)
            driver.find_element_by_id("%s_PassengerInputTravelerView_TextBoxLastName_%s"%(key, idx)).click()
            driver.find_element_by_id("%s_PassengerInputTravelerView_TextBoxLastName_%s"%(key, idx)).clear()
            driver.find_element_by_id("%s_PassengerInputTravelerView_TextBoxLastName_%s"%(key, idx)).send_keys(lname)
            driver.find_element_by_id("%s_PassengerInputTravelerView_DropDownListNationality_%s"%(key, idx)).click()
            Select(driver.find_element_by_id("%s_PassengerInputTravelerView_DropDownListNationality_%s"%(key, idx))).select_by_visible_text("India")
            driver.find_element_by_id("%s_PassengerInputTravelerView_DropDownListNationality_%s"%(key, idx)).click()
            Select(driver.find_element_by_id("%s_PassengerInputTravelerView_DropDownListBirthDateDay_%s"%(key, idx))).select_by_visible_text(str(bo_day))
            driver.find_element_by_id("%s_PassengerInputTravelerView_DropDownListBirthDateDay_%s"%(key, idx)).click()
            Select(driver.find_element_by_id("%s_PassengerInputTravelerView_DropDownListBirthDateMonth_%s"%(key, idx))).select_by_visible_text(str(bo_month))
            driver.find_element_by_id("%s_PassengerInputTravelerView_DropDownListBirthDateMonth_%s"%(key, idx)).click()
            Select(driver.find_element_by_id("%s_PassengerInputTravelerView_DropDownListBirthDateYear_%s"%(key, idx))).select_by_visible_text(str(bo_year))
            driver.find_element_by_id("%s_PassengerInputTravelerView_DropDownListBirthDateYear_%s"%(key, idx)).click()
            if 'NextButton' in driver.page_source:
                try:
                    driver.find_element_by_id("NextButton").click()
                except:
                    try:
                        driver.find_element_by_xpath("(//input[@id='radioButton'])[2]").click()
                        driver.find_element_by_xpath("//div[@id='dialog']/div[2]/button[2]/span").click()
                        driver.find_element_by_id("CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ButtonSubmit").click()
                    except:
                        error = "Faild to load Travel page"
            else:
                try:
                    driver.find_element_by_id("CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ButtonSubmit").click()
                    driver.find_element_by_xpath("(//input[@id='radioButton'])[2]").click()
                    driver.find_element_by_id("CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ButtonSubmit").click()
                except:
                    error = "Faild to load Travel page"
            return (driver, error)
        except:
            return (driver, "Failed to load Traveler page")


    def check_seg_date(self, book_dict, site_dep_date, site_segment_text):
        try:
            request_date = book_dict.get('departure_date', '')
            request_return_date = book_dict.get('return_date', '')
            request_orign = book_dict.get('origin', '')
            request_dest = book_dict.get('destination', '')
            site_dep = ''.join(site_dep_date.split('<>')[0]).strip()
            if book_dict.get('triptype', '') == "RoundTrip":
                site_return = ''.join(site_dep_date.split('<>')[1]).strip()
                req_re_date = datetime.datetime.strptime(book_dict.get('returndate', ''), '%Y-%m-%d')
                site_re_date = datetime.datetime.strptime(site_return, '%m/%d/%Y')
                print book_dict.get('tripid', ''), req_re_date, site_re_date
                if req_re_date == site_re_date: status = True
                else: status = False
            ow_date = datetime.datetime.strptime(book_dict.get('onewaydate', ''), '%Y-%m-%d')
            ow_site_date = datetime.datetime.strptime(site_dep, '%m/%d/%Y')
            print book_dict.get('tripid', ''), ow_date, ow_site_date
            if ow_date == ow_site_date: status = True
            else: status = False
            if request_orign in site_segment_text and request_dest in site_segment_text:
                status = True
            else: status = False
            return status
        except: False

    def wait_to_loadpage(self, driver):
        sel = Selector(text=driver.page_source)
        site_dep_date = '<>'.join(sel.xpath('//div[@class="dayHeadersLarge dayHeaderTodayImage"]/a/span[@class="todayDate hidden"]/text()').extract())
        if site_dep_date: status = True
        else: status = False
        return status

    def select_flight(self, driver, book_dict):
        driver.implicitly_wait(100)
        fare_class_dict = {'Regular': 'Regular', 'PremiumFlex': 'PremiumFlex',
                           'PremiumFlatbed': 'PremiumFlatbed', "Econamy": "Lowfare", "Economy": "Lowfare"}
        fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price, rt_flt_no = [
            ''] * 5
        time.sleep(20)
        for k in range(4):
            load_status = self.wait_to_loadpage(driver)
            if load_status:
                break
            time.sleep(3)
        driver.save_screenshot("%s_select_flight.png"%book_dict.get('tripid', ''))
        sel = Selector(text=driver.page_source)
        site_dep_date = '<>'.join(sel.xpath('//div[@class="dayHeadersLarge dayHeaderTodayImage"]/a/span[@class="todayDate hidden"]/text()').extract())
        site_segment_text = '<>'.join(sel.xpath('//div[@class="depart-return-msg"]/text()').extract())
        search_status = self.check_seg_date(book_dict, site_dep_date, site_segment_text)
        if not search_status:
            return (driver, '', '', search_status)
        table_nodes = sel.xpath('//table[@id="fareTable1_4"]//tr')
        retable_nodes = sel.xpath('//table[@id="fareTable2_4"]//tr')
        field_tab_index = sel.xpath(
            '//div[@class="tabsHeader"][1]//input//@id').extract()
        field_tab_value = sel.xpath(
            '//div[@class="tabsHeader"][1]//input//@value').extract()
        if book_dict.get('triptype', '') == 'RoundTrip':
            if len(field_tab_index) == 2 and len(field_tab_value) == 2:
                field_tab_index, refield_tab_index = field_tab_index
                field_tab_value, refield_tab_value = field_tab_value
            else:
                refield_tab_index, refield_tab_value = ['']*2
        else:
            field_tab_index = ''.join(field_tab_index)
            field_tab_value = ''.join(field_tab_value)
            refield_tab_index, refield_tab_value = ['']*2
        if not table_nodes:
            err = 'No Flithts found'
            #logging.debug('Flithts  not found')
        if not retable_nodes and book_dict.get('triptype', '') == 'RoundTrip':
            err = 'No Flights found'
            #logging.debug('Flithts  not found')
        member_time_zone = ''.join(
            sel.xpath('//input[@id="MemberLoginSelectView_HFTimeZone"]/@value').extract())
        flight_oneway_fares = {}
        for node in table_nodes:
            fares_ = {}
            flight_text = ''.join(node.xpath(
                './/div[@class="scheduleFlightNumber"]//span[@class="hotspot"]/@onmouseover').extract())
            if not flight_text:
                flight_text = ''.join(node.xpath(
                    './/div[@class="scheduleFlightNumber"]//div[@class="hotspot"]/@onmouseover').extract())
            if flight_text:
                flt_ids = re.findall('<b>(.*?)</b>', flight_text)
                if flt_ids:
                    try:
                        flt_id = '<>'.join(list(set(flt_ids))).replace(
                            ' ', '').strip()
                    except:
                        flt_id = '<>'.join(flt_ids).replace(' ', '').strip()
                else:
                    flt_id = ''
            else:
                flt_id = ''
            for i in range(2, 6):
                fare_cls = ''.join(node.xpath(
                    './..//th[%s]//div[contains(@class, "fontNormal")]//text()' % i).extract()).replace(' ', '').strip()
                fare_id = ''.join(node.xpath(
                    './/td[%s]//div[@id="fareRadio"]//input/@id' % i).extract())
                fare_name = ''.join(node.xpath(
                    './/td[%s]//div[@id="fareRadio"]//input/@name' % i).extract())
                fare_vlue = ''.join(node.xpath(
                    './/td[%s]//div[@id="fareRadio"]//input/@value' % i).extract())
                price = '<>'.join(node.xpath(
                    './/td[%s]//div[@class="price"]//div[@id="originalLowestFare"]//text()' % i).extract())
                if fare_id:
                    fares_.update(
                        {fare_cls: (fare_id, fare_name, fare_vlue, price)})
            if flt_id:
                flight_oneway_fares.update({flt_id: fares_})
        flight_return_fares = {}
        if retable_nodes:
            for renode in retable_nodes:
                refares_ = {}
                flight_text = ''.join(renode.xpath(
                    './/div[@class="scheduleFlightNumber"]//span[@class="hotspot"]/@onmouseover').extract())
                if not flight_text:
                    flight_text = ''.join(renode.xpath(
                        './/div[@class="scheduleFlightNumber"]//div[@class="hotspot"]/@onmouseover').extract())
                if flight_text:
                    reflt_ids = re.findall('<b>(.*?)</b>', flight_text)
                    if reflt_ids:
                        try:
                            reflt_id = '<>'.join(
                                list(set(reflt_ids))).replace(' ', '').strip()
                        except:
                            reflt_id = '<>'.join(
                                reflt_ids).replace(' ', '').strip()
                    else:
                        reflt_id = ''
                else:
                    reflt_id = ''
                for i in range(2, 6):
                    fare_cls = ''.join(renode.xpath(
                        './..//th[%s]//div[contains(@class, "fontNormal")]//text()' % i).extract()).replace(' ', '').strip()
                    flight_text = ''.join(renode.xpath(
                        './/div[@class="scheduleFlightNumber"]//span[@class="hotspot"]/@onmouseover').extract())
                    fare_id = ''.join(renode.xpath(
                        './/td[%s]//div[@id="fareRadio"]//input/@id' % i).extract())
                    fare_name = ''.join(renode.xpath(
                        './/td[%s]//div[@id="fareRadio"]//input/@name' % i).extract())
                    fare_vlue = ''.join(renode.xpath(
                        './/td[%s]//div[@id="fareRadio"]//input/@value' % i).extract())
                    price = '<>'.join(renode.xpath(
                        './/td[%s]//div[@class="price"]//div[@id="originalLowestFare"]//text()' % i).extract())
                    if fare_id:
                        refares_.update(
                            {fare_cls: (fare_id, fare_name, fare_vlue, price)})
                if reflt_id:
                    flight_return_fares.update({reflt_id: refares_})
        ct_flight_id = book_dict.get('onewayflightid', [])
        ct_ticket_class = book_dict.get(
            'onewayclass', []).replace(' ', '').strip()
        aa_keys = flight_oneway_fares.keys()
        print aa_keys
        fin_fare_dict, ow_flt_no = self.get_fin_fares_dict(
            flight_oneway_fares, ct_flight_id)
        final_flt_tuple = fin_fare_dict.get(fare_class_dict.get(ct_ticket_class, ''), ['']*4)
        fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price = final_flt_tuple
        if not fin_fare_vlue:
            final_flt_tuple = fin_fare_dict.get('Regular', ['']*4)
            fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price = final_flt_tuple
        refin_fare_dict = {}
        rect_ticket_class = book_dict.get(
            'returnclass', '').replace(' ', '').strip()
        if book_dict.get('triptype', '') == 'RoundTrip':
            rect_flight_id = book_dict.get('returnflightid', [])
            refin_fare_dict, rt_flt_no = self.get_fin_fares_dict(
                flight_return_fares, rect_flight_id)
        refinal_flt_tuple = refin_fare_dict.get(
            fare_class_dict.get(rect_ticket_class, ''), ['']*4)
        refin_fare_id, refin_fare_name, refin_fare_vlue, refin_price = refinal_flt_tuple
        if not refin_fare_vlue:
            refinal_flt_tuple = refin_fare_dict.get('Regular', ['']*4)
            refin_fare_id, refin_fare_name, refin_fare_vlue, refin_price = refinal_flt_tuple
        book_dict.update({'ow_flt': ow_flt_no, 'rt_flt': rt_flt_no})
        flt_no_ = book_dict.get('ow_flt', '').replace('<>', ' ').strip()
        rt_flt_no_ = book_dict.get('rt_flt', '').replace('<>', ' ').strip()
        flt = [flt_no_, rt_flt_no_]
        book_dict.update({'flights': flt})
        return (driver, fin_fare_id, refin_fare_id, search_status)


    def parse(self, response):
        '''Login to AirAsia'''
        sel = Selector(response)
        waiting_room = ''.join(sel.xpath('//title/text()').extract())
        if waiting_room == 'AirAsia Waiting Room' and response.meta.get('counter') < 3:
            time.sleep(15)
            counter += 1
            return Request(response.url, callback=self.parse, dont_filter=True, meta={'counter': counter})
        view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
        login_data_list.append(('__VIEWSTATE', view_state))
        login_data_list.append(('__VIEWSTATEGENERATOR', gen))
        self.pcc_name, book_dict = self.get_pcc_name()
        if book_dict.get('queue', '') == 'coupon':
            self.pcc_name = 'airasia_coupon_default'
        try:
            logging.debug('Booking using: %s' %
                          _cfg.get(self.pcc_name, 'username'))
        except:
            pass
        cookie = random.choice(airasia_login_cookie_list)
        cookies = {'i10c.bdddb': cookie}
        print cookies
        time.sleep(5)
        if self.multiple_pcc:
            logging.debug('Multiple PCC booking')
            self.insert_into_db(book_dict, "Multiple PCC booking")
            return
        else:
            try:
                user_name = _cfg.get(self.pcc_name, 'username')
                user_psswd = _cfg.get(self.pcc_name, 'password')
                self.book_using = user_name
                #login_data_list.append(('ControlGroupLoginAgentView$AgentLoginView$TextBoxUserID', str(user_name)))
                #login_data_list.append(('ControlGroupLoginAgentView$AgentLoginView$PasswordFieldPassword', str(user_psswd)))
                login_data = [
                    ('__EVENTTARGET',
                     'ControlGroupLoginAgentView$AgentLoginView$LinkButtonLogIn'),
                    ('__EVENTARGUMENT', ''),
                    ('__VIEWSTATE', '/wEPDwUBMGRktapVDbdzjtpmxtfJuRZPDMU9XYk='),
                    ('pageToken', ''),
                    ('ControlGroupLoginAgentView$AgentLoginView$TextBoxUserID',
                     str(user_name)),
                    ('ControlGroupLoginAgentView$AgentLoginView$PasswordFieldPassword', str(
                        user_psswd)),
                    ('ControlGroupLoginAgentView$AgentLoginView$HFTimeZone', '330'),
                    ('__VIEWSTATEGENERATOR', '05F9A2B0'),
                ]

                return FormRequest('https://booking2.airasia.com/LoginAgent.aspx',
                                   formdata=login_data, callback=self.parse_next, cookies=cookies, meta={'data': book_dict}, dont_filter=True)
            except:
                self.insert_into_db(book_dict, "PCC credentials not found")

    def parse_next(self, response):
        '''
        Parse the request to my bookings or manage my booking
        '''
        sel = Selector(response)
        try:
            original_request = eval(self.booking_dict)
        except:
            original_request = json.loads(self.booking_dict)
        temp_status = True
        manage_booking = sel.xpath('//a[@id="MyBookings"]/@href').extract()
        try:
            book_dict = eval(self.booking_dict)
        except:
            try:
                book_dict = json.loads(self.booking_dict)
            except:
                book_dict = {}
        if response.status == 403:
            self.insert_into_db(book_dict, "Login page got 403 status")
            self.send_mail('403 status', 'Login page got 403 status')
            return
        login_failed = ''.join(
            sel.xpath('//div[@id="errorSectionContent"]//text()').extract())
        if 'user/agent ID you entered is not valid' in login_failed:
            self.insert_into_db(
                book_dict, "Booking Scraper unable to login AirAsia")
            open('%s_login_failed' % book_dict.get('trip_ref',
                                                   'Check the booking dict'), 'w').write(response.body)
            logging.debug('Login Failed %s, %s, %s' %
                          (response.status, manage_booking, response.url))
            self.send_mail("Login Failed", "Booking Scraper unable to login AirAsia %s" %
                           book_dict.get('trip_ref', 'check the booking dict'))
            temp_status = False
            return
        if 'error404busy' in response.url.lower():
            self.insert_into_db(
                book_dict, "Booking Scraper unable to login due to server busy")
            open('%s_login_failed' % book_dict.get('trip_ref',
                                                   'Check the booking dict'), 'w').write(response.body)
            logging.debug('Booking Scraper unable to login due to server busy %s' %
                          book_dict.get('trip_ref', ''))
            return
        if 'err504.html' in response.url.lower():
            self.insert_into_db(
                book_dict, "Booking Scraper unable to login due to server busy")
            open('%s_login_failed' % book_dict.get('trip_ref',
                                                   'Check the booking dict'), 'w').write(response.body)
            logging.debug('Booking Scraper unable to login due to server busy %s' %
                          book_dict.get('trip_ref', ''))
            return
        if 'err502.html' in response.url.lower():
            self.insert_into_db(
                book_dict, "Booking Scraper unable to login due to server busy")
            open('%s_login_failed' % book_dict.get('trip_ref',
                                                   'Check the booking dict'), 'w').write(response.body)
            logging.debug('Booking Scraper unable to login due to server busy %s' %
                          book_dict.get('trip_ref', ''))
            return
        cookies = {}
        res_headers = json.dumps(str(response.headers))
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
        cookies = {}
        for i in my_dict.get('Set-Cookie', []):
            data = i.split(';')[0]
            if data:
                try:
                    key, val = data.split('=', 1)
                    if 'ASP.NET_SessionId' in key:
                        key = 'cookie: ASP.NET_SessionId'
                except:
                    continue
                cookies.update({key.strip(): val.strip()})
        self.logout_cookies = cookies
        self.logout_view_state = ''.join(sel.xpath(view_state_path).extract())

        if 'AgentHome' not in response.url:

            if 'loginagent.aspx' in response.url.lower():
                if self.garbage_retry < 5:
                    self.garbage_retry += 1
                    import time
                    time.sleep(50)
                    logging.debug(
                        '************Retry for Garbage response |%s*******************' % book_dict.get('trip_ref', ''))
                    headers = {
                        'Connection': 'keep-alive',
                        'Pragma': 'no-cache',
                        'Cache-Control': 'no-cache',
                        'Upgrade-Insecure-Requests': '1',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                    }
                    settings.overrides['HTTP_PROXY'] = ''
                    return Request('https://booking2.airasia.com/LoginAgent.aspx', callback=self.parse, headers=headers, cookies={}, dont_filter=True, meta={'content': True})
                else:
                    open('%s_garbage' % book_dict.get('trip_ref',
                                                      'Check the booking dict'), 'w').write(response.body)
                    logging.debug('Login Failed Server Busy %s, %s, %s' % (
                        response.status, manage_booking, response.url))
                    self.insert_into_db(
                        book_dict, 'Booking Scraper unable to login due to server busy Garbage')
                    return
            else:
                open('%s_login_failed' % book_dict.get(
                    'tripid', 'Check the booking dict'), 'w').write(response.body)
                self.insert_into_db(
                    book_dict, "Booking Scraper unable to login due to server busy")
                return
        if not manage_booking:
            self.insert_into_db(book_dict, "Response not loaded")
            open('%s_response_not_loaded' % book_dict.get('tripid',
                                                          'Check the booking dict'), 'w').write(response.body)
            logging.debug('Response not loaded %s, %s, %s' %
                          (response.status, manage_booking, response.url))
            temp_status = False
            return

        if self.booking_dict and temp_status:
            try:
                try:
                    book_dict = eval(self.booking_dict)
                except:
                    book_dict = json.loads(self.booking_dict)
                print book_dict
                original_request = book_dict
                self.booking_dict = book_dict
                book_dict = self.process_input()
                pnr = book_dict.get('pnr', '')
                print book_dict
            except Exception as e:
                logging.debug(e.message)
                self.send_mail('AirAsia Booking Faild', e.message)
                book_dict, pnr, original_request = {}, '', {}
                print e.message
            try:
                logging.debug(book_dict.get('tripid', ''))
            except:
                pass
            url = 'https://booking2.airasia.com/BookingList.aspx'
            return Request(url, callback=self.parse_search, dont_filter=True, meta={'book_dict': book_dict})
        else:
            try:
                self.insert_into_db(
                    original_request, "Booking Scraper unable to login AirAsia")
            except Exception as e:
                logging.debug(e.message)

    def parse_search(self, response):
        '''
        Fetching the details for Existing PNR
        '''
        sel = Selector(response)
        book_dict = response.meta.get('book_dict', {})
        pax_last_name = book_dict.get('pax_last_name', '')
        autopnr_status = response.meta.get('autopnr_status', 0)
        if not pax_last_name:
            self.insert_into_db(book_dict, "pax last name not found")
            print "pax last name not found"
            return
        if response.status != 200:
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
            self.send_mail('Internal Server Error', json.dumps(book_dict))
            return
        garbage = ''.join(sel.xpath('//title/text()').extract())
        if not garbage:
            self.insert_into_db(book_dict, "Failed due to server busy Garbage")
            open('%s_searchpage_not_loaded' % book_dict.get(
                'tripid', 'booking_dict'), 'w').write(response.body)
            return
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'cache-control': 'no-cache',
            'authority': 'booking2.airasia.com',
            'referer': 'https://booking2.airasia.com/AgentHome.aspx',
        }
        search_flights = 'https://booking2.airasia.com/Search.aspx'
        if self.queue != 'offline':
            self.go_with_selenium()
            return
        else:
            view_state = ''.join(sel.xpath(view_state_path).extract())
            gen = ''.join(sel.xpath(view_generator_path).extract())
            search_data_list.update({'__VIEWSTATE': str(view_state)})
            search_data_list.update({'__VIEWSTATEGENERATOR': str(gen)})
            pnr_no = book_dict.get('pnr', '')
            form_data = [
                ('__EVENTTARGET', 'ControlGroupBookingListView$BookingListSearchInputView$LinkButtonFindBooking'),
                ('__EVENTARGUMENT', ''),
                ('__VIEWSTATE', view_state),
                ('pageToken', ''),
                ('ControlGroupBookingListView$BookingListSearchInputView$Search', 'ForAgency'),
                ('ControlGroupBookingListView$BookingListSearchInputView$DropDownListTypeOfSearch', '5'),
                ('ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword',
                 pax_last_name.upper().strip()),
                ('__VIEWSTATEGENERATOR', '05F9A2B0'),
            ]
            if pax_last_name:
                url = "http://booking2.airasia.com/BookingList.aspx"
                return FormRequest(url, formdata=form_data, callback=self.parse_pnr_deatails,
                                   meta={'book_dict': book_dict, 'autopnr_status': autopnr_status, 'pax_last_name': pax_last_name})

    def parse_pnr_deatails(self, response):
        '''
        Checking the auto PNR presented in AirAsia or not
        '''
        sel = Selector(response)
        book_dict = response.meta.get('book_dict', {})
        autopnr_status = response.meta.get('autopnr_status', '0')
        if response.status != 200:
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
            return
        garbage = ''.join(sel.xpath('//title/text()').extract())
        if not garbage:
            self.insert_into_db(book_dict, "Failed due to server busy Garbage")
            open('%s_selectpnr_not_loaded' % book_dict.get(
                'tripid', 'booking_dict'), 'w').write(response.body)
            return
        view_state = ''.join(sel.xpath(view_state_path).extract())
        pax_last_name = response.meta.get('pax_last_name', '')
        gen = ''.join(sel.xpath(view_generator_path).extract())
        if book_dict.get('triptype', '') == 'OneWay' or book_dict.get('triptype', '') == 'RoundTrip':
            trip_status = True
        else:
            self.insert_into_db(
                book_dict, "Booking Faild As its MultiCity trip")
            trip_status = False
            return
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'cache-control': 'no-cache',
            'authority': 'booking2.airasia.com',
            'referer': 'https://booking2.airasia.com/AgentHome.aspx',
        }
        search_flights = 'https://booking2.airasia.com/Search.aspx'
        current_booking_table = sel.xpath(
            '//table[@id="currentTravelTable"]/tbody[@id="tableBodyRow"]//tr')
        cur_booking_dict, auto_book_dict = {}, {}
        if autopnr_status == 0:
            for node in current_booking_table:
                depart_date = normalize(
                    ''.join(node.xpath('./td[1]/span/text()').extract()))
                site_pax_name = ''.join(node.xpath('./td[5]/text()').extract())
                auto_pnr = ''.join(node.xpath('./td[4]/text()').extract())
                booking_id = ''.join(node.xpath(
                    './td[6]/a[contains(text(), "Modify")]/@href').extract())
                if auto_pnr and booking_id:
                    cur_booking_dict.update(
                        {auto_pnr: [depart_date, auto_pnr, site_pax_name, booking_id]})
            print cur_booking_dict
            airasia_server_error = ''.join(
                sel.xpath('//div[@id="errorSectionContent"]/p/text()').extract())
            if 'error' in airasia_server_error and not current_booking_table:
                self.insert_into_db(book_dict, airasia_server_error)

                open('%s_pnrsearchfail' % book_dict.get(
                    'tripid', 'Check the booking dict'), 'w').write(response.body)
                return
            if not current_booking_table:
                print "No details found with pax last name(%s), go ahead to booking" % pax_last_name
                if trip_status:
                    self.go_with_selenium()
                    return
            auto_book_dict = self.check_depature_date(
                book_dict, cur_booking_dict)  # date check
            if not auto_book_dict:
                print "No details found with pax last name(%s), go ahead to booking" % pax_last_name
                if trip_status:
                    self.go_with_selenium()
                    return
            auto_book_dict = self.check_hq_pax_name(
                book_dict, auto_book_dict)  # pax name check
            if not auto_book_dict:
                print "No details found with pax last name(%s), gohead to booking" % pax_last_name
                if trip_status:
                    self.go_with_selenium()
                    return
            if len(auto_book_dict.keys()) >= 5:
                print "Scraper have to check more than five PNRs"
                self.insert_into_db(
                    book_dict, "Scraper have to check more than five PNRs")
                return
            self.pnrs_tobe_checked = auto_book_dict.keys()
            self.auto_book_dict = auto_book_dict
        pax_last_name = book_dict.get('pax_last_name', '')
        try:
            check_pnr = self.pnrs_tobe_checked[0]
        except:
            check_pnr = []
        if check_pnr:
            event_argument = 'Edit:%s' % check_pnr
            details_lst = self.auto_book_dict.get(check_pnr, ['']*4)
            try:
                event_target, event_argument = re.findall(
                    '\((.*)\)', details_lst[3])
            except:
                event_target = 'ControlGroupBookingListView$BookingListSearchInputView'
                event_argument = 'Edit:%s' % check_pnr
            form_data = {
                '__EVENTTARGET': event_target,
                '__EVENTARGUMENT': event_argument,
                '__VIEWSTATE': view_state,
                'pageToken': '',
                'ControlGroupBookingListView$BookingListSearchInputView$Search': 'ForAgency',
                'ControlGroupBookingListView$BookingListSearchInputView$DropDownListTypeOfSearch': '5',
                'ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword': pax_last_name.upper().strip(),
                '__VIEWSTATEGENERATOR': gen,
            }
            url = 'https://booking2.airasia.com/BookingList.aspx'
            return FormRequest(url, callback=self.parse_details, formdata=form_data,
                               meta={'book_dict': book_dict, 'auto_pnr_dict': auto_book_dict, 'form_data': form_data})
        else:
            self.go_with_selenium()
            return

    def parse_details(self, response):
        sel = Selector(response)
        url = 'http://booking2.airasia.com/ChangeItinerary.aspx'
        self.insert_into_db(
            response.meta['book_dict'], "Bad response from Airline")
        yield FormRequest.from_response(response, callback=self.parse_existing_pax,
                                        meta={'book_dict': response.meta['book_dict'], 'form_data': response.meta['form_data']})

    def parse_existing_pax(self, response):
        '''PNR data parsing'''
        sel = Selector(response)
        book_dict = response.meta.get('book_dict', {})
        view_state = ''.join(sel.xpath(view_state_path).extract())
        if response.status != 200:
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
            return
        garbage = ''.join(sel.xpath('//title/text()').extract())
        if not garbage:
            self.insert_into_db(book_dict, "Failed due to server busy Garbage")
            open('%s_autopnr_not_loaded' % book_dict.get(
                'tripid', 'booking_dict'), 'w').write(response.body)
            return
        flight_status, segments_status = False, False
        form_data = response.meta['form_data']
        ow_flight_ids = normalize('<>'.join(sel.xpath(
            '//div[@class="booking-details-table"]//table/thead/tr/th[contains(text(), "Depart")]/../../../tbody[1]/tr/td[1]//text()[1]').extract())).strip().strip('<>')
        rt_flight_id = normalize('<>'.join(sel.xpath(
            '//div[@class="booking-details-table"]//table/thead/tr/th[contains(text(), "Return")]/../../../tbody[1]/tr/td[1]//text()[1]').extract())).strip().strip('<>')
        if ow_flight_ids:
            ow_flight_ids = ow_flight_ids.split('<>')
        else:
            ow_flight_ids = []
        if rt_flight_id:
            rt_flight_id = rt_flight_id.split('<>')
        else:
            rt_flight_id = []
        flight_id = ow_flight_ids + rt_flight_id
        booking_id = normalize(
            ''.join(sel.xpath(pax_page_booking_id_path).extract()))
        total_paid = normalize(
            ''.join(sel.xpath(pax_page_amount_path).extract()))
        depart = normalize(
            ''.join(sel.xpath(pax_page_depart_loc_path).extract()))
        from_airport_details = normalize(
            ' '.join(sel.xpath(pax_page_fr_air_path).extract()))
        to_airport_details = normalize(
            ' '.join(sel.xpath(pax_page_to_air_path).extract()))
        guest_name = normalize(
            '<>'.join(sel.xpath(pax_page_guest_name_path).extract()))
        mobile_no = normalize(
            ''.join(sel.xpath(pax_page_mo_no_path).extract()))
        email = normalize(''.join(sel.xpath(pax_page_email_path).extract()))
        hq_from = book_dict.get('origin_code', '')
        hq_to = book_dict.get('destination_code', '')
        booking_flt_ids = book_dict.get('onewayflightid', [])
        rt_booking_flt_ids = book_dict.get('returnflightid', [])
        book_dict.update({'airasia_price': total_paid})
        booking_flt_ids = booking_flt_ids + rt_booking_flt_ids
        flight_status = self.check_hq_flights(booking_flt_ids, flight_id)
        if not flight_id:
            print "flightid not found in response"
            self.insert_into_db(book_dict, "Bad response from Airline")
            self.pnrs_tobe_checked.remove(booking_id)
            return
        if hq_from in depart and hq_to in depart:
            segments_status = True
        else:
            segments_status = False
        airasia_guest_list = [normalize(x)
                              for x in guest_name.split('<>') if x]
        pax_status = self.check_guest_names(book_dict, airasia_guest_list)
        # check check_arrival_departure_date function in airasia_utils.py and add condition for time check
        if flight_status and segments_status and pax_status:

            book_dict['price_details'] = self.get_autopnr_pricingdetails(
                {'total': book_dict.get('airasia_price', ''), 'AUTO_PNR_EXISTS': True})
            message = "auto PNR exists:%s" % booking_id
            book_dict['status_message'] = message
            book_dict['pnr'] = booking_id
            flights = book_dict.get('onewayflightid', []) + \
                book_dict.get('returnflightid', [])
            book_dict['flights'] = str(flights)
            self.insert_into_db(book_dict, '')
            return
        else:
            try:
                self.pnrs_tobe_checked.remove(booking_id)
            except Exception as e:
                self.insert_into_db(book_dict, e.message)
            self.go_with_selenium()
            return

    def tolerance_check(self, driver, book_dict):
        time.sleep(5)
        driver.implicitly_wait(100)
        sel = Selector(text=driver.page_source)
        tolerance_value, is_proceed = 0, 0
        ct_price = book_dict.get('ctprice', '0')
        total_fare = ''.join(sel.xpath(
            '//div[@class="total-amount-bg-last"]//span[@id="overallTotal"]//text()').extract())
        try:
            total_fare = float(total_fare.replace(',', '').strip())
        except:
            total_fare = 0
        if total_fare != 0:
            tolerance_value = total_fare - float(ct_price)
            if float(tolerance_value) >= float(self.tolerance_amount):
                is_proceed = 0  # movie it to off line
            else:
                is_proceed = 1
        else:
            #open('%s_I5_fare_notloaded' % book_dict.get('tripid', 'Check the booking dict'), 'w').write(response.body)
            #self.insert_into_db(book_dict, "Fare response not loaded")
            tolerance_value, is_proceed = 0, 0
            return (driver, book_dict, is_proceed, "Fare response not loaded")
        book_dict.update({'tolerance_value': tolerance_value})
        book_dict.update({'airasia_price': total_fare})
        return (driver, book_dict, is_proceed, '')


    def get_response_details(self, driver, book_dict):
        time.sleep(5)
        driver.implicitly_wait(100)
        sel = Selector(text=driver.page_source)
        tax_dict1, tax_dict2, fin_tax = {}, {}, {}
        flt1_ = sel.xpath(
            '//div[@class="flightDisplay_1"]//div[@id="section_1"]//span[@class="right-text bold grey1"]//text()').extract()
        flt1 = []
        for lt in flt1_:
            lt = lt.replace(' ', '').strip()
            try:
                flt = lt[:2] + ' ' + lt[2:]
                flt1.append(flt)
            except:
                continue
            #flt = re.sub(lt[1], lt[1] + ' ', lt)
        flt1 = '<>'.join(flt1)
        seg = '-'.join(sel.xpath('//div[@class="flightDisplay_1"]//div[@id="section_1"]//div[@class="row2 mtop-row"]//div//text()').extract(
        )).replace('\n', '').replace('\t', '').replace('\r', '').strip()
        tax_key = sel.xpath(
            '//div[@class="flightDisplay_1"]//div[@id="section_1"]//span[@class="left-text black2"]//text()').extract()
        tax_val = sel.xpath(
            '//div[@class="flightDisplay_1"]//div[@id="section_1"]//span[@class="right-text black2"]//text()').extract()
        tot1_price = ''.join(
            sel.xpath('//span[@id="totalJourneyPrice_1"]//text()').extract())
        tot1_price = ''.join(re.findall('(\d+.\d+)', tot1_price))
        up_meal_code_dict = book_dict.get('oneway_meal_dict', {})
        for i, j in zip(tax_key, tax_val):
            if 'Adult' in i or 'Child' in i or 'Infant' in i:
                if '(' in i:
                    i = ''.join(re.findall('\d+ (.*)\(', i))
                else:
                    i = ''.join(re.findall('\d+ (.*)', i))
            vvv = ''.join(re.findall('(\d+.\d+)', j))
            if not vvv:
                j = ''.join(re.findall('(\d+)', j))
            else:
                j = vvv
            for key, va in up_meal_code_dict.iteritems():
                if va in i:
                    i = '%s meals' % key
                    break
            tax_dict1.update({i.replace(' ', ''): j, 'seg': seg,
                              'total': tot1_price, 'pcc': self.book_using})
        if flt1:
            fin_tax.update({flt1: tax_dict1})
        flt2_ = sel.xpath(
            '//div[@class="flightDisplay_2"]//div[@id="section_2"]//span[@class="right-text bold grey1"]//text()').extract()
        flt2 = []
        for lt in flt2_:
            lt = lt.replace(' ', '').strip()
            try:
                flt_ = lt[:2] + ' ' + lt[2:]
                flt2.append(flt_)
            except:
                continue
        flt2 = '<>'.join(flt2)
        # try: flt2 = re.sub(flt2[1],flt2[1]+' ', flt2)
        # except: flt2 = ''
        seg2 = '-'.join(sel.xpath('//div[@class="flightDisplay_2"]//div[@id="section_2"]//div[@class="row2 mtop-row"]//div//text()').extract(
        )).replace('\n', '').replace('\t', '').replace('\r', '').strip()
        tax2_key = sel.xpath(
            '//div[@class="flightDisplay_2"]//div[@id="section_2"]//span[@class="left-text black2"]//text()').extract()
        tax2_val = sel.xpath(
            '//div[@class="flightDisplay_2"]//div[@id="section_2"]//span[@class="right-text black2"]//text()').extract()
        tot2_price = ''.join(
            sel.xpath('//span[@id="totalJourneyPrice_2"]//text()').extract())
        tot2_price = ''.join(re.findall('(\d+.\d+)', tot2_price))
        dw_meal_code_dict = book_dict.get('return_meal_dict', {})
        for i, j in zip(tax2_key, tax2_val):
            if 'Adult' in i or 'Child' in i or 'Infant' in i:
                if '(' in i:
                    i = ''.join(re.findall('\d+ (.*)\(', i))
                else:
                    i = ''.join(re.findall('\d+ (.*)', i))
            vvv = ''.join(re.findall('(\d+.\d+)', j))
            if not vvv:
                j = ''.join(re.findall('(\d+)', j))
            else:
                j = vvv
            for key, va in dw_meal_code_dict.iteritems():
                if va in i:
                    i = '%s meals' % key
                    break
            tax_dict2.update({i.replace(' ', ''): j, 'seg': seg2,
                              'total': tot2_price, 'pcc': self.book_using})
        if flt2:
            fin_tax.update({flt2: tax_dict2})
        booking_data = ''.join(
            sel.xpath('//input[@name="HiddenFieldPageBookingData"]/@value').extract())
        amount = ''.join(sel.xpath(
            '//input[@id="CONTROLGROUPPAYMENTBOTTOM_PaymentInputViewPaymentView_AgencyAccount_AG_AMOUNT"]/@value').extract())
        print amount
        book_dict.update({'price_details': json.dumps(fin_tax)})
        return (driver, book_dict)

    def get_pnr_resposne(self, driver, book_dict):
        time.sleep(10)
        time.sleep(20)
        driver.implicitly_wait(100)
        sel = Selector(text=driver.page_source)
        #tax_dict = response.meta['tax_dict']
        confirm = ''.join(
            sel.xpath('//span[@class="confirm status"]//text()').extract())
        pnr_no = ''.join(sel.xpath(
            '//span[@id="OptionalHeaderContent_lblBookingNumber"]//text()').extract())
        paid_amount = ''.join(sel.xpath(
            '//span[@id="OptionalHeaderContent_lblTotalPaid"]//text()').extract())
        pax_details = ','.join(
            sel.xpath('//span[@class="guest-detail-name"]//text()').extract())
        flt_no = book_dict.get('ow_flt', '').replace('<>', ' ').strip()
        rt_flt_no = book_dict.get('rt_flt', '').replace('<>', ' ').strip()
        flt = [flt_no, rt_flt_no]
        book_dict.update({'flights': flt})
        #book_dict.update({'price_details': json.dumps(tax_dict)})
        book_dict.update({'status_message': confirm})
        book_dict.update({'airasia_price': paid_amount})
        book_dict.update({'pnr': pnr_no})
        try:
            logging.debug('Values: %s' % book_dict)
        except:
            pass
        if pnr_no:
            return (driver, book_dict, 'success')
            #elf.insert_into_db(book_dict, '')
        else:
            book_dict.update({'status_message': 'Unknown'})
            return (driver, book_dict, 'Unknown')
            #self.insert_into_db(
            #   book_dict, 'Payment failed whereas payment is successful')

