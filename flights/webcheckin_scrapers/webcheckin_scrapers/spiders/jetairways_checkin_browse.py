import re
import json
import base64
import smtplib
import MySQLdb
import datetime
from ast import literal_eval
from scrapy import signals
from webcheckin_scrapers.utils import *
from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher
from ConfigParser import SafeConfigParser
from scrapy.conf import settings

class JetairwaysCheckinBrowse(Spider):
    name = "jetairwayscheckin_browse"
    start_urls = ['https://www.jetairways.com/EN/IN/planyourtravel/web-check-in.aspx']
    handle_httpstatus_list = [404, 500]

    def __init__(self, *args, **kwargs):
        super(JetairwaysCheckinBrowse, self).__init__(*args, **kwargs)
	self.log = create_logger_obj('jetairways_webcheckin')
	self.check_dict = kwargs.get('jsons', {})
        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('webcheckin', 'IP')
        passwd = db_cfg.get('webcheckin', 'PASSWD')
        user = db_cfg.get('webcheckin', 'USER')
        db_name = db_cfg.get('webcheckin', 'DBNAME')
        self.conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()
	dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()


    def parse(self, response):
	url = 'https://www.jetairways.com/JQueryAddUserControl.aspx'
	sel = Selector(response)
	if isinstance(self.check_dict, dict):
		pass
	else:
		try:
			self.check_dict = eval(self.check_dict)
		except:
			self.check_dict.update({"status":"Failed"})
			status_ =  'dict format is wrong in given inputs'
			self.db_insert(status_)
	if isinstance(self.check_dict, dict):
		setcookie = response.headers.getlist('Set-Cookie')
		self.cookies = {}
		for i in setcookie:
		    i = i.split(';')
		    for j in i:
		        try:key, val = j.split('=', 1)
			except:continue
		        self.cookies[key]=val
		if self.check_dict.get('pnr') and self.check_dict.get('first_name') and self.check_dict.get('last_name') and self.check_dict.get('departure_code') and self.check_dict.get('phone_number'):
			data = {'ClickedControl': 'webcheckinjknew',
			  'PNRNumber': self.check_dict.get('pnr', ''),
			  'FirstName': self.check_dict.get('first_name', ''),
			  'LastName' : self.check_dict.get('last_name', ''),
			  'ddlAirport' : self.check_dict.get('departure_code', ''),
			  'SelType' : 'PNR',
			  'device' : 'desktop',
			  'Source' : 'InnerWebCHK',
			  'src' : 'WEB'}
			yield FormRequest(url, callback=self.parse_next, formdata=data)
		else:
			self.check_dict.update({"status":"Failed"})
			status_ = 'inputs keys in json dict are not specified properly'
			self.db_insert(status_)

    def parse_next(self, response):
	url = re.findall('\$\^(https.*?)\$\^', response.body)
	if not url:
		self.check_dict.update({"status":"Failed"})
		status_ = 'different url pattern for this PNR'
		self.db_insert(status_)
	if url:
		yield Request(url[0], callback=self.parse_again)

    def db_insert(self, status_):
	if not self.check_dict.get("status", ''):
		status_ = 'unexpected error' 
	insert_query = 'insert into  jetairways_webcheckin_status (sk, tripid, airline, status_message, error_message, created_at, modified_at) values(%s,%s,%s,%s,%s,now(),now())  on duplicate key update modified_at=now(), sk=%s, tripid=%s, status_message=%s, error_message=%s'
	values =  (self.check_dict.get('pnr', ''), self.check_dict.get('trip_ref', ''), 'JetAirways', self.check_dict.get('status', 'Failed'), status_, self.check_dict.get('pnr', ''), self.check_dict.get('trip_ref', ''), self.check_dict.get('status', 'Failed'), status_)
	self.cur.execute(insert_query, values)

    def parse_again(self, response):
	sel = Selector(response)
	if 'could not locate your reservation' in response.body.lower():
		self.check_dict.update({"status":"Failed"})
		status_ = 'could not locate your reservation'
		self.db_insert(status_)
	elif 'web check-in for your flight is currently closed' in response.body.lower():
		self.check_dict.update({"status":"Failed"})
		status_ = 'web check-in for your flight is currently closed'
		self.db_insert(status_)
	elif ('already checked in' in response.body.lower()) or ('you are already checked-in' in response.body.lower()):
		self.check_dict.update({"status":"Failed"})
		status_ =  'checked-in already'
		self.db_insert(status_)
	else:
		url = 'https://selfservice.jetairways.com/WCI/wci?execution=e1s1&_eventId_continue=foo'
		pax_list_website = sel.xpath('//table[@id="borderTable"]/tbody/tr[@class="tblGridAlternate"]')
		pax_list = len(pax_list_website)
		data = []
		for idx in range(pax_list):
		    guest_update = "guestUpdates%s" % idx
		    passenger_email = ''.join(sel.xpath('//input[@id="%s.passenger.email"]/@value' % guest_update).extract())
		    if not passenger_email:
			passenger_email = self.check_dict.get('email', '')
		    passenger_phnumber = ''.join(sel.xpath('//input[@id="%s.passenger.phNumber"]/@value' % guest_update).extract())
		    if not passenger_phnumber:
			passenger_phnumber = self.check_dict.get('phone_number', '')
		    passenger_gender = ''.join(sel.xpath('//input[contains(@id, "%s.guestType")][@checked]/@value' % guest_update).extract())
		    if not passenger_gender:
			passenger_gender = self.check_dict.get('gender', '')
		    passenger_toupdate = ''.join(sel.xpath('//input[@name="guestFqtvUpdates[%s].toUpdate"]/@value' % (0)).extract())
		    passenger_fqtvinfo = ''.join(sel.xpath('//input[@id="guestFqtvUpdates%s.fqtvInfo.plan"]/@value' % idx).extract())
		    passenger_fqtvinfor_number = ''.join(sel.xpath('//input[@id="guestFqtvUpdates%s.fqtvInfo.number"]/@value' % idx).extract())
		    guest_upd1 = ''.join(sel.xpath('//input[@name="guestUpdates[%s].selected"]/@value' % idx).extract())
		    if not guest_upd1:
			guest_upd1 = 'true'
		    guest_upd2 = ''.join(sel.xpath('//input[@name="_guestUpdates[%s].selected"]/@value' % idx).extract())
		    if not guest_upd2:
			guest_upd2 = 'on'
		    jet_pr = ''
		    if pax_list > 1 and idx == 0:
			jet_pr = ''
			data.extend([("toCheckinAll" , "true"),
				("_toCheckinAll", "on"),
			])
		    else:
			jet_pr = 'JetPrivilege'
		    data.extend([
			('guestUpdates[%s].selected'%idx, guest_upd1),
			('_guestUpdates[%s].selected'%idx, guest_upd2),
			('guestUpdates[%s].passenger.email'%idx, passenger_email),
			('guestUpdates[%s].passenger.phNumber'%idx, passenger_phnumber),
			('guestUpdates[%s].guestType'%idx, passenger_gender),
			('guestFqtvUpdates[%s].toUpdate'%idx, passenger_toupdate),
			('guestFqtvUpdates[%s].fqtvInfo.plan'%idx, passenger_fqtvinfo),
			('guestFqtvUpdates[%s].fqtvInfo.number'%idx, passenger_fqtvinfor_number),
			data.append(('null', jet_pr))
		    ])
		data = filter(None, data)
		yield FormRequest(url, callback=self.parse_meal, formdata=data, meta = {"pax_list":pax_list})

    def parse_meal(self, response):
	pax_list = response.meta.get('pax_list', '')
	sel = Selector(response)
	url = 'https://selfservice.jetairways.com/WCI/wci?execution=e1s2&_eventId_continue=true'
	form_data = []
	for idx, pa in enumerate(range(pax_list)):
		form_data.extend([
 		 ('null', 'No Preference'),
		  ('guestUpdates[%s].specialMealRequest.name' % idx, 'No Preference'),
		])
	yield FormRequest(url, callback=self.parse_flight, formdata=form_data, meta = {"pax_list":pax_list})

    def parse_flight(self, response):
	pax_list = response.meta.get('pax_list', '')
	sel = Selector(response)
	data = [
		  ('acknowledge', 'on'),
	]
	url = 'https://selfservice.jetairways.com/WCI/wci?execution=e1s3&_eventId_continue=foo'
	yield FormRequest(url, callback=self.parse_seat_select, formdata=data, meta = {"pax_list":pax_list})

    def parse_seat_select(self, response):
	pax_list = response.meta.get('pax_list', '')
        sel = Selector(response)
	seat_check = ''.join(sel.xpath('//input[@id="unassignedSeat"]/@value').extract())
	if 'true' in seat_check:
		self.check_dict.update({"status":"Failed"})
		status_ = 'Seat is not selected'
		self.db_insert(status_)
	else:
		form_data = {}
		form_nodes = sel.xpath('//input[contains(@name, "exitInfos")]')
		for form in form_nodes:
			key_ = ''.join(form.xpath('./self::input/@name').extract())
			value_ = ''.join(form.xpath('./self::input/@value').extract())
			form_data.update({key_:value_})
		form_nodes_bulk = sel.xpath('//input[contains(@name, "bulkheadInfos")]')
		for form_b in form_nodes_bulk:
			key_b = ''.join(form_b.xpath('./self::input/@name').extract())
			value_b = ''.join(form_b.xpath('./self::input/@value').extract())
			form_data.update({key_b:value_b})
		url = 'https://selfservice.jetairways.com/WCI/wci?execution=e1s4&_eventId_continue=foo'
		yield FormRequest(url, callback=self.parse_continue_to, formdata=form_data, meta = {"pax_list":pax_list})

    def parse_continue_to(self, response):
	sel = Selector(response)
	pax_list = response.meta.get('pax_list', '')
        if 'you have successfully checked in' in response.body.lower():
                status_ = 'checked_in_successfully'
                self.check_dict.update({"status":"success"})
                self.db_insert(status_)
	if self.check_dict.get("status", "") != 'success':
		url = "https://selfservice.jetairways.com/WCI/wci?execution=e1s5&_eventId_continue=foo&citrusTransactionResponse={%22firstName%22:%22null%22,%22lastName%22:%22null%22,%22transactionId%22:%22null%22,%22amount%22:%22null%22,%22email%22:%22null%22,%22mobileNo%22:%22null%22,%22txnDateTime%22:%22null%22,%22originalAmount%22:%22null%22,%22txStatus%22:%22null%22,%22cardType%22:%22null%22,%22addressZip%22:%22null%22,%22addressCountry%22:%22null%22,%22addressState%22:%22null%22,%22addressCity%22:%22null%22,%22addressStreet2%22:%22null%22,%22addressStreet1%22:%22null%22,%22txGateway%22:%22null%22,%22signature%22:%22null%22,%22pgTxnNo%22:%22null%22,%22issuerCode%22:%22null%22,%22paymentMode%22:%22null%22,%22adjustedAmount%22:%22null%22,%22transactionAmount%22:%22null%22,%22maskedCardNumber%22:%22null%22,%22cardHolderName%22:%22null%22,%22requestedCurrency%22:%22null%22,%22requestedAmount%22:%22null%22,%22dccCurrency%22:%22null%22,%22dccAmount%22:%22null%22,%22exchangeRate%22:%22null%22,%22dccOfferId%22:%22null%22,%22authIdCode%22:%22null%22,%22expiryMonth%22:%22null%22,%22expiryYear%22:%22null%22,%22encryptedCardNumber%22:%22null%22}"
		yield Request(url, callback=self.parse_select_boarding, method='POST', meta = {"pax_list":pax_list})

    def parse_select_boarding(self, response):
	pax_list = response.meta.get('pax_list', '')
	sel = Selector(response)
	url = "https://selfservice.jetairways.com/WCI/wci?execution=e1s6&_eventId_continue=true"
	data = []
        if 'you have successfully checked in' in response.body.lower():
                status_ = 'checked_in_successfully'
                self.check_dict.update({"status":"success"})
                self.db_insert(status_)
	if self.check_dict.get("status","") != 'success':
		for ia in range(pax_list):
			eema_ad = ''.join(sel.xpath('//input[@name="boardingPassUpdates[%s].emailAddress"]/@value' % ia).extract())
			data.extend ([
			  ('_boardingPassUpdates[%s].print' % ia, 'on'),
			  ('boardingPassUpdates[%s].send' % ia, 'true'),
			  ('_boardingPassUpdates[%s].send' % ia, 'on'),
			  ('boardingPassUpdates[%s].emailAddress' % ia, eema_ad),
			])	
			if ia == 0:
				data.extend ([('boardingPassUpdates[0].selected', 'true') ])
		yield FormRequest(url, callback=self.parse_continue_to, formdata=data, meta = {"pax_list":pax_list})
		
    def parse_final(self, response):
	if 'you have successfully checked in' in response.body.lower():
		status_ = 'checked_in_successfully'
		self.check_dict.update({"status":"success"})
		self.db_insert(status_)
