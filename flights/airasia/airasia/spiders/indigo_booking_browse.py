import re
import json
import time
import md5
import smtplib
import MySQLdb
import datetime
import requests
import smtplib, ssl
from email import encoders
from ast import literal_eval
from scrapy import signals
from booking_scrapers.utils import *
from scrapy.spiders import Spider
from collections import OrderedDict
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from scrapy.http import FormRequest, Request
from email.mime.multipart import MIMEMultipart
from scrapy.selector import Selector
from ConfigParser import SafeConfigParser
from scrapy.xlib.pydispatch import dispatcher
from indigo_utils import *
_cfg = SafeConfigParser()
_cfg.read('airline_names.cfg')

class IndigoBookBrowse(Spider, IndigoUtils):
    name = "indigobooking_browse"
    start_urls = ["https://www.goindigo.in/"]
    handle_httpstatus_list = [404, 500]

    def __init__(self, *args, **kwargs):
        super(IndigoBookBrowse, self).__init__(*args, **kwargs)
        self.ow_meals_connection = False
	self.multiple_pcc = False
        self.ow_baggage_connection = False
        self.rt_meals_connection = False
        self.rt_baggage_connection = False
        self.connection_check = False
        self.ow_flights_connection = False
        self.rt_flights_connection = False
        self.booking_dict = kwargs.get('jsons', {})
        self.proceed_to_book = 0
        self.adult_count, self.child_count, self.infant_count= '0', '0', '0'
        self.price_patt = re.compile('\d+')
        self.log = create_logger_obj('indigo_booking')
        self.trip_type = ''
        self.flight1 = self.flight2 = self.flight3 = self.flight4 = self.flight5 = {}
        self.ow_input_flight = self.rt_input_flight = {}
        self.ow_fullinput_dict = self.rt_fullinput_dict = {}
        self.journey = {"origin":"","destination":"","fromDate":"","toDate":"",
            "multiCity":[],"promo":"","market":"","currencyCode":"",
            "adults":'',"children":'',"infants":'',"journeyType":""}
        self.insert_query  = 'insert into indigo_booking_report (sk, airline, pnr, flight_number, from_location, to_location, triptype, cleartrip_price, indigo_price, status_message, tolerance_amount, error_message, paxdetails, price_details, created_at, modified_at) values (%s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), error_message=%s, paxdetails=%s, sk=%s, price_details=%s'
        self.final_insert_query  = 'insert into indigo_booking_report (sk, airline, pnr, flight_number, from_location, to_location, triptype, cleartrip_price, indigo_price, status_message, tolerance_amount, oneway_date, return_date, error_message, paxdetails, price_details, created_at, modified_at) values (%s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), error_message=%s, paxdetails=%s, sk=%s, price_details=%s, pnr=%s, status_message=%s, indigo_price=%s, cleartrip_price=%s'
        self.error_query = 'insert into indigo_booking_report (sk, airline, pnr, status_message, error_message, paxdetails, created_at, modified_at) values (%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), error_message=%s, sk=%s'
        self.conn = MySQLdb.connect(host='localhost', user = 'root', passwd='root', db='TICKETBOOKINGDB', charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()

    def parse(self, response):
        print 'Parse function works'
        sel = Selector(response)
	book_dict, self.pcc_name = self.get_pcc_name()
	if self.multiple_pcc:
            self.insert_error_msg(book_dict, "Multiple PCC booking")
            logging.debug('Multiple PCC booking')
            return
	try:
	        data = [
      ('agentLogin.Username', _cfg.get(self.pcc_name, 'login_name')),
      ('agentLogin.Password', _cfg.get(self.pcc_name, 'login_pwd')),
      ('IsEncrypted', 'true'),
                ]
	except:
		self.insert_error_msg(book_dict, "PCC %s not available for scrapper" % self.pcc_name)
		logging.debug('PCC not avaialble for scrapper')
		return
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
            all_segments = self.booking_dict['all_segments']                
            segment_len = len([i.keys() for i in all_segments])
            if self.booking_dict['trip_type'] == 'RT' and segment_len == 1:
                segments_list = []
                segment1 = filter(None, [i if i['seq_no'] == '1' else '' for i in all_segments[0][all_segments[0].keys()[0]]['segments']])
                segment2 = filter(None, [i if i['seq_no'] == '2' else '' for i in all_segments[0][all_segments[0].keys()[0]]['segments']])
                for index, seg in enumerate([segment1, segment2]):
                    new_all_segments = {}
                    amount = float('0')
                    if index == 0:
                        amount = all_segments[0][all_segments[0].keys()[0]]['amount']
                    new_all_segments.update({all_segments[0].keys()[0] : {'amount' : amount, 'segments' : seg}})
                    segments_list.append(new_all_segments)
                self.booking_dict['all_segments'] = segments_list
                book_dict = self.booking_dict
            pnr = book_dict.get('pnr', '')
            logging.debug(self.booking_dict.get('trip_ref'))
            book_dict = self.process_input()
        except Exception as e:
            logging.debug(e.message)
            self.send_mail('Input Error', e.message)
            #First Error Mesg To Db
            self.insert_error_msg(book_dict, "Wrong input dict format")
            book_dict, pnr = {}, ''
            return
        if book_dict['triptype'] == 'MultiCity':
            self.send_mail('Multicity triptype request received to scrapper', 'Multicity Booking Error')
            self.insert_error_msg(book_dict, "Multi-city booking")
            logging.debug('Multicity triptype request received to scrapper')
            return
        if self.ow_meals_connection or self.rt_meals_connection:
            self.insert_error_msg(book_dict, "Meals site level issue, so not handled")
            logging.debug('Meals multiple sectors not handled')
            return
        if self.ow_baggage_connection or self.rt_baggage_connection:
            self.insert_error_msg(book_dict, "Baggages site level issue, so not handled")
            logging.debug('Baggages multiple sectors not handled')
            return
        if self.connection_check:
            self.insert_error_msg(book_dict, "Connection Flights")
            logging.debug('Connection flights received')
            #return
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
            #Currently not supported
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
            self.send_mail("Unable to login on Login ID %s" % _cfg.get('indigo', 'login_name') , 'Scrapper Unable to login on Login ID')
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
        seg_flights = self.parse_flight_segments(seg_trips)
        #pickup the flight from seg_flights
        if not seg_flights:
            self.send_mail("Flights not found %s"%book_dict.get('tripid', ''), '')
            #Third Error Msg To Db
            self.insert_error_msg(book_dict, "Flights not found"%book_dict.get('tripid', ''))
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
        #print m1_sell, m2_sell
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
            yield FormRequest(url, callback=self.parse_mem, formdata=data, cookies=cookies, meta={'book_dict':book_dict})

    def parse_mem(self, response):
        print 'Seach click works'
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
        print 'flight select journey works'
        sel = Selector(response)
        book_dict = response.meta['book_dict']
        price_details = {}
        res_headers = json.dumps(str(response.request.headers))
        edit_data = json.loads(response.body)
        if not edit_data['indiGoPriceBreakdown']['indigoJourneyPrice']['indigoJourneyPriceItineraryList'][0]['journeyPriceItinerary'].keys():
            vals = (
                book_dict.get('tripid', ''), 'IndiGo', '', '', book_dict.get('origin', ''),
                book_dict.get('destination', ''), book_dict.get('triptype', ''), book_dict.get('ctprice', ''),
                '', 'Journey details empty, wrong input', '', 'Try again later', '', '{}',
                'Try again later', '', book_dict.get('tripid', ''), ''
                )
            self.cur.execute(self.insert_query, vals)
            self.conn.commit()
            return
        price_details, all_keys = self.process_price_details(edit_data, price_details, book_dict)
        if self.ow_baggage_connection or self.ow_meals_connection or self.rt_baggage_connection or self.rt_meals_connection:
            return
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
        sel = Selector(response)
        price_details = response.meta.get('price_details')
        #pay_summary = [i.strip() for i in sel.xpath('//div[@class="sumry_table"]//td/text()').extract()]
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
        default_datetime = datetime.datetime.strptime('1989-01-01', '%Y-%m-%d')
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
            key_pair_list = '<>'.join(response.xpath('//table[@summary="Flight details"]//tr//td[2]/text()').extract())
            infant_tuple = filter(None, [(key, val) if ' Infant' in key else '' for key,val in price_details.iteritems()])
            infant_value = ''
            if infant_tuple:
                try:
                    infant_count = book_dict['paxdetails']['infant']
                    infant_value = float(infant_tuple[-1]/int(infant_count))
                except:
                    infant_value = book_dict['paxdetails']['infant']
                    pass
            segments = '-'.join(sel.xpath('//div[@class="price-itinerary-journey"]//div[@class="stations_name"]/span[@class="stn"]/text()').extract())
            pnr, flight_no = 100, key_pair_list
            ow_date = datetime.datetime.strptime(book_dict.get('onewaydate', '1989-01-01'), '%Y-%m-%d')
            if book_dict.get('returndate', '1989-01-01'):
                rt_date = datetime.datetime.strptime(book_dict.get('returndate', '1989-01-01'), '%Y-%m-%d')
            else:
                rt_date = default_datetime
            vals = (
            book_dict.get('tripid', ''), 'IndiGo', pnr, flight_no, book_dict.get('origin', ''),
            book_dict.get('destination', ''), book_dict.get('triptype', ''), book_dict.get('ctprice', ''),
            str(amount), 'Success', tolerance_value, ow_date , rt_date ,'', '', json.dumps(price_details),
            '', '', book_dict.get('tripid', ''), json.dumps(price_details), pnr, 'Success', str(amount), book_dict.get('ctprice', '')
            )
            #self.insert_query = self.insert_query + ', price_details=%s, pnr=%s'
            try:
                self.cur.execute(self.final_insert_query, vals)
                self.conn.commit()
            except Exception as e:
                self.send_mail("IndiGo Booking Scraper Success Insert Failed: %s" % e, '')  
            if int(self.proceed_to_book) == 1:
		print "Booked"
		return
                yield FormRequest(url, callback=self.parse_create_payment, formdata=data, cookies=cookies,\
             headers=headers, meta={'book_dict':book_dict, 'cookies_':cookies, \
            'headers_':headers, "tamount":amount, 'tolerance_value':tolerance_value, 'price_details' : price_details, 'key_pair_list' : key_pair_list})
        else:
            self.send_mail("Fare increased by IndiGo for %s by %s or response error" % ((book_dict.get('tripid', ''), tolerance_value)), '')
            vals = (
                book_dict.get('tripid', ''), 'IndiGo', '', '', book_dict.get('origin', ''),
                book_dict.get('destination', ''), book_dict.get('triptype', ''), book_dict.get('ctprice', ''),
                amount, 'Booking failed, price rise', tolerance_value, 'Fare increased by IndiGo', '', json.dumps(price_details),
                'Fare increased by IndiGo', '', book_dict.get('tripid', ''), ''
                )
            #Manual Error Insert To Db
            self.cur.execute(self.insert_query, vals)
            self.conn.commit()

    def parse_create_payment(self, response):
        print 'create payment works'
        sel = Selector(response)
        cookies = response.meta['cookies_']
        price_details = response.meta.get('price_details')
        key_pair_list = response.meta.get('key_pair_list')
        headers = response.meta['headers_']
        url = 'https://book.goindigo.in/Booking/PostCommit'
        time.sleep(3)
        yield Request(url, callback=self.parse_final_report, headers=headers, \
        cookies=cookies, meta={'book_dict':response.meta['book_dict'], \
        'tamount':response.meta['tamount'], 'tolerance_value':response.meta['tolerance_value'], 'price_details' : price_details, 'key_pair_list' : key_pair_list}, dont_filter=True)

    def parse_final_report(self, response):
        print 'final report payment works'
        flight_no = response.meta.get('key_pair_list')
        price_details = response.meta.get('price_details')
        sel = Selector(response)
        book_dict = response.meta['book_dict']
        default_datetime = datetime.datetime.strptime('1989-01-01', '%Y-%m-%d')
        ow_date = datetime.datetime.strptime(book_dict.get('onewaydate', '1989-01-01'), '%Y-%m-%d')
        if book_dict.get('returndate', '1989-01-01'):
            rt_date = datetime.datetime.strptime(book_dict.get('returndate', '1989-01-01'), '%Y-%m-%d')
        else:
            rt_date = default_datetime
        id_price = response.meta['tamount']
        amount = response.meta['tamount']
        tolerance_value = response.meta['tolerance_value']
        pnr = ''.join(sel.xpath('//label[contains(text(), "Booking Reference")]/following-sibling::h4/text()').extract()).strip()
        names = book_dict.get('tripid', '') + pnr
        open('%s.html' % names, 'w').write(response.body)
        if pnr:
            booking_conform = ''.join(sel.xpath('//label[contains(text(), "Booking Status")]/following-sibling::h4//text()').extract()).strip()
            payment_status = ''.join(sel.xpath('//label[contains(text(), "Payment Status")]/following-sibling::h4//text()').extract()).strip()
            vals = (
                book_dict.get('tripid', ''), 'IndiGo', pnr, flight_no, book_dict.get('origin', ''),
                book_dict.get('destination', ''), book_dict.get('triptype', ''), book_dict.get('ctprice', ''),
                str(amount), booking_conform, tolerance_value, ow_date , rt_date ,'', '', json.dumps(price_details),
                '', '', book_dict.get('tripid', ''), json.dumps(price_details), pnr, booking_conform, str(amount), book_dict.get('ctprice', '')
                )
            #Manual Error Insert To DB 2
            try:
                self.cur.execute(self.final_insert_query, vals)
                self.conn.commit()
            except:
                self.send_mail("IndiGo Booking Scraper Success Insert Failed: %s" % names, price_details )  
        else:
            self.send_mail("IndiGo Booking Scraper Success Insert Failed: %s" % price_details, '')
            vals = (
                book_dict.get('tripid', ''), 'IndiGo', '', '', book_dict.get('origin', ''),
                book_dict.get('destination', ''), book_dict.get('triptype', ''), book_dict.get('ctprice', ''),
                amount, 'Payment Booking Failed,  Call airlines immediately', tolerance_value, 'Payment Failed', '', json.dumps(price_details),
                'Payment Failed', '', book_dict.get('tripid', ''), json.dumps(price_details)
                )
            #Manual Error Insert To Db
            self.cur.execute(self.insert_query, vals)
            self.conn.commit()
        print 'Done'
