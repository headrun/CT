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
from scrapy.utils.response import open_in_browser
from scrapy_splash import SplashFormRequest
from ConfigParser import SafeConfigParser

from scrapy.conf import settings

class GoAirCheckinBrowse(Spider):
    name = "goairwebcheckin_browse"
    start_urls = ["https://www.goair.in/plan-my-trip/web-check-in/"]
    handle_httpstatus_list = [404, 500]

    def __init__(self, *args, **kwargs):
        super(GoAirCheckinBrowse, self).__init__(*args, **kwargs)
	self.log = create_logger_obj('goair_webcheckin')
	self.check_dict = kwargs.get('jsons', {})
	self.ckeckin_dict = {}
        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('webcheckin', 'IP')
        passwd = db_cfg.get('webcheckin', 'PASSWD')
        user = db_cfg.get('webcheckin', 'USER')
        db_name = db_cfg.get('webcheckin', 'DBNAME')
        self.conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()
	self.insert_query = 'insert into goair_webcheckin_status (sk, tripid, airline, status_message, error_message, created_at, modified_at) values(%s,%s,%s,%s,%s,now(),now())  on duplicate key update modified_at=now(), sk=%s, tripid=%s, status_message=%s, error_message=%s'
	dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()

    def get_http(self, url):
	if 'http' not in url:
	    url = '%s%s'%('https://book.goair.in', url)
	return url

    def insert_into_db(self, input_dict, error):
	pnr = input_dict.get('pnr', '')
	status_message = input_dict.get('status', 'Failed')
	trip_id = input_dict.get('trip_ref', '')
	vals = (pnr, trip_id, 'GoAir', status_message, error, pnr, trip_id, status_message, error)
	self.cur.execute(self.insert_query, vals)

    def parse(self, response):
	sel = Selector(response)
	try: input_dict = eval(self.check_dict)
	except: input_dict = {}
	if input_dict:
	    pnr = input_dict.get('pnr', '').strip()
	    last_name = input_dict.get('last_name', '').strip()
	    email = input_dict.get('email', '').strip()
	    if not email:
		self.insert_into_db(input_dict, 'Email is mandatory')
		return
	else:
	    return
	params = (
 			('rl', pnr),
			('ln', email),
		)
	url = "https://book.goair.in/Booking/Index"
	yield FormRequest(url, callback=self.parse_bookview, formdata=params, method="GET", meta={'input_dict':input_dict})

    def parse_bookview(self, response):
	sel = Selector(response)
	input_dict = response.meta.get('input_dict', '')
        error_msg = ''.join(sel.xpath('//div[@class="error-msg alert alert-error"]//ul//li//text()').extract())
        if 'https://book.goair.in/' == response.url:
            self.insert_into_db(input_dict, normalize(error_msg))
            return
	elif 'InternalError' in response.url:
	    error = 'InternalError from GoAir'
	    self.insert_into_db(input_dict, error)
	    return
	error_text = ''.join(sel.xpath('//div[@class="error-msg alert alert-error"]//text()').extract())
	check_in_url = ''.join(sel.xpath('//div[@class="itin-flight"]/div[@class="itin-sub-header group"]/a/@href').extract())
	checkin_text = ''.join(sel.xpath('//div[@class="itin-flight"]/div[@class="itin-sub-header group"]/a/text()').extract())
	if 'Check-in' not in checkin_text:
	    error = checkin_text
	    self.insert_into_db(input_dict, error)
	    return
	if check_in_url:
	    check_in_url = self.get_http(check_in_url)
	else:
	    error = "CheckIn button not presented"
	    self.insert_into_db(input_dict, error)
	    return
	yield Request(check_in_url, callback=self.parse_checkin, meta={'input_dict':input_dict})

    def parse_checkin(self, response):
	sel = Selector(response)
	input_dict = response.meta.get('input_dict', '')
	table_nodes = sel.xpath('//form[@id="checkInForm"]/table//tr')
	request_token = ''.join(sel.xpath('//form[@id="checkInForm"]/input[@name="__RequestVerificationToken"]/@value').extract())
	pax_check_dict = {}
	for row in table_nodes:
	    sel_id = ''.join(row.xpath('./td[1]//input[@type="checkbox"]/@name').extract())
	    sel_key = ''.join(row.xpath('./td[1]//input[@type="checkbox"]/@value').extract())
	    num_id = ''.join(row.xpath('./td[1]/input/@name').extract())
	    num_key = ''.join(row.xpath('./td[1]/input/@value').extract())
	    if sel_id:
		pax_check_dict[sel_id] = sel_key
		pax_check_dict[num_id] = num_key
	if pax_check_dict:
	    pax_check_dict['__RequestVerificationToken'] = request_token
	else:
	    error = "No Pax presented for webcheckin"
	    self.insert_into_db(input_dict, error)
	    return
	url = 'https://book.goair.in/Checkin/Passengers'
	yield FormRequest(url, callback=self.parse_passengers, formdata=pax_check_dict, meta={'input_dict':input_dict})

    def parse_passengers(self, response):
	sel = Selector(response)
	input_dict = response.meta.get('input_dict', '')
	if 'Confirmation' not in response.url:
	    self.insert_into_db(input_dict, "Failed to navigate Confirmation page")
	    return
	data = [
 		 ('starterCheckInInput.hazmatTerms', 'on'),
	]
	url = 'https://book.goair.in/Checkin/Confirmation'
	yield FormRequest(url, callback=self.parse_confirm, formdata=data, meta={'input_dict':input_dict})
	
    def parse_confirm(self, response):
	sel = Selector(response)
	input_dict = response.meta.get('input_dict', '')
	if 'Seatmap' not in response.url:
	    self.insert_into_db(input_dict, "Failed to navigate Seatmap page")
	    return
	seat_fin_list = []
	seat_key_data = ''.join(sel.xpath('//script/text()[contains(., "viewModel")]').extract())
	data = ''.join(re.findall('.*viewModel = (.*)', seat_key_data))
	json_data = json.loads(normalize(data).strip(';'))
	pax_dict = json_data.get('seatAssignment', {}).get('journeys', [{}])[0].get('seatSegmentKeys', [{}])[0]
	pax_list = pax_dict.get('passengers', [])
	flight_key = pax_dict.get('flightKey', '')
	for lst in pax_list:
	    compartment = lst.get('assignedSeat', {}).get('compartment', '')
	    unit = lst.get('assignedSeat', {}).get('unit', '')
	    deck = lst.get('assignedSeat', {}).get('deck', '')
	    number = lst.get('number', '')
	    if unit:
		key = '%s|%s|%s|%s|%s'%(number, flight_key, deck, compartment, unit)
		seat_fin_list.append(('seatMap.PassengerSeatKeys[%s]'%number, key))
	if seat_fin_list:
	    request_token = ''.join(sel.xpath('//form[@action="/SeatMap/Checkin"]/input[@name="__RequestVerificationToken"]/@value').extract())
	    seat_fin_list.append(('__RequestVerificationToken', request_token))
	else:
	    error = "Seat not selected"
	    self.insert_into_db(input_dict, error)
	    return
	url = 'https://book.goair.in/SeatMap/Checkin'
	yield FormRequest(url, callback=self.parse_extras, formdata=seat_fin_list, meta={'input_dict':input_dict})

    def parse_extras(self, response):
	sel = Selector(response)
	input_dict = response.meta.get('input_dict', '')
	if 'Extras' not in response.url:
	    error = "Seat not selected"
	    self.insert_into_db(input_dict, error)
	data = [
	  ('goAirInsuranceQuote.IsBuyInsurance', 'False'),
	  ('goAirInsuranceQuote.Address.LineOne.Data', ''),
	  ('goAirInsuranceQuote.Address.PostalCode.Data', ''),
	  ('goAirInsuranceQuote.Address.LineTwo.Data', ''),
	  ('goAirInsuranceQuote.Address.City.Data', ''),
	  ('goAirInsuranceQuote.Address.Country.Data', ''),
	  ('goAirInsuranceQuote.Address.EmailAddress.Data', ''),
	]
	url = 'https://book.goair.in/Extras/Checkin'
	yield FormRequest(url, callback=self.parse_webcheckin, formdata=data, meta={'input_dict':input_dict})


    def parse_webcheckin(self, response):
	sel = Selector(response)
	input_dict = response.meta.get('input_dict', '')
	if 'Payment' in response.url:
	    error = "Selected Payment Seats"
	    self.insert_into_db(input_dict, error)
	    return
	if 'Checkin' in response.url:
	    input_dict['status'] = "Success"
	    self.insert_into_db(input_dict, '')
	    return
	else:
	    self.insert_into_db(input_dict, 'Checkin Failed whereas checkin success')
