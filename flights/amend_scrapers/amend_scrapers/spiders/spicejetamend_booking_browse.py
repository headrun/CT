from ast import literal_eval
from collections import OrderedDict
from ConfigParser import SafeConfigParser
import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import MySQLdb
import re
import requests
import smtplib
import ssl
import time
import md5

from scrapy.http import FormRequest
from scrapy.http import Request
from scrapy.spiders import Spider
from scrapy import signals
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher

from amend_scrapers.utils import *
from spicejet_amend_utils import *

from scrapy.conf import settings

import sys
sys.path.append(settings['ROOT_PATH'])

from root_utils import *

_cfg = SafeConfigParser()
_cfg.read(settings['BOOK_PCC_PATH'])


class SpiceJetAmendBrowse(Spider, SpicejetAmendUtils, Helpers):
    name = "spicejet_amendbooking_browse"
    start_urls = ["https://book.spicejet.com/LoginAgent.aspx"]
    handle_httpstatus_list = [404, 500]

    def __init__(self, *args, **kwargs):
        super(SpiceJetAmendBrowse, self).__init__(*args, **kwargs)
        self.request_verification = ''
	self.log = create_logger_obj('amend_booking')
        self.amend_dict = kwargs.get('jsons', {})
        self.proceed_to_book = 0
	self.trip_type = ''
	self.rt_round_amendment = False
	self.ow_amendment = False
	self.rt_amendment = False
        self.price_patt = re.compile('\d+')
        self.log = create_logger_obj('spicejet_amend_booking')
	self.insert_query = 'insert into spicejetamend_booking_report (sk, airline, pnr, flight_number, from_location, to_location, triptype, cleartrip_price, airline_price, status_message, tolerance_amount, oneway_date, return_date, error_message, request_input, price_details, created_at, modified_at) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), sk=%s, airline=%s, pnr=%s, flight_number=%s, from_location=%s, to_location=%s, triptype=%s, cleartrip_price=%s, airline_price=%s, status_message=%s, tolerance_amount=%s, oneway_date=%s, return_date=%s, error_message=%s, request_input=%s, price_details=%s'

        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('amendbooking', 'IP')
        passwd = db_cfg.get('amendbooking', 'PASSWD')
        user = db_cfg.get('amendbooking', 'USER')
        db_name = db_cfg.get('amendbooking', 'DBNAME')
        self.conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)
	

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()

    def insert_values_into_db(self, amend_dict, status_message, error_message):
	request = ast.literal_eval(self.amend_dict)
	sk = request.get('trip_ref', '')
	pnr = amend_dict.get('pnr', '')
	#flight_number = amend_dict.get('flight_no', '')
	flight_number = str(amend_dict.get('new_flight_ids', []))
	from_location = amend_dict.get('origin_code', '')
	to_location = amend_dict.get('destination_code', '')
	triptype = self.trip_type
	cleartrip_price = request.get('cleartrip_price', '')
	indigo_price = amend_dict.get('Total Price', '').strip()
	if ' ' in indigo_price:
	    indigo_price = indigo_price.split(' ')[0].replace(',', '').strip()
	tolerance_amount = amend_dict.get('price_diff', '')
	oneway_date = amend_dict.get('depart_date', '')
	try:
	    if oneway_date:
	        oneway_date = str(datetime.datetime.strptime(oneway_date, '%d %b %Y').date())
	    return_date = amend_dict.get('return_dapart_date', '')
	    if return_date:
	        return_date = str(datetime.datetime.strptime(return_date, '%d %b %Y').date())
	except:
	    oneway_date, return_date = ['']*2
	paxdetails = self.amend_dict
	cancel_details = amend_dict.get('price_dict', {})
	cancel_details['Total Price'] = indigo_price
	booking_details = json.dumps(amend_dict.get('booking_price', {}))
	price_details = json.dumps({'cancel_charges':json.dumps(cancel_details), 'booking_charges':booking_details})
	values = (
		sk, 'SpiceJet', pnr, flight_number, from_location,
		to_location, triptype, cleartrip_price, indigo_price,
		status_message, tolerance_amount, oneway_date, return_date,
		error_message, paxdetails, price_details,
		sk, 'SpiceJet', pnr, flight_number, from_location, to_location,
		triptype, cleartrip_price, indigo_price, status_message, tolerance_amount,
		oneway_date, return_date, error_message, paxdetails, price_details)
	self.cur.execute(self.insert_query, values)

    def parse(self, response):
        print 'Parse function works'
        sel = Selector(response)
	view_state = normalize(''.join(sel.xpath('//input[@id="viewState"]/@value').extract()))
        try:
	    pcc_name, amend_dict, err_msg = self.get_pcc_name()
	except Exception as e:
	    self.insert_values_into_db(self.amend_dict, "Amend Failed", e.message)
        if 'coupon' in pcc_name:
                self.pcc_name =  'spicejet_default'
        if err_msg:
	    self.insert_values_into_db(amend_dict, "Amend Failed", err_msg)
	    self.send_mail("Amend Failed", err_msg, "amend", "SpiceJet", "spicejet_common")
            logging.debug(err_msg)
            return
        try:
		data = [
		  ('__EVENTTARGET', ''),
		  ('__EVENTARGUMENT', ''),
		  ('__VIEWSTATE', view_state),
		  ('pageToken', ''),
		  ('ControlGroupLoginAgentView$AgentLoginView$TextBoxUserID',  _cfg.get(pcc_name, 'username')),
		  ('ControlGroupLoginAgentView$AgentLoginView$PasswordFieldPassword', _cfg.get(pcc_name, 'password')),
		  ('ControlGroupLoginAgentView$AgentLoginView$ButtonLogIn', 'Log In'),
		  ('ControlGroupLoginAgentView$SubAgentLoginView$TextBoxUserID', ''),
		  ('ControlGroupLoginAgentView$SubAgentLoginView$TextBoxSubAgentUserId', ''),
		  ('ControlGroupLoginAgentView$SubAgentLoginView$PasswordFieldPassword', ''),
		]
        except:
		self.insert_values_into_db(amend_dict, "Amend Failed", "PCC %s not available"%pcc_name)
		self.send_mail("Amend Failed", "PCC %s not available"%pcc_name, "amend", "SpiceJet", "spicejet_common")
                logging.debug('PCC not avaialble for scrapper')
                return
        url = 'https://book.spicejet.com/LoginAgent.aspx'
        yield FormRequest(url, callback=self.prase_login, formdata=data, meta={'amend_dict':amend_dict}, dont_filter=True)

    def prase_login(self, response):
        '''
        Login into SpiceJet
        '''
        print 'Login works'
        sel = Selector(response)
	amend_dict = response.meta['amend_dict']
        check_text = ''.join(sel.xpath('//div[@id="smoothmenu1"]//a[@id="MyBookings"]//@href').extract())
	if not check_text:
	    self.insert_values_into_db(amend_dict, "Amend Failed", "Login Failed")
	    self.send_mail("Amend Failed", "Login Failed", "amend", "SpiceJet", "spicejet_common")
            return
	cookies = {}
        request_headers = response.request.headers.get('Cookie', '').split(';')
        for i in request_headers:
            try: key, val = i.split('=', 1)
            except : continue
            cookies.update({key.strip():val.strip()})
        self.cookies = cookies
	pnr = amend_dict.get('pnr', '')
	url = 'https://book.spicejet.com/BookingList.aspx'
	if pnr:
            yield Request(url, callback=self.parse_booking_list, cookies=self.cookies,\
		meta={'amend_dict':amend_dict}, dont_filter=True)
	else:
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR not found")

    def parse_booking_list(self, response):
        '''
        Checking the option for change flight and navigating into change flight page
        '''
        sel = Selector(response)
	amend_dict = response.meta['amend_dict']
	agpkey = ''.join(sel.xpath('//input[@id="AGPKey"]/@value').extract())
	agmbkey = ''.join(sel.xpath('//input[@id="AGMBKey"]/@value').extract())
	agpreturnurl = ''.join(sel.xpath('//input[@id="AGPRETURNURL"]/@value').extract())
	loggedin = ''.join(sel.xpath('//input[@id="ISAGENTLOGGEDIN"]/@value').extract())
	qpkey = ''.join(sel.xpath('//input[@id="QPKey"]/@value').extract())
	reportkey = ''.join(sel.xpath('//input[@id="ReportsKey"]/@value').extract())
	viewstate = ''.join(sel.xpath('//input[@id="viewState"]/@value').extract())
	pnr = amend_dict.get('pnr', '')
	data = [
	  ('__EVENTTARGET', 'ControlGroupBookingListView$BookingListBookingListView$LinkButtonFindBooking'),
	  ('__EVENTARGUMENT', ''),
	  ('__VIEWSTATE', viewstate),
	  ('pageToken', ''),
	  ('AGPKey', agpkey),
	  ('AGPRETURNURL', agpreturnurl),
	  ('AGMBKey', agmbkey),
	  ('ISAGENTLOGGEDIN', loggedin),
	  ('QPKey', qpkey),
	  ('ReportsKey', reportkey),
	  ('ControlGroupBookingListView$BookingListBookingListView$Search', 'ForAgency'),
	  ('ControlGroupBookingListView$BookingListBookingListView$DropDownListTypeOfSearch', '1'),
	  ('ControlGroupBookingListView$BookingListBookingListView$TextBoxKeyword', pnr),
	]
	url = 'https://book.spicejet.com/BookingList.aspx'
	if pnr and agpkey:
	    yield FormRequest(url, callback=self.parse_search_pnr, formdata=data, meta={'amend_dict':amend_dict}, dont_filter=True)
	else:
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR not found")

    def parse_search_pnr(self, response):
        '''
        Selecting amendment route and amend journey date and navigating into flight selection
        '''
        sel = Selector(response)
	amend_dict = response.meta['amend_dict']
	check_pnr = normalize(''.join(sel.xpath('//table[@id="currentTravelTable"]/tbody/tr/td[4]/text()').extract())).strip()
	table_rows = sel.xpath('//table[@id="currentTravelTable"]/tbody/tr/td//a[contains(text(), "Modify")]/@id').extract()
	pnr_status = normalize(''.join(sel.xpath('//table[@id="bookingDetail"]/tbody/tr/td/text()').extract()))
	if check_pnr != amend_dict.get('pnr', ''):
	    print "PNR not found in SpiceJet"
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR details not found in SpiceJet")
	    return
	if len(table_rows) > 1:
	    print "Multiple details found"
	    self.insert_values_into_db(amend_dict, "Amend Failed", "Multiple details found for PNR-%s"%check_pnr)
	    return
	agpkey = normalize(''.join(sel.xpath('//input[@id="AGPKey"]/@value').extract()))
        agmbkey = normalize(''.join(sel.xpath('//input[@id="AGMBKey"]/@value').extract()))
        agpreturnurl = normalize(''.join(sel.xpath('//input[@id="AGPRETURNURL"]/@value').extract()))
        loggedin = normalize(''.join(sel.xpath('//input[@id="ISAGENTLOGGEDIN"]/@value').extract()))
        qpkey = normalize(''.join(sel.xpath('//input[@id="QPKey"]/@value').extract()))
        reportkey = normalize(''.join(sel.xpath('//input[@id="ReportsKey"]/@value').extract()))
        viewstate = normalize(''.join(sel.xpath('//input[@id="viewState"]/@value').extract()))
	event_argument = 'Edit:%s'%amend_dict.get('pnr', '')
	data = [
	  ('__EVENTTARGET', 'ControlGroupBookingListView$BookingListBookingListView'),
	  ('__EVENTARGUMENT', event_argument),
	  ('__VIEWSTATE', viewstate),
	  ('pageToken', ''),
	  ('AGPKey', agpkey),
	  ('AGPRETURNURL', agpreturnurl),
	  ('AGMBKey', agmbkey),
	  ('ISAGENTLOGGEDIN', loggedin),
	  ('QPKey', qpkey),
	  ('ReportsKey', reportkey),
	  ('ControlGroupBookingListView$BookingListBookingListView$Search', 'ForAgency'),
	  ('ControlGroupBookingListView$BookingListBookingListView$DropDownListTypeOfSearch', '1'),
	  ('ControlGroupBookingListView$BookingListBookingListView$TextBoxKeyword', amend_dict.get('pnr', '')),
	]
	url = 'https://book.spicejet.com/BookingList.aspx'
	if agpkey:
	    yield FormRequest(url, callback=self.parse_change_itinerary, formdata=data, meta={'amend_dict':amend_dict}, dont_filter=True)
	else:
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR details not found in SpiceJet")

    def parse_change_itinerary(self, response):
	sel = Selector(response)
	amend_dict = response.meta['amend_dict']
	if 'ChangeItinerary' not in response.url:
	    print "Failed to ChangeItinerary"
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR not have modify option")
	    return
	pnr_status = ''.join(sel.xpath('//table[@id="bookingDetail"]//tr/td/span[contains(text(), "PNR Status")]//text()').extract())
	if 'Cancelled' in pnr_status:
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR got Cancelled")
	    return
	agpkey = normalize(''.join(sel.xpath('//input[@id="AGPKey"]/@value').extract()))
        agmbkey = normalize(''.join(sel.xpath('//input[@id="AGMBKey"]/@value').extract()))
        agpreturnurl = normalize(''.join(sel.xpath('//input[@id="AGPRETURNURL"]/@value').extract()))
        loggedin = normalize(''.join(sel.xpath('//input[@id="ISAGENTLOGGEDIN"]/@value').extract()))
        qpkey = normalize(''.join(sel.xpath('//input[@id="QPKey"]/@value').extract()))
        reportkey = normalize(''.join(sel.xpath('//input[@id="ReportsKey"]/@value').extract()))
        viewstate = normalize(''.join(sel.xpath('//input[@id="viewState"]/@value').extract()))
	data = [
	  ('__EVENTTARGET', 'ControlGroupChangeItineraryView$ChangeControl$LinkButtonChangeFlights'),
	  ('__EVENTARGUMENT', ''),
	  ('__VIEWSTATE', viewstate),
	  ('pageToken', ''),
	  ('AGPKey', agpkey),
	  ('AGPRETURNURL', agpreturnurl),
	  ('AGMBKey', agmbkey),
	  ('ISAGENTLOGGEDIN', loggedin),
	  ('QPKey', qpkey),
	  ('ReportsKey', reportkey),
	  ('ControlGroupChangeItineraryView$ChangeControl$hiddenFieldButtonClick', ''),
	]
	url = 'https://book.spicejet.com/ChangeItinerary.aspx'
	if agpkey:
	    yield FormRequest(url, callback=self.parse_search_change, formdata=data, meta={'amend_dict':amend_dict}, dont_filter=True)
	else:
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR not have modify option")

    def parse_search_change(self, response):
	sel = Selector(response)
	amend_dict = response.meta['amend_dict']
	if 'SearchChange' not in response.url:
            self.insert_values_into_db(amend_dict, "Amend Failed", "Response timeout from SpiceJet")
            return
	agpkey = normalize(''.join(sel.xpath('//input[@id="AGPKey"]/@value').extract()))
        agmbkey = normalize(''.join(sel.xpath('//input[@id="AGMBKey"]/@value').extract()))
        agpreturnurl = normalize(''.join(sel.xpath('//input[@id="AGPRETURNURL"]/@value').extract()))
        loggedin = normalize(''.join(sel.xpath('//input[@id="ISAGENTLOGGEDIN"]/@value').extract()))
        qpkey = normalize(''.join(sel.xpath('//input[@id="QPKey"]/@value').extract()))
        reportkey = normalize(''.join(sel.xpath('//input[@id="ReportsKey"]/@value').extract()))
        viewstate = normalize(''.join(sel.xpath('//input[@id="viewState"]/@value').extract()))

	self.trip_type = self.get_trip_type(amend_dict)
        self.rt_round_amendment, self.ow_amendment, self.rt_amendment = self.get_amend_type(amend_dict)
        search_keys_dict = self.get_segment_details(amend_dict)

        ow_depart_date = search_keys_dict.get('amd_ow_depature_date', '')
        ori_return_dep_date = search_keys_dict.get('rt_depature_date', '')
        return_dapart_date = search_keys_dict.get('amd_rt_depature_date', '')
	origin = search_keys_dict.get('origin', '')
	dest = search_keys_dict.get('destination', '')
	rt_origin = search_keys_dict.get('rt_origin', '')
	rt_dest = search_keys_dict.get('rt_dest', '')
	ow_amend_origin = search_keys_dict.get('ow_amend_origin', '')
        ow_amend_dest = search_keys_dict.get('ow_amend_dest', '')
        rt_amend_origin = search_keys_dict.get('rt_amend_origin', '')
        rt_amend_dest = search_keys_dict.get('rt_amend_dest', '')
	request_origin = amend_dict.get('origin', '')
	request_destination = amend_dict.get('destination', '')
	if self.ow_amendment:
	    if  ow_amend_origin != request_origin :
	        print "Segments amend not handled"
		self.insert_values_into_db(amend_dict, "Amend Failed", "Segments amend not acceptable")
	        return
	    if  ow_amend_dest != request_destination:
		print "Segments amend not handled"
		self.insert_values_into_db(amend_dict, "Amend Failed", "Segments amend not acceptable")
		return
	if self.rt_amendment or self.rt_round_amendment:
	    if rt_amend_origin != request_destination:
		print "Segments amend not handled"
		self.insert_values_into_db(amend_dict, "Amend Failed", "Segments amend not acceptable")
                return
	    if rt_amend_dest != request_origin:
	        print "Segments amend not handled"
		self.insert_values_into_db(amend_dict, "Amend Failed", "Segments amend not acceptable")
	        return
	if ow_depart_date:
	    try:
		ow_year_month, ow_day = self.get_date_format(ow_depart_date)
	    except:
		ow_format = datetime.datetime.strptime(ow_depart_date, '%d-%b-%y')
		ow_year_month = '%s-%s'%(ow_format.year, ow_format.month)
		ow_day = str(ow_format.day)
	else:
	    ow_year_month, ow_day = ['']*2
	if return_dapart_date:
	    try:
		rt_year_month, rt_day = self.get_date_format(return_dapart_date)
	    except:
		rt_format = datetime.datetime.strptime(return_dapart_date, '%d-%b-%y')
                rt_year_month = '%s-%s'%(rt_format.year, rt_format.month)
                rt_day = str(rt_format.day)
	else:
	    rt_year_month, rt_day = ['']*2
	
        amend_dict.update({
		'origin_code':origin,
		'destination_code':dest,
                'ow_origin_code': ow_amend_origin,
                'ow_dest_code': ow_amend_dest,
                'return_dapart_date': return_dapart_date,
		'ow_depart_date':ow_depart_date,
		'rt_origin_code': rt_amend_origin,
		'rt_dest_code': rt_amend_dest
        })
	amend_dict.update({
		'ow_amendment_status':self.ow_amendment,
		'rt_amendment_status':self.rt_amendment,
		'rt_round_amendment':self.rt_round_amendment,
	})
	static_key = 'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$'
	static_key2 = 'ControlGroupSearchChangeView_AvailabilitySearchInputSearchChangeView'
	data = [
	  ('__EVENTTARGET', 'ControlGroupSearchChangeView$LinkButtonSubmit'),
	  ('__EVENTARGUMENT', ''),
	  ('__VIEWSTATE', viewstate),
	  ('pageToken', ''),
	  ('AGPKey', agpkey),
	  ('AGPRETURNURL', agpreturnurl),
	  ('AGMBKey', agmbkey),
	  ('ISAGENTLOGGEDIN', loggedin),
	  ('QPKey', qpkey),
	  ('ReportsKey', reportkey),
	] 
	if self.ow_amendment:
	    data.extend([
		  ('%sCheckBoxChangeMarket_1'%static_key, 'on'),
		  ('%sTextBoxMarketOrigin1'%static_key, ow_amend_origin),
		  ('%soriginStation1'%static_key2, ow_amend_origin),
		  ('%sTextBoxMarketDestination1'%static_key, ow_amend_dest),
		  ('%sdestinationStation1'%static_key2, ow_amend_dest),
		  ('%sDropDownListMarketDay1'%static_key, ow_day),
		  ('%sDropDownListMarketMonth1'%static_key, ow_year_month),
		  ('%sDropDownListMarketDateRange1'%static_key, '0|0'),
		])
	elif self.rt_amendment:
	    data.extend([
                  ('%sCheckBoxChangeMarket_2'%static_key, 'on'),
                  ('%sTextBoxMarketOrigin2'%static_key, rt_amend_origin),
                  ('%soriginStation2'%static_key2, rt_amend_origin),
                  ('%sTextBoxMarketDestination2'%static_key, rt_amend_dest),
                  ('%sdestinationStation2'%static_key2, rt_amend_dest),
                  ('%sDropDownListMarketDay2'%static_key, rt_day),
                  ('%sDropDownListMarketMonth2'%static_key, rt_year_month),
                  ('%sDropDownListMarketDateRange2'%static_key, '0|0'),])
	elif self.rt_round_amendment:
	    data.extend([
                  ('%sCheckBoxChangeMarket_1'%static_key, 'on'),
                  ('%sTextBoxMarketOrigin1'%static_key, ow_amend_origin),
                  ('%soriginStation1'%static_key2, ow_amend_origin),
                  ('%sTextBoxMarketDestination1'%static_key, ow_amend_dest),
                  ('%sdestinationStation1'%static_key2, ow_amend_dest),
                  ('%sDropDownListMarketDay1'%static_key, ow_day),
                  ('%sDropDownListMarketMonth1'%static_key, ow_year_month),
                  ('%sDropDownListMarketDateRange1'%static_key, '0|0'),
		  ('%sCheckBoxChangeMarket_2'%static_key, 'on'),
                  ('%sTextBoxMarketOrigin2'%static_key, rt_amend_origin),
                  ('%soriginStation2'%static_key2, rt_amend_origin),
                  ('%sTextBoxMarketDestination2'%static_key, rt_amend_dest),
                  ('%sdestinationStation2'%static_key2, rt_amend_dest),
                  ('%sDropDownListMarketDay2'%static_key, rt_day),
                  ('%sDropDownListMarketMonth2'%static_key, rt_year_month),
                  ('%sDropDownListMarketDateRange2'%static_key, '0|0'),
            ])
	else:
	    error = "Multi City Amend"
	    self.insert_values_into_db(amend_dict, "Amend Failed", error)
	    return
	url = 'https://book.spicejet.com/SearchChange.aspx'
	yield FormRequest(url, callback=self.parse_select_change, formdata=data, \
		meta={'amend_dict':amend_dict}, dont_filter=True, method="POST")

    def parse_select_change(self, response):
	sel = Selector(response)
	amend_dict = response.meta['amend_dict']
	if 'SelectChange' not in response.url:
            self.insert_values_into_db(amend_dict, "Amend Failed", "Response timeout from SpiceJet")
            return
	agpkey = normalize(''.join(sel.xpath('//input[@id="AGPKey"]/@value').extract()))
        agmbkey = normalize(''.join(sel.xpath('//input[@id="AGMBKey"]/@value').extract()))
        agpreturnurl = normalize(''.join(sel.xpath('//input[@id="AGPRETURNURL"]/@value').extract()))
        loggedin = normalize(''.join(sel.xpath('//input[@id="ISAGENTLOGGEDIN"]/@value').extract()))
        qpkey = normalize(''.join(sel.xpath('//input[@id="QPKey"]/@value').extract()))
        reportkey = normalize(''.join(sel.xpath('//input[@id="ReportsKey"]/@value').extract()))
        viewstate = normalize(''.join(sel.xpath('//input[@id="viewState"]/@value').extract()))

	ow_avail_flight_dict, rt_avail_flight_dict = {}, {}
	ow_table = sel.xpath('//table[@id="availabilityTable0"]//tr[contains(@class, "fare-row")]')
	key_list = ['cabin_baggage', 'free_checkin_baggage', 'free_meal_baggage']
	for row in ow_table:
	    #flight_id = row.xpath('./td[1]/span/a/span/text()').extract()
	    #flight_id = row.xpath('./td[1]//div[@class="flightInfo"]/p[1]/text()').extract()
	    flight_id = normalize('<>'.join(row.xpath('./td[1]//span/a//text()').extract())).split('<>')
	    flight_id = [normalize(x).replace(',', '').strip() for x in flight_id]
	    keys_dict = {}
	    for idx, td in enumerate(key_list, 3):
	    	key_name = ''.join(row.xpath('./td[%s]/p/input/@name'%idx).extract())
	    	key_val = ''.join(row.xpath('./td[%s]/p/input/@value'%idx).extract())
	    	price = ''.join(row.xpath('./td[%s]/p/label/span[@class="flightfare"]//text()'%idx).extract())
		keys_dict.update({td:[key_name, key_val, price]})
	    if keys_dict:
	        ow_avail_flight_dict.update({'<>'.join(list(set(flight_id))).replace(' ', ''):keys_dict})
	rt_table = sel.xpath('//table[@id="availabilityTable1"]//tr[contains(@class, "fare-row")]')
	for row in rt_table:
            #flight_id = row.xpath('./td[1]/span/a/span/text()').extract()
	    #flight_id = row.xpath('./td[1]//div[@class="flightInfo"]/p[1]/text()').extract()
	    flight_id = normalize('<>'.join(row.xpath('./td[1]//span/a//text()').extract())).split('<>')
            flight_id = [normalize(x).replace(',', '').strip() for x in flight_id]
            keys_dict = {}
            for idx, td in enumerate(key_list, 3):
                key_name = ''.join(row.xpath('./td[%s]/p/input/@name'%idx).extract())
                key_val = ''.join(row.xpath('./td[%s]/p/input/@value'%idx).extract())
                price = ''.join(row.xpath('./td[%s]/p/label/span[@class="flightfare"]//text()'%idx).extract())
                keys_dict.update({td:[key_name, key_val, price]})
	    if keys_dict:
                rt_avail_flight_dict.update({'<>'.join(list(set(flight_id))).replace(' ', ''):keys_dict})
	cabin_class = amend_dict.get('cabin_class', '')
	ow_flight_key, ow_flight = self.get_amend_sell_keys(amend_dict, ow_avail_flight_dict, cabin_class, False)
	rt_flight_key, rt_flight = self.get_amend_sell_keys(amend_dict, rt_avail_flight_dict, cabin_class, True)
	new_flights = [ow_flight , rt_flight]
	amend_dict['new_flight_ids'] = new_flights
	data = [
	  ('__EVENTTARGET', ''),
	  ('__EVENTARGUMENT', ''),
	  ('__VIEWSTATE', viewstate),
	  ('pageToken', ''),
	  ('AGPKey', agpkey),
	  ('AGPRETURNURL', agpreturnurl),
	  ('AGMBKey', agmbkey),
	  ('ISAGENTLOGGEDIN', loggedin),
	  ('QPKey', qpkey),
	  ('ReportsKey', reportkey),
	  ('ControlGroupSelectChangeView$ButtonSubmit', 'Continue'),
	]
	if not ow_flight_key and amend_dict.get('ow_amendment_status', '') == True:
	    print "flights not found"
	    self.insert_values_into_db(amend_dict, "Amend Failed", "Flights not found")
	    self.send_mail("Amend Failed", "Flights not found, TripId:%s"%amend_dict.get('trip_ref', ''), "amend", "SpiceJet", "spicejet_common")
	    return
	if not rt_flight_key and amend_dict.get('rt_amendment_status', '') == True:
	    print "flights not found"
	    self.insert_values_into_db(amend_dict, "Amend Failed", "Flights not found")
	    self.send_mail("Amend Failed", "Flights not found, TripId:%s"%amend_dict.get('trip_ref', ''), "amend", "SpiceJet", "spicejet_common")
	    return
	if not ow_flight_key and amend_dict.get('rt_round_amendment', '') == True:
	    print "flights not found"
	    self.insert_values_into_db(amend_dict, "Amend Failed", "Flights not found")
	    self.send_mail("Amend Failed", "Flights not found, TripId:%s"%amend_dict.get('trip_ref', '') ,"amend", "SpiceJet", "spicejet_common")
	    return
	if not ow_flight_key:
	    if amend_dict.get('rt_amendment_status', '') == True or amend_dict.get('rt_round_amendment', '') == True:
	        ow_flight_key, ow_flight = self.get_ori_amend_sell_keys(amend_dict, ow_avail_flight_dict, cabin_class, 'OW', False)
	if amend_dict.get('ow_amendment_status', '') == True:
	    data.extend([
		('ControlGroupSelectChangeView$AvailabilityInputSelectChangeView$market1', ow_flight_key),
	    ])
	elif amend_dict.get('rt_amendment_status', '') == True:
	    data.extend([
		('ControlGroupSelectChangeView$AvailabilityInputSelectChangeView$market1', ow_flight_key),
		('ControlGroupSelectChangeView$AvailabilityInputSelectChangeView$market2', rt_flight_key),
	    ])
	elif amend_dict.get('rt_round_amendment', '') == True:
	    data.extend([
		('ControlGroupSelectChangeView$AvailabilityInputSelectChangeView$market1', ow_flight_key),
		('ControlGroupSelectChangeView$AvailabilityInputSelectChangeView$market2', rt_flight_key),
	    ])
	else:
	    self.insert_values_into_db(amend_dict, "Amend Failed", "Flights not found")
	    return
	self.insert_values_into_db(amend_dict, "Amend Failed", "Response timeout from SpiceJet")
	url = 'https://book.spicejet.com/SelectChange.aspx'
	yield FormRequest(url, callback=self.parse_change_process, formdata=data, meta={'amend_dict':amend_dict}, dont_filter=True)

    def parse_change_process(self, response):
	sel = Selector(response)
	amend_dict = response.meta['amend_dict']
	if 'ChangeProcess' not in response.url:
	    self.insert_values_into_db(amend_dict, "Amend Failed", "Response timeout from SpiceJet")
	    return
        agpkey = normalize(''.join(sel.xpath('//input[@id="AGPKey"]/@value').extract()))
        agmbkey = normalize(''.join(sel.xpath('//input[@id="AGMBKey"]/@value').extract()))
        agpreturnurl = normalize(''.join(sel.xpath('//input[@id="AGPRETURNURL"]/@value').extract()))
        loggedin = normalize(''.join(sel.xpath('//input[@id="ISAGENTLOGGEDIN"]/@value').extract()))
        qpkey = normalize(''.join(sel.xpath('//input[@id="QPKey"]/@value').extract()))
        reportkey = normalize(''.join(sel.xpath('//input[@id="ReportsKey"]/@value').extract()))
        viewstate = normalize(''.join(sel.xpath('//input[@id="viewState"]/@value').extract()))
	data = [
	  ('__EVENTTARGET', ''),
	  ('__EVENTARGUMENT', ''),
	  ('__VIEWSTATE', viewstate),
	  ('pageToken', ''),
	  ('AGPKey', agpkey),
	  ('AGPRETURNURL', agpreturnurl),
	  ('AGMBKey', agmbkey),
	  ('ISAGENTLOGGEDIN', loggedin),
	  ('QPKey', qpkey),
	  ('ReportsKey', reportkey),
	  ('CONTROLGROUPPASSENGERCONTACTCHANGE$ButtonSubmit', ''),
	]
	url = 'https://book.spicejet.com/ChangeProcessContact.aspx'
	yield FormRequest(url, callback=self.parse_set_map, formdata=data, meta={'amend_dict':amend_dict}, dont_filter=True)

    def parse_set_map(self, response):
	sel = Selector(response)
	amend_dict = response.meta['amend_dict']
	if 'SeatMapFromPayment' not in response.url:
	    self.insert_values_into_db(amend_dict, "Amend Failed", "Response timeout from SpiceJet")
	    return
        agpkey = normalize(''.join(sel.xpath('//input[@id="AGPKey"]/@value').extract()))
        agmbkey = normalize(''.join(sel.xpath('//input[@id="AGMBKey"]/@value').extract()))
        agpreturnurl = normalize(''.join(sel.xpath('//input[@id="AGPRETURNURL"]/@value').extract()))
        loggedin = normalize(''.join(sel.xpath('//input[@id="ISAGENTLOGGEDIN"]/@value').extract()))
        qpkey = normalize(''.join(sel.xpath('//input[@id="QPKey"]/@value').extract()))
        reportkey = normalize(''.join(sel.xpath('//input[@id="ReportsKey"]/@value').extract()))
        viewstate = normalize(''.join(sel.xpath('//input[@id="viewState"]/@value').extract()))
	change_cancel_fee = normalize(''.join(sel.xpath('//td[contains(text(), "Change/Cancel Fee")]/following-sibling::td/text()').extract()))
	total_price = normalize(''.join(sel.xpath('//span[@class="total-price"]/text()').extract()))
	ow_tot_fare = normalize(''.join(sel.xpath('//div[@class="priceSummaryContainer"][1]//table[@class="priceSummary"]//h4[@class="t_price"]/span/text()').extract()))
	rt_tot_fare = normalize(''.join(sel.xpath('//div[@class="priceSummaryContainer"][2]//table[@class="priceSummary"]//h4[@class="t_price"]/span/text()').extract()))
	rt_pax_fare = normalize('<>'.join(sel.xpath('//div[@class="priceSummaryContainer"][2]//table[@class="priceSummary"]//tr[@class="onward-journey-fare"]//td[@class="rht"]//text()').extract())).strip().strip('<>')
	ow_pax_fare = normalize('<>'.join(sel.xpath('//div[@class="priceSummaryContainer"][1]//table[@class="priceSummary"]//tr[@class="onward-journey-fare"]//td[@class="rht"]//text()').extract())).strip().strip('<>')
	ow_tax_price_keys = sel.xpath('//div[@class="priceSummaryContainer"]//table[@class="priceSummary"]//div[@id="taxAndFeeContainerId_1_1"]//span[@class="floatLeft clearLeft"]//text()').extract()
	ow_tax_price_vals = sel.xpath('//div[@class="priceSummaryContainer"]//table[@class="priceSummary"]//div[@id="taxAndFeeContainerId_1_1"]//span[@class="clearRight floatRight"]//text()').extract()
	rt_tax_price_keys = sel.xpath('//div[@class="priceSummaryContainer"]//table[@class="priceSummary"]//div[@id="taxAndFeeContainerId_2_1"]//span[@class="floatLeft clearLeft"]//text()').extract()
	rt_tax_price_vals = sel.xpath('//div[@class="priceSummaryContainer"]//table[@class="priceSummary"]//div[@id="taxAndFeeContainerId_2_1"]//span[@class="clearRight floatRight"]//text()').extract()
	pax_cat_list = ['Adult', "Infant", "Child"]
	ow_fare_dict = {}
	for pax_cat in pax_cat_list:
	    val = normalize(''.join(sel.xpath('//div[@class="priceSummaryContainer"][1]//table[@class="priceSummary"]//tr[@class="onward-journey-fare"]//td[@class="lft"]//b[contains(text(), "%s")]/../following-sibling::td[@class="rht"]//text()'%pax_cat).extract()))
	    if val:
		ow_fare_dict.update({'%s Fare'%pax_cat: val})
	for k, v in zip(ow_tax_price_keys, ow_tax_price_vals):
	    ow_fare_dict[k] = v
	ow_fare_dict.update({
		'total_price':ow_tot_fare,
	})
	rt_fare_dict = {}
	for pax_cat in pax_cat_list:
	    rt_val = normalize(''.join(sel.xpath('//div[@class="priceSummaryContainer"][2]//table[@class="priceSummary"]//tr[@class="onward-journey-fare"]//td[@class="lft"]//b[contains(text(), "%s")]/../following-sibling::td[@class="rht"]//text()'%pax_cat).extract()))
	    if rt_val: rt_fare_dict.update({'%s Fare'%pax_cat: val})
	for k, v in zip(rt_tax_price_keys, rt_tax_price_vals):
            rt_fare_dict[k] = v
	if rt_fare_dict:
            rt_fare_dict.update({
                'total_price':rt_tot_fare,
            })
	fin_fare_dict = {}
	fin_fare_dict['total'] = total_price
	if ow_fare_dict:
	    fin_fare_dict[0] = ow_fare_dict
	if rt_fare_dict:
	    fin_fare_dict[1] = rt_fare_dict
	fin_fare_dict['Change/Cancel Fee'] = change_cancel_fee
	amend_dict['price_dict'] = fin_fare_dict
	amend_dict['Total Price'] = total_price
	headers = {
	    'Pragma': 'no-cache',
	    'Origin': 'https://book.spicejet.com',
	    'Accept-Encoding': 'gzip, deflate, br',
	    'Accept-Language': 'en-US,en;q=0.9',
	    'Upgrade-Insecure-Requests': '1',
	    'Content-Type': 'application/x-www-form-urlencoded',
	    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
	    'Cache-Control': 'no-cache',
	    'Referer': 'https://book.spicejet.com/SeatMapFromPayment.aspx',
	    'Connection': 'keep-alive',
	}
	data = [
	  ('__EVENTTARGET', 'ControlGroupUnitMapView$UnitMapViewControl$LinkButtonAssignUnit'),
	  ('__EVENTARGUMENT', ''),
	  ('__VIEWSTATE', viewstate),
	  ('pageToken', ''),
	  ('AGPKey', agpkey),
	  ('AGPRETURNURL', agpreturnurl),
	  ('AGMBKey', agmbkey),
	  ('ISAGENTLOGGEDIN', loggedin),
	  ('QPKey', qpkey),
	  ('ReportsKey', reportkey),
	  ('ControlGroupUnitMapView$UnitMapViewControl$compartmentDesignatorInput', ''),
	  ('ControlGroupUnitMapView$UnitMapViewControl$deckDesignatorInput', '1'),
	  ('ControlGroupUnitMapView$UnitMapViewControl$tripInput', '0'),
	  ('ControlGroupUnitMapView$UnitMapViewControl$passengerInput', '0'),
	]
	#self.insert_values_into_db(amend_dict, "Amend Failed", "Response timeout from SpiceJet")
	url = 'https://book.spicejet.com/SeatMapFromPayment.aspx'
	yield FormRequest(url, callback=self.parse_payment, formdata=data, headers=headers, meta={'amend_dict':amend_dict}, dont_filter=True)

    def parse_payment(self, response):
	sel = Selector(response)
	amend_dict = response.meta['amend_dict']
	if 'spicejet.com/Payment' not in response.url:
            self.insert_values_into_db(amend_dict, "Amend Failed", "Payment Failed")
            return
	agpkey = normalize(''.join(sel.xpath('//input[@id="AGPKey"]/@value').extract()))
        agmbkey = normalize(''.join(sel.xpath('//input[@id="AGMBKey"]/@value').extract()))
        agpreturnurl = normalize(''.join(sel.xpath('//input[@id="AGPRETURNURL"]/@value').extract()))
        loggedin = normalize(''.join(sel.xpath('//input[@id="ISAGENTLOGGEDIN"]/@value').extract()))
        qpkey = normalize(''.join(sel.xpath('//input[@id="QPKey"]/@value').extract()))
        reportkey = normalize(''.join(sel.xpath('//input[@id="ReportsKey"]/@value').extract()))
        viewstate = normalize(''.join(sel.xpath('//input[@id="viewState"]/@value').extract()))
	agency_account = ''.join(sel.xpath('//select[@name="CONTROLGROUPPAYMENTBOTTOM$ControlGroupPaymentInputViewPaymentView$DropDownListPaymentMethodCode"]/option/@value').extract())
	#amount = ''.join(sel.xpath('//input[@name="CONTROLGROUPPAYMENTBOTTOM$ControlGroupPaymentInputViewPaymentView$AgencyAccount_AG_AMOUNT"]/@value').extract())
	amount = normalize(''.join(sel.xpath('//div[@id="AgencyAccount_AG_PaymentSummary"]//table//tr//th[contains(text(), "Total Amount")]/../following-sibling::tr[1]/td/text()').extract()))
	if amount:
	    amount = ''.join(re.findall('\d+[0-9,.]', amount)).replace(',', '').strip()
	    if not amount:
		print "Price not found"
		self.insert_values_into_db(amend_dict, "Amend Failed", "Payment amount not found in Airline")
		return
	else:
	    print "Price not found"
	    self.insert_values_into_db(amend_dict, "Amend Failed", "Payment amount not found in Airline")
	    return
	total_amount_ = normalize(''.join(sel.xpath('//span[@class="total-price"]/text()').extract())).replace(',', '').strip()
	try:
	    total_amount_ = normalize(sel.xpath('//span[@class="total-price"]/text()').extract()[0]).replace(',', '').strip()
	except:
	    total_amount_ = 0
	ct_price = amend_dict.get('')
	tolerance_amount = amend_dict.get('tolerance_amount', 0)
	cleartrip_price = amend_dict.get('pax_paid_amount', 0)
	if total_amount_ == 0:
	    self.insert_values_into_db(amend_dict, "Amend Failed", "Total price not found")
	try:
		tolerance = float(total_amount_) - float(cleartrip_price)
		if tolerance <= float(tolerance_amount):
		    tolerance_check = True
		else:
		    tolerance_check = False
	except:
		tolerance_check = False
		tolerance = 0
		print "Total amount not found"
		self.insert_values_into_db(amend_dict, "Amend Failed", "Total price not found")
		return
	amend_dict['price_diff'] = tolerance
	proceed_to_book = amend_dict.get('proceed_to_book', 0)
	data = [
          ('__EVENTTARGET', ''),
          ('__EVENTARGUMENT', ''),
          ('__VIEWSTATE', viewstate),
          ('pageToken', ''),
          ('AGPKey', agpkey),
          ('AGPRETURNURL', agpreturnurl),
          ('AGMBKey', agmbkey),
          ('ISAGENTLOGGEDIN', loggedin),
          ('QPKey', qpkey),
          ('ReportsKey', reportkey),
	  ('PromoCodePaymentView$TextBoxPromoCode', ''),
	  ('PromoCodePaymentView$TextBoxAccountNumber', ''),
	  ('termcondition', 'on'),
	  ('DropDownListPaymentMethodCode', 'ExternalAccount:MC'),
	  ('DropDownListPaymentMethodCode', 'PrePaid:IB'),
	  ('WalletMode', 'WP'),
	  ('ATMDEBITGroup', 'MAESTRO'),
	  ('ATMCumDebit', 'SMP_DIRECTD'),
	  ('PrePaid_HB', ''),
	  ('NetBanking', ''),
	  ('CONTROLGROUPPAYMENTBOTTOM$ControlGroupPaymentInputViewPaymentView$DropDownListPaymentMethodCode', 'AgencyAccount:AG'),
	  ('CONTROLGROUPPAYMENTBOTTOM$ControlGroupPaymentInputViewPaymentView$AgencyAccount_AG_AMOUNT', amount),
	  ('CONTROLGROUPPAYMENTBOTTOM$ControlGroupPaymentInputViewPaymentView$storedPaymentId', ''),
	  ('CONTROLGROUPPAYMENTBOTTOM$ButtonSubmit', 'Confirm Payment'),
        ]
	url = 'https://book.spicejet.com/Payment.aspx'
	
	if tolerance_check:
	    if proceed_to_book == 1 or proceed_to_book == '1':
	        yield FormRequest(url, callback=self.parse_post_payment, formdata=data, meta={'amend_dict':amend_dict}, dont_filter=True)
	    else:
		print "Test booking"
                self.insert_values_into_db(amend_dict, "Amend Failed", "Test booking")
                return
	else:
	    print "Fare increased by airline"
	    self.insert_values_into_db(amend_dict, "Amend Failed", "Fare increased by airline")
	

    def parse_post_payment(self, response):
	sel = Selector(response)
	amend_dict = response.meta['amend_dict']
	time.sleep(30)
	self.insert_values_into_db(amend_dict, "Payment fail whereas payment success", "Payment fail whereas payment success")
	url = 'https://book.spicejet.com/Wait.aspx'
	headers = {
	    'Pragma': 'no-cache',
	    'Accept-Encoding': 'gzip, deflate, br',
	    'Accept-Language': 'en-US,en;q=0.9',
	    'Upgrade-Insecure-Requests': '1',
	    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
	    'Referer': 'https://book.spicejet.com/Payment.aspx',
	    'Connection': 'keep-alive',
	    'Cache-Control': 'no-cache',
	}
	yield Request(url, callback=self.parse_confirm_payment, headers=headers, dont_filter=True, meta={'amend_dict':amend_dict})

    def parse_confirm_payment(self, response):
	sel = Selector(response)
	amend_dict = response.meta['amend_dict']
	updated_date = ''.join(sel.xpath('//table[@id="bookingDetail"]//span[contains(text(), "Booking Date")]/strong/text()').extract())
	self.insert_values_into_db(amend_dict, "Success(Booking-date:%s)"%updated_date, "")
	with open('sg_amend_%s.html'%amend_dict.get('trip_ref', ''), 'w+') as f:
		f.write('%s'%response.body)
