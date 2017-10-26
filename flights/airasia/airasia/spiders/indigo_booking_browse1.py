import re
import json
import time
import md5
import smtplib
import MySQLdb
import datetime
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
_cfg = SafeConfigParser()
_cfg.read('airline_names.cfg')

class IndioBookBrowse(Spider):
    name = "indio1_browse"
    start_urls = ["https://www.goindigo.in/"]
    handle_httpstatus_list = [404, 500]

    def __init__(self, *args, **kwargs):
        super(IndioBookBrowse, self).__init__(*args, **kwargs)
	self.booking_dict = kwargs.get('jsons', {})
	self.price_patt = re.compile('\d+')
	self.trip_type = ''
	self.flight1 = self.flight2 = self.flight3 = self.flight4 = self.flight5 = {}
	self.ow_input_flight = self.rt_input_flight = {}
        self.ow_fullinput_dict = self.rt_fullinput_dict = {}
	self.journey = {"origin":"","destination":"","fromDate":"","toDate":"",
			"multiCity":[],"promo":"","market":"","currencyCode":"",
			"adults":'',"children":'',"infants":'',"journeyType":""}
	self.insert_query  = 'insert into indigo_booking_report (sk, airline, pnr, flight_number, from_location, to_location, triptype, cleartrip_price, indigo_price, status_message, tolerance_amount, error_message, paxdetails, price_details, created_at, modified_at) values (%s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), error_message=%s, paxdetails=%s, sk=%s'
        self.error_query = 'insert into indigo_booking_report (sk, airline, pnr, status_message, error_message, paxdetails, created_at, modified_at) values (%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), error_message=%s, sk=%s'
	self.conn = MySQLdb.connect(host='localhost', user = 'headrun', db='TICKETBOOKINGDB', charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()

    def get_travel_date(self, date):
        try:
            date_ = datetime.datetime.strptime(date.strip(), '%d-%b-%y')
            date_format = date_.strftime('%Y-%m-%d')
        except:
            date_format, day, month, year = ['']*4
        return date_format

    def process_input(self):
        book_dict, paxdls = {}, {}
        if self.booking_dict.get('trip_type', '') == 'OW': triptype = 'OneWay'
        elif self.booking_dict.get('trip_type', '') == 'RT': triptype = 'RoundTrip'
        else: triptype = 'MultiCity'
        self.get_input_segments(self.booking_dict)
        try: ow_input_flight = self.ow_input_flight[0]
        except: ow_input_flight = {}
        try:rt_input_flight = self.rt_input_flight[0]
        except: rt_input_flight = {}
        ow_flt_id, rt_flt_id = [], []
        for i in self.ow_input_flight:
            flt = i.get('flight_no', '')
            if flt: ow_flt_id.append(flt)
        for i in self.rt_input_flight:
            flt = i.get('flight_no', '')
            if flt: rt_flt_id.append(flt)
        pnr = self.booking_dict.get('auto_pnr', '')
        onewaymealcode = ow_input_flight.get('meal_codes', [])
        returnmealcode = rt_input_flight.get('meal_codes', [])
        onewaybaggagecode = ow_input_flight.get('baggage_codes', [])
        returnbaggagecode = rt_input_flight.get('baggage_codes', [])
        onewaydate = self.booking_dict.get('departure_date', '')#self.ow_input_flight.get('date', '')
        onewaydate = str(self.get_travel_date(onewaydate))
        returndate = self.booking_dict.get('return_date', '')#self.rt_input_flight.get('date', '')
        returndate = str(self.get_travel_date(returndate))
        origin = self.booking_dict.get('origin_code', '')
        destination = self.booking_dict.get('destination_code', '')
        pax_details = self.booking_dict.get('pax_details', {})
        contact_no = self.booking_dict.get('contact_mobile', '')
        countryphcode = self.booking_dict.get('country_phonecode', '')
        countrycode = self.booking_dict.get('country_code', '')
        email = self.booking_dict.get('emailid', '')
	ticket_class = self.booking_dict.get('ticket_booking_class', '')
	ticket_class_dict = {'Economy' : 'LITE', 'Regular' : 'SAVER', 'Business' : 'FLEXI'}
	ticket_class = ticket_class_dict.get(ticket_class, '')
        ct_ow_price = self.ow_fullinput_dict.get('amount', 0)
        ct_rt_price = self.rt_fullinput_dict.get('amount', 0)
	currencycode = self.booking_dict.get('currency_code', '')
        if triptype == 'RoundTrip': ct_price = ct_ow_price + ct_rt_price
        else: ct_price = ct_ow_price
        fin_pax, fin_infant, fin_child = [], [], []
	gender_format_dict = {'Mr': 'Male', 'Mrs': 'Female', 'Ms': 'Female' , 'Miss': 'Female', 'Mstr': 'Male'}
        for key, lst in pax_details.iteritems():
            pax_ = {}
            title, firstname, lastname, day, month, year = lst
	    gender = gender_format_dict.get(title.strip(), '')
            if day and month and year: dob = '%s-%s-%s'%(year, month, day)
            else: "1989-02-02"
            pax_.update({'title':title, 'firstname':firstname, 'lastname':lastname,
                        'dob':dob, 'gender': gender, 'email':email, 'countrycode':'IN'})
            if 'adult' in key:fin_pax.append(pax_)
            elif 'child'in key:fin_child.append(pax_)
            elif 'infant' in key:fin_infant.append(pax_)
	paxdls.update({
                        'adult':str(self.booking_dict.get('no_of_adults', 0)),
                        'child':str(self.booking_dict.get('no_of_children', 0)),
                        'infant':str(self.booking_dict.get('no_of_infants', 0))
                        })

        book_dict.update({
                        "tripid":self.booking_dict.get('trip_ref', ''),
                        'onewayflightid': ow_flt_id, "onewayclass": ticket_class,
                        'returnflightid': rt_flt_id, 'returnclass': ticket_class,
                        'pnr': pnr, 'onewaymealcode': onewaymealcode,
                        'returnmealcode': returnmealcode, 'ctprice': str(ct_price),
                        'onewaybaggagecode': onewaybaggagecode, 'returnbaggagecode':returnbaggagecode,
                        'onewaydate': onewaydate, 'returndate': returndate, 'paxdetails':paxdls,
                        'origin': origin, 'destination': destination,
                        'triptype': triptype, 'multicitytrip':{}, 'emergencycontact':{},
                        'guestdetails':fin_pax, 'infant': fin_infant, 'childdetails':fin_child,
                        "countrycode": countrycode, "countryphcode": countryphcode, "phonenumber": contact_no,
                        "email": email,"currencycode" : currencycode,
                        })
        return book_dict

    def parse(self, response):
	print 'Parse function works'
        sel = Selector(response)
	data = [
	  ('agentLogin.Username', _cfg.get('indigo', 'login_name')),
	  ('agentLogin.Password', _cfg.get('indigo', 'login_pwd')),
	  ('IsEncrypted', 'true'),
	]
	url = 'https://book.goindigo.in/Agent/Login'
	yield FormRequest(url, callback=self.prase_login, formdata=data)

    def prase_login(self, response):
	print 'Login works'
	sel = Selector(response)
	check_text = ''.join(sel.xpath('//input[@class="postLogin"]//@value').extract())
	login_status = True
	if 'LoginError' in response.url:
	    login_status = False
	try: 
		#book_dict = eval(self.book_dict)
		book_dict = OrderedDict(eval(self.booking_dict))
                self.booking_dict = book_dict
                pnr = book_dict.get('pnr', '')
                book_dict = self.process_input()
	except Exception as e:
		#logging.debug(e.message)
		self.send_mail('Input Error', e.message)
		#First Error Mesg To Db
		self.insert_error_msg(book_dict, "Wrong input dict format")
		book_dict, pnr = {}, ''
		return
	oneway_date = self.get_date_format(book_dict.get('onewaydate', ''))
	return_date = self.get_date_format(book_dict.get('returndate', ''))
	self.trip_type = book_dict.get('triptype', '')
	if self.trip_type == 'OneWay': journey_type = 'oneWay'
	elif self.trip_type == 'RoundTrip': journey_type = 'roundTrip'
	else: return #journey_type = 'multicity'
	pax = book_dict.get('paxdetails', {})
        adult_count, chaild_count, infant_count = pax.get('adult', '0'), pax.get('child', '0'), pax.get('infant', '0')
	currency_code = book_dict.get('currencycode', '')
	self.journey.update({'destination':book_dict.get('destination', ''),
		'origin':book_dict.get('origin', ''), 'fromDate':oneway_date,
		'adults':adult_count, 'children':chaild_count, 'infants':infant_count,
		'journeyType': journey_type, 'currencyCode':book_dict.get('currencycode', '')
		})
	if self.trip_type == 'RoundTrip':
	    self.journey.update({'toDate':return_date})	
	multicitytrip = book_dict.get('multicitytrip', {})
        self.flight1, self.flight2, self.flight3, self.flight4, self.flight5 = multicitytrip.get('flight1', {}), \
				multicitytrip.get('flight2', {}), multicitytrip.get('flight3', {}), \
				multicitytrip.get('flight4', {}), multicitytrip.get('flight5', {})
        flight1_date = self.get_date_format(self.flight1.get('date', ''))
        flight2_date = self.get_date_format(self.flight2.get('date', ''))
        flight3_date = self.get_date_format(self.flight3.get('date', ''))
	flight4_date = self.get_date_format(self.flight4.get('date', ''))
	flight5_date = self.get_date_format(self.flight5.get('date', ''))
        if self.trip_type == 'OneWay':
		search_trip = 'indiGoOneWaySearch%s'
	elif self.trip_type == 'RoundTrip':
		search_trip = 'indiGoRoundTripSearch%s'
	else:
		search_trip = 'indiGoMultiLegSearch%s'
	data = {
                  'indiGoPromoAuthenticationData.CustomerNumber': '',
                  'indiGoPromoAuthenticationData.PromoCode': '',
                  search_trip%'.CurrencyCode': currency_code,
                  search_trip%'.InfantCount': infant_count,
                  search_trip%'.IsArmedForces': 'false',
                  search_trip%'.IsFamilyFare': 'false',
                  search_trip%'.IsSRC': 'false',
                  search_trip%'.IsStudentFare': 'false',
                  search_trip%'.IsUMNR': 'false',
                  search_trip%'.MaxAdult': '9',
                  search_trip%'.MaxChild': '4',
                  search_trip%'.Origin': book_dict.get('origin', ''),
                  '_Submit': '',
                  'isArmedForceHiddenRT2': '0',
		}
	if chaild_count and chaild_count !='0':
	    data.update({
			  search_trip%'.PassengerCounts[1].Count': chaild_count,
			  search_trip%'.PassengerCounts[1].PaxType': 'CHD'
			})
	if adult_count and adult_count !='0':
	    data.update({
	                  search_trip%'.PassengerCounts[0].Count': adult_count,
	                  search_trip%'.PassengerCounts[0].PaxType': 'ADT',
			})
	if self.trip_type == 'OneWay' or self.trip_type == 'RoundTrip':
	    data.update({
		  search_trip%'.Origin': book_dict.get('origin', ''),
                  search_trip%'.ReturnDate': return_date,
                  search_trip%'.DepartureDate': oneway_date,
                  search_trip%'.Destination': book_dict.get('destination', ''),
                })
	if login_status:
	    url = 'https://book.goindigo.in/Flight/IndexAEM'
	    yield FormRequest(url, callback=self.parse_search, formdata=data, meta={'book_dict':book_dict})
	else:
	    self.send_mail("IndiGo Booking Scraper Login Failed", '')
	    #Second Error Msg to Db
	    self.insert_error_msg(book_dict, "IndiGo Booking Scraper Login Failed")

    def parse_search(self, response):
	print 'Search works'
	sel = Selector(response)
        book_dict = response.meta['book_dict']
	json_body = json.loads(response.body)
	res_headers = json.dumps(str(response.request.headers))
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
        cookies, fare_error = {}, False
	res_headers = json.dumps(str(response.request.headers))
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
        cookies = {}
        for i in my_dict.get('Cookie', []):
            data_ = i.split(';')
            for data in data_:
                try : key, val = data.split('=', 1)
                except : continue
                cookies.update({key.strip():val.strip()})
	avil_dict = json_body.get('indiGoAvailability', {})
	seg_trips = avil_dict.get('trips', [])
	seg_flights = {}
	for seg_idx, seg in enumerate(seg_trips):
	    flights = seg.get('flightDates', [])
	    if flights:flights = flights[0]
	    else: flights = {}
	    flt = flights.get('flights', [])
	    flight_dict = {}
	    for idx, i in enumerate(flt):
		carrier = i.get('carrierCode', '').strip()
		flt_no = i.get('flightNumber', '').strip()
		m_sellkey = i.get('sellKey', '').strip()
		fares = i.get('fares', [])
		fare_dict = {}
		for fare in fares:
		    productclass = fare.get('productClass', '')
		    f_sellkey = fare.get('sellKey', '')
		    pax_fares = fare.get('passengerFares', [])
		    if pax_fares: pax_fares = pax_fares[0]
		    else: pax_fares = {}
		    fareamount = pax_fares.get('fareAmount', 0)
		    fare_dict.update({productclass:(fareamount, f_sellkey)})
		flight_dict.update({'%s%s'%(carrier,flt_no):{'fares':fare_dict, 'sellkey':m_sellkey}})
	    seg_flights.update({seg_idx:flight_dict})
	#pickup the flight from seg_flights
	if not seg_flights:
	    self.send_mail("Flights not found %s"%book_dict.get('tripid', ''), '')
	    #Third Error Msd To Db
	    self.insert_error_msg(book_dict, "Flights not found %s"%book_dict.get('tripid', ''))
	m1_sell, m2_sell, m3_sell, m4_sell, m5_sell = ['']*5
	market1, market2, market3, market4, market5 = seg_flights.get(0, {}), seg_flights.get(1, {}),\
			seg_flights.get(2, {}), seg_flights.get(3, {}), seg_flights.get(4, {})
	m1_fare, m2_fare = '', ''
	if self.trip_type == 'OneWay' or self.trip_type == 'RoundTrip':
	    market1_ct_flight = book_dict.get('onewayflightid', '')#.replace(' ', '').replace('-', '')
	    m1_class = book_dict.get('onewayclass', '')
	    m1_fare, m1_sell = self.get_flight_keys(market1, m1_class, market1_ct_flight)
	    if not m1_sell: fare_error = True
	    if self.trip_type == 'RoundTrip':
		market2_ct_flight = book_dict.get('returnflightid', '')#.replace(' ', '').replace('-', '')
		m2_class = book_dict.get('returnclass', '')
		m2_fare, m2_sell = self.get_flight_keys(market2, m2_class, market2_ct_flight)
		if not m2_sell : fare_error = True
	price_details = {'ow_fare' : m1_fare, 'rt_fare' : m2_fare}
	print m1_sell, m2_sell
	if fare_error:
	    self.send_mail("Booking failed %s"%book_dict.get('tripid', ''), "Flight not found in selected class")
	    #Fourth Error Msg To Db
	    self.insert_error_msg(book_dict, "Flight not found in selected class")
	else:
	    data = { 
		  'indiGoAvailability_Submit': 'Select & Continue',
		  'wt_form': '1',
		  'indiGoAvailability.fareRules.DoesAgreeToTerms': '',
		  'stringFlexiIGPOW': '',
		  'stringFlexiIGPRT': '',
		  'stringFlexiIGPMCT': '',
		  'stringFlexiIGPMCF': '',
		  'stringFlexiIGPMCFI': '',
		  'gstContact.SkipInformation': 'true',
		  'gstContact.ReadOnly': 'true',
		  #'indiGoAvailability.MarketFareKeys[0]': sell,
		}
	    if self.trip_type == 'OneWay' or self.trip_type == 'RoundTrip':
	        data.update({
			'indiGoAvailability.MarketFareKeys[0]': m1_sell,
			})
	        if self.trip_type == 'RoundTrip':
	            data.update({'indiGoAvailability.MarketFareKeys[1]': m2_sell})
	    url = 'https://book.goindigo.in/Flight/SelectAEM'
	    yield FormRequest(url, callback=self.parse_mem, formdata=data, cookies=cookies, meta={'book_dict':book_dict, 'price_details' : price_details})

    def parse_mem(self, response):
	print 'Seach click works'
	sel = Selector(response)
	res_headers = json.dumps(str(response.request.headers))
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
	price_details = response.meta.get('price_details')
        cookies = {}
        for i in my_dict.get('Cookie', []):
            data_ = i.split(';')
            for data in data_:
                try : key, val = data.split('=', 1)
                except : continue
                cookies.update({key.strip():val.strip()})
	print cookies
	cookies.update({'journey': json.dumps(self.journey)})
	print self.journey
	cookies.update({'userSession': 'true',
    			's_ppv': 'flight-select',
    			's_ppn': 'flight-select',
    			's_cc': 'true',
			})
	headers = {
		    'Pragma': 'no-cache',
		    'Origin': 'https://www.goindigo.in',
		    'Accept-Encoding': 'gzip, deflate, br',
		    'Accept-Language': 'en-US,en;q=0.8',
		    'Accept': '*/*',
		    'Referer': 'https://www.goindigo.in/booking/passenger-edit.html',
		    'Connection': 'keep-alive',
		    'Cache-Control': 'no-cache',
		}
	url = 'https://book.goindigo.in/Passengers/EditAEM'
	yield Request(url, callback=self.parse_member, headers=headers, cookies=cookies,\
			 method='GET', meta={'book_dict':response.meta['book_dict'], 'price_details' : price_details})

    def parse_member(self, response):
	print 'flight select journey works'
	sel = Selector(response)
	print response.url	
	book_dict = response.meta['book_dict']
	open('edit_old.html', 'w').write(response.body)
	res_headers = json.dumps(str(response.request.headers))
	edit_data = json.loads(response.body)
	price_details = response.meta.get('price_details')
	print price_details
	baggage_keys, meal_keys = self.get_baggage_meals(edit_data, book_dict)
	print edit_data['indiGoAvailableSsr']
	import pdb;pdb.set_trace()
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
        cookies = {}
        for i in my_dict.get('Cookie', []):
            data_ = i.split(';')
            for data in data_:
                try : key, val = data.split('=', 1)
                except : continue 
                cookies.update({key.strip():val.strip()})
	cookies.update({'journey':self.journey})
	data = {
		  'clearTheAirSsr.IsSelected': 'False',
		  'contactCookie.RetainDetails': 'false',
		  'contactRegister.Member.DateOfBirth': '',
		  'contactRegister.Member.NewPasswordConfirmation': '',
		  'contactRegister.Member.Password': '',
		  'contactRegister.Member.Username': '',
		  'goodKarmaSsr.Selected': 'false',
		  'hidToSubmitMap': '1',
		  'indiGoContact.AddressLine1': '',
		  'indiGoContact.AddressLine2': '',
		  'indiGoContact.AgreeToPolicy': 'true',
		  'indiGoContact.City': '',
		  'indiGoContact.CountryCode': '',
		  'indiGoContact.CountryProvinceState': '',
		  'indiGoContact.EmergencyContactRelationship': '',
		  'indiGoContact.PostalCode':'',
		  'indiGoContact.ReceivePromotional': 'false',
		  'indiGoContact.TypeCode': 'P',
		  'indiGoContact.WorkPhone': '',
		  'indiGoContact.WorkPhoneCountryCode': '',
		  'indiGoPassengers.FavouriteIsMember': '0',
		  'indiGoPassengers.IsMegaCabSelected': 'false',
		  'indiGoPassengers.MatrixEmail': '',
		  'indiGoPassengers.MatrixMobileNumber': '',
		  'wt_fields': 'indiGoContact.Name.First;indiGoContact.Name.Last;indiGoContact.AddressLine1;indiGoContact.City;indiGoContact.CountryCode;indiGoContact.CountryProvinceState;indiGoContact.PostalCode;indiGoContact.HomePhone;indiGoContact.OtherPhone;indiGoContact.EmailAddress;',
		  'wt_form': '1',
		  'indiGoContact.HomePhone': book_dict.get('phonenumber', ''),
		  'indiGoContact.EmailAddress': book_dict.get('email', ''),
		  'indiGoContact.HomePhoneCountryCode': '91',
		  'indiGoContact.OtherPhone': '',
		  'indiGoContact.OtherPhoneCountryCode': '',
		  'indiGoPassengers.chkboxIndigoplus': 'false',
		  'indiGoSsr.Ssrs': 'undefined',
		  'fastForwardSsr.Selected': 'false',
		  'fastForwardSsr.FFWDSectors': '',
		  'indiGoInsurance.Selected': 'false',
		  'indiGoInsurance.TravelInsuranceTermsConditions': 'false',
		  'indiGoInsurance.InsuranceParticipantKey': '',
		  'indiGoInsurance.InsuranceQuoteKey': '',
		  'redirectToSeatmap.Selected': 'true',
		  'submitToSeatMap': 'Select Seats',
		}
	child_details = book_dict.get('childdetails', [])
	all_keys = baggage_keys + meal_keys
	data.update({'indiGoSsr.Ssrs' : all_keys})
	guests_lst = book_dict.get('guestdetails', [])
	if child_details:
		guests_lst.extend(child_details)
	for idx, i in enumerate(guests_lst):
	    if i.get('gender', '') == 'Male': gender = '1'
	    else: gender = '2'
	    data.update({
			'indiGoPassengers[%s].Name.First'%idx: i.get('firstname', ''),
  			'indiGoPassengers[%s].Name.Last'%idx: i.get('lastname', ''),
  			'indiGoPassengers[%s].Name.Title'%idx: i.get('title', ''),
 			'indiGoPassengers[%s].Info.Gender'%idx: gender,
  			'indiGoPassengers[%s].PassengerNumber'%idx: str(idx)
			})
	    if idx == 0:
		data.update({
				'indiGoContact.Name.First': i.get('firstname', ''),
                  		'indiGoContact.Name.Last': i.get('lastname', ''),
                  		'indiGoContact.Name.Title': i.get('title', ''),

			    })
	infant = book_dict.get('infant', [])
	if infant:
	    inf = infant[0]
	    birth_date = inf.get('dob', '')
            bo_day, bo_month, bo_year = ['']*3
            if birth_date:
                birth_date = datetime.datetime.strptime(birth_date, '%Y-%m-%d')
                bo_day, bo_month, bo_year = birth_date.day, birth_date.month, birth_date.year
		b_date = str(birth_date.date())
            gender = inf.get('gender', '')
            if gender == 'Male': gender_val = 1
            else: gender_val = 2
	    data.update({
			'indiGoPassengers.Infants[0].PreviousAttachedPassengerNumber': '0',
  			'indiGoPassengers.Infants[0].Info.Gender': str(gender_val),
  			'indiGoPassengers.Infants[0].Name.First': inf.get('firstname', ''),
  			'indiGoPassengers.Infants[0].Name.Last': inf.get('lastname', ''),
  			'indiGoPassengers.Infants[0].dobDay': str(bo_day),
  			'indiGoPassengers.Infants[0].dobMonth': str(bo_month),
  			'indiGoPassengers.Infants[0].dobYear': str(bo_year),
  			'indiGoPassengers.Infants[0].DateOfBirth': b_date,
  			'indiGoPassengers.Infants[0].AttachedPassengerNumber': '0',
			})
	url = 'https://book.goindigo.in/Passengers/EditAEM'
	yield FormRequest(url, callback=self.parse_pax, formdata=data, cookies=cookies, meta={'book_dict':book_dict, 'price_details' : price_details})

    def parse_pax(self, response):
	print 'Passenger edit works'
	open('edit.html', 'w').write(response.body)
	sel = Selector(response)
	price_details = response.meta.get('price_details')
	res_headers = json.dumps(str(response.request.headers))
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
        cookies = {}
        for i in my_dict.get('Cookie', []):
            data_ = i.split(';')
            for data in data_:
                try : key, val = data.split('=', 1)
                except : continue
                cookies.update({key.strip():val.strip()})
	headers = {
		    'Pragma': 'no-cache',
		    'Accept-Encoding': 'gzip, deflate, br',
		    'Accept-Language': 'en-US,en;q=0.8',
		    'Upgrade-Insecure-Requests': '1',
		    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
		    'Referer': 'https://www.goindigo.in/booking/seat-select.html',
		    'Connection': 'keep-alive',
		    'Cache-Control': 'no-cache',
		}
	url = 'https://book.goindigo.in/Payment/New'
	yield Request(url, callback=self.parse_payment, headers=headers, cookies=cookies, meta={'book_dict':response.meta['book_dict'], 'price_details' : price_details })	

    def parse_payment(self, response):
	print 'Payment works'
	book_dict = response.meta['book_dict']
	'''if 'Your session is about to expire in' in response.body:
		self.send_mail("Session expired, site response is slow for %s"%book_dict.get('tripid', ''), '')
		self.insert_error_msg(book_dict, "Session expired at payment function")
		return'''
	sel = Selector(response)
	price_details = response.meta.get('price_details')
	pay_summary = [i.strip() for i in sel.xpath('//div[@class="sumry_table"]//td/text()').extract()]
	from itertools import izip
	i = iter(pay_summary)
	price_details_ = dict(izip(i, i))
	price_details.update(price_details_)
	import pdb;pdb.set_trace()
	open('pays.html', 'w').write(response.body)
	res_headers = json.dumps(str(response.request.headers))
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
        cookies, journey = {}, {}
        for i in my_dict.get('Cookie', []):
            data_ = i.split(';')
            for data in data_:
                try : key, val = data.split('=', 1)
                except : continue
                cookies.update({key.strip():val.strip()})
	cookies.update({'journey':json.dumps(self.journey)})
	cookies.update({'journeyPath': '[{"id":"paxDetails","className":"passenger-details","i18nKey":"passengers"},{"id":"paxAddOns","className":"add-ons","i18nKey":"add-ons"},{"id":"paxInsurance","className":"insurance","i18nKey":"insurance"},{"id":"seatSelect","className":"seat-select","i18nKey":"seat-select"}]'})
	cookies.update({
			'RandomCookie': 'Random',
			'aemLoginStatus': 'Agent',
    			'userSession': 'true',
			's_cc': 'true',
			'_sdsat_Login Status': 'Logged In',
			's_ppn': 'Checkout',
			})
	ct_price = book_dict.get('ctprice', '0')
	token = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[@name="__RequestVerificationToken"]/@value').extract())
	ac = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[@id="agencyPayment_AccountNumber"]/@value').extract())
	#pay_methond = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[@id="agencyPayment_PaymentMeth:wodCode"]/@value').extract())
	pay_methond = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[contains(@id, "agencyPayment_PaymentMethodCode")]/@value').extract())
	ac_type = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[@id="agencyPayment_PaymentMethodType"]/@value').extract())
	amount = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[@id="agencyPayment_QuotedAmount"]/@value').extract())
	currency_type = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[@id="agencyPayment_QuotedCurrencyCode"]/@value').extract())
	is_proceed, tolerance_value = 0, 0
	if not amount:
	    self.send_mail("Agency Account not found %s"%book_dict.get('tripid', ''), '')
	    #Fifth Error Msg To Db
	    self.insert_error_msg(book_dict, "Agency Account not found")
	else:
	    tolerance_value, is_proceed = self.check_tolerance(ct_price, amount)
	headers = {
		    'Pragma': 'no-cache',
		    'Accept-Encoding': 'gzip, deflate, br',
		    'Accept-Language': 'en-US,en;q=0.8',
		    'Upgrade-Insecure-Requests': '1',
		    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
		    'Referer': 'https://book.goindigo.in/Payment/New',
		    'Connection': 'keep-alive',
		    'Cache-Control': 'no-cache',
		}
	if is_proceed == 1:
	    data = {
		  '__RequestVerificationToken': token,
		  'agencyPayment.AccountNumber': ac,
		  'agencyPayment.PaymentMethodCode': pay_methond,
		  'agencyPayment.PaymentMethodType': ac_type,
		  'agencyPayment.QuotedCurrencyCode': currency_type,
		  'agencyPayment.QuotedAmount': amount,
		}
	    url = 'https://book.goindigo.in/Payment/Create'
	    print "Do not go forward"
	    import pdb;pdb.set_trace()
	    #yield FormRequest(url, callback=self.parse_create_payment, formdata=data, cookies=cookies,\
			 #headers=headers, meta={'book_dict':book_dict, 'cookies_':cookies, \
			#'headers_':headers, "tamount":amount, 'tolerance_value':tolerance_value, 'price_details' : price_details})
	else:
	    self.send_mail("fare increased by IndiGo for %s or response error"%book_dict.get('tripid', ''), '')
	    vals = (
                book_dict.get('tripid', ''), 'IndiGo', '', '', book_dict.get('origin', ''),
                book_dict.get('destination', ''), book_dict.get('triptype', ''), book_dict.get('ctprice', ''),
                amount, 'Booking Failed', tolerance_value, 'Fare increased by IndiGo', '', '{}',
                'Fare increased by IndiGo', '', book_dict.get('tripid', '')
                )
	    #Manual Error Insert To Db
            self.cur.execute(self.insert_query, vals)
	    self.conn.commit()

    def parse_create_payment(self, response):
	print 'create payment works'
	print response.url
	sel = Selector(response)
	cookies = response.meta['cookies_']
	price_details = response.meta.get('price_details')
	#Proof
	open('PostCommit.html', 'w').write(response.body)
	headers = response.meta['headers_']
	import pdb;pdb.set_trace()
	url = 'https://book.goindigo.in/Booking/PostCommit'
	time.sleep(3)
	yield Request(url, callback=self.parse_final_report, headers=headers, \
		cookies=cookies, meta={'book_dict':response.meta['book_dict'], \
		'tamount':response.meta['tamount'], 'tolerance_value':response.meta['tolerance_value'], 'price_details' : price_details}, dont_filter=True)

    def parse_final_report(self, response):
	print 'final report payment works'
	print response.url
	price_details = response.meta.get('price_details')
	open('IndigoFinal.html', 'w').write(response.body)
	sel = Selector(response)
	book_dict = response.meta['book_dict']
	id_price = response.meta['tamount']
	tolerance_value = response.meta['tolerance_value']
	pnr = ''.join(sel.xpath('//label[contains(text(), "Booking Reference")]/following-sibling::h4/text()').extract())
	booking_conform = ''.join(sel.xpath('//label[contains(text(), "Booking Status")]/following-sibling::h4//text()').extract())
	import pdb;pdb.set_trace()
	payment_status = ''.join(sel.xpath('//label[contains(text(), "Payment Status")]/following-sibling::h4//text()').extract())
	#price_details = '{}'#Code needed here
	vals = (
		book_dict.get('tripid', ''), 'IndiGo', pnr, '', book_dict.get('origin', ''),
		book_dict.get('destination', ''), book_dict.get('triptype', ''), book_dict.get('ctprice', ''),
		id_price, booking_conform, tolerance_value, '', '', price_details,
		'', '', book_dict.get('tripid', '')
		)
	#Manual Error Insert To DB 2
	try:
		self.cur.execute(self.insert_query, vals)
		self.conn.commit()
	except:
		self.send_mail("IndiGo Booking Scraper Success Insert Failed: %s" % pnr, '')	
		
	print 'Done'
	    

    def check_tolerance(self, ctprice, indiprice):
	tolerance_value, is_proceed = 0, 0
	total_fare = float(indiprice)
        if total_fare != 0:
            tolerance_value = total_fare - float(ctprice.replace(',', '').strip())
            if tolerance_value >= 2000:
                    is_proceed = 0  #movie it to off line
            else: is_proceed = 1
        else:
            tolerance_value, is_proceed = 0, 0
	return (tolerance_value, is_proceed)

    def get_date_format(self, text):
        if text:
            try:
                date = datetime.datetime.strptime(text, '%Y-%m-%d')
                re_date = date.strftime('%d %b %Y')
                return re_date
            except:
                return ''
        else: return ''

    def get_flight_keys(self, seg_ft, ct_class, ct_flt_id):
	'''
	Should return customer selected flight + fare from Json comparing with the customer inputs.
	Sell keys below needs to be passed to next function, important one as it is used throughout.
	'''
	if not seg_ft:
	    return ('', '')
	fare_class_dict = {'FLEXI':'J', 'SAVER': 'R', 'LITE': 'B'}
        fin_fare_dict = {}
	#Check the loop here
        for key in seg_ft.keys():
	    bool_check = False
	    for ct_flt_id_ in ct_flt_id:
		    ct_id = ct_flt_id_.replace(' ', '').replace('-', '') 
	            if ct_id == key:
        	        fin_fare_dict = seg_ft.get(key, {})
                	bool_check = True
	            else:
        	        fin_fare_dict = {}
	    if bool_check:
		    break
	fares_dict = fin_fare_dict.get('fares', {})
        final_flt_tuple = fares_dict.get(fare_class_dict.get(ct_class, ''), ['']*2)
	flt_sell = fin_fare_dict.get('sellkey', '')
        finfare, fare_sell = final_flt_tuple
	if flt_sell and fare_sell:
	    fin_sell = '%s|%s'%(fare_sell, flt_sell)
	else: fin_sell = ''
	return (finfare, fin_sell)

    def insert_error_msg(self, book_dict, err):
	vals = (
                book_dict.get('tripid', ''), 'IndiGo', '', '', book_dict.get('origin', ''),
                book_dict.get('destination', ''), book_dict.get('triptype', ''), book_dict.get('ctprice', ''),
                '', 'Booking Failed', '', err, '','',
                err, '', book_dict.get('tripid', '')
                )
	try:
	        self.cur.execute(self.insert_query, vals)
	except:
		print 'some insert error'
		import pdb;pdb.set_trace()
        self.conn.commit()

    def send_mail(self, sub, error_msg):
        recievers_list = []
        '''
        recievers_list = ['rfan.madha@cleartrip.com',
                                'rohit.kulkarni@cleartrip.com',
                                'samir.nayak@cleartrip.com',
                                'pallavi.khandekar@cleartrip.com',
                             ]
        '''
        recievers_list = ["prasadk@notemonk.com", "aravind@headrun.com"]
        #recievers_list = ["prasadk@notemonk.com", "rohit.kulkarni@cleartrip.com"]
        sender, receivers = 'prasadk@notemonk.com', ','.join(recievers_list)
        ccing = []
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '%s On %s'%(sub, str(datetime.datetime.now().date()))
        mas = '<p>%s</p>'%error_msg
        msg['From'] = sender
        msg['To'] = receivers
        msg['Cc'] = ','.join(ccing)
        tem = MIMEText(''.join(mas), 'html')
        msg.attach(tem)
        s = smtplib.SMTP('smtp.gmail.com:587')
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(sender, 'amma@nanna')
        s.sendmail(sender, (recievers_list + ccing), msg.as_string())
        s.quit()

    def get_fin_fares_dict(self, flight_fares, ct_flights):
        aa_keys = flight_fares.keys()
        fin_fare_dict, flight_no = {}, ''
        for key in aa_keys:
            flt_status_key = False
            for ct_flt in ct_flights:
                ct_flt = ct_flt.replace(' ', '').replace('-', '').strip()
                if ct_flt.lower() in key.lower(): flt_status_key = True
                else: flt_status_key = False
            if flt_status_key:
                fin_fare_dict = flight_fares.get(key, {})
                flight_no = key
                break
            else:
                fin_fare_dict, flight_no = {}, ''
        return (fin_fare_dict, flight_no)

    def get_input_segments(self, segments):
        all_segments = segments.get('all_segments', [])
        ow_flight_dict, rt_flight_dict = {}, {}
        dest = segments.get('destination_code', '').strip()
        origin = segments.get('origin_code', '').strip()
        from_to = '%s-%s'%(origin, dest)
        if len(all_segments) == 1:
            key = ''.join(all_segments[0].keys())
            ow_flight_dict = all_segments[0][key]
            self.ow_fullinput_dict = ow_flight_dict
            if ow_flight_dict:
                try: self.ow_input_flight = ow_flight_dict.get('segments', [])
                except: self.ow_input_flight = {}
            else:
                self.ow_input_flight = {}
        elif len(all_segments) == 2:
            key1, key2 = ''.join(all_segments[0].keys()), ''.join(all_segments[1].keys())
            flight_dict1, flight_dict2 = all_segments[0][key1], all_segments[1][key2]
            f_to = flight_dict1.get('segments', [])
            self.ow_input_flight = flight_dict1.get('segments', [])
            self.rt_input_flight = flight_dict2.get('segments', [])
            self.ow_fullinput_dict, self.rt_fullinput_dict = flight_dict2, flight_dict1
        else:
            vals = (
                        segments.get('trip_ref', ''), 'AirAsia', '', '', segments.get('origin_code', ''),
                        segments.get('destination_code', ''), "Booking Failed", '', "Multi-city booking", json.dumps(segments),
                        'Multi-city booking', json.dumps(segments), segments.get('trip_ref', ''),
                   )
            self.cur.execute(self.existing_pnr_query, vals)

    def get_baggage_meals(self, edit_data, book_dict):
	baggages, meals = [], []
	if edit_data['indiGoAvailableSsr']['availableSsrsList'] != None:
		meals_available_ow = edit_data['indiGoAvailableSsr']['availableSsrsList']['ssrsMealsList'][0]['paxSsrsList'][0]['ssrsList']
		baggages_available_ow = edit_data['indiGoAvailableSsr']['availableSsrsList']['ssrsBaggagesList'][0]['paxSsrsList'][0]['ssrsList']
		
		meals_available_rt = edit_data['indiGoAvailableSsr']['availableSsrsList']['ssrsMealsList'][1]['paxSsrsList'][0]['ssrsList']
		baggages_available_rt = edit_data['indiGoAvailableSsr']['availableSsrsList']['ssrsBaggagesList'][1]['paxSsrsList'][0]['ssrsList']

		baggages, meals = [], []
		for i in baggages_available_ow:
			for j in book_dict['onewaybaggagecode']:
				if j in i['value']:
					baggages.append(i['key'])
		for k in meals_available_ow:
			for l in book_dict['onewaymealcode']:
				if l in k['key']:
					meals.append(k['key'])
		for i in baggages_available_rt:
			for j in book_dict['returnbaggagecode']:
				if j in i['value']:
					baggages.append(i['key'])
		for k in meals_available_rt:
			for l in book_dict['returnmealcode']:
				if l in k['key']:
					meals.append(k['key'])
	if baggages == [] or meals == []:
		print 'baggage : %s' % len(baggages)
		print 'meals : %s' % len(meals)
		
	return baggages, meals
