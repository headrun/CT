# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
import unittest, time, re

import datetime
from scrapy.selector import Selector

import os
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
from airasia_xpaths import *
from ast import literal_eval
from scrapy import signals
#from booking_scrapers.utils import *
from scrapy.spider import Spider
from collections import OrderedDict

from airasia_utils import *

from scrapy.conf import settings

from indigo_utils import IndigoUtils


import sys
from utils import *


sys.path.append(settings['ROOT_PATH'])
from airasia_login_cookie import airasia_login_cookie_list

_cfg = SafeConfigParser()
_cfg.read(settings['BOOK_PCC_PATH'])



class UntitledTestCase(unittest.TestCase, AirAsiaUtils, IndigoUtils):
    booking_dict = '{}'
    def setUp(self):
        self.driver = webdriver.Firefox()
        #self.driver = webdriver.PhantomJS()
        self.driver.implicitly_wait(30)
        self.base_url = "https://booking2.airasia.com/AgentHome.aspx"
        self.verificationErrors = []
        self.accept_next_alert = True
        self.log = create_logger_obj('airasia_booking')
        #self.booking_dict = kwargs.get('jsons', {})
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
        #settings.overrides['HTTP_PROXY'] = ''
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


    def date_picker(self, driver, book_dict):
        ow_date = book_dict.get('onewaydate', '')
        print ow_date
        day, month, year = self.date_month_year(ow_date)
        print day, month, year
        #driver.find_element_by_link_text("<<").click()
        for i in range(10):
            try:
                #driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchViewdate_picker_display_id_1").clear()
                driver.find_element_by_xpath("(//td[@onclick='jQuery.datepicker._selectDay(0,%s,%s, this);'])[%s]"%(int(month)-1, year, day)).click()
                print "Here"
                break
            except:driver.find_element_by_link_text(">>").click()
        rt_date = book_dict.get('returndate', '')
        if rt_date:
            driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchViewdate_picker_display_id_2").click()
            day, month, year = self.date_month_year(rt_date)
            for i in range(10):
                try:
                    driver.find_element_by_xpath("(//td[@onclick='jQuery.datepicker._selectDay(1,%s,%s, this);'])[%s]"%(int(month)-1, year, day)).click()
                    break
                except:driver.find_element_by_link_text(">>").click()
        return driver

    def select_pax(self, driver, book_dict):
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
        Select(driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_DropDownListPassengerType_ADT"))
        driver.implicitly_wait(5)
        time.sleep(10)
        Select(driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_DropDownListPassengerType_ADT")).select_by_visible_text("%s %s"%(no_of_adults, adult_text))
        driver.implicitly_wait(5)
        #driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_DropDownListPassengerType_ADT").click()
        driver.implicitly_wait(5)
        driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_DropDownListPassengerType_CHD").click()
        driver.implicitly_wait(5)
        time.sleep(10)
        Select(driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_DropDownListPassengerType_CHD")).select_by_visible_text("%s %s"%(no_of_child, child_text))
        driver.implicitly_wait(5)
        #driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_DropDownListPassengerType_CHD").click()
        driver.implicitly_wait(5)
        driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_DropDownListPassengerType_INFANT").click()
        driver.implicitly_wait(5)
        driver.find_element_by_id("ControlGroupSearchView_ButtonSubmit").click()
        return driver

    def date_month_year(self, date_):
        #date = datetime.datetime.strptime(date_, '%d-%b-%y')
        date = datetime.datetime.strptime(date_, '%Y-%m-%d')
        return (str(date.day), str(date.month).lstrip('0'), str(date.year))

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


    def flight_search(self, driver, book_dict):
        driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_OneWay").click()
        #driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchView_RoundTrip").click()
        driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchVieworiginStationMultiColumn1_1").click()
        driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchVieworiginStationMultiColumn1_1").clear()
        driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchVieworiginStationMultiColumn1_1").send_keys("blr")
        driver.find_element_by_xpath("//p[@id='originStationContainer1']/div/div[2]/div/div[2]/ul/li[2]/a/b").click()
        driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchViewdestinationStationMultiColumn1_1").click()
        driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchViewdestinationStationMultiColumn1_1").clear()
        driver.find_element_by_id("ControlGroupSearchView_AvailabilitySearchInputSearchViewdestinationStationMultiColumn1_1").send_keys("goi")
        driver.find_element_by_xpath("//p[@id='destinationStationContainer1']/div/div[2]/div/div[2]/ul/li[2]/a/b").click()
        #driver.find_element_by_link_text("20").click()
        driver = self.date_picker(driver, book_dict)
        driver = self.select_pax(driver, book_dict)
        return driver


    def test_untitled_test_case(self):
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
            self.booking_dict = ast.literal_eval(self.booking_dict)
            book_dict = self.process_input()
        except Exception as e:
            logging.debug(e.message)
            self.insert_into_db(book_dict, e.message)
            #self.send_mail('AirAsia Booking Faild', e.message)
            return
        driver = self.driver
        #*****************login**********************************************
        driver.get("https://booking2.airasia.com/AgentHome.aspx")
        driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_TextBoxUserID").click()
        driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_TextBoxUserID").clear()
        driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_TextBoxUserID").send_keys(user_name)
        driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_PasswordFieldPassword").click()
        driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_PasswordFieldPassword").clear()
        driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_PasswordFieldPassword").send_keys(user_psswd)
        driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_LinkButtonLogIn").click()
        #***********************book my flight ********************************
        driver.implicitly_wait(100)
        try:driver.find_element_by_xpath('//a[@id="Search"]').click()
        except: import pdb;pdb.set_trace()
        #***********************search page **********************************
        driver = self.flight_search(driver, book_dict)#flight search
        driver, ow_flt_id, rt_flt_id = self.select_flight(driver, book_dict)#select flights
        import pdb;pdb.set_trace()
        if rt_flt_id:
            driver.find_element_by_id(ow_flt_id).click()
            driver.find_element_by_id("ControlGroupSelectView_ButtonSubmit").click()
        elif ow_flt_id:
            driver.find_element_by_id(ow_flt_id).click()
            driver.find_element_by_id("ControlGroupSelectView_ButtonSubmit").click()
        else:
            print "Flights not found"
        driver = self.form_filling(driver, book_dict)
        driver.find_element_by_id("CONTROLGROUPADDONSFLIGHTVIEW_ButtonSubmit").click()#addon
        driver.find_element_by_id("ControlGroupUnitMapView_UnitMapViewControl_LinkButtonAssignUnit").click()#unitmap
        driver.find_element_by_id("AgencyAccount").click()#agency sc

    def form_filling(self, driver, book_dict):
        Select(driver.find_element_by_id("CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ContactInputTravelerView_DropDownListOtherPhoneIDC")).select_by_visible_text("India(+91)")
        driver.find_element_by_id("CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ContactInputTravelerView_DropDownListOtherPhoneIDC").click()
        driver.find_element_by_id("CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ContactInputTravelerView_TextBoxOtherPhone").click()
        driver.find_element_by_id("CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ContactInputTravelerView_TextBoxOtherPhone").clear()
        driver.find_element_by_id("CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ContactInputTravelerView_TextBoxOtherPhone").send_keys("9553552623")
        driver.find_element_by_id("NextButton").click()
        driver.implicitly_wait(30)
        guestdetails = book_dict.get('guestdetails', [])
        guestdetails.extend(book_dict.get('childdetails', []))
        import pdb;pdb.set_trace()
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

                driver = self.pax_details_filling(driver, book_dict, pax_de, idx)
                time.sleep(2)
                driver.implicitly_wait(30)
        return driver

    def pax_details_filling(self, driver, book_dict, pax_de, idx):
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
        try:driver.find_element_by_id("NextButton").click()
        except: driver.find_element_by_id("CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ButtonSubmit").click()
        return driver


    def select_flight(self, driver, book_dict):
        driver.implicitly_wait(100)
        fare_class_dict = {'Regular': 'Regular', 'PremiumFlex': 'PremiumFlex',
                           'PremiumFlatbed': 'PremiumFlatbed', "Econamy": "Lowfare", "Economy": "Lowfare"}
        fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price, rt_flt_no = [
            ''] * 5

        time.sleep(20)
        sel = Selector(text=driver.page_source)
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
        import pdb;pdb.set_trace()
        ct_flight_id = book_dict.get('onewayflightid', [])
        ct_ticket_class = book_dict.get(
            'onewayclass', []).replace(' ', '').strip()
        aa_keys = flight_oneway_fares.keys()
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
        print "Stop"
        return (driver, fin_fare_id, refin_fare_id)

    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException as e: return False
        return True

    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException as e: return False
        return True

    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True

    def tearDown(self):
        self.driver.quit()
        self.conn.close()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    UntitledTestCase.booking_dict = os.environ.get('jsons', '{}')
    unittest.main()
