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


class AirAsiaBookingBrowse(Spider, AirAsiaUtils, IndigoUtils):
    name = "airasiabooking_browse"
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
	settings.overrides['HTTP_PROXY'] = ''
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

    def parse(self, response):
        '''Login to AirAsia'''
        sel = Selector(response)
        waiting_room = ''.join(sel.xpath('//title/text()').extract())
        if waiting_room == 'AirAsia Waiting Room' and response.meta.get('counter') < 3:
            time.sleep(15)
            counter += 1
            return Request(response.url, callback=self.parse, dont_filter=True, meta={'counter' : counter})
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
	'''
	garbage = ''.join(sel.xpath('//title/text()').extract())
	if not garbage:
		self.insert_into_db(book_dict, "Failed due to server busy Garbage")
		open('%s_managemybook_not_loaded' % book_dict.get('trip_ref', 'booking_dict'), 'w').write(response.body)
		return
	'''
	login_failed = ''.join(sel.xpath('//div[@id="errorSectionContent"]//text()').extract())
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
		self.insert_into_db(book_dict, "Booking Scraper unable to login due to server busy")
		open('%s_login_failed' % book_dict.get('trip_ref', 'Check the booking dict'), 'w').write(response.body)
		logging.debug('Booking Scraper unable to login due to server busy %s'%book_dict.get('trip_ref', ''))
		return
	if 'err504.html' in response.url.lower():
                self.insert_into_db(book_dict, "Booking Scraper unable to login due to server busy")
                open('%s_login_failed' % book_dict.get('trip_ref', 'Check the booking dict'), 'w').write(response.body)
                logging.debug('Booking Scraper unable to login due to server busy %s'%book_dict.get('trip_ref', ''))
                return
	if 'err502.html' in response.url.lower():
                self.insert_into_db(book_dict, "Booking Scraper unable to login due to server busy")
                open('%s_login_failed' % book_dict.get('trip_ref', 'Check the booking dict'), 'w').write(response.body)
                logging.debug('Booking Scraper unable to login due to server busy %s'%book_dict.get('trip_ref', ''))
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
			logging.debug('************Retry for Garbage response |%s*******************'%book_dict.get('trip_ref', ''))
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
			return Request('https://booking2.airasia.com/LoginAgent.aspx', callback=self.parse, headers=headers, cookies={}, dont_filter=True, meta={'content' : True})
		else:
                	open('%s_garbage' % book_dict.get('trip_ref', 'Check the booking dict'), 'w').write(response.body)
                	logging.debug('Login Failed Server Busy %s, %s, %s' % (response.status, manage_booking, response.url))
                	self.insert_into_db(book_dict, 'Booking Scraper unable to login due to server busy Garbage')
                	return
            else:
                open('%s_login_failed' % book_dict.get('tripid', 'Check the booking dict'), 'w').write(response.body)
                self.insert_into_db(book_dict, "Booking Scraper unable to login due to server busy")
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
	error_check = normalize(''.join(sel.xpath('//div[@id="errorSectionContent"]//text()').extract()))
	if error_check:
		self.insert_into_db(book_dict, error_check)
		open('%s_search_error' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
		return
        garbage = ''.join(sel.xpath('//title/text()').extract())
        if not garbage:
                self.insert_into_db(book_dict, "Failed due to server busy Garbage")
                open('%s_searchpage_not_loaded' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
                return
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'cache-control': 'no-cache',
            'authority': 'booking2.airasia.com',
            'referer': 'https://booking2.airasia.com/AgentHome.aspx',
        }
        search_flights = 'https://booking2.airasia.com/Search.aspx'
        if self.queue != 'offline':
            return Request(search_flights, callback=self.parse_search_flights,
                           headers=headers, dont_filter=True, meta={'book_dict': book_dict})

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
        error_check = normalize(''.join(sel.xpath('//div[@id="errorSectionContent"]//text()').extract()))
        if error_check:
                self.insert_into_db(book_dict, error_check)
                open('%s_pnrdetails_error' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
                return
        garbage = ''.join(sel.xpath('//title/text()').extract())
        if not garbage:
                self.insert_into_db(book_dict, "Failed due to server busy Garbage")
                open('%s_selectpnr_not_loaded' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
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
        '''
	if self.queue != 'offline':
	    return Request(search_flights, callback=self.parse_search_flights, \
                        headers=headers, dont_filter=True, meta={'book_dict':book_dict})
	'''
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
                
                open('%s_pnrsearchfail' % book_dict.get('tripid', 'Check the booking dict'), 'w').write(response.body)
                return
            if not current_booking_table:
                print "No details found with pax last name(%s), go ahead to booking" % pax_last_name
                if trip_status:
                    return Request(search_flights, callback=self.parse_search_flights,
                                   dont_filter=True, meta={'book_dict': book_dict})
            auto_book_dict = self.check_depature_date(
                book_dict, cur_booking_dict)  # date check
            if not auto_book_dict:
                print "No details found with pax last name(%s), go ahead to booking" % pax_last_name
                if trip_status:
                    return Request(search_flights, callback=self.parse_search_flights,
                                   dont_filter=True, meta={'book_dict': book_dict})
            auto_book_dict = self.check_hq_pax_name(
                book_dict, auto_book_dict)  # pax name check
            if not auto_book_dict:
                print "No details found with pax last name(%s), gohead to booking" % pax_last_name
                if trip_status:
                    return Request(search_flights, callback=self.parse_search_flights,
                                   dont_filter=True, meta={'book_dict': book_dict})
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
            if book_dict.get('triptype', '') == 'OneWay' or book_dict.get('triptype', '') == 'RoundTrip':
                return Request(search_flights, callback=self.parse_search_flights,
                               headers=headers, dont_filter=True, meta={'book_dict': book_dict})

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
        error_check = normalize(''.join(sel.xpath('//div[@id="errorSectionContent"]//text()').extract()))
        if error_check:
                self.insert_into_db(book_dict, error_check)
                open('%s_pnr_error' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
                return
        garbage = ''.join(sel.xpath('//title/text()').extract())
        if not garbage:
                self.insert_into_db(book_dict, "Failed due to server busy Garbage")
                open('%s_autopnr_not_loaded' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
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

            book_dict['price_details'] = self.get_autopnr_pricingdetails({'total' : book_dict.get('airasia_price', ''), 'AUTO_PNR_EXISTS' : True})
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
            url = 'https://booking2.airasia.com/BookingList.aspx'
            return Request(url, callback=self.parse_search,
                           meta={'book_dict': book_dict, 'form_data': form_data, 'autopnr_status': 1}, dont_filter=True)

    def fetch_auto_pnr_booking(self, response):
        sel = Selector(response)
        book_dict = response.meta.get('book_dict', {})
        event_argument = 'Edit:RSZSHK'
        view_state = ''.join(sel.xpath(view_state_path).extract())
        if response.status != 200:
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
            return
        form_data = response.meta['form_data']
        form_data['__VIEWSTATE'] = view_state
        form_data['__EVENTARGUMENT'] = event_argument
        headers = {
            'Pragma': 'no-cache',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://booking2.airasia.com/ItineraryReadOnly.aspx',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
        }
        url = 'https://booking2.airasia.com/BookingList.aspx'
        return FormRequest(url, callback=self.parse_details, formdata=form_data, headers=headers,
                           meta={'book_dict': book_dict, 'form_data': form_data}, dont_filter=True)

    def parse_search_flights(self, response):
        '''Fetching flights'''
        sel = Selector(response)
        book_dict = response.meta.get('book_dict', {})
        if response.status != 200:
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
            return
        garbage = ''.join(sel.xpath('//title/text()').extract())
        if not garbage:
                self.insert_into_db(book_dict, "Failed due to server busy Garbage")
                open('%s_flightsearch_not_loaded' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
                return
        error_check = normalize(''.join(sel.xpath('//div[@id="errorSectionContent"]//text()').extract()))
        if error_check:
                self.insert_into_db(book_dict, error_check)
                open('%s_search_error' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
                return
        view_state = normalize(''.join(sel.xpath(view_state_path).extract()))
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
        origin = book_dict.get('origin', '')
        dest = book_dict.get('destination', '')
        trip_type = book_dict.get('triptype', '')
        oneway_date = book_dict.get('onewaydate', '')
        return_date = book_dict.get('returndate', '')
        oneway_date_ = datetime.datetime.strptime(oneway_date, '%Y-%m-%d')
        bo_day, bo_month, bo_year = oneway_date_.day, oneway_date_.month, oneway_date_.year
        boarding_date = oneway_date_.strftime('%m/%d/%Y')
        if return_date:
            return_date_ = datetime.datetime.strptime(return_date, '%Y-%m-%d')
            re_day, re_month, re_year = return_date_.day, return_date_.month, return_date_.year,
            return_date = return_date_.strftime('%m/%d/%Y')
        else:
            return_date, re_day, re_month, re_year = '', '', '', '',
        no_of_adt = book_dict.get('paxdetails', {}).get('adult', '0')
        no_of_chd = book_dict.get('paxdetails', {}).get('child', '0')
        no_of_infant = book_dict.get('paxdetails', {}).get('infant', '0')
        # OneWay,RoundTrip
        form_data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': view_state,
            'pageToken': '',
            'ControlGroupSearchView$MultiCurrencyConversionViewSearchView$DropDownListCurrency': 'default',
            'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListSearchBy': 'columnView',
            '__VIEWSTATEGENERATOR': gen,
            'ControlGroupSearchView$ButtonSubmit': 'Search',
        }
        form_data.update({'ControlGroupSearchView$AvailabilitySearchInputSearchView$RadioButtonMarketStructure': trip_type,

                          'ControlGroupSearchView_AvailabilitySearchInputSearchVieworiginStation1': origin,
                          'ControlGroupSearchView$AvailabilitySearchInputSearchView$TextBoxMarketOrigin1': origin,
                          'ControlGroupSearchView_AvailabilitySearchInputSearchViewdestinationStation1': dest,
                          'ControlGroupSearchView$AvailabilitySearchInputSearchView$TextBoxMarketDestination1': dest,
                          'date_picker': str(boarding_date),
                          'date_picker': '',
                          'date_picker': str(return_date),
                          'date_picker': '',
                          'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListMarketDay1': str(bo_day),
                          'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListMarketMonth1': '%s-%s' % (bo_year, bo_month),
                          'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListMarketDay2': str(re_day),
                          'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListMarketMonth2': '%s-%s' % (re_year, re_month),
                          'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListPassengerType_ADT': no_of_adt,
                          'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListPassengerType_CHD': no_of_chd,
                          'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListPassengerType_INFANT': no_of_infant,

                          })
        if book_dict.get('triptype', '') == 'OneWay' or book_dict.get('triptype', '') == 'RoundTrip':
            if book_dict.get('triptype', '') == 'OneWay':
                form_data.update({'oneWayOnly': '1', })
            select_url = 'https://booking2.airasia.com/Search.aspx'
            yield FormRequest(select_url, callback=self.parse_select_fare,
                              formdata=form_data, meta={'form_data': form_data, 'book_dict': book_dict})

    def parse_select_fare(self, response):
        '''Selecting flight as per request'''
        sel = Selector(response)
        book_dict = response.meta.get('book_dict', {})
        form_data = response.meta['form_data']
        if response.status != 200:
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
            return
        garbage = ''.join(sel.xpath('//title/text()').extract())
        if not garbage:
                self.insert_into_db(book_dict, "Failed due to server busy Garbage")
                open('%s_flightid_not_loaded' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
                return
        error_check = normalize(''.join(sel.xpath('//div[@id="errorSectionContent"]//text()').extract()))
        if error_check:
                self.insert_into_db(book_dict, error_check)
                open('%s_select_error' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
                return
        fare_class_dict = {'Regular': 'Regular', 'PremiumFlex': 'PremiumFlex',
                           'PremiumFlatbed': 'PremiumFlatbed', "Econamy": "Lowfare", "Economy": "Lowfare"}
        view_state = normalize(''.join(sel.xpath(view_state_path).extract()))
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
        fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price, rt_flt_no = [
            ''] * 5
        refin_fare_id, refin_fare_name, refin_fare_vlue, refin_price = [''] * 4
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
            logging.debug('Flithts  not found')
        if not retable_nodes and book_dict.get('triptype', '') == 'RoundTrip':
            err = 'No Flights found'
            logging.debug('Flithts  not found')
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
        fin_fare_dict, ow_flt_no = self.get_fin_fares_dict(
            flight_oneway_fares, ct_flight_id)
        final_flt_tuple = fin_fare_dict.get(
            fare_class_dict.get(ct_ticket_class, ''), ['']*4)
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
        if fin_fare_vlue:
            form_data.update({
                             field_tab_index: field_tab_value,
                             fin_fare_name: fin_fare_vlue,
                             'ControlGroupSelectView$SpecialNeedsInputSelectView$RadioButtonWCHYESNO': 'RadioButtonWCHNO',
                             '__VIEWSTATEGENERATOR': gen,
                             '__VIEWSTATE': view_state,
                             'ControlGroupSelectView$ButtonSubmit': 'Continue',
                             })
            url = 'https://booking2.airasia.com/Select.aspx'
            if book_dict.get('triptype', '') == 'RoundTrip' and refin_fare_vlue:
                form_data.update({refield_tab_index: refield_tab_value,
                                  'ControlGroupSelectView$AvailabilityInputSelectView$market2': refin_fare_vlue,
                                  })
                yield FormRequest(url, callback=self.parse_travel, formdata=form_data,
                                  meta={'form_data': form_data, 'book_dict': book_dict}, method="POST")

            elif fin_fare_vlue and book_dict.get('triptype', '') == 'OneWay':
                yield FormRequest(url, callback=self.parse_travel, formdata=form_data,
                                  meta={'form_data': form_data, 'book_dict': book_dict}, method="POST")
            else:
                self.insert_into_db(book_dict, "Could not find flights")
                logging.debug("Couldn't find flights for %s" %
                              book_dict.get('tripid', ''))
		open('%s_flight_not_found' % book_dict.get('tripid', 'garbage'), 'w').write(response.body)
                self.send_mail("Couldn't find flights for %s" %
                               book_dict.get('tripid', ''), json.dumps(book_dict))
        else:
            self.insert_into_db(book_dict, "No flights find in selected class")
            logging.debug("Couldn't find flights for given class  %s" %
                          book_dict.get('tripid', ''))
	    open('%s_flight_not_found' % book_dict.get('tripid', 'garbage'), 'w').write(response.body)
            self.send_mail("Couldn't find flights for %s" %
                           book_dict.get('tripid', ''), json.dumps(book_dict))

    def parse_travel(self, response):
        '''Booking form filling'''
        sel = Selector(response)
        book_dict = response.meta.get('book_dict', {})
        if response.status != 200:
            logging.debug('Internal Server Error')
	    open('%s_travel_page' % book_dict.get('tripid', 'garbage'), 'w').write(response.body)
            self.send_mail('Internal Server Error', json.dumps(book_dict))
            return
        garbage = ''.join(sel.xpath('//title/text()').extract())
        if not garbage:
                self.insert_into_db(book_dict, "Failed due to server busy Garbage")
                open('%s_travel_not_loaded' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
                return
        error_check = normalize(''.join(sel.xpath('//div[@id="errorSectionContent"]//text()').extract()))
        if error_check:
                self.insert_into_db(book_dict, error_check)
                open('%s_travel_error' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
                return
        umeal_key_lst = book_dict.get('onewaymealcode', [])
        dmeal_key_lst = book_dict.get('returnmealcode', [])
        guest_count = book_dict.get('paxdetails', {})
        emergency_contact = book_dict.get('emergencycontact', {})
        guest_ph_number = book_dict.get('phonenumber', '')
        view_state = normalize(''.join(sel.xpath(view_state_path).extract()))
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
        flyerfare = ''.join(
            sel.xpath('//input[@name="HiFlyerFare"]/@value').extract())
        booking_data = ''.join(
            sel.xpath('//input[@name="HiddenFieldPageBookingData"]/@value').extract())
        token_field = ''.join(sel.xpath(
            '//input[@name="CONTROLGROUP_OUTERTRAVELER$CONTROLGROUPTRAVELER$ContactInputTravelerView$CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ContactInputTravelerViewHtmlInputHiddenAntiForgeryTokenField"]/@value').extract())
        add_key = 'CONTROLGROUP_OUTERTRAVELER$CONTROLGROUPTRAVELER$%s'
        baggage_up_name = ''.join(sel.xpath(
            '//ul[@class="add-on-forms "][1]//li[@class="baggageContainer"]//select/@name').extract())
        baggage_up_codes = ''.join(sel.xpath(
            '//ul[@class="add-on-forms "]//li[@class="baggageContainer"]//select/@ssr-data').extract())
        if baggage_up_codes:
            try:
                default_bg_code = baggage_up_codes.split(
                    '|')[0].split(' ')[0].strip()
            except:
                default_bg_code = ''
        else:
            default_bg_code = ''
        oneway_hg_baggage = book_dict.get('onewaybaggagecode', '')
        if oneway_hg_baggage and baggage_up_name:
            oneway_baggage_value = baggage_up_name.split('TravelerView$')[-1]\
                .replace('journey', 'ssrCode_%s_ssrNum' % oneway_hg_baggage)
        # elif default_bg_code: oneway_baggage_value = baggage_up_name.split('TravelerView$')[-1]\
        #		.replace('journey', 'ssrCode_%s_ssrNum'%default_bg_code)
        else:
            oneway_baggage_value = ''
        meal_check_or = '%s%s' % (book_dict.get(
            'origin', ''), book_dict.get('destination', ''))
        up_meal_lst, dw_meal_lst = [], []
        up_meal_code_dict, rt_meal_code_dict = {}, {}
        if umeal_key_lst:
            for m_code in umeal_key_lst:
                # up_meal_keys = sel.xpath('//ul[@class="add-on-forms "][1]//li[@data-ssr-id="%s"]\
                #	//div[@class="ucmealpanel-item-selection"]//input/@name'%m_code).extract()
                up_meal_keys = sel.xpath('//ul[@class="add-on-forms "][1]//li[@data-ssr-id="%s"]\
				/div[@class="ucmealpanel-item-selection"]/div/input/@name' % m_code).extract()
                up_meal_text = sel.xpath('//ul[@class="add-on-forms "][1]//li[@data-ssr-id="%s"]\
				/div[@class="ucmealpanel-item-selection"]/div/input/@ssr-label' % m_code).extract()
                if up_meal_text:
                    up_meal_text = up_meal_text[0]
                else:
                    up_meal_text = ''
                up_meal_code_dict.update({m_code: up_meal_text})
                for i in up_meal_keys:
                    if meal_check_or in i:
                        if i:
                            up_meal_lst.append((i, 1))
                            break
        baggage_down_name = ''.join(sel.xpath(
            '//ul[@class="add-on-forms "][2]//li[@class="baggageContainer"]//select/@name').extract())
        baggage_down_codes = ''.join(sel.xpath(
            '//ul[@class="add-on-forms "]//li[@class="baggageContainer"]//select/@ssr-data').extract())
        if baggage_down_codes:
            try:
                def_bg_code = baggage_down_codes.split(
                    '|')[0].split(' ')[0].strip()
            except:
                def_bg_code = ''
        else:
            def_bg_code = ''
        return_hg_baggage = book_dict.get('returnbaggagecode', '')
        if return_hg_baggage and baggage_down_name:
            return_baggage_value = baggage_down_name.split('TravelerView$')[-1]\
                .replace('journey', 'ssrCode_%s_ssrNum' % return_hg_baggage)
        # elif def_bg_code: return_baggage_value = baggage_down_name.split('TravelerView$')[-1]\
        #				.replace('journey', 'ssrCode_%s_ssrNum'%def_bg_code)
        else:
            return_baggage_value = ''
        dm_meal_check_or = '%s%s' % (book_dict.get(
            'destination', ''), book_dict.get('origin', ''))
        if dmeal_key_lst:
            for d_code in dmeal_key_lst:
                down_meal_keys = sel.xpath(
                    '//ul[@class="add-on-forms "][1]//li[@data-ssr-id="%s"]/div[@class="ucmealpanel-item-selection"]/div/input/@name' % d_code).extract()
                meal_text = sel.xpath(
                    '//ul[@class="add-on-forms "][1]//li[@data-ssr-id="%s"]/div[@class="ucmealpanel-item-selection"]/div/input/@ssr-label' % d_code).extract()
                if meal_text:
                    meal_text = meal_text[0]
                else:
                    meal_text = ''
                rt_meal_code_dict.update({d_code: meal_text})
                for j in down_meal_keys:
                    if dm_meal_check_or in j:
                        if j:
                            dw_meal_lst.append((j, 1))
                            break
        data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': view_state,
            'pageToken': '',
            'MemberLoginTravelerView2$TextBoxUserID': '',
            'hdRememberMeEmail': '',
            'MemberLoginTravelerView2$PasswordFieldPassword': '',
            'memberLogin_chk_RememberMe': 'on',
            'HiFlyerFare': flyerfare,
            'isAutoSeats': 'false',
            'CONTROLGROUP_OUTERTRAVELER$CONTROLGROUPTRAVELER$ContactInputTravelerView$CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ContactInputTravelerViewHtmlInputHiddenAntiForgeryTokenField': token_field,
            add_key % 'ContactInputTravelerView$HiddenSelectedCurrencyCode': 'INR',
            add_key % 'ContactInputTravelerView$DropDownListTitle': 'MS',
            add_key % 'ContactInputTravelerView$TextBoxFirstName': 'Preeti',
            add_key % 'ContactInputTravelerView$TextBoxLastName': 'Yadav',
            add_key % 'ContactInputTravelerView$TextBoxWorkPhone': '022 4055 4000',
            add_key % 'ContactInputTravelerView$TextBoxFax': '',
            add_key % 'ContactInputTravelerView$TextBoxEmailAddress': book_dict.get('email', ''),
            add_key % 'ContactInputTravelerView$DropDownListHomePhoneIDC': '91',
            add_key % 'ContactInputTravelerView$TextBoxHomePhone': guest_ph_number,
            add_key % 'ContactInputTravelerView$DropDownListOtherPhoneIDC': '91',
            add_key % 'ContactInputTravelerView$TextBoxOtherPhone': guest_ph_number,
            add_key % 'ContactInputTravelerView$EmergencyTextBoxGivenName': emergency_contact.get('firstname', ''),
            add_key % 'ContactInputTravelerView$EmergencyTextBoxSurname': emergency_contact.get('lastname', ''),
            add_key % 'ContactInputTravelerView$DropDownListMobileNo': emergency_contact.get('mobilephcode', ''),
            add_key % 'ContactInputTravelerView$EmergencyTextBoxMobileNo': emergency_contact.get('mobilenumber', ''),
            add_key % 'ContactInputTravelerView$DropDownListRelationship': 'other',
            add_key % 'ContactInputTravelerView$DropDownListSelectedGSTState': '',
            add_key % 'ContactInputTravelerView$GSTTextBoxCompanyName': '',
            add_key % 'ContactInputTravelerView$GSTTextBoxCompanyStreet': '',
            add_key % 'ContactInputTravelerView$GSTTextBoxCompanyPostalCode': '',
            add_key % 'ContactInputTravelerView$DropDownListGSTCountry': 'IN',
            add_key % 'ContactInputTravelerView$DropDownListGSTState': 'AN',
            add_key % 'ContactInputTravelerView$GSTTextboxRegistrationNumber': '',
            add_key % 'ContactInputTravelerView$GSTTextboxCompanyEmail': '',

            'drinkcountname': '0',
            'drinkcountname': '0',
            'checkBoxInsuranceName': 'InsuranceInputControlAddOnsViewAjax$CheckBoxInsuranceAccept',
            'checkBoxInsuranceId': 'CONTROLGROUP_InsuranceInputControlAddOnsViewAjax_CheckBoxInsuranceAccept',
            'checkBoxAUSNoInsuranceId': 'InsuranceInputControlAddOnsViewAjax_CheckBoxAUSNo',
            'declineInsuranceLinkButtonId': 'InsuranceInputControlAddOnsViewAjax_LinkButtonInsuranceDecline',
            'iniiiisuranceLinkCancelId': 'InsuranceInputControlAddOnsViewAjax_LinkButtonInsuranceDecline',
            'radioButtonNoInsuranceId': 'InsuranceInputControlAddOnsViewAjax_RadioButtonNoInsurance',
            'radioButtonYesInsuranceId': 'InsuranceInputControlAddOnsViewAjax_RadioButtonYesInsurance',
            'radioButton': 'on',
            'HiddenFieldPageBookingData': booking_data,
            '__VIEWSTATEGENERATOR': gen,
            'CONTROLGROUP_OUTERTRAVELER$CONTROLGROUPTRAVELER$ButtonSubmit': 'Continue',
        }
        guestdetails = book_dict.get('guestdetails', [])
        guestdetails.extend(book_dict.get('childdetails', []))
        for idx, details in enumerate(guestdetails):
            birth_date = details.get('dob', '')
            bo_day, bo_month, bo_year = ['']*3
            if birth_date:
                birth_date = datetime.datetime.strptime(birth_date, '%Y-%m-%d')
                bo_day, bo_month, bo_year = birth_date.day, birth_date.month, birth_date.year
            gender = details.get('gender', '')
            if gender == 'Male' or gender == 'M':
                gender_val = 1
            else:
                gender_val = 2
            if details:
                data.update({
                    add_key % 'PassengerInputTravelerView$DropDownListTitle_%s' % idx: details.get('title', '').upper(),
                    add_key % 'PassengerInputTravelerView$DropDownListGender_%s' % idx: str(gender_val),
                    add_key % 'PassengerInputTravelerView$TextBoxFirstName_%s' % idx: details.get('firstname', ''),
                    add_key % 'PassengerInputTravelerView$TextBoxLastName_%s' % idx: details.get('lastname', ''),
                    add_key % 'PassengerInputTravelerView$DropDownListNationality_%s' % idx: book_dict.get('countrycode', ''),
                    add_key % 'PassengerInputTravelerView$DropDownListBirthDateDay_%s' % idx: str(bo_day),
                    add_key % 'PassengerInputTravelerView$DropDownListBirthDateMonth_%s' % idx: str(bo_month),
                    add_key % 'PassengerInputTravelerView$DropDownListBirthDateYear_%s' % idx: str(bo_year),
                    add_key % 'PassengerInputTravelerView$TextBoxCustomerNumber_%s' % idx: '',
                })

        infants = book_dict.get('infant', [])
        for idf, inf in enumerate(infants):
            birth_date = inf.get('dob', '')
            bo_day, bo_month, bo_year = ['']*3
            if birth_date:
                birth_date = datetime.datetime.strptime(birth_date, '%Y-%m-%d')
                bo_day, bo_month, bo_year = birth_date.day, birth_date.month, birth_date.year
            gender = inf.get('gender', '')
            if gender == 'Male' or gender == 'M':
                gender_val = 1
            else:
                gender_val = 2
            data.update({
                add_key % 'PassengerInputTravelerView$DropDownListAssign_0_0': '0',
                add_key % 'PassengerInputTravelerView$DropDownListGender_0_%s' % idf: str(gender),
                add_key % 'PassengerInputTravelerView$TextBoxFirstName_0_%s' % idf: inf.get('firstname', ''),
                add_key % 'PassengerInputTravelerView$TextBoxLastName_0_%s' % idf: inf.get('lastname', ''),
                add_key % 'PassengerInputTravelerView$DropDownListNationality_0_%s' % idf: inf.get('countrycode', ''),
                add_key % 'PassengerInputTravelerView$DropDownListBirthDateDay_0_%s' % idf: str(bo_day),
                add_key % 'PassengerInputTravelerView$DropDownListBirthDateMonth_0_%s' % idf: str(bo_month),
                add_key % 'PassengerInputTravelerView$DropDownListBirthDateYear_0_%s' % idf: str(bo_year),
            })
        if oneway_baggage_value:
            data.update({baggage_up_name: oneway_baggage_value})
        if return_baggage_value:
            data.update({baggage_down_name: return_baggage_value})
        if up_meal_lst:
            for i in up_meal_lst:
                key, val = i
                data.update({key: str(val)})
        if dw_meal_lst:
            for i in dw_meal_lst:
                key, val = i
                data.update({key: str(val)})
        len_meal = len(umeal_key_lst)
        data.update({"drinkcountname": str(len_meal)})
        for idx, m_code in enumerate(umeal_key_lst):
            data.update(
                {'ctl00$BodyContent$ucTravelerForm1_form$addOnsPanel1$mealPanel2$SelectedMeal_%s' % idx: m_code})
        for idx, m_code in enumerate(dmeal_key_lst):
            data.update(
                {'ctl00$BodyContent$ucTravelerForm1_form$addOnsPanel1$mealPanel2$SelectedMeal_%s' % idx: m_code})
        travel_url = 'https://booking2.airasia.com/Traveler.aspx'
        book_dict.update({'oneway_meal_dict': up_meal_code_dict,
                          'return_meal_dict': rt_meal_code_dict})
        yield FormRequest(travel_url, callback=self.parse_form, formdata=data, meta={'book_dict': book_dict}, dont_filter=True)

    def parse_form(self, response):
        '''parsing seat selection page'''
        book_dict = response.meta.get('book_dict', {})
        if response.status != 200:
            logging.debug('Internal Server Error')
	    open('%s_travel' % book_dict.get('tripid', 'Check the booking dict'), 'w').write(response.body)
            self.send_mail('Internal Server Error', json.dumps(book_dict))
            return
        sel = Selector(response)
        tolerance_value = 0
        ct_price = book_dict.get('ctprice', '0')
        total_fare = ''.join(sel.xpath(
            '//div[@class="total-amount-bg-last"]//span[@id="overallTotal"]//text()').extract())
        try:
            total_fare = float(total_fare.replace(',', '').strip())
        except:
            total_fare = 0
        garbage = ''.join(sel.xpath('//title/text()').extract())
        if not garbage:
                self.insert_into_db(book_dict, "Failed due to server busy Garbage")
                open('%s_form_not_loaded' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
                return
        error_check = normalize(''.join(sel.xpath('//div[@id="errorSectionContent"]//text()').extract()))
        if error_check:
                self.insert_into_db(book_dict, error_check)
                open('%s_form_error' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
                return
        if total_fare != 0:
            tolerance_value = total_fare - float(ct_price)
            if float(tolerance_value) >= float(self.tolerance_amount):
                is_proceed = 0  # movie it to off line
            else:
                is_proceed = 1
        else:
	    open('%s_I5_fare_notloaded' % book_dict.get('tripid', 'Check the booking dict'), 'w').write(response.body)
	    self.insert_into_db(book_dict, "Fare response not loaded")
            tolerance_value, is_proceed = 0, 0
	    return
        book_dict.update({'tolerance_value': tolerance_value})
        book_dict.update({'airasia_price': total_fare})
        view_state = normalize(''.join(sel.xpath(view_state_path).extract()))
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
        booking_data = ''.join(
            sel.xpath('//input[@name="HiddenFieldPageBookingData"]/@value').extract())
        data = [
            ('__EVENTTARGET', ''),
            ('__EVENTARGUMENT', ''),
            ('__VIEWSTATE', view_state),
            ('pageToken', ''),
            ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$DriverAgeTextBox',
             'Please enter your age'),
            ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedCarPosition', ''),
            ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedCarModel', ''),
            ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedCarPrice', ''),
            ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedCarTotalPrice', ''),
            ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedCarDateTime', ''),
            ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedReferenceType', ''),
            ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedReferenceID', ''),
            ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedReferenceIDContext', ''),
            ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedReferenceDateTime', ''),
            ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedReferenceUrl', ''),
            ('HiddenFieldPageBookingData', booking_data),
            ('__VIEWSTATEGENERATOR', gen),
            ('CONTROLGROUPADDONSFLIGHTVIEW$ButtonSubmit', 'Continue'),
        ]
        travel_url = 'https://booking2.airasia.com/AddOns.aspx'
        if is_proceed == 1:
            book_dict.update({'tolerance_value': tolerance_value})
            yield FormRequest(travel_url, callback=self.parse_seat, dont_filter=True, formdata=data, meta={'book_dict': book_dict})
        else:
	    book_dict.update({'tolerance_value': tolerance_value})
	    open('%s_I5_fare_increased' % book_dict.get('tripid', 'Check the booking dict'), 'w').write(response.body)
            self.insert_into_db(book_dict, "Fare increased by Airline")
            self.send_mail('Fare increased by AirAsia', json.dumps(book_dict))

    def parse_seat(self, response):
        '''
        collecting payment details and submit payment
        '''
        sel = Selector(response)
        book_dict = response.meta.get('book_dict', {})
        if response.status != 200:
            logging.debug('Internal Server Error')
	    open('%s_select_seat' % book_dict.get('tripid', 'Check the booking dict'), 'w').write(response.body)
            self.send_mail('Internal Server Error', json.dumps(book_dict))
            return
        garbage = ''.join(sel.xpath('//title/text()').extract())
        if not garbage:
                self.insert_into_db(book_dict, "Failed due to server busy Garbage")
                open('%s_seat_not_loaded' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
                return
        error_check = normalize(''.join(sel.xpath('//div[@id="errorSectionContent"]//text()').extract()))
        if error_check:
                self.insert_into_db(book_dict, error_check)
                open('%s_seat_error' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
                return
        view_state = normalize(''.join(sel.xpath(view_state_path).extract()))
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
        bookingdata = ''.join(
            sel.xpath('//input[@id="HiddenFieldPageBookingDataId"]/@value').extract())
        data = [
            ('__EVENTTARGET',
             'ControlGroupUnitMapView$UnitMapViewControl$LinkButtonAssignUnit'),
            ('__EVENTARGUMENT', ''),
            ('__VIEWSTATE', str(view_state)),
            ('pageToken', ''),
            ('ControlGroupUnitMapView$UnitMapViewControl$compartmentDesignatorInput', ''),
            ('ControlGroupUnitMapView$UnitMapViewControl$deckDesignatorInput', '1'),
            ('ControlGroupUnitMapView$UnitMapViewControl$tripInput', '0'),
            ('ControlGroupUnitMapView$UnitMapViewControl$passengerInput', '0'),
            ('ControlGroupUnitMapView$UnitMapViewControl$HiddenEquipmentConfiguration_0_PassengerNumber_0', ''),
            ('ControlGroupUnitMapView$UnitMapViewControl$EquipmentConfiguration_0_PassengerNumber_0', ''),
            ('ControlGroupUnitMapView$UnitMapViewControl$EquipmentConfiguration_0_PassengerNumber_0_HiddenFee', 'NaN'),
            ('HiddenFieldPageBookingData', str(bookingdata)),
            ('__VIEWSTATEGENERATOR', str(gen)),
        ]
        url = 'https://booking2.airasia.com/UnitMap.aspx'
        cookie = ''.join(re.findall("i10c.bdddb=(.*)'\)", response.body))
        cookies = {'i10c.bdddb': cookie}
        # Navigating to Patment Process
        yield FormRequest(url, callback=self.parse_unitmap, formdata=data, cookies=cookies, meta={'book_dict': book_dict, 'v_state': view_state, 'gen': gen})

    def parse_unitmap(self, response):
        '''
        Parsing to Agency Account for payment
        '''
        sel = Selector(response)
        book_dict = response.meta['book_dict']

        error_check = normalize(''.join(sel.xpath('//div[@id="errorSectionContent"]//text()').extract()))
        if error_check:
                self.insert_into_db(book_dict, error_check)
                open('%s_unitmap_error' % book_dict.get('tripid', 'booking_dict'), 'w').write(response.body)
                return
        amount = ''.join(sel.xpath(
            '//div[@class="totalAmtText"]//following-sibling::div[1]/text()').extract())
        amount = ''.join(re.findall('\d+,?\d+', amount))
        booking_data = ''.join(
            sel.xpath('//input[@name="HiddenFieldPageBookingData"]/@value').extract())
        view_state = normalize(''.join(sel.xpath(view_state_path).extract()))
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
        data = [
            ('__EVENTTARGET', 'CONTROLGROUPPAYMENTBOTTOM$PaymentInputViewPaymentView'),
            ('__EVENTARGUMENT', 'AgencyAccount'),
            ('__VIEWSTATE', agency_viewstate),
            ('pageToken', ''),
            ('eventTarget', ''),
            ('eventArgument', ''),
            ('viewState', agency_viewstate),
            ('pageToken', ''),
            ('PriceDisplayPaymentView$CheckBoxTermAndConditionConfirm', 'on'),
            ('CONTROLGROUPPAYMENTBOTTOM$MultiCurrencyConversionViewPaymentView$DropDownListCurrency', 'default'),
            ('MCCOriginCountry', 'IN'),
            ('CONTROLGROUPPAYMENTBOTTOM$PaymentInputViewPaymentView$HiddenFieldUpdatedMCC', ''),
            ('HiddenFieldPageBookingData', str(booking_data)),
            ('__VIEWSTATEGENERATOR', str(gen)),
        ]
        url = 'https://booking2.airasia.com/Payment.aspx'
        # Navigating to Agency Account
        if not 'Payment' in response.url:
	    open('%s_I5_payment' % book_dict.get('tripid', 'Check the booking dict'), 'w').write(response.body)
            self.insert_into_db(book_dict, "Payment Failed")
            self.send_mail('Payment Failed', json.dumps(book_dict))
        else:
            yield FormRequest(url, callback=self.parse_agency, formdata=data, dont_filter=True,  meta={'book_dict': response.meta['book_dict'],
                                                                                                       'booking_data': booking_data, 'gen': gen, 'amount': amount})

    def parse_agency(self, response):
        '''
        collecting payment details and submit payment
        '''
        sel = Selector(response)
        book_dict = response.meta['book_dict']
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
        if not booking_data:
            booking_data = response.meta['booking_data']
        amount = ''.join(sel.xpath(
            '//input[@id="CONTROLGROUPPAYMENTBOTTOM_PaymentInputViewPaymentView_AgencyAccount_AG_AMOUNT"]/@value').extract())
        print amount
        book_dict.update({'price_details': json.dumps(fin_tax)})
        if int(self.proceed_to_book) == 1:
            view_state = sel.xpath('//input[@id="viewState"]/@value').extract()
            if view_state:
                view_state = view_state[0]
            else:
                view_state = ''
            gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
            data = {
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                '__VIEWSTATE': view_state,
                'pageToken': '',
                'pageToken': '',
                'eventTarget': '',
                'eventArgument': '',
                'viewState': view_state,
                'PriceDisplayPaymentView$CheckBoxTermAndConditionConfirm': 'on',
                'MCCOriginCountry': 'IN',
                'CONTROLGROUPPAYMENTBOTTOM$PaymentInputViewPaymentView$AgencyAccount_AG_AMOUNT': amount,
                'HiddenFieldPageBookingData': booking_data,
                '__VIEWSTATEGENERATOR': gen,
                'CONTROLGROUPPAYMENTBOTTOM$ButtonSubmit': 'Submit payment',
            }
            url = 'https://booking2.airasia.com/Payment.aspx'
            # Submit Payment
            if amount:
                book_dict.update({'status_message': 'Unknown'})
                #self.insert_into_db(book_dict, 'Payment failed whereas payment is successful')
                yield FormRequest(url, callback=self.parse_itinerary, formdata=data, dont_filter=True,
                                  meta={'book_dict': response.meta['book_dict'], 'tax_dict': fin_tax})
            else:
		open('%s_I5_payment' % book_dict.get('tripid', 'Check the booking dict'), 'w').write(response.body)
                self.insert_into_db(book_dict, 'Payment Failed')
                self.send_mail('Payment Failed', json.dumps(book_dict))
        else:
            # testing report generation
            flt_no = book_dict.get('ow_flt', '').replace('<>', ' ').strip()
            rt_flt_no = book_dict.get('rt_flt', '').replace('<>', ' ').strip()
            flt = [flt_no, rt_flt_no]
            pnr_no, conform, pax_details = '100', 'Mock is Successful', ''
            book_dict['pnr'] = pnr_no
            trip_type_ = '%s_%s_%s' % (book_dict.get(
                'triptype', ''), self.queue, self.book_using)
            self.insert_into_db(book_dict, 'Mock is Successful')

    def parse_itinerary(self, response):
        '''
        parsing itinerary form response
        '''
        sel = Selector(response)
        time.sleep(20)
        time.sleep(25)
        yield FormRequest.from_response(response, callback=self.parse_fin_details, dont_filter=True,
                                        meta={'book_dict': response.meta['book_dict'], 'tax_dict': response.meta['tax_dict']})

    def parse_fin_details(self, response):
        '''
        collecting the final booking detais
        '''
        sel = Selector(response)
        book_dict = response.meta['book_dict']
        try:
            open('I5_%s.html' % book_dict.get(
                'tripid'), 'w').write(response.body)
        except:
            logging.debug('Issue in capture')
        tax_dict = response.meta['tax_dict']
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
        book_dict.update({'price_details': json.dumps(tax_dict)})
        book_dict.update({'status_message': confirm})
        book_dict.update({'airasia_price': paid_amount})
        book_dict.update({'pnr': pnr_no})
        try:
            logging.debug('Values: %s' % book_dict)
        except:
            pass
        if pnr_no:
            self.insert_into_db(book_dict, '')
        else:
            book_dict.update({'status_message': 'Unknown'})
            self.insert_into_db(
                book_dict, 'Payment failed whereas payment is successful')

    def get_input_segments(self, segments):
        '''
        returing segments
        '''
        all_segments = segments.get('all_segments', [])
        ow_flight_dict, rt_flight_dict = {}, {}
        dest = segments.get('destination_code', '').strip()
        origin = segments.get('origin_code', '').strip()
        from_to = '%s-%s' % (origin, dest)
        if len(all_segments) == 1:
            key = ''.join(all_segments[0].keys())
            ow_flight_dict = all_segments[0][key]
            self.ow_fullinput_dict = ow_flight_dict
            if ow_flight_dict:
                try:
                    self.ow_input_flight = ow_flight_dict.get('segments', [])
                except:
                    self.ow_input_flight = {}
            else:
                self.ow_input_flight = {}
        elif len(all_segments) == 2:
            key1, key2 = ''.join(all_segments[0].keys()), ''.join(
                all_segments[1].keys())
            flight_dict1, flight_dict2 = all_segments[0][key1], all_segments[1][key2]
            f_to = flight_dict1.get('segments', [])
            self.ow_input_flight = flight_dict1.get('segments', [])
            self.rt_input_flight = flight_dict2.get('segments', [])
            self.ow_fullinput_dict, self.rt_fullinput_dict = flight_dict2, flight_dict1
        else:
            self.insert_into_db(segments, "Multi-city booking")
