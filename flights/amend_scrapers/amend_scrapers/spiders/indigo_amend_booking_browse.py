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
from indigo_amend_utils import *

from scrapy.conf import settings

import sys
sys.path.append(settings['ROOT_PATH'])

from root_utils import *


_cfg = SafeConfigParser()
_cfg.read(settings['BOOK_PCC_PATH'])


class IndigoAmendBrowse(Spider, IndigoAmendUtils, Helpers):
    name = "indigo_amendbooking_browse"
    start_urls = ["https://www.goindigo.in/"]
    handle_httpstatus_list = [404, 500]

    def __init__(self, *args, **kwargs):
        super(IndigoAmendBrowse, self).__init__(*args, **kwargs)
        self.request_verification = ''
        self.amend_dict = kwargs.get('jsons', {})
        self.proceed_to_book = 0
	self.trip_type = ''
	self.rt_round_amendment = False
	self.ow_amendment = False
	self.rt_amendment = False
        self.price_patt = re.compile('\d+')
        self.log = create_logger_obj('indigo_amend_booking')
	self.insert_query = 'insert into indigoamend_booking_report (sk, airline, pnr, flight_number, from_location, to_location, triptype, cleartrip_price, airline_price, status_message, tolerance_amount, oneway_date, return_date, error_message, request_input, price_details, created_at, modified_at) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), sk=%s, airline=%s, pnr=%s, flight_number=%s, from_location=%s, to_location=%s, triptype=%s, cleartrip_price=%s, airline_price=%s, status_message=%s, tolerance_amount=%s, oneway_date=%s, return_date=%s, error_message=%s, request_input=%s, price_details=%s'

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
	flight_number = amend_dict.get('flight_no', '')
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
		sk, 'Indigo', pnr, flight_number, from_location,
		to_location, triptype, cleartrip_price, indigo_price,
		status_message, tolerance_amount, oneway_date, return_date,
		error_message, paxdetails, price_details,
		sk, 'Indigo', pnr, flight_number, from_location, to_location,
		triptype, cleartrip_price, indigo_price, status_message, tolerance_amount,
		oneway_date, return_date, error_message, paxdetails, price_details)
	self.cur.execute(self.insert_query, values)

    def parse(self, response):
        print 'Parse function works'
        sel = Selector(response)
        try:
	    self.pcc_name, amend_dict, err_msg = self.get_pcc_name()
	except Exception as e:
	    self.insert_values_into_db(amend_dict, "Amend Failed", e.message)
        if 'coupon' in self.pcc_name:
                self.pcc_name =  'indigo_default'
        if err_msg:
	    self.insert_values_into_db(amend_dict, "Amend Failed", err_msg)
	    self.send_mail("Amend Failed", err_msg, "amend", "Indigo", "indigo_common")
            logging.debug(err_msg)
            return
        try:
                data = [
              ('agentLogin.Username', _cfg.get(self.pcc_name, 'username')),
              ('agentLogin.Password', _cfg.get(self.pcc_name, 'password')),
              ('IsEncrypted', 'true'),
                ]
        except:
		self.insert_values_into_db(amend_dict, "Amend Failed", "PCC %s not available"%self.pcc_name)
		self.send_mail("Amend Failed", "PCC %s not available"%self.pcc_name , "amend", "Indigo", "indigo_common")
                logging.debug('PCC not avaialble for scrapper')
                return
        url = 'https://book.goindigo.in/Agent/Login'
        yield FormRequest(url, callback=self.prase_login, formdata=data, meta={'amend_dict':amend_dict})

    def prase_login(self, response):
        '''
        Login into Indigo
        '''
        print 'Login works'
        sel = Selector(response)
	amend_dict = response.meta['amend_dict']
        check_text = ''.join(sel.xpath('//input[@class="postLogin"]//@value').extract())
        login_status = True
        if 'LoginError' in response.url:
	    self.insert_values_into_db(amend_dict, "Amend Failed", "Login Failed")
	    self.send_mail("Login Failed", "Login Failed", "amend", "Indigo", "indigo_common")
            login_status = False
	    return
        cookies = {}
        coo_data = response.headers.get('Set-Cookie', '')
        data = coo_data.split(';')[0]
        if data:
            try :
                key, val = data.split('=', 1)
                if key == '__RequestVerificationToken':
                    self.request_verification = key
            except : pass 
            cookies.update({key.strip():val.strip()})
        request_headers = response.request.headers.get('Cookie', '').split(';')
        for i in request_headers:
            try: key, val = i.split('=', 1)
            except : continue
            cookies.update({key.strip():val.strip()})
        self.cookies =  cookies
	pnr = amend_dict.get('pnr', '')
	if pnr:
            data = [
                  ('__RequestVerificationToken', self.request_verification),
                  ('indiGoMyBookings.BookingSearchRecordLocator', pnr),
                  ('indiGoMyBookings_Submit', 'Get Itinerary'),
                ]
            url = 'https://book.goindigo.in/Agent/MyBookings'
            yield FormRequest(url, callback=self.parse_booking_view, formdata=data, \
			cookies=self.cookies, meta={'amend_dict':amend_dict}, dont_filter=True)
	else:
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR not found")

    def parse_booking_view(self, response):
        '''
        Checking the option for change flight and navigating into change flight page
        '''
        sel = Selector(response)
	amend_dict = response.meta['amend_dict']
        cookies = {}
        request_headers = response.request.headers.get('Cookie', '').split(';')
        for i in request_headers:
            try: key, val = i.split('=', 1)
            except : continue
            cookies.update({key.strip():val.strip()})
        self.cookies = cookies
        check_amend_option = normalize(''.join(sel.xpath('//ul[@class="nav"]//li/a[@href="/Flight/CancelRebook"]//text()').extract()))
        if not check_amend_option:
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR doesn't have change flight option")
	    self.send_mail("Amend Failed", "PNR %s doesn't have change flight option"%amend_dict.get('pnr', ''), "amend", "Indigo", "indigo_common")
            return
        if 'Booking/View' in response.url:
            url = 'https://book.goindigo.in/Flight/CancelRebook'
            yield Request(url, callback=self.parse_rebook, cookies=self.cookies, dont_filter=True, meta={'amend_dict':amend_dict})
        else:
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR %s details not found"%amend_dict.get('pnr', ''))
	    self.send_mail("Amend Failed", "PNR %s details not found"%amend_dict.get('pnr', ''), "amend", "Indigo", "indigo_common")

    def parse_rebook(self, response):
        '''
        Selecting amendment route and amend journey date and navigating into flight selection
        '''
        sel = Selector(response)
	amend_dict = response.meta['amend_dict']
        if 'CancelRebook' not in response.url:
            print "Scraper Faild to navigate Rebook"
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR %s, Scraper Faild to navigate Rebook"%amend_dict.get('pnr', ''))
	    self.send_mail("Amend Failed", "Scraper Faild to navigate Rebook, TripId:%s"%amend_dict.get('trip_ref', ''), "amend", "Indigo", "indigo_common")
            return
	self.trip_type = self.get_trip_type(amend_dict)
	self.rt_round_amendment, self.ow_amendment, self.rt_amendment = self.get_amend_type(amend_dict)
        sell_key = normalize(''.join(sel.xpath('//div[@class="tableWrapMain"]/table/tbody/tr[1]/td[2]/input[@id="indiGoCancelRebook_SpecificJourneySellKey"]/@value').extract()))
        rebook_flight_key = normalize(''.join(sel.xpath('//div[@class="tableWrapMain"]/table/tbody/tr[1]/td[2]//input[@name="indiGoCancelRebook.SelectedCancelRebookFlights[0].FromJourney"]/@value').extract()))
        return_sell_key = normalize(''.join(sel.xpath('//div[@class="tableWrapMain"]/table/tbody/tr[2]/td[2]/input[@id="indiGoCancelRebook_SpecificJourneySellKey"]/@value').extract()))
        return_rebook_flight_key = normalize(''.join(sel.xpath('//div[@class="tableWrapMain"]/table/tbody/tr[2]/td[2]//input[@name="indiGoCancelRebook.SelectedCancelRebookFlights[1].FromJourney"]/@value').extract()))
	search_keys_dict = self.get_segment_details(amend_dict)
	origin_code = search_keys_dict.get('origin', '')
	dest_code = search_keys_dict.get('destination', '')
	depart_date = search_keys_dict.get('amd_ow_depature_date', '')
	ori_return_dep_date = search_keys_dict.get('rt_depature_date', '')
	return_dapart_date = search_keys_dict.get('amd_rt_depature_date', '')
	amend_dict.update({
		'origin_code':origin_code,
		'destination_code':dest_code,
		'depart_date':depart_date,
		'return_dapart_date': return_dapart_date,
	})
        data = [
          ('indiGoCancelRebook.SpecificJourneySellKey', str(sell_key)),
          ('indiGoCancelRebook.IndiGoPlus', ''),
          ('indiGoCancelRebook.SelectedCancelRebookFlights[0].Origin', str(origin_code)),
          ('hdnOriginStationCF', ''),
          ('indiGoCancelRebook.SelectedCancelRebookFlights[0].Destination', str(dest_code)),
          ('hdnDestStationCF', ''),
          ('indiGoCancelRebook.SelectedCancelRebookFlights[0].DepartureDate', str(depart_date)),
          ('indiGoCancelRebook_Submit', 'Select and Continue'),
        ]
        if self.trip_type == 'OW':
            data.extend([
                        ('indiGoCancelRebook.ReturningDepartureDate', ''),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[0].FromJourney', str(rebook_flight_key.replace('false', ''))),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[0].FromJourney', 'false'),
            ])
        elif self.trip_type == 'RT':
            if self.ow_amendment:
                data.extend([
                        ('indiGoCancelRebook.ReturningDepartureDate', str(ori_return_dep_date)),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[0].FromJourney', str(rebook_flight_key.replace('false', ''))),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[0].FromJourney', 'false'),
                        ('indiGoCancelRebook.IndiGoPlus', ''),
                        ('indiGoCancelRebook.SpecificJourneySellKey', str(return_sell_key)),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[1].Origin', str(dest_code)),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[1].Destination', str(origin_code)),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[1].FromJourney', 'false'),
                    ])
            elif self.rt_amendment:
                data.extend([
                        ('indiGoCancelRebook.IndiGoPlus', ''),
                        ('indiGoCancelRebook.ReturningDepartureDate', str(ori_return_dep_date)),
                        ('indiGoCancelRebook.SpecificJourneySellKey', str(return_sell_key)),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[1].Origin', str(dest_code)),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[1].Destination', str(origin_code)),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[1].DepartureDate', str(return_dapart_date)),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[1].FromJourney', str(return_rebook_flight_key.replace('false', ''))),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[1].FromJourney', 'false'),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[0].FromJourney', 'false'),
                ])
            else:
                data.extend([
                        #('indiGoCancelRebook.ReturningDepartureDate', str(ori_return_dep_date)),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[0].FromJourney', str(rebook_flight_key.replace('false', ''))),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[0].FromJourney', 'false'),
                        ('indiGoCancelRebook.IndiGoPlus', ''),
                        ('indiGoCancelRebook.SpecificJourneySellKey', str(return_sell_key)),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[1].Origin', str(dest_code)),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[1].Destination', str(origin_code)),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[1].DepartureDate', str(return_dapart_date)),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[1].FromJourney', str(return_rebook_flight_key.replace('false', ''))),
                        ('indiGoCancelRebook.SelectedCancelRebookFlights[1].FromJourney', 'false'),
                ])
        else:
            print "Multi city"
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR %s, Multi city amend"%amend_dict.get('pnr', ''))
	    #self.send_mail("Amend Failed", "Multi city amend", "amend", "Indigo", "indigo_common")
            return
        url = 'https://book.goindigo.in/Flight/CancelRebook?Length=0'
        yield FormRequest(url, callback=self.parse_cancelrebook, formdata=data, \
			cookies=self.cookies, dont_filter=True, meta={'amend_dict':amend_dict})

    def parse_cancelrebook(self, response):
        '''
        parsing the json url to get avail flight details
        '''
        sel = Selector(response)
	amend_dict = response.meta['amend_dict']
        if 'flight-select-modification' not in response.url:
            msg = "scraper failed to navigate flight modification, TripId:%s"%amend_dict.get('trip_ref', '')
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR %s, %s"%(amend_dict.get('pnr', ''), msg))
	    self.send_mail("Amend Failed", msg, "amend", "Indigo", "indigo_common")
            return
        self.cookies.update({
                '_sdsat_Login Status': 'Logged In',
                'aemLoginStatus': 'Agent',
                's_ppn': 'flight-select-modification',
                's_ppv': 'flight-select-modification',
        })
        url = 'https://book.goindigo.in/Flight/SelectAEM?FilterTrips=0'
        yield Request(url, callback=self.parse_rebook_flight, cookies=self.cookies, method="GET", meta={'amend_dict':amend_dict})

    def parse_rebook_flight(self, response):
        sel = Selector(response)
        '''
        pick the amend flight and submitting
        '''
	amend_dict = response.meta['amend_dict']
        if 'SelectAEM' not in response.url:
            msg = "Scraper failed to Selecting Flight, TripId:%s"%amend_dict.get('trip_ref', '')
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR %s, %s"%(amend_dict.get('pnr', ''), msg))
	    self.send_mail("Amend Failed", msg, "amend", "Indigo", "indigo_common")
            return
        json_body = json.loads(response.body)
        ow_avail_flights = self.get_avail_flights(json_body, 'OW')
        if self.trip_type == 'RT':
            try:
                rt_avail_flights = self.get_avail_flights(json_body, 'RT')
            except:
                rt_avail_flights = {}
        else: rt_avail_flights = {}
	cabin_class = amend_dict.get('cabin_class', '')	
	flight_fin_key, flight_id = self.get_amend_sell_keys(amend_dict, ow_avail_flights, cabin_class, False)
	rt_flight_fin_key, rt_flight_id = self.get_amend_sell_keys(amend_dict, rt_avail_flights, cabin_class, True)
	if flight_fin_key:
	   ow_booking_price_list = self.trip_pricing_details(flight_fin_key, self.cookies)
	else: ow_booking_price_list = []
	if rt_flight_fin_key:
	    rt_booking_price_list = self.trip_pricing_details(rt_flight_fin_key, self.cookies)
	else: rt_booking_price_list = []
	amend_dict['booking_price'] = {flight_id:ow_booking_price_list, rt_flight_id:rt_booking_price_list}
	amend_dict['flight_no'] = str([flight_id, rt_flight_id])
	if not flight_fin_key:
	    msg = "Flight not found, TripId:%s"%amend_dict.get('trip_ref', '')
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR %s, %s"%(amend_dict.get('pnr', ''), msg))
	    self.send_mail("Amend Failed", msg, "amend", "Indigo", "indigo_common")
	    return
	if not rt_flight_fin_key and self.rt_round_amendment:
	    msg = "Flight not found, TripId:%s"%amend_dict.get('trip_ref', '')
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR %s, %s"%(amend_dict.get('pnr', ''), msg))
	    self.send_mail("Amend Failed", msg, "amend", "Indigo", "indigo_common")
	    return
        data = [
          ('indiGoAvailability_Submit', 'Select & Continue'),
          ('wt_form', '1'),
          ('indiGoAvailability.fareRules.DoesAgreeToTerms', ''),
          ('stringFlexiIGPOW', ''),
          ('stringFlexiIGPRT', ''),
          ('stringFlexiIGPMCT', ''),
          ('stringFlexiIGPMCF', ''),
          ('stringFlexiIGPMCFI', ''),
          ('gstContact.SkipInformation', 'true'),
          ('gstContact.ReadOnly', 'true'),
        ]
        if self.trip_type == 'OW':
            data.extend([('indiGoAvailability.MarketFareKeys[0]', str(flight_fin_key))])
        elif self.trip_type == 'RT':
            if self.ow_amendment or self.rt_amendment:
                data.extend([('indiGoAvailability.MarketFareKeys[0]', str(flight_fin_key))])
            else:
                data.extend([
                        ('indiGoAvailability.MarketFareKeys[0]', str(flight_fin_key)),
                        ('indiGoAvailability.MarketFareKeys[1]', str(rt_flight_fin_key)),
                ])
                
        headers = {
            'Pragma': 'no-cache',
            'Origin': 'https://www.goindigo.in',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': '*/*',
            'Cache-Control': 'no-cache',
            'Referer': 'https://www.goindigo.in/booking/flight-select-modification.html',
            'Connection': 'keep-alive',
        }
        url = 'https://book.goindigo.in/Flight/SelectAEM'
        yield FormRequest(url, callback=self.parse_booking_final, formdata=data, \
		cookies=self.cookies, headers=headers, dont_filter=True, meta={'amend_dict':amend_dict})

    def parse_booking_final(self, response):
        sel = Selector(response)
	amend_dict = response.meta['amend_dict']
        if 'AssignSeatWithRoleOneAEM' not in response.url:
            msg = "scraper failed to navigate Booking View, TripId:%s"%amend_dict.get('trip_ref', '')
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR %s, %s"%(amend_dict.get('pnr', ''), msg))
	    self.send_mail("Amend Failed", msg, "amend", "Indigo", "indigo_common")
            return 
        url = 'https://book.goindigo.in/Booking/View'
        yield Request(url, callback=self.parse_final, cookies=self.cookies, dont_filter=True,\
			meta={'amend_dict':response.meta['amend_dict']})
    
    def parse_final(self, response):
        '''
        receiving the amendment booking view and its details
        and navigating into payment page
        '''
        sel = Selector(response)
	amend_dict = response.meta['amend_dict']
	price_dict = {}
	price_keys = sel.xpath('//div[@class="sumry_table"]//table//tr//td[1]//text()').extract()
	for key in price_keys:
	    key = normalize(key.strip())
	    value = normalize(''.join(sel.xpath('//div[@class="sumry_table"]//table//tr\
			//td[contains(text(), "%s")]/following-sibling::td//text()'%normalize(key)).extract()))
	    if value:
	        value = value.split(' ')[0]
		price_dict.update({key:value.replace(',', '').strip()})
        res_token = ''.join(sel.xpath('//form[@action="/Booking/Finish"]//input[@name="__RequestVerificationToken"]/@value').extract())
        if not res_token:
            msg = "Scraper failed to get Amend flight details, TripId:%s"%amend_dict.get('trip_ref', '')
            with open('%s_amend.html'%amend_dict.get('pnr', ''), 'w+') as f:
                f.write('%s'%response.body)
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR %s, %s"%(amend_dict.get('pnr', ''), msg))
	    self.send_mail("Amend Failed", msg, "amend", "Indigo", "indigo_common")
            return
        data = [
                ('__RequestVerificationToken', res_token),
        ]
	amend_dict.update({'price_dict':price_dict})
        url = 'https://book.goindigo.in/Booking/Finish'
        yield FormRequest(url, callback=self.parse_payment, formdata=data, dont_filter=True,\
			 meta={'amend_dict':amend_dict, 'price_dict':price_dict})

    def parse_payment(self, response):
        '''
        checking tolerance and submitting payment
        '''
        sel = Selector(response)
	amend_dict = response.meta['amend_dict']
        with open('%s_before_payment.html'%amend_dict.get('pnr', ''), 'w+') as f:
            f.write('%s'%response.body)
        if 'Payment/New' not in response.url:
            msg = "scraper failed to navigate Payment page, TripId:%s"%amend_dict.get('trip_ref', '')
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR %s, %s"%(amend_dict.get('pnr', ''), msg))
	    self.send_mail("Amend Failed", msg, "amend", "Indigo", "indigo_common")
            return
        total_fares = {}
        tot_keys = ["Total Price", "Total Paid", "Total Amount Due"]
        for i in tot_keys:
            price = normalize(''.join(sel.xpath('//div[@class="paymentFinalDetails paymt_review"]//ul//li//span[contains(text(), "%s")]/following-sibling::label//text()'%i).extract()))
            total_fares.update({i:price})
	due_amount = total_fares.get('Total Amount Due', '')
	amend_dict.update({'Total Price':total_fares.get('Total Price')})
	token = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[@name="__RequestVerificationToken"]/@value').extract())
	ac = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[@id="agencyPayment_AccountNumber"]/@value').extract())
	pay_methond = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[contains(@id, "agencyPayment_PaymentMethodCode")]/@value').extract())
	ac_type = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[@id="agencyPayment_PaymentMethodType"]/@value').extract())
	amount = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[@id="agencyPayment_QuotedAmount"]/@value').extract())
	currency_type = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[@id="agencyPayment_QuotedCurrencyCode"]/@value').extract())
	data = {
          '__RequestVerificationToken': token,
          'agencyPayment.AccountNumber': ac,
          'agencyPayment.PaymentMethodCode': pay_methond,
          'agencyPayment.PaymentMethodType': ac_type,
          'agencyPayment.QuotedCurrencyCode': currency_type,
          'agencyPayment.QuotedAmount': amount,
            }
	if due_amount:
	    tolerance_level, price_diff = self.check_tolerance_level(amend_dict, due_amount)
	    amend_dict.update({'price_diff':price_diff})
	else:
	    price_diff = ''
	    msg = "Price Due amount not found, TripId:%s"%amend_dict.get('trip_ref', '')
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR %s, %s"%(amend_dict.get('pnr', ''), msg))
	    self.send_mail("Amend Failed", msg, "amend", "Indigo", "indigo_common")
	    return
	if tolerance_level:
	    msg = "Fare increased by Airline, TripId:%s"%amend_dict.get('trip_ref', '')
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR %s, %s"%(amend_dict.get('pnr', ''), msg))
	    self.send_mail("Amend Failed", msg, "amend", "Indigo", "indigo_common")
	    return
	if int(amend_dict.get('proceed_to_book', 0)) == 1:
	    url = 'https://book.goindigo.in/Payment/Create'
	    yield FormRequest(url, callback=self.create_payment, formdata=data, meta={'amend_dict':amend_dict})
	else:
	    self.insert_values_into_db(amend_dict, "Amend Failed", "PNR %s, %s"%(amend_dict.get('pnr', ''), 'Test Booking'))

    def create_payment(self, response):
	sel = Selector(response)
	amend_dict = response.meta.get('amend_dict', {})
	url = 'https://book.goindigo.in/Booking/PostCommit'
	self.insert_values_into_db(amend_dict, "Success", "PNR %s, %s"%(amend_dict.get('pnr', ''), ''))	
        time.sleep(3)
	amend_dict = response.meta['amend_dict']
	with open('%s_create_payment.html'%amend_dict.get('pnr', ''), 'w+') as f:
            f.write('%s'%response.body)
	headers = {
	    'Pragma': 'no-cache',
	    'Accept-Encoding': 'gzip, deflate, br',
	    'Accept-Language': 'en-US,en;q=0.9',
	    'Upgrade-Insecure-Requests': '1',
	    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
	    'Referer': 'https://book.goindigo.in/Booking/PostCommit',
	    'Connection': 'keep-alive',
	    'Cache-Control': 'no-cache',
	}
        yield Request(url, headers=headers, callback=self.parse_final_report,\
		meta={'amend_dict':response.meta['amend_dict']}, dont_filter=True)

    def parse_final_report(self, response):
	sel = Selector(response)
	amend_dict = response.meta['amend_dict']
	with open('%s_payment.html'%amend_dict.get('pnr', ''), 'w+') as f:
            f.write('%s'%response.body)
	self.insert_values_into_db(amend_dict, "Success", "PNR %s, %s"%(amend_dict.get('pnr', ''), ''))
