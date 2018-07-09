import re
import ast
import json
import md5
import time
import MySQLdb
import smtplib
import datetime
import inspect
import smtplib, ssl
from email import encoders
from scrapy import signals
from ast import literal_eval
from scrapy.spider import Spider
from scrapy.selector import Selector
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from splitcancellation_scrapers.utils import *
from ConfigParser import SafeConfigParser
from scrapy.http import FormRequest, Request
from scrapy.xlib.pydispatch import dispatcher
from email.mime.multipart import MIMEMultipart
from indigosplit_cancellation_utils import *

from scrapy.conf import settings

import sys
sys.path.append(settings['ROOT_PATH'])

from root_utils import Helpers

_cfg = SafeConfigParser()
_cfg.read(settings['BOOK_PCC_PATH'])

class IndigosplitCancellationBrowse(Spider, IndigoSCancel, Helpers):
    name = "indigosplit_cancallation_browse"
    start_urls = ["https://www.goindigo.in/"]

    def __init__(self, *args, **kwargs):
        super(IndigosplitCancellationBrowse, self).__init__(*args, **kwargs)
        self.source_name = 'indigosplit'
        pnr_no = ''
        self.new_pnr = ''
	self.journey_mismatch = ''
        self.cancel = False
        self.log = create_logger_obj('indigosplit_cancellation')
        self.cancellation_dict = ast.literal_eval(kwargs.get('jsons', '{}'))
        self.insert_query = 'insert into indigosplit_cancellation_report(sk, airline, pnr, new_pnr, pcc, flight_number, error_message, status, cancel_amount, pricing_details, request_input, aux_info, created_at, modified_at) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now()) on duplicate key update modified_at=now(), error_message=%s, pricing_details=%s, request_input=%s, cancel_amount=%s, status=%s, new_pnr=%s'
        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('splitcancel', 'IP')
        passwd = db_cfg.get('splitcancel', 'PASSWD')
        user = db_cfg.get('splitcancel', 'USER')
        db_name = db_cfg.get('splitcancel', 'DBNAME')
        self.conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()

    def spider_closed(self, spider):
	self.cur.close()
	self.conn.close()

    def parse(self, response):
        '''Parse Login'''
        if not self.cancellation_dict:
            self.log.debug('Empty Request')
            return
        login_data_list = []
        self.pcc_name  = self.get_pcc_name()#'indigo_%s' % self.cancellation_dict['details'][0]['pcc']
        if len(self.cancellation_dict['details']) == 2:
            self.log.debug('Multiple PNR Cancellation')
            self.insert_into_table(err='Multiple PNR Cancellation')
            return
        print self.pcc_name
        cancellation_type = self.cancellation_dict['details'][0].get('cancellation_type', '').get('type', '')
        pnr_no = self.cancellation_dict['details'][0].get('pnr', '')
        self.log.debug("Search for PNR: %s" % pnr_no)
	if cancellation_type.upper() not in ['PARTIAL','FULL']:
            self.insert_into_table(err='Cancellation type is wrong')
            self.log.debug('Cancellation type is wrong')
            return
	if len(self.cancellation_dict['details'][0]['all_segment_details']) != len(self.cancellation_dict['details'][0]['cancelled_segment_details']):
		self.insert_into_table(err='Failing as Partial segment cancellation')
		self.log.debug('Partial segment cancellation error')
                return
        sel = Selector(response)
        try:
            self.log.debug("Login using : %s" % _cfg.get(self.pcc_name, 'login_name'))
            data = [
      ('agentLogin.Username', _cfg.get(self.pcc_name, 'login_name')),
      ('agentLogin.Password', _cfg.get(self.pcc_name, 'login_pwd').strip("'")),
      ('IsEncrypted', 'true'),
                ]
        except:
            self.insert_into_table(err="PCC %s not available for scrapper" % self.pcc_name)
            logging.debug('PCC not avaialble for scrapper')
            return
        url = 'https://book.goindigo.in/Agent/Login'
        yield FormRequest(url, callback=self.parse_next, formdata=data, meta={'pnr_no' : self.cancellation_dict['details'][0]['pnr']})

    def parse_next(self, response):
        sel = Selector(response)
        pnr_no = response.meta['pnr_no']
        if response.status == 200:
            token = ''.join(sel.xpath('//div[@class="bookingRef"]//input[@name="__RequestVerificationToken"]/@value').extract())
            url = 'https://book.goindigo.in/Agent/MyBookings'
            data = {'__RequestVerificationToken' : token}
            data.update({'indiGoMyBookings.BookingSearchRecordLocator' : pnr_no})
            data.update({'indiGoMyBookings_Submit' : 'Get Itinerary'})
	    cancellation_type = self.cancellation_dict['details'][0].get('cancellation_type', '').get('type', '')
	    if cancellation_type.upper() =='PARTIAL':
		return FormRequest(url, callback=self.parse_itinerary, formdata=data, dont_filter=True, meta={'pnr_no' : pnr_no, 'cancel' : response.meta.get('cancel', False)})
	    elif cancellation_type.upper() =='FULL':
		return FormRequest(url, callback=self.parse_itinerary, formdata=data, dont_filter=True, meta={'pnr_no' : pnr_no, 'cancel' : response.meta.get('cancel', True)})
        else:
            self.send_mail(sub="Indigo Split Unable to login on Login ID %s" % _cfg.get(self.pcc_name, 'username') , error_msg='6E Split Scrapper Unable to login on Login ID', airline='Indigo', config='splitcancel', receiver='indigo_common')
	    self.insert_into_table(err="6E splitcancel Unable to Login on %s" % _cfg.get(self.pcc_name, 'username'))
            self.log.debug('%s Login Failure for 6E spli cancel: %s' % (_cfg.get(self.pcc_name, 'username'), response.url))

    def parse_itinerary(self, response):
        sel = Selector(response)
        pnr_no = response.meta.get('pnr_no', '')
        cancel = response.meta.get('cancel', False)#Change it  to False after checks###
        #send one meta here for differentiating split and cancel
        if pnr_no:
            #capture that split or cancel thing, not here, next function
            #Payment status check
	    try: ref, _, status, _1, dob, payment_status = [i.strip() for i in sel.xpath('//div[@class="processStep"]/ul/li/h4//text()').extract()]
	    except:
		self.log.debug("%s" % sel.xpath('//div[@class="processStep"]/ul/li/h4/text()').extract())
		self.insert_into_table(err="Xpaths changed in site, need to check" )
		return
            if payment_status.upper() != 'COMPLETE':
                self.log.debug("Payment status is not complete, it is %s" % payment_status)
                self.insert_into_table(err="Payment status is not complete" )
                return
	    if status.upper() == 'CANCELLED':
		self.log.debug("Already cancelled %s" % pnr_no)
		self.insert_into_table(err="Already cancelled" )
                return
            if not cancel:
                split_button = ''.join(sel.xpath('//div[contains(@class, "modifyBookingWrapper")]//ul/li//a[contains(text(), "Split")]').extract())
                if not split_button:
                    self.insert_into_table(err='No split option available')
                    self.log.debug('No split option available')
                    return
	    if not cancel or self.cancellation_dict['details'][0].get('cancellation_type', '').get('type', '').upper()=='FULL':
                all_pax = [' '.join(i[1:]).title().strip() for i in self.cancellation_dict['details'][0]['all_pax_details']]
		if len(all_pax) != len(set(all_pax)):
                    self.log.debug('Duplicate passengers(gender title)')
                    self.insert_into_table(mesg='', err="Duplicate passengers - gender title")
                    return
                passenger_details = sel.xpath('//div[@class="passenger_views"]//li/h2/text()').extract()
                all_pax_len = len(all_pax)
                passengers_len = len(passenger_details)
                if all_pax_len != passengers_len:
                    self.log.debug("length of passengers are not same %s %s" % (all_pax_len, passengers_len))
                    self.insert_into_table(err='length of passengers are not same')
		    return
                counter = 0
                for j in all_pax:
                    for i in passenger_details:
                        i = ' '.join(i.strip().title().replace('  ', ' ').split()[1:])#i.strip().title().replace('  ', ' ')
                        if i == j:
                            counter += 1
                            break
			try: self.log.debug('%s %s' % (i,  j))
			except: pass
                if counter != all_pax_len:
                    self.log.debug('not matching names of passengers')
                    self.insert_into_table(err='Passenger names mismatch')
                    return
            #Jouney details check
            journey_details = sel.xpath('//div[@class="itiFlightDetails flights_table"]/table//tr')
            journey_check = self.journey_check(journey_details)
            #See if it is one way or roundtrip
            #Expecting only 2 rows always, put a for loop and use index to differentiate btw trip types

            if journey_check:
                self.log.debug('Journey details do not match')
                self.insert_into_table(err='Journey details mismatch %s' % self.journey_mismatch)
                return
            if cancel:
                #Have to do it later
                undo_button = ''.join(sel.xpath('//button[@id="btnUndoCheckIn"]').extract())
                if undo_button:
                    url = 'https://book.goindigo.in/Booking/UndoCheckIn'
                    token = ''.join(sel.xpath('//input[@name="__RequestVerificationToken"]/@value').extract())
        	    self.log.debug("Undoing the split PNR")
                    #index = 'Capture journey index, need PNRs for that'#Look into this
		    index = ''.join(sel.xpath('//div[@class="modal-content"]//form[@action="/Booking/UndoCheckIn"]//input[@name="hdnUndoCheckInJourneyIndex"]/@value').extract())
                    data = {'hdnUndoCheckInJourneyIndex' : index}
                    data.update({'__RequestVerificationToken' : token})
                    return FormRequest(url, callback=self.parse_itinerary, formdata=data, meta={'pnr_no' : pnr_no, 'cancel' : cancel}, dont_filter=True)
		if self.cancellation_dict['details'][0].get('cancellation_type', '').get('type', '').upper()=='FULL':
                        self.log.debug("Cancel start for Full PNR %s" % pnr_no)
		elif self.cancellation_dict['details'][0].get('cancellation_type', '').get('type', '').upper()=='PARTIAL':
			self.log.debug("Cancel start for split PNR %s" % pnr_no)
		return Request('https://book.goindigo.in/Flight/CancelAll', callback=self.parse_cancel_start, dont_filter=True, meta={'pnr_no' : pnr_no})
            elif split_button:
                self.log.debug("Split Initiated for PNR : %s" % pnr_no)
                rolecode = ''.join(sel.xpath('//input[@name="RoleCode"]/@value').extract())
                split_url = 'https://dbusinessapps.goindigo.in/WebsiteAppDigital/splitpnr/index'
                data = {'PNR' : pnr_no, 'RoleCode' : rolecode}
                self.log.debug("Can split")
                return FormRequest(split_url, callback=self.parse_split_book, formdata=data, dont_filter=True, meta={'pnr_no' : pnr_no})

    def parse_split_book(self, response):
        sel = Selector(response)
        pnr_no = response.meta.get('pnr_no', '')
        table_contents = sel.xpath('//div[@class="tableWrap splitTable"]//table//tr')
        hdnPax = self.findall_splits(table_contents)
        data = {'hdnPnr' : pnr_no}
        data.update({'hdnPax' : ',%s' % hdnPax})
        #check here if properly coming or not
        if not hdnPax:
            self.log.debug('No one to split')
            self.insert_into_table(err="person not available for split")
	    open('%s_no_split' %self.cancellation_dict['trip_ref'], 'w').write(response.body)
	    return
        split_pax_url = 'https://dbusinessapps.goindigo.in/WebsiteAppDigital/SplitPNR/IndexPNR'
        return FormRequest(split_pax_url, callback=self.parse_ajax_receive, formdata=data, meta={'pnr_no' : pnr_no}, dont_filter=True)

    def parse_ajax_receive(self, response):
        sel = Selector(response)
        pnr_no = response.meta.get('pnr_no', '')
        self.log.debug('Splitted: %s' % pnr_no)
        open('%s_split' % pnr_no, 'w').write(response.body)
        new_split_pnr = ''.join(sel.xpath('//div[@class="itiFlightDetails"]//input[@id="hdnSplitPNR"]/@value').extract())
        if new_split_pnr:
            self.log.debug("New PNR for cancel: %s" % new_split_pnr)
            self.new_pnr = new_split_pnr
            url = 'https://book.goindigo.in/Agent/MyBookings'
            return Request(url, callback=self.parse_next, dont_filter=True, meta={'cancel' : True, 'pnr_no': new_split_pnr})
        else:
            self.log.debug("Something wrong while splitting the PNR")
            self.insert_into_table(err='Something wrong while splitting the PNR')
            self.send_mail(sub='Something wrong while splitting the PNR %s %s' % (pnr_no, new_split_pnr), error_msg='Something wrong while splitting the PNR', airline='Indigo', receiver='indigo_common', config='splitcancel')


    def parse_cancel_start(self, response):
        sel = Selector(response)
        token = ''.join(sel.xpath('//input[@name="__RequestVerificationToken"]/@value').extract())
        url = 'https://book.goindigo.in/Booking/Finish'
	time.sleep(5)
        yield FormRequest(url, callback=self.parse_cancel_finish, formdata={'__RequestVerificationToken' : token}, dont_filter=True)

    def parse_cancel_finish(self, response):
        sel = Selector(response)
        url = 'https://book.goindigo.in/Booking/PostCommit'
	time.sleep(25)
        yield Request(url, callback=self.parse_post_cancel, dont_filter=True)

    def parse_post_cancel(self, response):
        time.sleep(5)
        url = 'https://book.goindigo.in/Booking/ViewAEM'
        yield Request(url, callback=self.parse_post_cancel_after)

    def parse_post_cancel_after(self, response):
        sel = Selector(response)
        trip_id = self.cancellation_dict['trip_ref']
        try:
            detail = json.loads(response.body)
        except:
            self.insert_error_msg(err='Payment failed json body')
            self.send_mail("Indigo Cancelling Payment Failed Json body: %s" % self.booking_dict['trip_ref'], '')
            return
        open('%s_cancel' % trip_id, 'w').write(response.body)
        status= detail['indiGoBookingDetail']['bookingStatusMsg']
        pay_status = detail['indiGoBookingDetail']['paymentStatus']
        ref = detail['indiGoBookingDetail']['recordLocator']
        price_summary = sel.xpath('//div[@class="priceSummary rice_smry"]//td//text()').extract()
        cancel_amount = detail['indiGoPriceBreakdown']['cancelChangeFees']
        payment_dict = detail['indiGoPriceBreakdown']['indigoJourneyPrice']
        dob = detail['indiGoBookingDetail']['bookingDate']
        extras_dict = detail['indiGoPriceBreakdown']['cancelChangeFee']

        confirmation_dict = {'Booking Reference' : ref, 'Status' : status, 'date_of_booking' : dob, 'payment_status' : pay_status, 'refund_amount' : detail['indiGoPriceBreakdown']['refundAmount']}
        pricing_details = [confirmation_dict, payment_dict, extras_dict]
	cancellation_type = self.cancellation_dict['details'][0].get('cancellation_type', '').get('type', '')
	if status != 'Cancelled':
	    if cancellation_type.upper() =='PARTIAL':
		self.insert_into_table('Split done but cancel failed', 'Split success but Cancel Failed', cancel_amount, pricing_details)
	    elif cancellation_type.upper() =='FULL':
		self.insert_into_table('cancel failed', 'Cancel Failed', cancel_amount, pricing_details)
	    return
	else:
		if cancellation_type.upper() =='PARTIAL':
			self.insert_into_table('Split and Cancel Success', '', cancel_amount, pricing_details)
			self.log.debug('Split cancelSuccess %s %s' % (trip_id, self.cancellation_dict['details'][0]['pnr']))
		elif cancellation_type.upper() =='FULL':
			self.insert_into_table('Full Cancel Success', '', cancel_amount, pricing_details)
			self.log.debug('Full cancelSuccess %s %s' % (self.cancellation_dict['details'][0]['pnr'], trip_id))
