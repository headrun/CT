import re
import ast
import json
import md5
import time
import MySQLdb
import smtplib
import datetime
import inspect
import time
import smtplib
import ssl
from email import encoders
from scrapy import signals
from ast import literal_eval
from scrapy.spider import Spider
from scrapy.selector import Selector
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from booking_scrapers.utils import *
from ConfigParser import SafeConfigParser
from scrapy.http import FormRequest, Request
from scrapy.xlib.pydispatch import dispatcher
from email.mime.multipart import MIMEMultipart
from spicejet_utils import *
from goair_utils import *

from scrapy.conf import settings

import sys
sys.path.append(settings['ROOT_PATH'])

from root_utils import Helpers

_cfg = SafeConfigParser()
_cfg.read(settings['BOOK_PCC_PATH'])


class SpicejetBookingBrowse(Spider, SGBooking, GoairUtils, Helpers):
    name = "spicejet_booking_browse"
    start_urls = ["https://book.spicejet.com/LoginAgent.aspx"]

    def __init__(self, *args, **kwargs):
        super(SpicejetBookingBrowse, self).__init__(*args, **kwargs)
        self.source_name = 'spicejet'
        self.multiple_pcc = False
        self.user_psswd = ''
        self.book_using = ''
        self.meals_issue, self.baggage_issue = False, False
        self.amount, self.tolerance_value = '', ''
        self.log = create_logger_obj('spicejet_booking')
        self.booking_dict = ast.literal_eval(kwargs.get('jsons', '{}'))
        self.special_rt_change()
        all_adults = int(
            self.booking_dict['no_of_adults']) + int(self.booking_dict['no_of_children'])
        if int(self.booking_dict['no_of_infants']) > all_adults:
            self.log.debug('Infants more than adults')
            self.insert_error_msg(err='Infants more thanadults')
            return
        self.ow_input_flight = self.booking_dict['all_segments'][0].values()[
            0]['segments']
        try:
            self.rt_input_flight = self.booking_dict['all_segments'][1].values()[
                0]['segments']
        except:
            self.rt_input_flight = {}
        self.ow_flight_nos = '<>'.join(
            [i['flight_no'] for i in self.ow_input_flight])
        self.rt_flight_nos = '<>'.join(
            [i['flight_no'] for i in self.rt_input_flight])
        self.onewaymealcode, self.returnmealcode = self.mealcode_inputs()
        self.onewaybaggagecode, self.returnbaggagecode = self.baggagecode_inputs()
        check = self.meal_baggage_proper()
        if not check:
            return
        self.auto_phone_check = True
        self.ct_price = sum([i.values()[0]['amount']
                             for i in self.booking_dict['all_segments']])
        self.queue = self.booking_dict['queue']
        self.journey_mismatch = ''
        self.pcc_name = ''
        self.pnrs_to_be_checked, self.pnrs_checked = [], []
        self.adult_fail, self.child_fail, self.infant_fail = False, False, False
        self.tt = ''
        self.insert_query = 'insert into spicejet_booking_report (sk, airline, pnr, flight_number, from_location, to_location, triptype, cleartrip_price, airline_price, status_message, tolerance_amount, oneway_date, return_date, error_message, paxdetails, price_details, created_at, modified_at) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now()) on duplicate key update modified_at=now(), pnr=%s, flight_number=%s, airline_price=%s, status_message=%s, error_message=%s, paxdetails=%s, price_details=%s, triptype=%s, cleartrip_price=%s, tolerance_amount=%s'
        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('booking', 'IP')
        passwd = db_cfg.get('booking', 'PASSWD')
        user = db_cfg.get('booking', 'USER')
        db_name = db_cfg.get('booking', 'DBNAME')
        self.conn = MySQLdb.connect(
            host=host, user=user, passwd=passwd, db=db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()

    def meal_baggage_proper(self):
        persons = int(self.booking_dict['no_of_adults']) + \
            int(self.booking_dict['no_of_children'])
        if len(self.onewaymealcode) > persons:
            self.insert_error(err='one person one meal check failure')
            return False
        elif len(self.onewaybaggagecode) > persons:
            self.insert_error(err='one person one baggage check failure')
            return False
        elif len(self.returnmealcode) > persons:
            self.insert_error(err='one person one meal check failure')
            return False
        elif len(self.returnbaggagecode) > persons:
            self.insert_error(err='one person one baggage check failure')
            return False
        return True

    def parse(self, response):
        '''Parse Login'''
        if not self.booking_dict:
            self.log.debug('Empty Request')
            self.insert_error_msg(err='Empty request')
            return
        login_data_list = []

        self.pcc_name = self.get_pcc_name()  # 'spicejet_BOMCL23479'
        self.log.debug('Login PCC: %s' % self.pcc_name)

        if self.multiple_pcc:
            self.log.debug('Multiple PCC fail')
            self.insert_error_msg(err='Multiple PCC Booking fail')
            return
        sel = Selector(response)
        # self.special_rt_change()
        self.pax_details()
        if self.adult_fail or self.child_fail or self.infant_fail:
            self.insert_error_msg(err="Duplicate passengers")
            self.log.debug('Duplicate passengers')
            return
        view_state = ''.join(
            sel.xpath('//input[@id="viewState"]/@value').extract())
        login_data_list.append(('__VIEWSTATE', view_state))
        try:
            user_name = _cfg.get(self.pcc_name, 'username')
            self.user_psswd = _cfg.get(self.pcc_name, 'password')
            self.log.debug('Login using %s' % user_name)
        except:
            self.log.debug('PCC %s not in scrapper config' % self.pcc_name,)
            self.insert_error_msg(err='PCC not available for scrapper')
            return
        self.book_using = user_name
        try:
            self.tt = '%s_%s_%s' % (
                self.booking_dict['trip_type'], self.queue, self.book_using)
        except:
            pass
        login_data_list.append(
            ('ControlGroupLoginAgentView$AgentLoginView$ButtonLogIn', 'Log In'))
        login_data_list.append(
            ('ControlGroupLoginAgentView$AgentLoginView$TextBoxUserID', str(user_name)))
        login_data_list.append(
            ('ControlGroupLoginAgentView$AgentLoginView$PasswordFieldPassword', str(self.user_psswd)))
        yield FormRequest('https://book.spicejet.com/LoginAgent.aspx',
                          formdata=login_data_list, callback=self.parse_next, meta={'user_name': user_name, 'phone_check': False})

    def parse_next(self, response):
        sel = Selector(response)
        check = response.meta['phone_check']
        if response.status == 200:
            first_dict = self.get_first_details(sel, check)
            if self.queue == 'offline':
                url = 'https://book.spicejet.com/BookingList.aspx'
                return FormRequest(url, callback=self.parse_autopnr, dont_filter=True, formdata=first_dict, meta={'auto_pnr': True, 'phone_check': check})
            else:
                # Go to search straightaway and book
                url = 'https://book.spicejet.com/Select.aspx'
                return FormRequest(url, callback=self.parse_login, dont_filter=True)
        else:
            self.send_mail("SpiceJet Unable to login on Login ID %s" % response.meta.get(
                'username', ''), 'Scrapper Unable to login on Login ID', airline='Spicejet', config='booking', receiver='spicejet_common')
            self.insert_error_msg(
                err='Unable to login on LOGIN ID %s' % response.meta.get('username', ''))

    def parse_autopnr(self, response):
        sel = Selector(response)
        datas = []
        check = response.meta['phone_check']
        auto_pnr = response.meta['auto_pnr']
        second_dict = self.get_first_details(sel, check)
        for i in self.pnrs_checked:
            try: self.pnrs_to_be_checked.remove(i)
            except: self.log.debug('something wrong with autopnr removal')
        if not self.pnrs_to_be_checked and auto_pnr:
	    records = sel.xpath('//table[@id="currentTravelTable"]//tr')
       	    for record in records:
                modify_present = record.xpath('./td/a[contains(@id, "Modify")]')
                if modify_present:
			try: dep, org, dest, pnr, _, _, _, lastname, firstname = record.xpath('./td/text()').extract()
			except:
				print record.xpath('./td/text()').extract()
				self.insert_error_msg(err='Xpath changed in site for auto pnr check')
				return
			if dest != self.booking_dict['destination_code']: continue
			if org != self.booking_dict['origin_code']: continue
			try: dep_date = datetime.datetime.strptime(dep.strip(), '%d %b, %Y').strftime('%d-%b-%y')
			except: dep_date = ''
			if dep_date != self.booking_dict['departure_date']: continue
			self.pnrs_to_be_checked.append((pnr, '%s %s' % (lastname, firstname)))
        #self.pnrs_to_be_checked = [i[0] for i in datas]
        self.log.debug('PNRs Found: %s' % self.pnrs_to_be_checked)
        if len(self.pnrs_to_be_checked):
            for data in self.pnrs_to_be_checked:
                self.log.debug('Checking PNR: %s' % data[0])
            second_dict.update({
                '__EVENTTARGET': 'ControlGroupBookingListView$BookingListBookingListView',
                '__EVENTARGUMENT': 'Edit:%s' % data[0],
                'ControlGroupBookingListView$BookingListBookingListView$TextBoxKeyword': data[1]
            })
            url = 'https://book.spicejet.com/BookingList.aspx'
            return FormRequest(url, callback=self.parse_pnrpage, formdata=second_dict, dont_filter=True, meta={'data' : data, 'phone_check' : check})
        elif len(self.pnrs_to_be_checked) >= 5:
            self.insert_error_msg(
                err="More than 5 pnrs to check, failing to manual queue")
            self.log.debug('More than 5 pnrs to check')
            return
        else:
            if not self.auto_phone_check:
                # yield to prase_login function
                url = 'https://book.spicejet.com/Search.aspx'
                self.log.debug('No auto PNRs to check, go ahead for booking')
                return Request(url, callback=self.parse_login, dont_filter=True)
            else:
                self.auto_phone_check = False
                self.pnrs_checked = []
                url = 'https://book.spicejet.com/BookingList.aspx'
                return Request(url, callback=self.parse_next, dont_filter=True, meta={'phone_check': True})

    def parse_pnrpage(self, response):
        sel = Selector(response)
        data = response.meta['data']
        check = response.meta['phone_check']
        pnr, lname = data[0], data[1]
        passengers_check = False
        journey_details = sel.xpath(
            '//table[@id="flight-journey-detail"]//tr/td/text()').extract()
        journey_check = self.journey_check(journey_details)
        if journey_check:
            self.log.debug("Journey details mismatch")
            self.insert_error_msg(
                err="Journey details mismatch %s" % self.journey_mismatch)
            return
        passenger_details = sel.xpath(
            '//table[@class="tgrid-MMB hide-mobile passenger-information"]//tr[@class="passenger-info-border"]')
        person_present = False
        all_pax = [' '.join(i[1:3])
                   for i in self.booking_dict['pax_details'].values()]
        all_pax_len = len(all_pax)
        if all_pax_len != len(set(all_pax)):
            self.log.debug('Duplicate passengers(gender title)')
            self.insert_error_msg(
                mesg='', err="Duplicate passengers - gender title")
            return
        passengers_len = len(passenger_details)
        if all_pax_len != passengers_len:
            self.log.debug("length of passengers are not same")
            self.insert_error_msg('', err="length of passengers are not same %s %s" % (
                all_pax_len, passengers_len))
            return
        counter = 0
        for j in all_pax:
            for i in passenger_details:
                name = ''.join(i.xpath(
                    './td[@class="passenger-info-name"]/text()').extract()).replace('  ', ' ').strip().title()
                name = ' '.join(name.split()[1:])
                if name == j.title():
                    counter += 1
                    break
                self.log.debug('%s %s' % (name,  j))
        if counter != all_pax_len:
            self.log.debug("not matching names of passengers")
            passengers_check = True
            self.insert_error_msg(mesg='', err="not matching names of passengers")
            return
        a_price = sel.xpath('//tr[contains(@class, "passenger-payment")]//td/span[contains(text(), "Total")]/..//text()').extract(
        )[-1].replace(u'\xa0INR', '').replace(',', '')
        if not passengers_check and not journey_check:
            data = sel.xpath(
                '//div[@class="sumry_table"]//td//text()').extract()

            try:
                data = filter(None, map(unicode.strip, data))
            except:
                data = {}
            total_dict = {}
            if data:
                data = {data[i].strip(): data[i+1].strip()
                        for i in range(0, len(data), 2)}
                total_dict['total'] = data.pop('Total Price')
            total_dict.update({'AUTO_PNR_EXISTS': True})

            p_details = self.get_autopnr_pricingdetails(total_dict)
            self.insert_error_msg(pnr=pnr, p_details=json.dumps(
                p_details), a_price=a_price, mesg='Auto PNR exists: %s' % pnr)
            self.log.debug('Auto PNR exists: %s' % pnr)
            return
        self.pnrs_checked.append((pnr, lname))
        self.log.debug('PNRs checked : %s' % self.pnrs_checked)
        self.log.debug("Tried with PNR : %s" % (pnr))
        profile_url = 'https://book.spicejet.com/BookingList.aspx'
        yield Request(profile_url, callback=self.parse_autopnr, dont_filter=True, meta={'auto_pnr': False, 'phone_check': check})

    def parse_login(self, response):
        sel = Selector(response)
        triptype_dict = {'OW': 'OneWay', 'RT': 'RoundTrip'}
        triptype = triptype_dict[self.booking_dict['trip_type']]
        origin = self.booking_dict['origin_code']
        destination = self.booking_dict['destination_code']
        currency = self.booking_dict['currency_code']
        dep_date = self.booking_dict['departure_date']
        dep_date = datetime.datetime.strptime(
            dep_date, '%d-%b-%y').strftime('%d/%m/%Y')
        day = dep_date.split('/')[0]
        year_month = '-'.join((dep_date.split('/')[:0:-1]))
        ret_date = self.booking_dict.get('return_date', '')
        ret_day, retyear_month = '', ''
        if ret_date:
            ret_date = datetime.datetime.strptime(
                ret_date, '%d-%b-%y').strftime('%d/%m/%Y')
            #ret_day = ret_date.split('/')[0]
            #retyear_month = '-'.join((ret_date.split('/')[:0:-1]))
            dep_date = ret_date
        no_of_adults, no_of_children, no_of_infants = self.booking_dict[
            'no_of_adults'], self.booking_dict['no_of_children'], self.booking_dict['no_of_infants'],
        search_dict = {'pageToken': ''}
        view_state = ''.join(
            sel.xpath('//input[@id="viewState"]/@value').extract())
        search_dict.update({
            '__EVENTTARGET': 'ControlGroupSearchView$AvailabilitySearchInputSearchView$ButtonSubmit',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': view_state,
            'ControlGroupSearchView$AvailabilitySearchInputSearchView$RadioButtonMarketStructure': triptype,
            'ControlGroupSearchView$AvailabilitySearchInputSearchView$Date2': dep_date,
            'ControlGroupSearchView$AvailabilitySearchInputSearchView$TextBoxMarketOrigin1': origin,
            'ControlGroupSearchView_AvailabilitySearchInputSearchVieworiginStation1': origin,
            'ControlGroupSearchView$AvailabilitySearchInputSearchView$TextBoxMarketDestination1': destination,
            'ControlGroupSearchView_AvailabilitySearchInputSearchViewdestinationStation1': destination,
            'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListMarketDay1': day,
            'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListMarketMonth1': year_month,
            'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListPassengerType_ADT': no_of_adults,
            'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListPassengerType_CHD': no_of_children,
            'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListPassengerType_INFANT': no_of_infants,
            'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListCurrency': currency,
        })

        url = 'https://book.spicejet.com/Search.aspx'
        return FormRequest(url, callback=self.parse_search, formdata=search_dict, dont_filter=True)

    def parse_search(self, response):
        sel = Selector(response)
        # Get all flights from listings in a dict
        class_mapping_dict = {'Handbaggage': ['Hand Baggage Only'], 'Economy_0': ['Summer Sale', 'Regular Saver', 'Spice Flex'], 'Economy_1': ['Summer Sale', 'Holiday Return', 'Regular Saver', 'Spice Flex'], 'Business': ['Spice Flex']}
        ticketclass_dict = self.get_flight_fares(sel)
        if self.booking_dict['ticket_booking_class'] == 'Economy':
            if self.book_using == 'BOMCLC9742':
                self.booking_dict['ticket_booking_class'] = 'Economy_1'
            else:
                self.booking_dict['ticket_booking_class'] = 'Economy_0'
        print self.booking_dict['ticket_booking_class']
        ticket_class = class_mapping_dict.get(
            self.booking_dict['ticket_booking_class'], '')
        # if set(ticketclass_dict.keys()).issubset(ticket_class) and ticketclass_dict.keys() != []:
        if ticketclass_dict.keys() != []:
            # ticketclass_dict[ticket_class].get(self.ow_flight_nos, '')
            try: fb_code = self.ow_input_flight[0]['fare_basis_code']
            except: fb_code = ''
            flights_ow_key_value = self.find_flight_keyval(
                ticket_class, ticketclass_dict, self.ow_flight_nos, True, fb_code)
            if not flights_ow_key_value:
                self.insert_error_msg(err='Flight not found in selected class')
                self.log.debug('Flight not found in selected class')
                return
            gst_token = ''.join(sel.xpath(
                '//input[contains(@name, "InputGSTViewSelectViewHtmlInputHiddenAntiForgeryTokenField")]/@value').extract())
            view_state = ''.join(
                sel.xpath('//input[@id="viewState"]/@value').extract())
            select_flight_dict = {'__EVENTARGUMENT': '', '__EVENTTARGET': ''}
            select_flight_dict.update({
                'ControlGroupSelectView$ContactInputGSTViewSelectView$ControlGroupSelectView_ContactInputGSTViewSelectViewHtmlInputHiddenAntiForgeryTokenField': gst_token,
                'ControlGroupSelectView$ContactInputGSTViewSelectView$CheckBoxGST': 'on',
                'ControlGroupSelectView$ButtonSubmit': 'Continue',
                '__VIEWSTATE': view_state,
            })
            select_flight_dict.update({flights_ow_key_value.split(
                '#<>#')[0]: flights_ow_key_value.split('#<>#')[-1]})
            if self.rt_flight_nos:
                # ticketclass_dict[ticket_class].get(self.rt_flight_nos, '')
            	try: fb_code = self.rt_input_flight[0]['fare_basis_code']
            	except: fb_code = ''
                flights_rt_key_value = self.find_flight_keyval(
                    ticket_class, ticketclass_dict, self.rt_flight_nos, False, fb_code)

                if not flights_rt_key_value:
                    self.insert_error_msg(
                        err='Return flight not found in selected class')
                    self.log.debug('Return flight not found in selected class')
                    return
                select_flight_dict.update({flights_rt_key_value.split(
                    '#<>#')[0]: flights_rt_key_value.split('#<>#')[-1]})
            url = 'https://book.spicejet.com/Select.aspx'
            return FormRequest(url, callback=self.parse_selected, formdata=select_flight_dict, dont_filter=True)
        else:
            self.insert_error_msg(err='No flights with selected class')
            self.log.debug('No flights with selected class')
            return

    def parse_selected(self, response):
        sel = Selector(response)
        select_next_dict = self.get_first_details(sel, False, False)

        select_next_dict.update({
                                '__EVENTARGUMENT': '', '__EVENTTARGET': '',
                                'pageToken': '',  'InsuranceSingle': 'No',
                                'ISAGENTLOGGEDIN': 'True',
                                'CONTROLGROUPPASSENGER$ButtonSubmit': 'Continue',

                                })
        title_state_country = sel.xpath(
            '//div[@class="agent-section-row"]//select')
        for i in title_state_country:
            key = ''.join(i.xpath('./@name').extract())
            value = ''.join(i.xpath('./option[@selected]/@value').extract())
            select_next_dict.update({key: value})
        form_fill_details = sel.xpath(
            '//div[@class="agent-section-row"]//input')
        for i in form_fill_details:
            key = ''.join(i.xpath('./@name').extract())
            value = ''.join(i.xpath('./@value').extract())
            if value == 'middle':
                value = ''
            if 'TextBoxCountryCodeHomePhone' in key or 'TextBoxCountryCodeOtherPhone' in key:
                value = '91'
            elif 'TextBoxWorkPhone' in key:
                value = value.strip('022')
            elif 'TextBoxHomePhone' in key or 'TextBoxOtherPhone' in key:
                value = self.booking_dict['contact_mobile']
            elif 'Country' in key:
                value = 'IN'
            elif 'TextBoxFax' in key:
                value = ''
            select_next_dict.update({key: value})
        hidden_excess_bgs = sel.xpath(
            '//div[@class="mealdropdown baggage-count"]//input[@type="hidden"]')
        for i in hidden_excess_bgs:
            key = ''.join(i.xpath('./@id').extract())
            value = ''.join(i.xpath('./@value').extract())
            select_next_dict.update({key: value})
        passenger_details = self.booking_dict['adults']
        passenger_details.extend(self.booking_dict['children'])
        select_next_dict.update(
            {'CONTROLGROUPPASSENGER$ContactInputPassengerView$DropDownListSuffix': 'none'})
        hq_baggages = self.onewaybaggagecode, self.returnbaggagecode
        if not self.onewaybaggagecode and not self.returnbaggagecode:
            baggage_xpath = ''.join(sel.xpath(
                '//div[@class="mealdropdown"]//select[contains(@id, "BaggageInputViewPassengerView")]/@name').extract())
            select_next_dict.update({baggage_xpath: ''})
        else:
            update_select_dict = self.update_baggages(hq_baggages, sel)
            if not update_select_dict or self.baggage_issue:
                self.insert_error_msg(err="Issue with baggages")
                return
            select_next_dict.update(update_select_dict)
        hq_meals = self.onewaymealcode, self.returnmealcode
        if not self.onewaymealcode and not self.returnmealcode:
            meals_xpath = sel.xpath(
                '//div[@class="mealDropdown"]//input[contains(@id, "MealLegInputViewPassengerView") and @type="text"]/@name').extract()
            meals_xpath_select = sel.xpath(
                '//div[@class="mealDropdown"]//select[contains(@id, "Select_CONTROLGROUPPASSENGER")]/@name').extract()
            all_meals_keys = meals_xpath + meals_xpath_select
            for i in all_meals_keys:
                select_next_dict.update({i: ''})
        else:
            update_select_dict = self.update_meals(hq_meals, sel)
            if not update_select_dict or self.meals_issue:
                self.insert_error_msg(err="Issue with meals")
                return
            select_next_dict.update(update_select_dict)
        token = ''.join(sel.xpath(
            '//input[contains(@name, "HiddenAntiForgeryTokenField")]/@value').extract())
        token_key = ''.join(sel.xpath(
            '//input[contains(@name, "HiddenAntiForgeryTokenField")]/@name').extract())
        select_next_dict.update({token_key: token})
        for h, i in enumerate(passenger_details):
            if i.get('gender', '') == 'Male':
                gender = '1'
            else:
                gender = '2'
            select_next_dict.update({
                'CONTROLGROUPPASSENGER$PassengerInputViewPassengerView$DropDownListTitle_%s' % h:  i.get('title'),
                'CONTROLGROUPPASSENGER$PassengerInputViewPassengerView$DropDownListDocumentType%s_%s' % (h, h): 'A',
                'CONTROLGROUPPASSENGER$PassengerInputViewPassengerView$DropDownListGender_%s' % h: gender,
                'CONTROLGROUPPASSENGER$PassengerInputViewPassengerView$TextBoxFirstName_%s' % h: i.get('firstname'),
                'CONTROLGROUPPASSENGER$PassengerInputViewPassengerView$TextBoxLastName_%s' % h: i.get('lastname'),
            })

        # Keep one check for infant len and adult + child len equal or not, if not fail it initially itself
        for h, i in enumerate(self.booking_dict['infants']):
            year,  month, day = i.get('dob').split('-')
            select_next_dict.update({
                'CONTROLGROUPPASSENGER$PassengerInputViewPassengerView$DropDownListTitle_%s_%s' % (h, h): i.get('title'),
                'CONTROLGROUPPASSENGER$PassengerInputViewPassengerView$DropDownListAssign_%s_%s' % (h, h): str(h),
                'CONTROLGROUPPASSENGER$PassengerInputViewPassengerView$DropDownListBirthDateDay_%s_%s' % (h, h): day,
                'CONTROLGROUPPASSENGER$PassengerInputViewPassengerView$DropDownListBirthDateMonth_%s_%s' % (h, h): month,
                'CONTROLGROUPPASSENGER$PassengerInputViewPassengerView$DropDownListBirthDateYear_%s_%s' % (h, h): year,
                'CONTROLGROUPPASSENGER$PassengerInputViewPassengerView$DropDownListDocumentType%s_%s' % (h, h): 'A',
                'CONTROLGROUPPASSENGER$PassengerInputViewPassengerView$TextBoxFirstName_%s_%s' % (h, h): i.get('firstname'),
                'CONTROLGROUPPASSENGER$PassengerInputViewPassengerView$TextBoxLastName_%s_%s' % (h, h): i.get('lastname'),
            })
        select_next_dict['CONTROLGROUPPASSENGER$ContactInputPassengerView$TextBoxEmailAddress'] = self.booking_dict['emailid']
        select_next_dict['CONTROLGROUPPASSENGER$ContactInputPassengerView$DropDownListCountry'] = 'IN'
        url = 'https://book.spicejet.com/Contact.aspx'
        yield FormRequest(url, callback=self.parse_seat, formdata=select_next_dict, dont_filter=True)

    def parse_seat(self, response):
        sel = Selector(response)
        seat_next_dict = self.get_first_details(sel, False, False)
        seat_next_dict.update({
            '__EVENTARGUMENT': '',
            '__EVENTTARGET': 'ControlGroupUnitMapView$UnitMapViewControl$LinkButtonSubmit',
            'pageToken': '',

        })
        data = sel.xpath(
            '//div[@class="pax-seat-selection"]//td[@class="seatSelect"]/input')
        data = sel.xpath('//div[@id="seatMapMainContent"]//input')
        for i in data:
            key = ''.join(i.xpath('./@name').extract())
            if key.startswith('ssr') or key == '':
                continue
            value = ''.join(i.xpath('./@value').extract())
            counter = 0
            for i in ['MaxSSR', 'CouponFare', 'CouponFareSpiceMax', 'MaxMealSSR', 'SeatMealSSR',  'tripInput', 'deckDesignatorInput', 'compartmentDesignatorInput', 'passengerInput']:
                if i not in key:
                    counter += 1
            if counter == 9:
                value = ''

            seat_next_dict.update({key: value})
        p_details = self.price_details(sel)
        url = 'https://book.spicejet.com/SeatMapFromPayment.aspx'
        yield FormRequest(url, callback=self.parse_payment_start, formdata=seat_next_dict, dont_filter=True, meta={'p_details': p_details})

    def parse_payment_start(self, response):
        sel = Selector(response)
        p_details = response.meta['p_details']
        data = self.get_autopnr_pricingdetails({})
        counter = 0
        for key, value in p_details.iteritems():
            try: p_details[key].update(data.values()[counter])
            except:
                try: p_details[key].update(data.values()[counter])
                except Exception as e: self.log.debug(e)
            counter += 1
        payment_dict = self.get_first_details(sel, False, False)
        ATMCumDebit = ''.join(
            sel.xpath('//div[@id="AtmBankDropDownContainer"]//option/@value').extract())
        ATMDEBITGroup = ''.join(sel.xpath(
            '//div[@id="PrePaid_AD"]//input[@name="ATMDEBITGroup" and @checked]/@value').extract())
        AgencyAccount_AG_AMOUNT = ''.join(sel.xpath(
            '//input[contains(@name, "AgencyAccount_AG_AMOUNT")]/@value').extract())
        self.amount = AgencyAccount_AG_AMOUNT
        is_proceed, tolerance_value = 0, 0
        if not AgencyAccount_AG_AMOUNT:
            self.send_mail("Agency Account not found %s" %
                           self.booking_dict['trip_ref'], '', 'booking', 'spicejet', 'spicejet_common')
            self.insert_error_msg(err="Agency Account not found")
            return
        else:
            tolerance_value, is_proceed = self.check_tolerance(
                self.ct_price, AgencyAccount_AG_AMOUNT)
        payment_dict = payment_dict.items()
        self.tolerance_value = tolerance_value
        if is_proceed == 1:
            payment_dict.extend(
                [('ATMCumDebit', ATMCumDebit),
                 ('ATMDEBITGroup', ATMDEBITGroup),
                 ('CONTROLGROUPPAYMENTBOTTOM$ButtonSubmit', 'Confirm Payment'),
                 ('CONTROLGROUPPAYMENTBOTTOM$ControlGroupPaymentInputViewPaymentView$AgencyAccount_AG_AMOUNT',
                  AgencyAccount_AG_AMOUNT),
                 ('CONTROLGROUPPAYMENTBOTTOM$ControlGroupPaymentInputViewPaymentView$DropDownListPaymentMethodCode', 'AgencyAccount:AG'),
                 ('CONTROLGROUPPAYMENTBOTTOM$ControlGroupPaymentInputViewPaymentView$hdHoldpaidflag', 'false'),
                 ('CONTROLGROUPPAYMENTBOTTOM$ControlGroupPaymentInputViewPaymentView$storedPaymentId', ''),
                 ('DropDownListPaymentMethodCode', 'PrePaid:IB'),
                 ('DropDownListPaymentMethodCode', 'ExternalAccount:MC'),
                 ('ISAGENTLOGGEDIN', 'TRUE'),
                 ('TextBoxAMT', AgencyAccount_AG_AMOUNT),
                 ('TextBoxCC::VerificationCode', self.user_psswd),
                 ('WalletMode', 'WP'),
                 ('TextBoxCC::AccountHolderName', ''),
                 ('NetBanking', ''),
                 ('PrePaid_HB', ''),
                 ('PromoCodePaymentView$TextBoxAccountNumber', ''),
                 ('PromoCodePaymentView$TextBoxPromoCode', ''),
                 ('TextBoxACCTNO', ''),
                 ('TextBoxEXPDAT', ''),
                 ('__EVENTARGUMENT', ''),
                 ('__EVENTTARGET', ''),
                 ('pageToken', ''),
                 ('termcondition', 'on')]
            )
            if self.booking_dict['proceed_to_book'] == 1:
                url = 'https://book.spicejet.com/Payment.aspx'
                yield FormRequest(url, callback=self.parse_wait, formdata=payment_dict, dont_filter=True, meta={'p_details': p_details})
            else:
                self.insert_error_msg(mesg='Mock Success', pnr='TEST101', p_details=p_details,
                                      a_price=AgencyAccount_AG_AMOUNT, tolerance=tolerance_value)
                self.log.debug('Mock success')
                return
        else:
            self.insert_error_msg(err='Fare increased by Spicejet', mesg='Booking failed, price rise',
                                  p_details=json.dumps(p_details), a_price=str(AgencyAccount_AG_AMOUNT))
            self.send_mail("Fare increased by Spicejet for %s by %s or response error" % ((self.booking_dict.get('trip_ref', ''), tolerance_value)), '', 'booking', 'spicejet', 'spicejet_common')
            url = 'https://book.spicejet.com/LoginAgent.aspx'
            yield Request(url, callback=self.parse_logout, dont_filter=True)

    def parse_wait(self, response):
        url = 'https://book.spicejet.com/Wait.aspx'
        time.sleep(30)
        time.sleep(35)
        settings.set('DOWNLOAD_DELAY', 65, priority='cmdline')
        yield Request(url, callback=self.parse_final, dont_filter=True, meta={'p_details': response.meta['p_details']})

    def parse_final(self, response):
        sel = Selector(response)
        p_details = response.meta['p_details']
        pnr = ''.join(sel.xpath(
            '//table[@id="bookingDetail"]//td[@class="width-confirm-pnr"]//strong/text()').extract()) or ''.join(sel.xpath('//div[@id="RecordLocator"]/text()').extract())
        open('%s%s.html' %
             (self.booking_dict['trip_ref'], pnr), 'a').write(response.body)
        status = ''.join(sel.xpath(
            '//table[@id="bookingDetail"]//td[@class="width-pnr-status"]//strong/text()').extract())
        if pnr:
            self.insert_error_msg(mesg=status, pnr=pnr, p_details=p_details,
                                  a_price=self.amount, tolerance=self.tolerance_value)
            self.log.debug('Trip ID %s Booked successfully : %s' %
                           (self.booking_dict['trip_ref'], pnr))
        else:
            self.insert_error_msg(mesg=status, pnr=pnr, p_details=p_details, err="Scrapper did not get PNR from site",
                                  a_price=self.amount, tolerance=self.tolerance_value)
            self.log.debug('PNR not created - Error in booking')
        url = 'https://book.spicejet.com/LoginAgent.aspx'
        yield Request(url, callback=self.parse_logout, dont_filter=True)

    def parse_logout(self, response):
        if response.status == 200:
            self.log.debug('Logged out successfully')
