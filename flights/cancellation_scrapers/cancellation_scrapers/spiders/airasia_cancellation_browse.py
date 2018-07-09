import ast
import re
import json
import md5
import random
import time
import smtplib
import datetime
import smtplib
import ssl
from email import encoders
from ast import literal_eval
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from ConfigParser import SafeConfigParser
from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
import MySQLdb
from airasia_cancel_xpaths import *
from cancellation_scrapers.utils import *
from scrapy.conf import settings

import sys
sys.path.append(settings['ROOT_PATH'])
from airasia_login_cookie import *

_cfg = SafeConfigParser()
#_cfg.read('airline_names.cfg')
_cfg.read(settings['BOOK_PCC_PATH'])
counter = 0


class AirAsiaBrowse(Spider):
    name = "airasia_browse"
    start_urls = ["https://booking2.airasia.com/AgentHome.aspx"]
    handle_httpstatus_list = [403]

    def __init__(self, *args, **kwargs):
        super(AirAsiaBrowse, self).__init__(*args, **kwargs)
        self.source_name = 'airasia'
        self.log = create_logger_obj('airasia_cancellation')
        self.cancellation_dict = kwargs.get('jsons', {})
        self.multiple_pcc = False
        self.logout_view_state = ''
        self.logout_cookies = {}
	self.garbage_retry = 0
        print self.cancellation_dict
        self.insert_query = 'insert into airasia_cancellation_report (sk, airline, cancellation_message, cancellation_status, destination, flight_id, manual_refund_queue, arrival_time, origin, pax_name, payment_status, cancellation_status_mesg, past_dated_booking, refund_computation_queue, tripid, error, created_at, modified_at) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), sk=%s, airline=%s, cancellation_message=%s, cancellation_status=%s, destination=%s, flight_id=%s, manual_refund_queue=%s, arrival_time=%s, origin=%s, pax_name=%s, payment_status=%s, cancellation_status_mesg=%s, past_dated_booking=%s, refund_computation_queue=%s, tripid=%s, error=%s'
        self.update_status_query = 'update cancellation_report set cancellation_status_mesg=%s, payment_status=%s where sk=%s and tripid=%s'
        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('cancel', 'IP')
        passwd = db_cfg.get('cancel', 'PASSWD')
        user = db_cfg.get('cancel', 'USER')
        db_name = db_cfg.get('cancel', 'DBNAME')
        self.conn = MySQLdb.connect(
            host=host, user=user, passwd=passwd, db=db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()
        headers = {
            'pragma': 'no-cache',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-GB,en-US;q=0.8,en;q=0.6',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'cache-control': 'no-cache',
            'authority': 'booking2.airasia.com',
        }
        import requests
        data = [
            ('__EVENTTARGET', 'MemberLoginAgentHomeView$LinkButtonLogOut'),
            ('__EVENTARGUMENT', ''),
            ('__VIEWSTATE', self.logout_view_state),
            ('pageToken', ''),
            ('__VIEWSTATEGENERATOR', '05F9A2B0'),
        ]
        response = requests.post('https://booking2.airasia.com/AgentHome.aspx',
                                 headers=headers, cookies=self.logout_cookies, data=data)

    def insert_report_into_db(self, cnl_dict, error_msg):
        sk = cnl_dict.get('pnr', '')
        if not sk:
            try:
                sk = cnl_dict.get('details', [{}])[0].get('pnr', '')
            except:
                sk = ''
        airline = 'AirAsia'
        cancellation_message = cnl_dict.get('cancellation_message', '')
        cancellation_status = cnl_dict.get('cancellation_status', '')
        destination = cnl_dict.get('destination', '')
        flight_id = cnl_dict.get('flight_id', '')
        manual_refund_queue = cnl_dict.get('manual_refund_queue', '')
        origin = cnl_dict.get('origin', '')
        pax_name = cnl_dict.get('pax_name', '')
	pax_name = '%s#<>#retry_count:%s'%(pax_name, str(self.garbage_retry))
        payment_status = cnl_dict.get('payment_status', '')
        cancellation_status_mesg = cnl_dict.get('cancellation_status_mesg', '')
        past_dated_booking = cnl_dict.get('past_dated_booking', '')
        refund_computation_queue = cnl_dict.get('refund_computation_queue', '')
        tripid = cnl_dict.get('tripid', '')
        if not tripid:
            tripid = cnl_dict.get('trip_ref', '')
        error = error_msg
        arrival_time = ''
        insert_vals = (sk, airline, cancellation_message, cancellation_status, destination,
                       flight_id, manual_refund_queue, arrival_time, origin, pax_name, payment_status,
                       cancellation_status_mesg, past_dated_booking, refund_computation_queue, tripid, error,
                       sk, airline, cancellation_message, cancellation_status, destination, flight_id,
                       manual_refund_queue, arrival_time, origin, pax_name, payment_status,
                       cancellation_status_mesg, past_dated_booking, refund_computation_queue, tripid, error,)
        self.cur.execute(self.insert_query, insert_vals)
        self.conn.commit()

    def process_input(self, request):
        trip_id = request.get('trip_ref', '')
        details = request.get('details', [])
        proceed_to_cancel = request.get('proceed_to_cancel', '1')
        processed_dict = {}
        try:
            oneway_trip = details[0]
        except:
            oneway_trip = {}
            return
        pnr = oneway_trip.get('pnr', '')
        cnl_pax_lst = oneway_trip.get('cancelled_pax_details', [])
        all_pax_lst = oneway_trip.get('all_pax_details', [])
        cnl_type = oneway_trip.get('cancellation_type', {}).get('type', '')
        all_segment_details = oneway_trip.get('all_segment_details', [])
        cancelled_segment_details = oneway_trip.get(
            'cancelled_segment_details', [])
        ln_cnl_seg = len(cancelled_segment_details)
        origin = cancelled_segment_details[0].get('segment_src', '')
        departure_date = cancelled_segment_details[0].get('departure_date', '')
        departure_time = cancelled_segment_details[0].get('departure_time', '')
        desctnation = cancelled_segment_details[ln_cnl_seg -
                                                1].get('segment_dest', '')
        flt_ids, cancelled_seg, all_seg, rt_flt_id = [], [], [], []
        oneway_cnl_sectors, oneway_full_sectors = [], []
        return_cnl_sectors, return_full_sectors = [], []
        trip_type = 'oneway'
        for i in cancelled_segment_details:
            flight_no = i.get('flight_no', '')
            seq_no = i.get('seq_no', '')
            segment_src = i.get('segment_src', '')
            segment_dest = i.get('segment_dest', '')
            flt_ids.append(flight_no)
            cancelled_seg.append(segment_src)
            cancelled_seg.append(segment_dest)
            if seq_no == '1':
                oneway_cnl_sectors.append(i)
            elif seq_no == '2':
                return_cnl_sectors.append(i)
        for j in all_segment_details:
            seq_no = j.get('seq_no', '')
            segment_src = j.get('segment_src', '')
            segment_dest = j.get('segment_dest', '')
            if seq_no == '2':
                trip_type = "roundtrip"
            all_seg.append(segment_src)
            all_seg.append(segment_dest)
            if seq_no == '1':
                oneway_full_sectors.append(j)
            elif seq_no == '2':
                return_full_sectors.append(j)
        ln_cnl_ow = len(oneway_full_sectors)
        ow_origin = oneway_full_sectors[0].get('segment_src', '')
        ow_desctnation = oneway_full_sectors[ln_cnl_ow -
                                             1].get('segment_dest', '')
        processed_dict = {"origin": ow_origin, "flightid": '<>'.join(flt_ids),
                          "oneway_cancellationdetails": cnl_pax_lst, "pnr": pnr,
                          "tripid": trip_id, "cancellationdatetime": datetime.datetime.now(),
                          "oneway_paxdetails": all_pax_lst, "destination": ow_desctnation,
                          "contactdetails": {"MobilePhone": "", "Email": ""},
                          "airline": "Air Asia", "paxtype": "", "cancelled_seg": cancelled_seg,
                          "departuredatetime": '%s %s' % (departure_date, departure_time),
                          "trip_type": trip_type, "via": "", "cnl_type": cnl_type,
                          "oneway_cnl_sectors": oneway_cnl_sectors, "oneway_full_sectors": oneway_full_sectors,
                          "return_cnl_sectors": return_cnl_sectors, "return_full_sectors": return_full_sectors,
                          "proceed_to_cancel": proceed_to_cancel,
                          }
        return processed_dict

    def get_pcc_name(self):
        pcc_name = ''
        data = self.cancellation_dict
        data_ = ast.literal_eval(data)
        data = data_['details']
        if len(data) == 1:
            pcc_name = 'airasia_%s' % data[0]['pcc']
        elif len(data) == 2:
            if data[0]['pcc'] != data[1]['pcc']:
                self.multiple_pcc = True
            else:
                pcc_name = 'airasia_%s' % data[0]['pcc']
        return data_, pcc_name

    def check_multi_pnr(self, request):
        pnr_list = []
        trip_id = request.get('trip_ref', '')
        details = request.get('details', [])
        if len(details) > 1:
            try:
                pnr_list.append(details[0].get('pnr', ''))
                pnr_list.append(details[1].get('pnr', ''))
            except:
                pnr_list = []
        else:
            pnr_list = []
        return pnr_list

    def parse(self, response):
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
        cancel_dict, self.pcc_name = self.get_pcc_name()
        if cancel_dict.get('pcc', '') == 'coupon':
            self.pcc_name = 'airasia_coupon_default'
        if self.multiple_pcc:
            logging.debug('Multiple PCC cancellation')
            self.insert_report_into_db(
                cancel_dict, 'Multiple PCC cancellation')
            self.send_mail("Multiple PCC cancellation", self.cancellation_dict)
            return
        try:
            multi_pnr = self.check_multi_pnr(eval(self.cancellation_dict))
        except:
            multi_pnr = []
        try: logging.debug(response.request.cookies)
        except: pass
        cookie = random.choice(airasia_login_cookie_list)
        cookies = {'i10c.bdddb': cookie}
        time.sleep(5)
        print cookies
        try: logging.debug(cookies)
        except: pass
        if multi_pnr:
            cancel_dict.update({'pnr': '<>'.join(multi_pnr)})
            self.insert_report_into_db(
                cancel_dict, 'Multiple PNRs not Acceptable')
            return
        try:
            user_name = _cfg.get(self.pcc_name, 'username')
            user_psswd = _cfg.get(self.pcc_name, 'password')
            logging.debug('Booking using : %s - %s' %
                          (self.pcc_name, user_name))
            #login_data_list.append(('ControlGroupLoginAgentView$AgentLoginView$TextBoxUserID', str(user_name)))
            #login_data_list.append(('ControlGroupLoginAgentView$AgentLoginView$PasswordFieldPassword', str(user_psswd)))
            login_data = [
                ('__EVENTTARGET',
                 'ControlGroupLoginAgentView$AgentLoginView$LinkButtonLogIn'),
                ('__EVENTARGUMENT', ''),
                ('__VIEWSTATE', '/wEPDwUBMGRktapVDbdzjtpmxtfJuRZPDMU9XYk='),
                ('pageToken', ''),
                ('ControlGroupLoginAgentView$AgentLoginView$TextBoxUserID', str(
                    user_name)),
                ('ControlGroupLoginAgentView$AgentLoginView$PasswordFieldPassword', str(
                    user_psswd)),
                ('ControlGroupLoginAgentView$AgentLoginView$HFTimeZone', '330'),
                ('__VIEWSTATEGENERATOR', '05F9A2B0'),
            ]

            return FormRequest('https://booking2.airasia.com/LoginAgent.aspx',
                               formdata=login_data, callback=self.parse_next, cookies=cookies, dont_filter=True)
        except:
            logging.debug('PCC not avaialble for scrapper')
            self.insert_report_into_db(
                cancel_dict, 'PCC not avaialble for scrapper')
            self.send_mail(
                "PCC not avaialble for AirAsia cancellation scrapper", self.cancellation_dict)
            return

    def parse_next(self, response):
        sel = Selector(response)
        manage_booking = sel.xpath('//a[@id="MyBookings"]/@href').extract()
        try:
            cnl_dict_ = eval(self.cancellation_dict)
        except:
            try:
                cnl_dict_ = json.loads(self.cancellation_dict)
            except:
                cnl_dict_ = {}
        if response.status == 403:
            self.insert_report_into_db(cnl_dict_, 'Login page got 403 status')
            self.send_mail('403 status', 'Login page got 403 status')
            return
        login_failed = ''.join(sel.xpath('//div[@id="errorSectionContent"]//text()').extract())
	if 'user/agent ID you entered is not valid' in login_failed:
                self.insert_report_into_db(cnl_dict_, 'Scraper unable to login AirAsia')
                open('%s_login_failed' %  cnl_dict_.get('trip_ref', 'Check the cancel dict'), 'w').write(response.body)
                logging.debug('Login Failed %s, %s, %s' % (response.status, manage_booking, response.url))
                self.send_mail("Login Failed", "Cancellation scraper failed to login AirAsia %s" % cnl_dict_.get('trip_ref', 'check the cancel dict'))
                return
        if 'error404busy' in response.url.lower():
                self.insert_report_into_db(cnl_dict_, "Cancel Scraper unable to login due to server busy")
                open('%s_login_failed' % cnl_dict_.get('trip_ref', 'Check the cancel dict'), 'w').write(response.body)
                logging.debug('Cancle Scraper unable to login due to server busy %s'%cnl_dict_.get('trip_ref', ''))
                return
	if 'err504.html' in response.url.lower():
                self.insert_report_into_db(cnl_dict_, "Cancel Scraper unable to login due to server busy")
                open('%s_login_failed' % cnl_dict_.get('trip_ref', 'Check the cancel dict'), 'w').write(response.body)
                logging.debug('Cancle Scraper unable to login due to server busy %s'%cnl_dict_.get('trip_ref', ''))
                return
	if 'err502.html' in response.url.lower():
                self.insert_report_into_db(cnl_dict_, "Cancel Scraper unable to login due to server busy")
                open('%s_login_failed' % cnl_dict_.get('trip_ref', 'Check the cancel dict'), 'w').write(response.body)
                logging.debug('Cancle Scraper unable to login due to server busy %s'%cnl_dict_.get('trip_ref', ''))
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
			logging.debug('************Retry for Garbage response %s********'%cnl_dict_.get('trip_ref', ''))
			headers = {
				'Connection': 'keep-alive',
				'Pragma': 'no-cache',
				'Cache-Control': 'no-cache',
				'Upgrade-Insecure-Requests': '1',
				'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
				'Accept-Encoding': 'gzip, deflate, br',
				'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
				}
			settings.overrides['HTTP_PROXY'] = ''#'http://%s@%s' % (random.choice(list(open('/root/scrapers/flights/api_service/luminati_ips.list'))).strip().replace('zproxy.lum-superproxy.io:22225:', ''), 'zproxy.lum-superproxy.io:22225')
			settings.overrides['USER_AGENT'] = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'
			return Request('https://booking2.airasia.com/LoginAgent.aspx', callback=self.parse, headers=headers, cookies={}, dont_filter=True, meta={'content' : True})
		else:
      	        	open('%s_garbage' %  cnl_dict_.get('trip_ref', 'Check the cancel dict'), 'w').write(response.body)
			logging.debug('Login Failed Server Busy %s, %s, %s' % (response.status, manage_booking, response.url))
			self.insert_report_into_db(cnl_dict_, 'Scraper unable to log in AirAsia Due to Server Busy Garbage')
			return
            else:
                logging.debug('Login Failed Server Busy %s, %s, %s' % (
                    response.status, manage_booking, response.url))
                self.insert_report_into_db(
                    cnl_dict_, 'Scraper unable to log in AirAsia Due to Server Busy')
                return
        if not manage_booking:
            open('%s_login_failed' % cnl_dict_.get('trip_ref',
                                                   'Check the cancel dict'), 'w').write(response.body)
            self.insert_report_into_db(cnl_dict_, 'Response not loaded')
            logging.debug('Response not loaded %s, %s, %s' %
                          (response.status, manage_booking, response.url))
            return
        if self.cancellation_dict:
            try:
                cnl_dict_ = eval(self.cancellation_dict)
                cnl_dict = self.process_input(cnl_dict_)
                print cnl_dict
            except Exception as e:
                cnl_dict = {}
                try:
                    cnl_dict_ = eval(self.cancellation_dict)
                except:
                    cnl_dict_ = {}
                self.insert_report_into_db(cnl_dict_, 'Wrong input format')
            if cnl_dict:
                url = 'https://booking2.airasia.com/BookingList.aspx'
                return Request(url, callback=self.parse_search, dont_filter=True, meta={'cnl_dict': cnl_dict})

    def parse_search(self, response):
        sel = Selector(response)
        cnl_dict = response.meta['cnl_dict']
        cnl_dict.update({'cancellation_status': 0})
        cnl_dict.update({'cancellation_status_mesg': 'Failed'})
        view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
        search_data_list.update({'__VIEWSTATE': str(view_state)})
        search_data_list.update({'__VIEWSTATEGENERATOR': str(gen)})
        pnr_no = cnl_dict.get('pnr', '')
        if pnr_no:
            search_data_list.update(
                {'ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword': pnr_no})
            url = "http://booking2.airasia.com/BookingList.aspx"
            yield FormRequest(url, formdata=search_data_list, callback=self.parse_pnr_deatails, meta={'cnl_dict': cnl_dict})
        else:
            self.insert_report_into_db(
                cnl_dict, 'Scraper got empty PNR in request')

    def parse_pnr_deatails(self, response):
        sel = Selector(response)
        cnl_dict = response.meta['cnl_dict']
        view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
        res_headers = json.dumps(str(response.headers))
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
        cookies = {}
        for i in my_dict.get('Set-Cookie', []):
            data = i.split(';')[0]
            if data:
                try:
                    key, val = data.split('=', 1)
                except:
                    continue
                cookies.update({key.strip(): val.strip()})
        nodes = sel.xpath(table_nodes_path)
        if not nodes:
            error_msg = "No details found with PNR %s" % cnl_dict.get(
                'pnr', '')
            self.insert_report_into_db(cnl_dict, error_msg)
            self.send_mail("[AirAsia Cancellation]" +
                           error_msg, self.cancellation_dict)
        elif len(nodes) >= 2:
            error_msg = "More than one results found with PNR %s" % cnl_dict.get(
                'pnr', '')
            self.insert_report_into_db(cnl_dict, error_msg)
            self.send_mail("[AirAsia Cancellation]" +
                           error_msg, self.cancellation_dict)
        elif len(nodes) == 1:
            for node in nodes:
                data_dict = {}
                ids = ''.join(node.xpath(table_row_id_path).extract())
                if not ids:
                    error_msg = 'It does not have modify option PNR-%s' % cnl_dict.get(
                        'pnr', '')
                    self.insert_report_into_db(cnl_dict, error_msg)
                    continue
                href = ''.join(node.xpath(table_row_href_path).extract())
                date_lst = node.xpath(flight_date_path).extract()
                origin = ''.join(node.xpath(flight_origin_path).extract())
                desti = ''.join(node.xpath(flight_dest_path).extract())
                book_id = ''.join(node.xpath(flight_booking_id_path).extract())
                guest_name = ''.join(node.xpath(pax_name_path).extract())
                data_dict.update({'origin': origin, 'destination': desti,
                                  'booking_id': book_id, 'guest_name': guest_name})
                edit_key = 'Edit:' + \
                    ''.join(re.findall('Edit:(.*)', href)).strip(")'")
                cookies.update({'_gali': ids})
                booking_headers.update({'Cookie': '_gali=%s' % normalize(ids)})
                if ids:
                    booking_data_list.update(
                        {'__EVENTARGUMENT': normalize(edit_key)})
                    booking_data_list.update(
                        {'__VIEWSTATE': normalize(view_state)})
                    booking_data_list.update(
                        {'ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword': normalize(book_id)})
                    url = 'https://booking2.airasia.com/BookingList.aspx'
                    yield FormRequest(url, callback=self.parse_details, headers=booking_headers,
                                      formdata=booking_data_list, meta={'data_dict': data_dict, 'cnl_dict': cnl_dict})
        else:
            error_msg = "No details found with PNR %s" % cnl_dict.get(
                'pnr', '')
            self.insert_report_into_db(cnl_dict, error_msg)
            self.send_mail("[AirAsia Cancellation]" +
                           error_msg, self.cancellation_dict)

    def parse_details(self, response):
        sel = Selector(response)
        url = 'http://booking2.airasia.com/ChangeItinerary.aspx'
        yield FormRequest.from_response(response, callback=self.parse_next1,
                                        meta={'url': url, 'data_dict': response.meta['data_dict'],
                                              'cnl_dict': response.meta['cnl_dict']})

    def parse_next1(self, response):
        sel = Selector(response)
        data_dict = response.meta['data_dict']
        cnl_dict = response.meta['cnl_dict']
        check_cancel_button = ''.join(sel.xpath(
            '//div[@id="atAGlanceContent"]//ul//li//a[contains(text(), "Cancel Flight")]//text()').extract())
        if 'ItineraryReadOnly' in response.url:
            error_msg = "Cancel Flight button not presented"
            self.insert_report_into_db(cnl_dict, error_msg)
            self.send_mail("[AirAsia Cancellation]" +
                           error_msg, self.cancellation_dict)
            return
        if not check_cancel_button:
            error_msg = "Cancel Flight button not presented"
            self.insert_report_into_db(cnl_dict, error_msg)
            self.send_mail("[AirAsia Cancellation]" +
                           error_msg, self.cancellation_dict)
            return

        if not 'ChangeItinerary' in response.url:
            error_msg = "Scraper failed to navigate ChangeItinerary page"
            self.insert_report_into_db(cnl_dict, error_msg)
            self.send_mail("[AirAsia Cancellation]" +
                           error_msg, self.cancellation_dict)
            return
        cancellation_status, err_msg = 0, ''
        check_resposne, pnr_status, loc_status, flight_status = False, False, False, False
        airasia_dict, vals = {}, {}
        booking_id = normalize(
            ''.join(sel.xpath(pax_page_booking_id_path).extract()))
        total_paid = normalize(
            ''.join(sel.xpath(pax_page_amount_path).extract()))
        depart = normalize(
            ''.join(sel.xpath(pax_page_depart_loc_path).extract()))
        flight_id = sel.xpath(pax_page_flight_id_path).extract()
        from_airport_details = normalize(
            ' '.join(sel.xpath(pax_page_fr_air_path).extract()))
        to_airport_details = normalize(
            ' '.join(sel.xpath(pax_page_to_air_path).extract()))
        guest_name = normalize(
            '<>'.join(sel.xpath(pax_page_guest_name_path).extract()))
        mobile_no = normalize(
            ''.join(sel.xpath(pax_page_mo_no_path).extract()))
        email = normalize(''.join(sel.xpath(pax_page_email_path).extract()))
        payment_details_lst = normalize(
            ' '.join(sel.xpath(pax_page_payment_path).extract()))
        airasia_depart_date_text = '<>'.join(re.findall(
            '\d{2} \w+ \d{4}', from_airport_details)).strip().split('<>')
        airasia_depart_date_text = [
            x for x in airasia_depart_date_text if normalize(x).strip()]
        if airasia_depart_date_text:
            airasia_depart_date_text = airasia_depart_date_text[0]
        else:
            airasia_depart_date_text = ''
        airasia_depart_time = '<>'.join(re.findall(
            '\((\d+:.*)\)', from_airport_details)).strip().split('<>')
        airasia_depart_time = [
            x for x in airasia_depart_time if normalize(x).strip()]
        if airasia_depart_time:
            airasia_depart_time = airasia_depart_time[0]
        else:
            airasia_depart_time = ''
        # return_details
        re_depart = normalize(
            ''.join(sel.xpath(return_pax_page_depart_loc_path).extract()))
        re_flight_id = sel.xpath(return_pax_page_flight_id_path).extract()
        re_from_airport_details = normalize(
            ' '.join(sel.xpath(return_pax_page_fr_air_path).extract()))
        re_to_airport_details = normalize(
            ' '.join(sel.xpath(return_pax_page_to_air_path).extract()))
        fares_one_dict, fare_re_dict, fares_dict = {}, {}, {}
        fares_three_dict, fare_four_dict = {}, {}
        fare_keys = sel.xpath(
            '//table[@class="priceDisplay"]//tr//td[1]/text()').extract()
        check_fare_table = sel.xpath(
            '//table[@class="priceDisplay"]//tr[1]//td//text()').extract()
        for key in fare_keys:
            fr_val2 = normalize(''.join(sel.xpath(
                '//table[@class="priceDisplay"]//tr//td[contains(text(), "%s")]/following-sibling::td[not(contains(@class, "bold grey-color"))][2]/text()' % key).extract()))
            fr_val3 = normalize(''.join(sel.xpath(
                '//table[@class="priceDisplay"]//tr//td[contains(text(), "%s")]/following-sibling::td[not(contains(@class, "bold grey-color"))][3]/text()' % key).extract()))
            fr_val4 = normalize(''.join(sel.xpath(
                '//table[@class="priceDisplay"]//tr//td[contains(text(), "%s")]/following-sibling::td[not(contains(@class, "bold grey-color"))][4]/text()' % key).extract()))
            fr_val = sel.xpath(
                '//table[@class="priceDisplay"]//tr//td[contains(text(), "%s")]/following-sibling::td[1]/text()' % key).extract()
            if fr_val:
                fr_val = normalize(fr_val[0])
            fr_val = self.get_clean_data(fr_val)
            fr_val2 = self.get_clean_data(fr_val2)
            fr_val3 = self.get_clean_data(fr_val3)
            fr_val4 = self.get_clean_data(fr_val4)
            if fr_val:
                fares_one_dict.update({key: fr_val})
            if fr_val2:
                fare_re_dict.update({key: fr_val2})
            if fr_val3:
                fares_three_dict.update({key: fr_val3})
            if fr_val4:
                fare_four_dict.update({key: fr_val4})
        if fares_one_dict:
            fares_dict.update({'1': fares_one_dict})
        if fare_re_dict:
            fares_dict.update({'2': fare_re_dict})
        if fares_three_dict:
            fares_dict.update({'3': fares_three_dict})
        if fare_four_dict:
            fares_dict.update({'4': fare_four_dict})
        total_paid = self.get_clean_data(total_paid)
        fares_dict.update({'due_amount': '0'})
        fares_dict.update({'total': total_paid})
        cnl_dict.update({'payment_status': json.dumps(fares_dict)})
        air_depart_date = ''
        if airasia_depart_date_text:
            try:
                air_depart_date = datetime.datetime.strptime(
                    airasia_depart_date_text, '%d %b %Y').date()
            except:
                err_msg = 'Regex not matched with AirAsia date format'
                self.insert_report_into_db(cnl_dict, err_msg)
                return
            try:
                air_depart_date = str(air_depart_date) + \
                    ' ' + airasia_depart_time
                air_depart_date = datetime.datetime.strptime(
                    air_depart_date, '%Y-%m-%d %I:%M %p')
            except:
                err_msg = 'Regex not matched with AirAsia time format'
                self.insert_report_into_db(cnl_dict, err_msg)
                return
        else:
            air_depart_date = ''
            err_msg = 'AirAsia travel date not found'
            self.insert_report_into_db(cnl_dict, err_msg)
            return

        airasia_dict.update({'booking_id': booking_id, 'total_paid': total_paid,
                             'depart': depart, 'flight_id': flight_id, 'from_airport_details': from_airport_details,
                             'to_airport_details': to_airport_details, 'guest_name': guest_name,
                             'mobile_no': mobile_no, 'email': email})
        flight_ids = [x for x in flight_id if normalize(x).strip()]
        re_flight_ids = [x for x in re_flight_id if normalize(x).strip()]
        flight_ids.extend(re_flight_ids)
        if normalize(cnl_dict.get('pnr', '')) == normalize(booking_id):
            pnr_status = True
        input_flt_id = cnl_dict.get('flightid', '').replace(
            ' ', '').replace('-', '').replace(u'\u2010', '').strip()
        flt_rank = 0
        for i in flight_ids:
            i = i.replace(' ', '').replace(
                '-', '').replace(u'\u2010', '').strip()
            if i.lower() in input_flt_id.lower():
                flight_status = True
                flt_rank = flt_rank + 1
            else:
                flight_status = False
        if flt_rank != len(flight_ids):
            flight_status = False
        travel_date_status, past_dated_booking, refund_computation_queue, \
            manual_refund_queue = self.check_travel_date(
                cnl_dict, air_depart_date)
        loc_status, depart_loc, arrival_loc = self.check_depart_arrival_loc(
            cnl_dict, depart)
        pax_oneway_status, ignore_oneway_pax_check = self.check_pax_status(
            cnl_dict, guest_name)
        cancle_msg, pax_count, pax_cnl_status = self.get_cancellation_type(
            cnl_dict)
        cnl_dict.update({'cancellation_message': cancle_msg})
        cnl_dict.update({'pax_name': guest_name})
        cnl_dict.update({'manual_refund_queue': manual_refund_queue})
        cnl_dict.update({'flight_id': str(flight_ids)})
        if ignore_oneway_pax_check == 1:
            self.insert_report_into_db(
                cnl_dict, 'Two Pax presented with same name')
            self.send_mail(
                "[AirAsia Cancellation] Two Pax presented with same name", self.cancellation_dict)
            return
        if not pax_oneway_status:
            self.insert_report_into_db(
                cnl_dict, 'Pax name not matched with AirAsia')
            self.send_mail(
                "[AirAsia Cancellation] Pax name not matched", self.cancellation_dict)
            return
        if past_dated_booking:
            past_dated = 1
        else:
            past_dated = '0'
        cnl_dict.update({'past_dated_booking': past_dated})
        if refund_computation_queue:
            refund_com_q = 1
        else:
            refund_com_q = 0
        cnl_dict.update({'refund_computation_queue': refund_com_q})
        if not travel_date_status:
	    err_msg = 'Itinerary not matched'
	    self.insert_report_into_db(cnl_dict, 'Itinerary not matched')
	    self.send_mail("[AirAsia Cancellation] Itinerary not matched", self.cancellation_dict)
	    return
        '''
        if not flight_status: #enable if flight id check is needed
	    err_msg = '%s and Flight Id not matched'%cancle_msg
	    self.insert_report_into_db(cnl_dict, err_msg)
	    self.send_mail("[AirAsia Cancellation]" + err_msg, self.cancellation_dict)
	    return
	'''
        #if flight_status and pnr_status and loc_status and travel_date_status and manual_refund_queue==0 and not past_dated_booking:
	if pnr_status and loc_status and travel_date_status and manual_refund_queue==0 and not past_dated_booking:
	    if ignore_oneway_pax_check == 1:
	        cancellation_status = '0'
	        err_msg = 'Two Pax presented with same name'
		cancle_msg = 'Two Pax presented with same name'
		self.insert_report_into_db(cnl_dict, err_msg)
		return
   	    else:
	        cancellation_status = 1
		if not pax_oneway_status:
		    cancellation_status = 0
		    err_msg = 'Pax name not matched with AirAsia'
        if past_dated_booking:
            cancle_msg = "Past dated Booking"
            cancellation_status = 0
            self.insert_report_into_db(cnl_dict, cancle_msg)
            return
        if pax_cnl_status == 0:
            cancellation_status = 0
        view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
        cancel_data = {
            '__EVENTTARGET': 'ChangeControl$LinkButtonCancelFlight',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': view_state,
            'pageToken': '',
            'MemberLoginChangeItineraryView2$TextBoxUserID': '',
            'hdRememberMeEmail': '',
            'MemberLoginChangeItineraryView2$PasswordFieldPassword': '',
            'memberLogin_chk_RememberMe': 'on',
            'HiddenFieldPageBookingData': normalize(booking_id),
            '__VIEWSTATEGENERATOR': gen,
        }
        cancel_url = 'https://booking2.airasia.com/ChangeItinerary.aspx'
        proceed_to_cancel = cnl_dict.get('proceed_to_cancel', 1)
        cnl_dict.update({'payment_status': json.dumps(fares_dict)})
        if proceed_to_cancel:
            proceed_to_cancel = int(proceed_to_cancel)
        if cancellation_status == 1 and proceed_to_cancel == 1:
            fin_cnl_status = 'Flight/s cancelled successfully! Before'
            cnl_dict.update({'cancellation_status_mesg': fin_cnl_status})
            cnl_dict.update({'cancellation_status': cancellation_status})
            #self.insert_report_into_db(cnl_dict, '')
            yield FormRequest(cancel_url, callback=self.parse_cancel_pnr, formdata=cancel_data,
                              method="POST", meta={'view_state': view_state, 'cnl_dict': cnl_dict, 'fare_dict': fares_dict})
        elif proceed_to_cancel == 0 and cancellation_status == 1:
            # Successful response for testing
            fin_cnl_status = 'Flight/s cancelled successfully!'
            cnl_dict.update({'cancellation_status_mesg': fin_cnl_status})
            cnl_dict.update({'cancellation_status': 0})
            self.insert_report_into_db(cnl_dict, 'Test Request')
        else:
            cnl_dict.update({'cancellation_status_mesg': 'Falied'})
            cnl_dict.update({'cancellation_status': 0})
            self.insert_report_into_db(cnl_dict, cancle_msg)
            self.send_mail("[AirAsia Cancellation]" +
                           cancle_msg, self.cancellation_dict)

    def parse_cancel_pnr(self, response):
        sel = Selector(response)
        prv_v_state = response.meta['view_state']
        cnl_dict = response.meta['cnl_dict']
        fare_dict = response.meta['fare_dict']
        gen = ''.join(sel.xpath(view_generator_path).extract())
        file_name = 'I5_cancel_B_%s.html' % cnl_dict.get('tripid', '')
        with open(file_name, 'w+') as f:
            f.write('%s' % response.body)

        cnl_form_data = {
            '__EVENTTARGET': 'ControlGroupFlightCancelView$FlightDisplayFlightCancelView$LinkButtonSubmit',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': normalize(prv_v_state),
            'pageToken': '',
            'pageToken': '',
            'eventTarget': 'ControlGroupFlightCancelView$FlightDisplayFlightCancelView$LinkButtonSubmit',
            'eventArgument': '',
            'viewState': normalize(prv_v_state),
            'ControlGroupFlightCancelView$FlightDisplayFlightCancelView$CheckBoxCancel_0': 'on',
            'ControlGroupFlightCancelView$FlightDisplayFlightCancelView$OthersBox': '',
            '__VIEWSTATEGENERATOR': normalize(gen),
        }
        url = 'https://booking2.airasia.com/FlightCancel.aspx'

        yield FormRequest(url, callback=self.parse_final_cancellation, formdata=cnl_form_data, meta={'cnl_dict': cnl_dict, 'fare_dict': fare_dict})

    def parse_final_cancellation(self, response):
        sel = Selector(response)
        cnl_dict = response.meta['cnl_dict']
        fare_dict = response.meta['fare_dict']
        file_name = 'I5_cancel_%s.html' % cnl_dict.get('tripid', '')
        with open(file_name, 'w+') as f:
            f.write('%s' % response.body)
        status = sel.xpath('//div[@id="cancelContent"]//text()').extract()
        print '******%s*******' % status
        try:
            self.log.debug('Check status here : %s' % status)
        except:
            pass
        fin_cnl_status = normalize(
            ''.join(sel.xpath('//div[@id="cancelContent"]//text()').extract()))
        cnl_dict.update({'cancellation_status_mesg': fin_cnl_status})
        if not fin_cnl_status:
            cnl_dict.update({'cancellation_status': 0})
            self.insert_report_into_db(cnl_dict, 'Cancellation Failed')
            self.send_mail(
                "[I5]:Cancellation Failed whereas cancellation success", self.cancellation_dict)
            return
        cnl_pnr = normalize(''.join(sel.xpath(
            '//span[@id="OptionalHeaderContent_lblBookingNumber"]//text()').extract()))
        pay_due_amount = normalize(''.join(sel.xpath('//div[contains(text(), "Payment amount due")]\
			/../following-sibling::td/div/text()').extract()))
        pay_due_amount = ''.join(re.findall('\d+', pay_due_amount))
        #fin_cnl_status = 'Flight/s cancelled successfully!'

        cnl_dict.update({'cancellation_status_mesg': fin_cnl_status})
        cnl_dict.update({'cancellation_status': 1})
        cnl_dict.update({'payment_status': json.dumps(fare_dict)})
        total_fare = ''.join(sel.xpath(
            '//span[@id="OptionalHeaderContent_lblTotalPaid"]//text()').extract())
        fares_one_dict, fare_re_dict, fares_dict = {}, {}, {}
        fares_three_dict, fare_four_dict = {}, {}
        fare_keys = sel.xpath(
            '//table[@class="priceDisplay"]//tr//td[1]/text()').extract()
        for key in fare_keys:
            fr_val = sel.xpath(
                '//table[@class="priceDisplay"]//tr//td[contains(text(), "%s")]/following-sibling::td[1]/text()' % key).extract()
            fr_val2 = sel.xpath(
                '//table[@class="priceDisplay"]//tr//td[contains(text(), "%s")]/following-sibling::td[2]/text()' % key).extract()
            fr_val3 = sel.xpath(
                '//table[@class="priceDisplay"]//tr//td[contains(text(), "%s")]/following-sibling::td[3]/text()' % key).extract()
            fr_val4 = sel.xpath(
                '//table[@class="priceDisplay"]//tr//td[contains(text(), "%s")]/following-sibling::td[4]/text()' % key).extract()
            if fr_val:
                fr_val = normalize(fr_val[0])
                if fr_val:
                    fr_val = self.get_clean_data(fr_val)
                else:
                    fr_val = ''
            else:
                fr_val = ''
            if fr_val2:
                fr_val2 = normalize(fr_val2[0])
                if fr_val2:
                    fr_val2 = self.get_clean_data(fr_val2)
                else:
                    fr_val2 = ''
            else:
                fr_val2 = ''
            if fr_val3:
                fr_val3 = normalize(fr_val3[0])
                if fr_val3:
                    fr_val3 = self.get_clean_data(fr_val3)
                else:
                    fr_val3 = ''
            else:
                fr_val3 = ''
            if fr_val4:
                fr_val4 = normalize(fr_val4[0])
                if fr_val4:
                    fr_val4 = self.get_clean_data(fr_val4)
                else:
                    fr_val4 = ''
            else:
                fr_val4 = ''
            if fr_val:
                fares_one_dict.update({key: fr_val})
            if fr_val2:
                fare_re_dict.update({key: fr_val2})
            if fr_val3:
                fares_three_dict.update({key: fr_val3})
            if fr_val4:
                fare_four_dict.update({key: fr_val4})
        if fares_one_dict:
            fares_dict.update({'1': fares_one_dict})
        if fare_re_dict:
            fares_dict.update({'2': fare_re_dict})
        if fares_three_dict:
            fares_dict.update({'3': fares_three_dict})
        if fare_four_dict:
            fares_dict.update({'4': fare_four_dict})
        total_paid = self.get_clean_data(total_fare)
        fares_dict.update({'total': total_paid})
        payment_table = sel.xpath(
            '//table[@class="rgMasterTable"]/thead//tr//th[contains(text(), "Payment")]/../../../tbody//tr//td[1]/div/text()').extract()
        for key in payment_table:
            val = normalize(''.join(sel.xpath(
                '//div[contains(text(), "%s")]/../following-sibling::td/div/text()' % key).extract())).strip()
            if ' ' in val:
                val = val.replace(',', '').split(' ')[0]
            if val:
                fares_dict[key] = val
        cnl_dict.update({'payment_status': json.dumps(fares_dict)})
        self.insert_report_into_db(cnl_dict, '')

    def check_travel_date(self, cnl_dict, airasia_date):
        dep_date = cnl_dict.get('departuredatetime', '')
        pax_cnl_date = cnl_dict.get('cancellationdatetime', '')
        try:
            a_day, a_month, a_year, a_minute, a_hour = airasia_date.day, \
                airasia_date.month, airasia_date.year, airasia_date.minute, airasia_date.hour
        except:
            a_day, a_month, a_year, a_minute, a_hour = ['']*5
        cur_date_ = datetime.datetime.now()
        past_dated_booking, refund_computation_queue, tr_datetime_cnl_status = False, False, False
        if not pax_cnl_date:
            self.insert_report_into_db(
                cnl_dict, 'cancellation date not found in input')
            return (False, 0, False, 0)
        if not dep_date:
            self.insert_report_into_db(
                cnl_dict, 'Departure date not found in input')
            return (False, 0, False, 0)
        else:
            manual_refund_queue = 0
            cnt_date = datetime.datetime.strptime(dep_date, '%d-%b-%y %H:%M')
            if cnt_date.day == a_day and cnt_date.month == a_month and cnt_date.year == a_year:
                travel_datetime_status = True
            else:
                travel_datetime_status = False
            if pax_cnl_date:
                if pax_cnl_date.date() > airasia_date.date():
                    past_dated_booking = True
            # time diff b/w current date to flight
            diff_bw_curdate_airdate = pax_cnl_date - airasia_date
            ca_diff_days = diff_bw_curdate_airdate.days
            ca_diff_second = diff_bw_curdate_airdate.seconds
            if ca_diff_days == 0:
                if ca_diff_second <= 14400:
                    refund_computation_queue = True
                else:
                    tr_datetime_cnl_status = True
            if not travel_datetime_status:
                if tr_datetime_cnl_status:
                    manual_refund_queue = 1
                    travel_datetime_status = True
            return (travel_datetime_status, past_dated_booking, refund_computation_queue, manual_refund_queue)

    def check_pax_status(self, cnl_dict, pax_names):
        pax_oneway_status, pax_return_status = False, False
        oneway_pax_lst, return_pax_lst = [], []
        p_names_ = cnl_dict.get('oneway_cancellationdetails', [])
        for i in p_names_:
            oneway_pax_lst.append(' '.join(i))
        test_oneway_pax_lst = []
        for i in oneway_pax_lst:
            i = i.replace('Mrs ', '').replace('Mr ', '')\
                .replace('Ms ', '').replace('Miss ', '').replace('Mstr ', '').strip()
            test_oneway_pax_lst.append(i)
        if len(test_oneway_pax_lst) != len(set(test_oneway_pax_lst)):
            ignore_oneway_pax_check = 1
        else:
            ignore_oneway_pax_check = 0
        site_pax_workds_list = []
        site_pax_names = pax_names.split('<>')
        for pax in site_pax_names:
            pax = pax.split(' ')
            for pax_ in pax:
                pax_ = pax_.strip()
                if pax_:
                    site_pax_workds_list.append(pax_.lower())
        hq_pax_list_words = []
        for name in test_oneway_pax_lst:
            name_lst = name.split(' ')
            for p_name in name_lst:
                p_name = p_name.lower().strip()
                if p_name:
                    hq_pax_list_words.append(p_name)
        for hq_ in hq_pax_list_words:
            if hq_ in site_pax_workds_list:
                pax_oneway_status = True
            else:
                pax_oneway_status = False
                break
        return (pax_oneway_status, ignore_oneway_pax_check)

    def get_cancellation_type(self, cnl_dict):
        full, partial = ['']*2
        pax_booked = cnl_dict.get('oneway_paxdetails', [])
        trip_type = cnl_dict.get('trip_type', '')
        pax_cancle = cnl_dict.get('oneway_cancellationdetails', [])
        pax_count = len(pax_cancle)
        cnl_type = cnl_dict.get('cnl_type', '').strip().lower()
        if 'full' in cnl_type and (len(pax_booked) == len(pax_cancle)):
            status_code = 1
        else:
            status_code = 0
        oneway_cnl_sectors = len(cnl_dict.get('oneway_cnl_sectors', []))
        oneway_full_sectors = len(cnl_dict.get('oneway_full_sectors', []))
        return_cnl_sectors = len(cnl_dict.get('return_cnl_sectors', []))
        return_full_sectors = len(cnl_dict.get('return_full_sectors', []))
        if oneway_cnl_sectors == 0 and return_cnl_sectors == 0:
            return ("No cancellations found", oneway_cnl_sectors, 0)
        else:
            if trip_type == 'oneway':
                if status_code == 1:
                    if oneway_cnl_sectors == oneway_full_sectors and len(pax_cancle) == 1:
                        return ("Oneway single pax cancellation", pax_count, status_code)
                    elif oneway_cnl_sectors == oneway_full_sectors:
                        return ("Oneway  multiple pax full cancellation", pax_count, status_code)
                    elif (oneway_full_sectors > oneway_cnl_sectors):
                        return ("Oneway Split PNR cancellation", pax_count, status_code)
                    else:
                        self.send_mail(
                            "scraper faild to fetch cancellation_type", self.cancellation_dict)
                        self.insert_report_into_db(
                            cnl_dict, 'scraper faild to fetch cancellation_type')
                        return ("scraper faild to fetch cancellation_type", pax_count, status_code)
                else:
                    return ("Oneway trip partial pax cancellation", pax_count, 0)
            else:
                if status_code == 1:
                    if (oneway_full_sectors == oneway_cnl_sectors) and (return_cnl_sectors == 0):
                        return ("Round trip partial sector cancellation", pax_count, 0)

                    elif (oneway_cnl_sectors == 0) and (return_cnl_sectors == return_full_sectors):
                        return ("Round trip partial sector cancellation", pax_count, 0)

                    elif (oneway_full_sectors > oneway_cnl_sectors) and (return_cnl_sectors == 0):
                        return ("Split PNR cancellation", pax_count, 0)

                    elif (oneway_cnl_sectors == 0) and (return_full_sectors > return_cnl_sectors):
                        return ("Split PNR cancellation", pax_count, 0)

                    elif (oneway_full_sectors == oneway_cnl_sectors) and (return_full_sectors == return_cnl_sectors):
                        return ("Round trip full sector cancellation", pax_count, 1)

                    elif (oneway_full_sectors > oneway_cnl_sectors) and (return_full_sectors > return_cnl_sectors):
                        return ("Round trip partial pax cancellation", pax_count, 0)

                    else:
                        self.send_mail(
                            "scraper faild to fetch cancellation_type", self.cancellation_dict)
                        self.insert_report_into_db(
                            cnl_dict, 'scraper faild to fetch cancellation_type')
                        return ("scraper faild to fetch cancellation_type on round-trip", pax_count, 0)
                else:
                    return ("Round trip partial pax cancellation", pax_count, 0)

    def check_depart_arrival_loc(self, cnl_dict, air_data):
        status = False
        from_, to_ = [''] * 2
        if '-' in air_data:
            loc_list = air_data.split('-')
            if len(loc_list) == 2:
                from_, to_ = loc_list
                via = ''
            elif len(loc_list) == 3:
                from_, via, to_ = loc_list
            else:
                self.insert_report_into_db(cnl_dict, 'Locations not matched')

        cnl_segs = '<>'.join(cnl_dict.get('cancelled_seg', []))
        air_data = air_data.split()
        for site_seg in air_data:
            if site_seg.strip() in air_data:
                status = True
            else:
                status = False
        if not status:
            self.insert_report_into_db(cnl_dict, 'Locations not matched')
        return (status, from_, to_)

    def send_mail(self, sub, error_msg=''):
        print "mail"
        recievers_list = []
        recievers_list = ast.literal_eval(
            _cfg.get('airasia_common', 'recievers_list'))
        if '403' in sub:
            import way2sms
            obj = way2sms.sms('9442843049', 'bhava')
            phones = [u'9553552623', u'8217866491']
            for i in phones:
                sent = obj.send(i, 'AirAsia-Canecl:Login page got 403 status')
                if sent:
                    print 'Sent sms successfully'
            return
        if 'Login' in sub:
            recievers_list = ast.literal_eval(
                _cfg.get('airasia_common', 'login_recievers_list'))
            import way2sms
            obj = way2sms.sms('9442843049', 'bhava')
            phones = ast.literal_eval(_cfg.get('airasia_common', 'phones'))
            for i in phones:
                sent = obj.send(
                    i, 'Unable to login to AirAsia cancel,Please check %s' % self.pcc_name)
                if sent:
                    print 'Sent sms successfully'
        #recievers_list = ast.literal_eval(_cfg.get('airasia_common', 'recievers_list'))
        sender, receivers = 'ctmonitoring17@gmail.com', ','.join(
            recievers_list)
        ccing = []
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'AirAsia Cancel: %s On %s' % (
            sub, str(datetime.datetime.now().date()))
        mas = '<p>%s</p>' % error_msg
        msg['From'] = sender
        msg['To'] = receivers
        msg['Cc'] = ','.join(ccing)
        tem = MIMEText(''.join(mas), 'html')
        msg.attach(tem)
        s = smtplib.SMTP('smtp.gmail.com:587')
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(sender, 'ctmonitoring@123')
        s.sendmail(sender, (recievers_list + ccing), msg.as_string())
        s.quit()

    def get_clean_data(self, fr_val):
        if isinstance(fr_val, list):
            try:
                fr_val = fr_val[0]
            except:
                fr_val = ''
        if ',' in fr_val:
            fr_val = fr_val.replace(',', '')
        if '.' in fr_val:
            fr_val = ''.join(re.findall('\d+.\d+', fr_val))
        else:
            fr_val = ''.join(re.findall('\d+', fr_val))
        return fr_val
