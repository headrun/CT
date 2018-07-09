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
from spicejetsplit_cancellation_utils import *

from scrapy.conf import settings

import sys
sys.path.append(settings['ROOT_PATH'])

from root_utils import Helpers

_cfg = SafeConfigParser()
_cfg.read(settings['BOOK_PCC_PATH'])


class SpicejetsplitCancellationBrowse(Spider, SGCancel, Helpers):
    name = "spicejetsplit_cancallation_browse"
    start_urls = ["https://book.spicejet.com/LoginAgent.aspx"]

    def __init__(self, *args, **kwargs):
        super(SpicejetsplitCancellationBrowse, self).__init__(*args, **kwargs)
        self.source_name = 'spicejet'
        pnr_no = ''
        self.new_pnr = ''
        self.cancel = False
        self.log = create_logger_obj('spicejet_cancellation')
        self.cancellation_dict = ast.literal_eval(kwargs.get('jsons', '{}'))
        self.insert_query = 'insert into spicejet_cancellation_report(sk, airline, pnr, new_pnr, pcc, flight_number, error_message, status, cancel_amount, pricing_details, request_input, aux_info, created_at, modified_at) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now()) on duplicate key update modified_at=now(), error_message=%s, pricing_details=%s, request_input=%s, cancel_amount=%s, status=%s, new_pnr=%s'
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
		self.insert_into_table('', 'Empty request')
    		return
    	login_data_list = []
    	if len(self.cancellation_dict['details']) == 2:
		self.insert_into_table('', 'Multiple PNR cancellation not possible')
		self.log.debug('Multiple PNR cancellation not possible')
    		return

	pcc_name = self.get_pcc_name()#'spicejet_BOMCL23479'
	self.log.debug('Login PCC: %s' % pcc_name)
    	cancellation_type = self.cancellation_dict['details'][0].get('cancellation_type', '').get('type', '')
    	pnr_no = self.cancellation_dict['details'][0].get('pnr', '')
    	self.log.debug("Search for PNR: %s" % pnr_no)
	if cancellation_type.upper() not in ['PARTIAL','FULL']:
		self.insert_into_table('', 'Cancellation type is wrong')
		self.log.debug('Cancellation type is wrong')
    		return
	if len(self.cancellation_dict['details'][0]['all_segment_details']) != len(self.cancellation_dict['details'][0]['cancelled_segment_details']):
                self.insert_into_table('', 'Failing as Partial segment cancellation')
                self.log.debug('Partial segment cancellation error')
                return
        sel = Selector(response)
        view_state = ''.join(sel.xpath('//input[@id="viewState"]/@value').extract())
        login_data_list.append(('__VIEWSTATE', view_state))
	try:
		user_name = _cfg.get(pcc_name, 'username')
		user_psswd = _cfg.get(pcc_name, 'password')
	except:
		self.insert_into_table('',"PCC %s not available for scrapper" % pcc_name)
		self.log.debug('PCC not avaialble for scrapper')
		return
	self.log.debug('Login using %s' % user_name)
        login_data_list.append(('ControlGroupLoginAgentView$AgentLoginView$ButtonLogIn', 'Log In'))
        login_data_list.append(('ControlGroupLoginAgentView$AgentLoginView$TextBoxUserID', str(user_name)))
        login_data_list.append(('ControlGroupLoginAgentView$AgentLoginView$PasswordFieldPassword', str(user_psswd)))
        yield FormRequest('https://book.spicejet.com/LoginAgent.aspx', \
                formdata=login_data_list, callback=self.parse_next, meta={'pnr_no' : pnr_no, 'user_name' : user_name})

    def parse_next(self, response):
    	sel = Selector(response)
    	pnr_no = response.meta['pnr_no']
    	if response.status == 200:
    		url = 'https://book.spicejet.com/BookingList.aspx'
    		return Request(url, callback=self.parse_search, dont_filter=True, meta={'pnr_no' : pnr_no})
    	else:
            self.send_mail("SpiceJet Unable to login on Login ID %s" % response.meta.get('username', '') , 'Scrapper Unable to login on Login ID', airline='Spicejet', config='splitcancel', receiver='spicejet_common')
	    self.insert_into_table('', 'Unable to login on LOGIN ID %s' % response.meta.get('username', ''))

    def parse_search(self, response):
    	sel = Selector(response)
    	pnr_no = response.meta.get('pnr_no', '')
    	cancel = response.meta.get('cancel', False)#Change it  to False after checks###
        view_state = ''.join(sel.xpath('//input[@id="viewState"]/@value').extract())
	cancellation_type = self.cancellation_dict['details'][0].get('cancellation_type', '').get('type', '')
        search_data_list = {}
        search_data_list.update({'__VIEWSTATE': str(view_state)})
        #send one meta here for differentiating split and cancel
        if pnr_no:
			agp_key = ''.join(sel.xpath('//input[@id="AGPKey"]/@value').extract())
			agp_returnurl = ''.join(sel.xpath('//input[@id="AGPRETURNURL"]/@value').extract())
			qp_Key = ''.join(sel.xpath('//input[@id="QPKey"]/@value').extract())
			reports_key = ''.join(sel.xpath('//input[@id="ReportsKey"]/@value').extract())
			search_data_list.update({'ControlGroupBookingListView$BookingListBookingListView$TextBoxKeyword': pnr_no})
			search_data_list.update({'__EVENTTARGET' : 'ControlGroupBookingListView$BookingListBookingListView$LinkButtonFindBooking'})
			search_data_list.update({'ControlGroupBookingListView$BookingListBookingListView$Search' : 'ForAgency'})
			search_data_list.update({'ControlGroupBookingListView$BookingListBookingListView$DropDownListTypeOfSearch' : '1'})
			search_data_list.update({'AGPKey' : agp_key})
			search_data_list.update({'AGPRETURNURL' : agp_returnurl})
			search_data_list.update({'QPKey' : qp_Key})
			search_data_list.update({'ReportsKey' : reports_key})
			search_data_list.update({'pageToken' : ''})
			search_data_list.update({'__EVENTARGUMENT' : ''})
			url = "https://book.spicejet.com/BookingList.aspx"
			if cancellation_type.upper() =='PARTIAL':
				return FormRequest(url, formdata=search_data_list, callback=self.parse_pnr_details, meta={'pnr_no' : pnr_no, 'search_data_list': search_data_list, 'cancel' : cancel}, dont_filter=True)
			elif cancellation_type.upper() =='FULL':
				return FormRequest(url, formdata=search_data_list, callback=self.parse_pnr_details, meta={'pnr_no' : pnr_no, 'search_data_list': search_data_list, 'cancel' : 'True'}, dont_filter=True)
			#response.xpath('//table[@id="currentTravelTable"]//td[4]/text()').extract()

    def parse_pnr_details(self, response):
    	sel = Selector(response)
    	pnr_no = response.meta.get('pnr_no', '')
    	cancel = response.meta.get('cancel', '')
    	#capture that split or cancel thing, not here, next function
    	search_data_list = response.meta['search_data_list']
    	view_state = ''.join(sel.xpath('//input[@id="viewState"]/@value').extract())
    	eventarg = 'Edit:%s' % pnr_no
	self.log.debug("%s editing..." % pnr_no)
    	search_data_list.update({'__EVENTARGUMENT' : eventarg})
        search_data_list.update({'__VIEWSTATE': str(view_state)})
        search_data_list.update({'__EVENTTARGET' : 'ControlGroupBookingListView$BookingListBookingListView'})
    	url = "https://book.spicejet.com/BookingList.aspx"
    	return FormRequest(url, callback=self.parse_modify, dont_filter=True, formdata=search_data_list, meta={'pnr_no' : pnr_no, 'cancel' : cancel})

    def parse_modify(self, response):
    	sel = Selector(response)
    	pnr_no = response.meta.get('pnr_no', '')
    	cancel = response.meta.get('cancel', '')
    	#self.cancel =True#Hardcoding now for testing
    	payment_status = ''.join(sel.xpath('//td[@class="width-payment-status"]//strong/text()').extract())
    	pnr_status = ''.join(sel.xpath('//td[@class="width-pnr-status"]//strong/text()').extract())
    	if payment_status.upper() != 'PAID':
		self.log.debug("Payment status is not paid, it is %s" % payment_status)
		self.insert_into_table('', "Payment status is not paid, it is %s" % payment_status)
    		return
    	if pnr_status.upper() == 'CANCELLED':
		self.log.debug("Pnr status is %s" % pnr_status)
		self.insert_into_table('', "Pnr status  is %s" % pnr_status)
    		return
    	booking_detail = sel.xpath('//table[@id="bookingDetail"]//tr/td/span//strong/text()').extract()
    	if booking_detail:
    		if booking_detail[0] != pnr_no:
			self.log.debug("Does not match the given PNR")
	                self.insert_into_table('', "Does not match the given PNR" )
    			return
    	journey_details = sel.xpath('//table[@id="flight-journey-detail"]//tr/td/text()').extract()
    	journey_check = self.journey_check(journey_details)
    	if journey_check:
		self.log.debug("Journey details mismatch")
		self.insert_into_table('', "Journey details mismatch" )
    		return
    	passenger_details = sel.xpath('//table[@class="tgrid-MMB hide-mobile passenger-information"]//tr[@class="passenger-info-border"]')
    	person_present = False
    	all_pax = [' '.join(i[1:]).title().strip() for i in self.cancellation_dict['details'][0]['all_pax_details']]
    	all_pax_len = len(all_pax)
	if all_pax_len != len(set(all_pax)):
            self.log.debug('Duplicate passengers(gender title)')
            self.insert_into_table(mesg='', err="Duplicate passengers - gender title")
            return
    	passengers_len = len(passenger_details)
	if not cancel or self.cancellation_dict['details'][0].get('cancellation_type', '').get('type', '').upper()=='FULL':
	    	if all_pax_len != passengers_len:
			self.log.debug("length of passengers are not same")
	                self.insert_into_table('', "length of passengers are not same %s %s" % (all_pax_len, passengers_len) )
			return
	    	counter = 0
	    	for j in all_pax:
		    	for i in passenger_details:
		    		name = ''.join(i.xpath('./td[@class="passenger-info-name"]/text()').extract()).replace('  ', ' ').strip().title()
				name = ' '.join(name.split()[1:])
		    		if name == j:
		    			counter += 1
		    			break

		    		self.log.debug('%s %s' % (name,  j))
		if counter != all_pax_len:
			self.log.debug("not matching names of passengers")
                        self.insert_into_table('', "not matching names of passengers")
			return

    	split_booking_url = ''.join(sel.xpath('//table[@id="mmb-options-list"]//a[contains(text(), "Split Booking")]/@href').extract())
    	#if split and split url go with this yield else go with cancel yield
    	if cancel:
    		cancel_data_list = {}
    		view_state = ''.join(sel.xpath('//input[@id="viewState"]/@value').extract())
		agp_key = ''.join(sel.xpath('//input[@id="AGPKey"]/@value').extract())
		agp_returnurl = ''.join(sel.xpath('//input[@id="AGPRETURNURL"]/@value').extract())
		qp_Key = ''.join(sel.xpath('//input[@id="QPKey"]/@value').extract())
		reports_key = ''.join(sel.xpath('//input[@id="ReportsKey"]/@value').extract())
		cancel_data_list.update({'AGPKey' : agp_key})
		cancel_data_list.update({'AGPRETURNURL' : agp_returnurl})
		cancel_data_list.update({'QPKey' : qp_Key})
		cancel_data_list.update({'ReportsKey' : reports_key})
		cancel_data_list.update({'pageToken' : ''})
		cancel_data_list.update({'__EVENTARGUMENT' : ''})
		cancel_data_list.update({'__EVENTTARGET' : 'ControlGroupChangeItineraryView$ChangeControl$LinkButtonCancelBooking',\
		'ControlGroupChangeItineraryView$ChangeControl$hiddenFieldButtonClick' : ''})
		cancel_data_list.update({'__VIEWSTATE': str(view_state)})
		url = 'https://book.spicejet.com/ChangeItinerary.aspx'
		if self.cancellation_dict['details'][0].get('cancellation_type', '').get('type', '').upper()=='FULL':
                        self.log.debug("Cancel start for Full PNR")
                elif self.cancellation_dict['details'][0].get('cancellation_type', '').get('type', '').upper()=='PARTIAL':
                        self.log.debug("Cancel start for split PNR")
		return FormRequest(url, callback=self.parse_cancel_start, formdata=cancel_data_list, meta={'pnr_no' : pnr_no})
	elif split_booking_url:
		split_booking_url = 'https://book.spicejet.com/' + split_booking_url
    		return Request(split_booking_url, callback=self.parse_split_book, meta={'pnr_no' : pnr_no})
	elif not self.cancel and not split_booking_url:
			self.log.debug("Split tab not available")
                        self.insert_into_table('', "Split tab not available")
			#need to write to db and then send as response
	else:
			self.log.debug("Developer to check this case")
                        self.insert_into_table('', "Alert, something failed unexpected")

    def parse_split_book(self, response):
		#UFKQ7U
		#//span[@class="SpiltPNRSubHeader" and contains(text(), "New")]/../text()
		#pnrs_list = //div[@id="SplitPNRresult"]/table//tr/th/text()
		sel = Selector(response)
		pnr_no = response.meta.get('pnr_no', '')
		table_contents = sel.xpath('//table[@class="split-main-table"]//tr//td//text()').extract()
		split_pax_nos_url = self.findall_splits(table_contents)
		#[u'MR. Monideep Roychowdhury (ADULT,Male)', u'109855786', u'MS. Moumita Majumder (ADULT,Female)', u'109855787']
		#check here if properly coming or not
		if not split_pax_nos_url:
			self.log.debug("Cannot split due to parsing name from site, Regex issue")
                        self.insert_into_table('', "Cannot split due to parsing name from site")
			return
		#Should not allow to split please for live PNRs
		return FormRequest(split_pax_nos_url, callback=self.parse_ajax_receive, meta={'pnr_no' : pnr_no})

    def parse_ajax_receive(self, response):
		pnr_no = response.meta.get('pnr_no', '')
		if 'success' in response.body:
			self.log.debug("Split success")
		return Request('https://book.spicejet.com/ChangeItinerary.aspx', callback=self.parse_ajax_after, dont_filter=True, meta={'pnr_no': pnr_no})


    def parse_ajax_after(self, response):
		#Capture the PNR here and then  yield it to parse_search for cancelling along with "cancel" : True meta
		#Here change the self.pnr to this new PNR captured
		sel = Selector(response)
		pnr_no= response.meta.get('pnr_no',  '')
		open('somes.html', 'w').write(response.body)
		url = 'https://book.spicejet.com/BookingList.aspx'
		pnr_no = ''.join(sel.xpath('//div[@id="SplitPNRresult"]//table//tr/th[2]/text()').extract())#'C6Q6XC'#'XE65PN'#<>C6Q6XC'
		meta={'cancel' : True, 'pnr_no' : pnr_no}
		self.log.debug("New PNR for cancel: %s" % pnr_no)
		self.new_pnr = pnr_no
		return Request(url, callback=self.parse_search, meta=meta, dont_filter=True)
		#yield the new pnr no to self.parse_search
		#(Pdb) resp = requests.get('https://book.spicejet.com/ChangeItinerary.aspx')


    def parse_cancel_start(self, response):
		sel = Selector(response)
		cancel_data_list = {}
		view_state = ''.join(sel.xpath('//input[@id="viewState"]/@value').extract())
		agp_key = ''.join(sel.xpath('//input[@id="AGPKey"]/@value').extract())
		agp_returnurl = ''.join(sel.xpath('//input[@id="AGPRETURNURL"]/@value').extract())
		qp_Key = ''.join(sel.xpath('//input[@id="QPKey"]/@value').extract())
		reports_key = ''.join(sel.xpath('//input[@id="ReportsKey"]/@value').extract())
		cancel_data_list.update({'AGPKey' : agp_key})
		cancel_data_list.update({'AGPRETURNURL' : agp_returnurl})
		cancel_data_list.update({'QPKey' : qp_Key})
		cancel_data_list.update({'ReportsKey' : reports_key})
		cancel_data_list.update({'pageToken' : ''})
		cancel_data_list.update({'__EVENTARGUMENT' : ''})
		cancel_data_list.update({'__EVENTTARGET' : 'ControlGroupChangeItineraryView$ChangeControl$LinkButtonCancelBooking',\
		'ControlGroupChangeItineraryView$ChangeControl$hiddenFieldButtonClick' : ''})
		cancel_data_list.update({'ControlGroupChangeItineraryView$BookingDetailChangeItineraryView$BookingDetailsFinalizebuttionView$ButtonFinalize' : 'Confirm Cancellation'})
		cancel_data_list.update({'__VIEWSTATE': str(view_state)})
		yield FormRequest(response.url, callback=self.parse_cancel_confirm, formdata=cancel_data_list)

    def parse_cancel_confirm(self, response):
		sel = Selector(response)
		amount_cancel =  ''.join(sel.xpath('//div[@id="AgencyAccount_AG_PaymentSummary"]/table//tr[2]/td/text()').extract())
		if amount_cancel:
			amount_cancel = ''.join(re.findall('\d+.\d+', amount_cancel.replace(',', '')))
		agency_account = ''.join(sel.xpath('//select[@id="AgencyAccount_RefundPaymentMethodCode"]/option/@value').extract())
		post_data_dict = {}
		view_state = ''.join(sel.xpath('//input[@id="viewState"]/@value').extract())
		agp_key = ''.join(sel.xpath('//input[@id="AGPKey"]/@value').extract())
		agp_returnurl = ''.join(sel.xpath('//input[@id="AGPRETURNURL"]/@value').extract())
		qp_Key = ''.join(sel.xpath('//input[@id="QPKey"]/@value').extract())
		reports_key = ''.join(sel.xpath('//input[@id="ReportsKey"]/@value').extract())
		post_data_dict.update({'ATMCumDebit': 'SMP_DIRECTD'})
		post_data_dict.update({'ATMDEBITGroup' : 'MAESTRO'})
		post_data_dict.update({'CONTROLGROUPPAYMENTBOTTOM$ButtonSubmit' : 'Confirm Refund'})
		post_data_dict.update({'CONTROLGROUPPAYMENTBOTTOM$ControlGroupPaymentInputViewPaymentView$AgencyAccount_AG_AMOUNT' : amount_cancel})
		post_data_dict.update({'AGPKey' : agp_key})
		post_data_dict.update({'AGPRETURNURL' : agp_returnurl})
		post_data_dict.update({'CONTROLGROUPPAYMENTBOTTOM$ControlGroupPaymentInputViewPaymentView$DropDownListPreviousPayments' : agency_account})
		post_data_dict.update({'DropDownListPaymentMethodCode' : 'ExternalAccount:MC'})
		post_data_dict.update({'DropDownListPaymentMethodCode' : 'PrePaid:IB'})
		post_data_dict.update({'DropDownListPaymentMethodCode' : 'AgencyAccount:AG'})
		post_data_dict.update({'NetBanking' : ''})
		post_data_dict.update({'PrePaid_HB' : ''})
		post_data_dict.update({'PromoCodePaymentView$TextBoxAccountNumber' : ''})
		post_data_dict.update({'PromoCodePaymentView$TextBoxPromoCode' : ''})
		post_data_dict.update({'QPKey' : qp_Key})
		post_data_dict.update({'ReportsKey' : reports_key})
		post_data_dict.update({'TextBoxAMT' : amount_cancel})
		post_data_dict.update({'TextBoxCC::VerificationCode' : ''})
		post_data_dict.update({'WalletMode' : 'WP'})
		post_data_dict.update({'__EVENTARGUMENT' : ''})
		post_data_dict.update({'__EVENTTARGET' : ''})
		post_data_dict.update({'__VIEWSTATE' : str(view_state)})
		post_data_dict.update({'pageToken' : ''})
		post_data_dict.update({'termcondition' : 'on'})
		url = 'https://book.spicejet.com/Payment.aspx'
		yield FormRequest(url, callback=self.parse_post_cancel, formdata=post_data_dict, meta={'amount_cancel' : amount_cancel})

    def parse_post_cancel(self, response):
		#here wait.aspx is the url
		amount_cancel = response.meta.get('amount_cancel', '')
		url = 'https://book.spicejet.com/ChangeItinerary.aspx'
		yield Request(url,  callback=self.parse_cancel_complete, dont_filter=True, meta={'amount_cancel' : amount_cancel})

    def parse_cancel_complete(self, response):
		sel = Selector(response)
		open('SGSplit_final_%s.html' % self.cancellation_dict.get('trip_ref', ''), 'w').write(response.body)
		cancel_amount = response.meta.get('amount_cancel', '')
		cancel_status = ''.join(sel.xpath('//table[@id="bookingDetail"]//td[@class="width-pnr-status"]//strong/text()').extract())
		confirmation_details = [i.strip() for i in sel.xpath('//table[@id="bookingDetail"]//td//text()').extract()]
		confirmation_dict = {item : confirmation_details[index+1] for index, item in enumerate(confirmation_details) if index % 2 == 0}
		payment_details = filter(None, [i.replace(u'\xa0', '').replace('-', '').strip() for i in sel.xpath('//div[@id="priceHideForModes"]//table[@class="tgrid-MMB"]/tr//text()').extract()])
		payment_dict = {item : payment_details[index+1] for index, item in enumerate(payment_details) if index % 2 == 0}
		extras = sel.xpath('//table[@id="paymentDisplayTable"]//tr//td//text()').extract()
		extra_details = [extras[i:i+4] for i in  range(0,  len(extras), 4)]
		extras_list = []
		for i in extra_details:
			temp= {}
			temp['payment_type'] = inspect.cleandoc(i[0]).replace('\r\n', '')
			temp['acc_no'] = i[1]
			temp['amount'] = i[2]
			temp['status'] = i[3]
			extras_list.append(temp)
		extras_dict = {'extra_details' : extras_list}
		pricing_details = [confirmation_dict, payment_dict, extras_dict]
		cancellation_type = self.cancellation_dict['details'][0].get('cancellation_type', '').get('type', '')
		#write to db that it is success with "sk_index" as sk
		if cancel_status != 'Cancelled':
			if cancellation_type.upper() =='PARTIAL':
				self.insert_into_table('Split done but cancel failed', 'Split success but Cancel Failed', cancel_amount, pricing_details)
			elif cancellation_type.upper() =='FULL':
				self.insert_into_table('cancel failed', 'Cancel Failed', cancel_amount, pricing_details)
			return
		else:
			if cancellation_type.upper() =='PARTIAL':
				self.insert_into_table('Split and Cancel Success', '', cancel_amount, pricing_details)
			elif cancellation_type.upper() =='FULL':
				self.insert_into_table('Full Cancel Success', '', cancel_amount, pricing_details)
				cancellation_type = self.cancellation_dict['details'][0].get('cancellation_type', '').get('type', '')
