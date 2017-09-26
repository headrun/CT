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
    name = "indiobooking_browse"
    start_urls = ["https://www.goindigo.in/"]
    handle_httpstatus_list = [404, 500]
    def __init__(self, *args, **kwargs):
        super(IndioBookBrowse, self).__init__(*args, **kwargs)
	self.book_dict = kwargs.get('jsons', {})
	self.price_patt = re.compile('\d+')
	self.trip_type = ''
	self.flight1 = self.flight2 = self.flight3 = self.flight4 = self.flight5 = {}
	self.journey = {"origin":"","destination":"","fromDate":"","toDate":"",
			"multiCity":[],"promo":"","market":"","currencyCode":"INR",
			"adults":'',"children":'',"infants":'',"journeyType":""}

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
	except :
		#send mail
		book_dict = {}
	oneway_date = self.get_date_format(book_dict.get('onewaydate', ''))
	return_date = self.get_date_format(book_dict.get('returndate', ''))
	self.trip_type = book_dict.get('triptype', '')
	if self.trip_type == 'OneWay': journey_type = 'oneWay'
	elif self.trip_type == 'RoundTrip': journey_type = 'roundTrip'
	else: journey_type = 'multicity'
	pax = book_dict.get('paxdetails', {})
        adult_count, chaild_count, infant_count = pax.get('adult', '0'), pax.get('chaild', '0'), pax.get('infant', '0')
	self.journey.update({'destination':book_dict.get('destination', ''),
		'origin':book_dict.get('origin', ''), 'fromDate':oneway_date,
		'adults':adult_count, 'children':chaild_count,
		'infants':infant_count, 'journeyType': journey_type
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
                  search_trip%'.CurrencyCode': 'INR',
                  search_trip%'.InfantCount': '0',
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
	import pdb;pdb.set_trace()
	#pickup the flight from seg_flights
	if not seg_flights:
	    #send mail
	    err = "Failed to fetch flights"
	m1_sell, m2_sell, m3_sell, m4_sell, m5_sell = ['']*5
	market1, market2, market3, market4, market5 = seg_flights.get(0, {}), seg_flights.get(1, {}),\
			seg_flights.get(2, {}), seg_flights.get(3, {}), seg_flights.get(4, {})

	if self.trip_type == 'OneWay' or self.trip_type == 'RoundTrip':
	    market1_ct_flight = book_dict.get('onewayflightid', '')
	    m1_class = book_dict.get('onewayclass', '')
	    m1_fare, m1_sell = self.get_flight_keys(market1, m1_class, market1_ct_flight)
	    if not m1_sell: fare_error = True
	    if self.trip_type == 'RoundTrip':
		market2_ct_flight = book_dict.get('returnflightid', '')
		m2_class = book_dict.get('returnclass', '')
		m2_fare, m2_sell = self.get_flight_keys(market2, m2_class, market2_ct_flight)
		if not m2_sell : fare_error = True
	else:
	    m1_ct_flight = self.flight1.get('flightid', '')
	    m1_class = self.flight1.get('class', '')
	    m1_fare, m1_sell = self.get_flight_keys(market1, m1_class, m1_ct_flight)
	    m2_ct_flight = self.flight2.get('flightid', '')
            m2_class = self.flight2.get('class', '')
            m2_fare, m2_sell = self.get_flight_keys(market2, m2_class, m2_ct_flight)
	    m3_ct_flight = self.flight3.get('flightid', '')
            m3_class = self.flight3.get('class', '')
            m3_fare, m3_sell = self.get_flight_keys(market3, m3_class, m3_ct_flight)
	    m4_ct_flight = self.flight4.get('flightid', '')
            m4_class = self.flight4.get('class', '')
            m4_fare, m4_sell = self.get_flight_keys(market4, m4_class, m4_ct_flight)
	    m5_ct_flight = self.flight5.get('flightid', '')
            m5_class = self.flight5.get('class', '')
            m5_fare, m5_sell = self.get_flight_keys(market5, m5_class, m5_ct_flight)
	    if market1 and not m1_sell: fare_error = True
	    if market2 and not m2_sell: fare_error = True
	    if market3 and not m3_sell: fare_error = True
	    if market4 and not m4_sell: fare_error = True
	    if market5 and not m5_sell: fare_error = True
	if fare_error:
	    error_val = "Flight not found in selected class"
	    #send mail
	    import pdb;pdb.set_trace()
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
	url = 'https://book.goindigo.in/Passengers/EditAEM'
	yield FormRequest(url, callback=self.parse_pax, formdata=data, cookies=cookies)

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
	yield Request(url, callback=self.parse_payment, headers=headers, cookies=cookies)	

    def parse_payment(self, response):
	sel = Selector(response)
	import pdb;pdb.set_trace()
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

    def get_date_format(self, text):
        if text:
            try:
                date = datetime.datetime.strptime(text, '%Y-%m-%d')
                re_date = date.strftime('%d %b %Y')
                return re_date
            except:
                return ''
        else: return 

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
