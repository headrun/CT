import ast
import re
import time
import json
import md5
import random
import smtplib
import MySQLdb
import datetime
from random import randint
import smtplib, ssl
from email import encoders
from ast import literal_eval
from scrapy import signals
from scrapy.spider import Spider
from collections import OrderedDict
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from scrapy.http import FormRequest, Request
from email.mime.multipart import MIMEMultipart
from scrapy.selector import Selector
from ConfigParser import SafeConfigParser
from scrapy.xlib.pydispatch import dispatcher
from scrapy.conf import settings
from airasia_login_cookie import *
from seat_finder_tool_scrapers.utils import *

import sys
sys.path.append(settings['ROOT_PATH'])

_cfg = SafeConfigParser()
_cfg.read(settings['BOOK_PCC_PATH'])

class AirAsiaSeatFinderBrowse(Spider):
    name = "airasia_seatfinder_browse"
    start_urls = ["https://booking2.airasia.com/AgentHome.aspx"]
    handle_httpstatus_list = [404, 500, 400, 403]

    def __init__(self, *args, **kwargs):
        super(AirAsiaSeatFinderBrowse, self).__init__(*args, **kwargs)
        self.csv_dict = ast.literal_eval(kwargs.get('jsons', '{}'))
        self.log = create_logger_obj('airasia_seatfinder')
        self.logout_view_state = ''
        self.logout_cookies = {}
        self.insert_query = 'insert into seat_finder(sk,airline,pnr,pcc,ticket_number,error_message, status,remarks, request_input,aux_info,created_at,modified_at) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), pnr=%s, ticket_number=%s, status=%s, error_message=%s,remarks=%s'
        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('seatfinder', 'IP')
        passwd = db_cfg.get('seatfinder', 'PASSWD')
        user = db_cfg.get('seatfinder', 'USER')
        db_name = db_cfg.get('seatfinder', 'DBNAME')
        self.conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = db_name, charset="utf8", use_unicode=True)
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
        response = requests.post('https://booking2.airasia.com/AgentHome.aspx', headers=self.headers, cookies=self.logout_cookies, data=data)

    def send_mail(self, sub, error_msg=''):
        receivers_list = ast.literal_eval(_cfg.get('airasia_common', 'receivers_list'))
        if 'Login' in sub:
            receivers_list = ast.literal_eval(_cfg.get('airasia_common', 'login_receivers_list'))
        sender, receivers = 'ctmonitoring17@gmail.com', ','.join(receivers_list)
        ccing = ['sathwick.katta@cleartrip.com']
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'AirAsia PROD: %s On %s'%(sub, str(datetime.datetime.now().date()))
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
        s.sendmail(sender, (receivers_list + ccing), msg.as_string())
        s.quit()

    def parse(self, response):
        '''Login Page'''
        if not self.csv_dict:
            self.log.debug('Empty Request')
            self.insert_into_table('', 'Empty request')
            return

	self.log.debug("parse function")
        details_dict = self.csv_dict
        agent_pcc = details_dict.get('agent_pcc','')
        pcc_name = 'airasia_'+agent_pcc
        if details_dict.get('queue', '') == 'coupon':
            self.pcc_name = 'airasia_coupon_default'

        sel = Selector(response)
        view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
        login_data_list.append(('__VIEWSTATE', view_state))
        login_data_list.append(('__VIEWSTATEGENERATOR', gen))
        cookie = random.choice(airasia_login_cookie_list)
        cookies = {'i10c.bdddb':cookie}
        try:
            self.log.debug('Login using: %s' % _cfg.get(pcc_name, 'username'))
            user_name = _cfg.get(pcc_name, 'username')
            user_psswd = _cfg.get(pcc_name, 'password')
            self.book_using = user_name
            login_data = [
                      ('__EVENTTARGET', 'ControlGroupLoginAgentView$AgentLoginView$LinkButtonLogIn'),
                      ('__EVENTARGUMENT', ''),
                      ('__VIEWSTATE', '/wEPDwUBMGRktapVDbdzjtpmxtfJuRZPDMU9XYk='),
                      ('pageToken', ''),
                      ('ControlGroupLoginAgentView$AgentLoginView$TextBoxUserID', str(user_name)),
                      ('ControlGroupLoginAgentView$AgentLoginView$PasswordFieldPassword', str(user_psswd)),
                      ('ControlGroupLoginAgentView$AgentLoginView$HFTimeZone', '330'),
                      ('__VIEWSTATEGENERATOR', '05F9A2B0'),
                    ]
            yield FormRequest('https://booking2.airasia.com/LoginAgent.aspx', \
                     formdata=login_data, callback=self.parse_next, cookies=cookies, meta={'details_dict' : details_dict}, dont_filter=True)
        except:
            self.insert_into_table(err= "PCC credentials not found")
	    self.log.debug("PCC credentials not found")
    def parse_next(self, response):
        '''
        Logged in. Parse the request to my bookings or manage my booking
        '''
        if response.status == 403:
            self.insert_into_table(err="Login page got 403 status")
            self.send_mail('403 status', 'Login page got 403 status')
	    self.log.debug("Login page got 403 status")
            return

	self.log.debug("parse_next function")
        sel = Selector(response)
        ##For logout Usage###
        res_headers = json.dumps(str(response.headers))
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
        cookies = {}
        for i in my_dict.get('Set-Cookie', []):
            data = i.split(';')[0]
            if data:
                try :
                   key, val = data.split('=', 1)
                   if 'ASP.NET_SessionId' in key:
                       key = 'cookie: ASP.NET_SessionId'
                except : continue
                cookies.update({key.strip():val.strip()})
        self.logout_cookies = cookies
        self.logout_view_state = ''.join(sel.xpath(view_state_path).extract())
        ###DONE###
        details_dict = response.meta.get('details_dict','')
        url = 'https://booking2.airasia.com/BookingList.aspx'
        yield Request(url, callback=self.parse_search, dont_filter=True, meta={'details_dict':details_dict})

    def parse_search(self, response):
        '''
        Fetching the details for Existing PNR
        '''
        if response.status != 200:
            self.log.debug('Internal Server Error')
            self.send_mail('Internal Server Error','Internal Server Error')
            self.insert_into_table(err='Internal Server Error')
            return

	self.log.debug("parse_search function")
        sel = Selector(response)
        details_dict = response.meta.get('details_dict','{}')
        pnr_no = details_dict.get('airline_pnr', '')
	self.log.debug("searcing for PNR:%s"%pnr_no)
        headers = {
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                        'cache-control': 'no-cache',
                        'authority': 'booking2.airasia.com',
                        'referer': 'https://booking2.airasia.com/AgentHome.aspx',
                }

        view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
        search_data_list.update({'__VIEWSTATE': str(view_state)})
        search_data_list.update({'__VIEWSTATEGENERATOR':str(gen)})
        form_data = [
          ('__EVENTTARGET', 'ControlGroupBookingListView$BookingListSearchInputView$LinkButtonFindBooking'),
          ('__EVENTARGUMENT', ''),
          ('__VIEWSTATE', view_state),
          ('pageToken', ''),
          ('ControlGroupBookingListView$BookingListSearchInputView$Search', 'ForAgency'),
          ('ControlGroupBookingListView$BookingListSearchInputView$DropDownListTypeOfSearch', '1'),
          ('ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword', pnr_no.strip()),
          ('__VIEWSTATEGENERATOR', '05F9A2B0'),]
        if pnr_no:
            url = "http://booking2.airasia.com/BookingList.aspx"
            return FormRequest(url, formdata=form_data, callback=self.parse_pnr_details,\
                 meta={'details_dict':details_dict})

    def parse_pnr_details(self, response):
        '''
        Checking the auto PNR presented in AirAsia or not
        '''

	if response.status != 200:
            self.log.debug('Internal Server Error')
            self.send_mail('Internal Server Error', 'Internal Server Error')
            self.insert_into_table(err='Internal Server Error, no response at the PNR search page')
            return

        sel = Selector(response)
        details_dict = response.meta.get('details_dict', {})
        pnr_no = details_dict.get('airline_pnr','')
	self.log.debug('parse_pnr_details function- prn :%s'%pnr_no)
        total_bookings = response.xpath('//table[@id="currentTravelTable"]/tbody/tr').extract()
        ##PNR RETRIEVE CHECK###
        if not len(total_bookings)>=1:
            status = 'Closed'
            remarks = 'Unable To View PNR'
            self.insert_into_table('',pnr_no,status,remarks)
	    self.log.debug("length of total bookings is 0. Hence Unable To View PNR")
            return
        ###END###

        view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
        check_pnr=pnr_no
        if check_pnr:
            event_target = 'ControlGroupBookingListView$BookingListSearchInputView'
            event_argument = 'View:%s'%check_pnr
            form_data = {
                  '__EVENTTARGET': event_target,
                  '__EVENTARGUMENT': event_argument,
                  '__VIEWSTATE': view_state,
                  'pageToken': '',
                  'ControlGroupBookingListView$BookingListSearchInputView$Search': 'ForAgency',
                  'ControlGroupBookingListView$BookingListSearchInputView$DropDownListTypeOfSearch': '1',
                  'ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword': pnr_no.strip(),
                  '__VIEWSTATEGENERATOR': gen,
                }
            url = 'https://booking2.airasia.com/BookingList.aspx'
            return FormRequest(url, callback=self.itinerary_details, formdata=form_data,\
                 meta={'details_dict':details_dict,  'form_data':form_data})
	else:
	    self.log.debug("check pnr!=pnr.Hence Failed. Pnr=%s"%pnr_no)

    def itinerary_details(self, response):
        sel = Selector(response)
        '''PNR data parsing'''
        if 'ItineraryReadOnly.aspx' in response.url:
            details_dict = response.meta.get('details_dict', {})
	    self.log.debug("itinerary function.Pnr:%s"%details_dict.get('airline_pnr',''))
            seats = ','.join(response.xpath('//div[@class="paxSSR this1"][not(contains(text(),"Assignment"))][contains(text(),"Seat")]/text()').extract())
            pnr_status = ''.join(response.xpath('//span[@class="confirm status"]/text()').extract())
            src_dst = ''.join(response.xpath('//th[@class="rgHeader"][contains(text(),"Depart")]/following-sibling::th/text()').extract())
            amount_payed = ''.join(response.xpath('//span[@id="OptionalHeaderContent_lblTotalPaid"]/text()').extract())
            status = remarks =''
            if seats:
                    status = 'Flown'
                    remarks = seats.replace('Seat ','').strip() + ' {' + src_dst + '}'
            elif seats=='' and pnr_status.upper()=='CONFIRMED':
                    status = 'Closed'
                    remarks = 'No Seat Numbers'
            elif seats=='' and pnr_status.upper()=='CLOSED':
                    status = 'Closed'
                    remarks ='No Seat Numbers'
            elif pnr_status.upper()=='NEED PAYMENT':
                    status='Payment Due'
                    remarks = 'Confirm'
            else:
                    status ='Failed'
                    remarks ='Failed'
		    self.log.debug('Pnr Status is: %s and seats:%s. Not within the range of conditions'%(pnr_status,seats))
                    #error_message='Pnr Status is: %s and seats:%s. Not within the range of conditions'%(pnr_status,seats)
                    #self.insert_into_table(err=error_message)
                    #return

            sk = details_dict.get('booking_no','')
            airline = details_dict.get('airline','')
            pnr = details_dict.get('airline_pnr','')
            pcc = details_dict.get('airline_pnr','')
            status = status.replace('SEAT','').strip()
            remarks = remarks
            request_input = json.dumps(details_dict)
            aux_info = ''
            self.insert_into_table('',pnr,status,remarks)
        else:
            if response.status != 200:
                self.log.debug('Internal Server Error at Itinerary page')
                self.insert_into_table(err='Internal Server Error at Itinerary page')
            else:
                self.log.debug("Response Issue at Itinerary page")
                self.insert_into_table(err="Response Issue at Itinerary Page")
            return
    def insert_into_table(self, err='',pnr='',status='',remarks=''):
        details_dict = self.csv_dict
        sk = details_dict.get('booking_no','')
        airline = details_dict.get('airline','')
        pcc = details_dict.get('agent_pcc','')
        ticket_number = details_dict.get('ticket_no','')
        pnr = details_dict.get('airline_pnr','')
	self.log.debug('Inserting into DB for PNR:%s'%pnr)
        err = err
        status = status
        remarks = remarks
        request_input = json.dumps(details_dict)
        aux_info=''
        vals = (sk,airline,pnr,pcc,ticket_number,err,status,remarks, request_input,aux_info,pnr,ticket_number,status,err,remarks)
        try:
            self.cur.execute(self.insert_query, vals)
        except Exception as e:
            print 'some insert error'
            self.log.debug('Some insert error %s\n%s\n%s' % (e, self.insert_query, vals))
        self.conn.commit()
