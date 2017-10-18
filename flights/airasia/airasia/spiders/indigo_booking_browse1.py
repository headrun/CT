import re
import json
import md5
import smtplib
import MySQLdb
import datetime
import smtplib, ssl
from email import encoders
from ast import literal_eval
from scrapy import signals
from scrapy.spider import Spider
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from scrapy.http import FormRequest, Request
from email.mime.multipart import MIMEMultipart
from scrapy.selector import Selector
from ConfigParser import SafeConfigParser
from scrapy.xlib.pydispatch import dispatcher

class IndioBookBrowse(Spider):
    name = "indio1_browse"
    start_urls = ["https://www.goindigo.in/"]
    handle_httpstatus_list = [404, 500]
    def __init__(self, *args, **kwargs):
        super(IndioBookBrowse, self).__init__(*args, **kwargs)
	self.book_dict = kwargs.get('jsons', {})
	self.price_patt = re.compile('\d+')
	self.trip_type = ''
	self.flight1 = self.flight2 = self.flight3 = self.flight4 = self.flight5 = {}
	self.ow_input_flight = self.rt_input_flight = {}
        self.ow_fullinput_dict = self.rt_fullinput_dict = {}
	self.journey = {"origin":"","destination":"","fromDate":"","toDate":"",
			"multiCity":[],"promo":"","market":"","currencyCode":"",
			"adults":'',"children":'',"infants":'',"journeyType":""}
	self.insert_query = 'insert into indigo_booking_report (sk, airline, pnr, flight_number, from_location, to_location, triptype, cleartrip_price, indigo_price, status_message, tolerance_amount, error_message, paxdetails, created_at, modified_at) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), error_message=%s, paxdetails=%s, sk=%s'
	self.error_query = 'insert into indigo_booking_report (sk, airline, pnr, status_message, error_message, paxdetails, created_at, modified_at) values (%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), error_message=%s, sk=%s'
	self.conn = MySQLdb.connect(host="localhost", user = "root", db='TICKETBOOKINGDB', charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()

    def parse(self, response):
        sel = Selector(response)
	data = [
	  ('agentLogin.Username', 'oti003'),
	  ('agentLogin.Password', 'Clr@987IND'),
	  ('IsEncrypted', 'true'),
	]
	url = 'https://book.goindigo.in/Agent/Login'
	yield FormRequest(url, callback=self.prase_login, formdata=data)

    def prase_login(self, response):
	sel = Selector(response)
	check_text = ''.join(sel.xpath('//input[@class="postLogin"]//@value').extract())
	login_status = True
	if 'LoginError' in response.url:
	    login_status = False
	try: book_dict = eval(self.book_dict)
	except Exception as e:
		self.send_mail('Input Error', e.message)
		book_dict = {}
	oneway_date = self.get_date_format(book_dict.get('onewaydate', ''))
	return_date = self.get_date_format(book_dict.get('returndate', ''))
	self.trip_type = book_dict.get('triptype', '')
	if self.trip_type == 'OneWay': journey_type = 'oneWay'
	elif self.trip_type == 'RoundTrip': journey_type = 'roundTrip'
	else: journey_type = 'multicity'
	pax = book_dict.get('paxdetails', {})
        adult_count, chaild_count, infant_count = pax.get('adult', '0'), pax.get('chaild', '0'), pax.get('infant', '0')
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
	else:
	    data.update({
		  		search_trip%'.Origin': self.flight1.get('origin', ''),
		  		search_trip%'.OriginOne': self.flight1.get('origin', ''),
		  		search_trip%'.DestinationOne': self.flight1.get('destination', ''),
		  		search_trip%'.DepartureDateOne': flight1_date,
		 		search_trip%'.OriginTwo': self.flight2.get('origin', ''),
		  		search_trip%'.DestinationTwo': self.flight2.get('destination', ''),
		  		search_trip%'.DepartureDateTwo': flight2_date,
			})
	    if flight3_date:
		data.update({
		  		search_trip%'.OriginThree': self.flight3.get('origin', ''),
		  		search_trip%'.DestinationThree': self.flight3.get('destination', ''),
		  		search_trip%'.DepartureDateThree': flight3_date,
			     })
	    if flight4_date:
		data.update({
				search_trip%'.OriginFour': self.flight4.get('origin', ''),
		  		search_trip%'.DestinationFour': self.flight4.get('destination', ''),
		  		search_trip%'.DepartureDateFour': flight4_date,
			    })
	    if flight5_date:
		data.update({
				search_trip%'.OriginFive': self.flight5.get('origin', ''),
		  		search_trip%'.DestinationFive': self.flight5.get('destination', ''),
		  		search_trip%'.DepartureDateFive': flight5_date,
			
			    })
	if login_status:
	    url = 'https://book.goindigo.in/Flight/IndexAEM'
	    yield FormRequest(url, callback=self.parse_search, formdata=data, meta={'book_dict':book_dict})
	else:
	    self.send_mail("IndiGo Booking Scraper Login Failed", '')
	    self.insert_error_msg(book_dict, "IndiGo Booking Scraper Login Failed")

    def parse_search(self, response):
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
	    self.insert_error_msg(book_dict, "Flights not found %s"%book_dict.get('tripid', ''))
	m1_sell, m2_sell, m3_sell, m4_sell, m5_sell = ['']*5
	market1, market2, market3, market4, market5 = seg_flights.get(0, {}), seg_flights.get(1, {}),\
			seg_flights.get(2, {}), seg_flights.get(3, {}), seg_flights.get(4, {})

	if self.trip_type == 'OneWay' or self.trip_type == 'RoundTrip':
	    market1_ct_flight = book_dict.get('onewayflightid', '').replace(' ', '').replace('-', '')
	    m1_class = book_dict.get('onewayclass', '')
	    m1_fare, m1_sell = self.get_flight_keys(market1, m1_class, market1_ct_flight)
	    if not m1_sell: fare_error = True
	    if self.trip_type == 'RoundTrip':
		market2_ct_flight = book_dict.get('returnflightid', '').replace(' ', '').replace('-', '')
		m2_class = book_dict.get('returnclass', '')
		m2_fare, m2_sell = self.get_flight_keys(market2, m2_class, market2_ct_flight)
		if not m2_sell : fare_error = True
	else:
	    m1_ct_flight = self.flight1.get('flightid', '').replace(' ', '').replace('-', '')
	    m1_class = self.flight1.get('class', '')
	    m1_fare, m1_sell = self.get_flight_keys(market1, m1_class, m1_ct_flight)
	    m2_ct_flight = self.flight2.get('flightid', '').replace(' ', '').replace('-', '')
            m2_class = self.flight2.get('class', '')
            m2_fare, m2_sell = self.get_flight_keys(market2, m2_class, m2_ct_flight)
	    m3_ct_flight = self.flight3.get('flightid', '').replace(' ', '').replace('-', '')
            m3_class = self.flight3.get('class', '')
            m3_fare, m3_sell = self.get_flight_keys(market3, m3_class, m3_ct_flight)
	    m4_ct_flight = self.flight4.get('flightid', '').replace(' ', '').replace('-', '')
            m4_class = self.flight4.get('class', '')
            m4_fare, m4_sell = self.get_flight_keys(market4, m4_class, m4_ct_flight)
	    m5_ct_flight = self.flight5.get('flightid', '').replace(' ', '').replace('-', '')
            m5_class = self.flight5.get('class', '')
            m5_fare, m5_sell = self.get_flight_keys(market5, m5_class, m5_ct_flight)
	    if market1 and not m1_sell: fare_error = True
	    if market2 and not m2_sell: fare_error = True
	    if market3 and not m3_sell: fare_error = True
	    if market4 and not m4_sell: fare_error = True
	    if market5 and not m5_sell: fare_error = True
	if fare_error:
	    self.send_mail("Booking failed %s"%book_dict.get('tripid', ''), "Flight not found in selected class")
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
	    else:
	        data.update({
			'indiGoAvailability.MarketFareKeys[0]': m1_sell,
			'indiGoAvailability.MarketFareKeys[1]': m2_sell,
			})
	        if m3_sell: data['indiGoAvailability.MarketFareKeys[2]'] = m3_sell
	        if m4_sell: data['indiGoAvailability.MarketFareKeys[3]'] = m4_sell
	        if m5_sell: data['indiGoAvailability.MarketFareKeys[4]'] = m5_sell
	    url = 'https://book.goindigo.in/Flight/SelectAEM'
	    yield FormRequest(url, callback=self.parse_mem, formdata=data, cookies=cookies, meta={'book_dict':book_dict})

    def parse_mem(self, response):
	sel = Selector(response)
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
	cookies.update({'journey': json.dumps(self.journey)})
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
			 method='GET', meta={'book_dict':response.meta['book_dict']})

    def parse_member(self, response):
	sel = Selector(response)
	book_dict = response.meta['book_dict']
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
	guests_lst = book_dict.get('guestdetails', [])
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
  			'indiGoPassengers.Infants[0].Gender': gender,
  			'indiGoPassengers.Infants[0].Name.First': inf.get('firstname', ''),
  			'indiGoPassengers.Infants[0].Name.Last': inf.get('lastname', ''),
  			'indiGoPassengers.Infants[0].dobDay': str(bo_day),
  			'indiGoPassengers.Infants[0].dobMonth': str(bo_month),
  			'indiGoPassengers.Infants[0].dobYear': str(bo_year),
  			'indiGoPassengers.Infants[0].DateOfBirth': b_date,
  			'indiGoPassengers.Infants[0].AttachedPassengerNumber': '0',
			})
	url = 'https://book.goindigo.in/Passengers/EditAEM'
	yield FormRequest(url, callback=self.parse_pax, formdata=data, cookies=cookies, meta={'book_dict':book_dict})

    def parse_pax(self, response):
	sel = Selector(response)
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
	yield Request(url, callback=self.parse_payment, headers=headers, cookies=cookies, meta={'book_dict':response.meta['book_dict']})	

    def parse_payment(self, response):
	sel = Selector(response)
	book_dict = response.meta['book_dict']
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
	pay_methond = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[@id="agencyPayment_PaymentMeth:wodCode"]/@value').extract())
	ac_type = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[@id="agencyPayment_PaymentMethodType"]/@value').extract())
	amount = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[@id="agencyPayment_QuotedAmount"]/@value').extract())
	currency_type = ''.join(sel.xpath('//form[@action="/Payment/Create"]/input[@id="agencyPayment_QuotedCurrencyCode"]/@value').extract())
	if not amount:
	    self.send_mail("Agency Account not found %s"%book_dict.get('tripid', ''), '')
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
	    #print block
	    yield FormRequest(url, callback=self.parse_create_payment, formdata=data, cookies=cookies,\
			 meta={'book_dict':book_dict, 'cookies_':cookies, \
			'headers_':headers, "tamount":amount, 'tolerance_value':tolerance_value})
	else:
	    self.send_mail("fare increased by IndiGo for %s"%book_dict.get('tripid', ''), '')
	    vals = (
                book_dict.get('tripid', ''), 'IndiGo', '', '', book_dict.get('origin', ''),
                book_dict.get('destination', ''), book_dict.get('triptype', ''), book_dict.get('ctprice', ''),
                amount, 'Booking Failed', tolerance_value, 'Fare increased by IndiGo', '',
                'Fare increased by IndiGo', '', book_dict.get('tripid', '')
                )
            self.cur.execute(self.insert_query, vals)
	    self.conn.commit()

    def parse_create_payment(self, response):
	sel = Selector(response)
	cookies = response.meta['cookies_']
	headers = response.meta['headers_']
	url = 'https://book.goindigo.in/Booking/PostCommit'
	yield Request(url, callback=self.parse_final_report, headers=headers, \
		cookies=cookies, meta={'book_doct':response.meta['book_dict'], \
		'tamount':response.meta['tamount'], 'tolerance_value':response.meta['tolerance_value']})

    def parse_final_report(self, response):
	sel = Selector(response)
	book_dict = response.meta['book_dict']
	id_price = response.meta['tamount']
	tolerance_value = response.meta['tolerance_value']
	pnr = ''.join(sel.xpath('//label[contains(text(), "Booking Reference")]/following-sibling::h4/text()').extract())
	booking_conform = ''.join(sel.xpath('//label[contains(text(), "Booking Status")]/following-sibling::h4//text()').extract())
	payment_status = ''.join(sel.xpath('//label[contains(text(), "Payment Status")]/following-sibling::h4//text()').extract())
	vals = (
		book_dict.get('tripid', ''), 'IndiGo', pnr, '', book_dict.get('origin', ''),
		book_dict.get('destination', ''), book_dict.get('triptype', ''), book_dict.get('ctprice', ''),
		id_price, booking_conform, tolerance_value, '', '',
		'', '', book_dict.get('tripid', '')
		)
	self.cur.execute(self.insert_query, vals)
	self.conn.commit()
	    

    def check_tolerance(self, ctprice, indiprice):
	tolerance_value, is_proceed = 0, 0
	total_fare = float(indiprice)
        if total_fare != 0:
            tolerance_value = total_fare - int(ctprice.replace(',', '').strip())
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
	if not seg_ft:
	    return ('', '')
	fare_class_dict = {'FLEXI':'J', 'SAVER': 'R', 'LITE': 'B'}
        fin_fare_dict = {}
        for key in seg_ft.keys():
            if ct_flt_id in key:
                fin_fare_dict = seg_ft.get(key, {})
                break
            else:
                fin_fare_dict = {}
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
                '', 'Booking Failed', '', err, '',
                err, '', book_dict.get('tripid', '')
                )
        self.cur.execute(self.insert_query, vals)
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
        recievers_list = ["prasadk@notemonk.com"]
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
