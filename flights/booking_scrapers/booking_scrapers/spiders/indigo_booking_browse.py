import re
import json
import time
import md5
import smtplib
import MySQLdb
import datetime
import requests
import smtplib
import ssl
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

from scrapy.conf import settings

import sys
sys.path.append(settings['ROOT_PATH'])

_cfg = SafeConfigParser()
_cfg.read(settings['BOOK_PCC_PATH'])


class IndigoBookBrowse(Spider, IndigoUtils):
    name = "indigobooking_browse"
    start_urls = ["https://www.goindigo.in/"]
    handle_httpstatus_list = [404, 500]

    def __init__(self, *args, **kwargs):
        super(IndigoBookBrowse, self).__init__(*args, **kwargs)
        self.ow_meals_connection = False
        self.multiple_pcc = False
        self.ow_farebasis_class, self.rt_farebasis_class = '', ''
        self.adult_fail, self.child_fail, self.infant_fail = False, False, False
        self.ow_baggage_connection = False
        self.auto_phone_check = True
        self.rt_meals_connection = False
        self.mb_check = False
        self.srt_check = False
        self.rt_baggage_connection = False
        self.connection_check = False
        self.ow_flights_connection = False
        self.rt_flights_connection = False
        self.booking_dict = literal_eval(kwargs.get('jsons', {}))
        self.proceed_to_book = 0
        self.queue = 'offline'
        self.adult_count, self.child_count, self.infant_count = '0', '0', '0'
        self.price_patt = re.compile('\d+')
        self.log = create_logger_obj('indigo_booking')
        self.trip_type = ''
        self.book_dict = {}
        self.ct_price = 0
        self.pnrs_checked = []
        self.pnrs_tobe_checked = []
        self.book_using = ''
        self.tt = ''
        self.flight1 = self.flight2 = self.flight3 = self.flight4 = self.flight5 = {}
        self.ow_input_flight = self.rt_input_flight = {}
        self.ow_flight_nos, self.rt_flight_nos = '', ''
        self.ow_fullinput_dict = self.rt_fullinput_dict = {}
        self.journey = {"origin": "", "destination": "", "fromDate": "", "toDate": "",
                        "multiCity": [], "promo": "", "market": "", "currencyCode": "",
                        "adults": '', "children": '', "infants": '', "journeyType": ""}

        self.insert_query = 'insert into indigo_booking_report (sk, airline, pnr, flight_number, from_location, to_location, triptype, cleartrip_price, indigo_price, status_message, tolerance_amount, oneway_date, return_date, error_message, paxdetails, price_details, created_at, modified_at) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now()) on duplicate key update modified_at=now(), pnr=%s, flight_number=%s, indigo_price=%s, status_message=%s, error_message=%s, paxdetails=%s, price_details=%s, triptype=%s, cleartrip_price=%s, tolerance_amount=%s'
        self.inserttwo_query = 'insert into indigo_booking_report (sk, airline, pnr, flight_number, from_location, to_location, triptype, cleartrip_price, indigo_price, status_message, tolerance_amount, error_message, paxdetails, price_details, created_at, modified_at) values (%s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), error_message=%s, paxdetails=%s, sk=%s, price_details=%s'
        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('booking', 'IP')
        passwd = db_cfg.get('booking', 'PASSWD')
        user = db_cfg.get('booking', 'USER')
        db_name = db_cfg.get('booking', 'DBNAME')
        self.conn = MySQLdb.connect(
            host=host, user=user, passwd=passwd, db=db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()

    def parse(self, response):
        print 'Parse function works'
        sel = Selector(response)
        book_dict, self.pcc_name = self.get_pcc_name()
        if self.booking_dict.get('queue', '') == 'coupon':
            self.pcc_name = 'indigo_coupon_default'
        book_dict = self.process_input()
        self.book_dict = book_dict
        self.queue = self.booking_dict['queue']
        try:
            self.log.debug('Booking using: %s' %
                           _cfg.get(self.pcc_name, 'login_name'))
        except:
            try:
                self.log.debug('Booking using: %s' % self.pcc_name)
            except:
                pass
        if self.multiple_pcc:
            self.insert_error_msg(err="Multiple PCC booking")
            self.log.debug('Multiple PCC booking')
            return
        try:
            data = [
                ('agentLogin.Username', _cfg.get(self.pcc_name, 'login_name')),
                ('agentLogin.Password', _cfg.get(
                    self.pcc_name, 'login_pwd').strip("'")),
                ('IsEncrypted', 'true'),
            ]
            self.book_using = _cfg.get(self.pcc_name, 'login_name')
        except:
            self.insert_error_msg(
                err="PCC %s not available for scrapper" % self.pcc_name)
            self.log.debug('PCC not avaialble for scrapper')
            return
        try:
            self.tt = '%s_%s_%s' % (
                self.booking_dict['trip_type'], self.queue, self.book_using)
        except:
            pass
        url = 'https://book.goindigo.in/Agent/Login'
        yield FormRequest(url, callback=self.parse_autopnr, formdata=data, meta={'book_dict': book_dict})
        #if self.queue == 'offline':
        #    yield FormRequest(url, callback=self.parse_autopnr, formdata=data, meta={'book_dict': book_dict})
        #else:
        #    yield FormRequest(url, callback=self.prase_login, formdata=data, meta={'book_dict': book_dict})

    def parse_autopnr(self, response):
        sel = Selector(response)
        if 'LoginError' in response.url:
            self.send_mail("Unable to login on Login ID %s" % _cfg.get(
                self.pcc_name, 'login_name'), 'Scrapper Unable to login on Login ID')
            # Second Error Msg to Db
            self.insert_error_msg(err="IndiGo Booking Scraper Login Failed")
        url = 'https://book.goindigo.in/Agent/AgentBookingDetail'
        yield Request(url, callback=self.parse_findbooking, dont_filter=True, meta={'book_dict': response.meta['book_dict']})

    def parse_findbooking(self, response):
        sel = Selector(response)
        token = ''.join(sel.xpath(
            '//form[@action="/Agent/AgentBookingDetail"]/input/@value').extract())
        phone,  lastname, code = '', '', ''
        flight_date = datetime.datetime.today().strftime('%d %b %Y')
        if response.meta.get('phone_check', ''):
            searchby = 'Phonenumber'
            phone = self.booking_dict['contact_mobile']
            code = '91'
            self.log.debug('Checking for %s' % phone)
        else:
            flight_date = datetime.datetime.strptime(
                self.booking_dict['departure_date'], '%d-%b-%y').strftime('%d %b %Y')
            lastname = self.booking_dict['pax_details'][self.booking_dict['pax_details'].keys()[
                0]][2]
            searchby = 'Name'
            self.log.debug('Checking for %s on %s' % (lastname, flight_date))
        find_book_list = {'__RequestVerificationToken': token}
        find_book_list.update(
            {'indiGoBookingDetailReport.AgentSearchBy': searchby})
        find_book_list.update({'indiGoBookingDetailReport.CustomerID': ''})
        find_book_list.update({'indiGoBookingDetailReport.Email': ''})
        find_book_list.update(
            {'indiGoBookingDetailReport.FlightDate': flight_date})
        find_book_list.update({'indiGoBookingDetailReport.LastName': lastname})
        find_book_list.update(
            {'indiGoBookingDetailReport.MobileCountryCode': code})
        find_book_list.update({'indiGoBookingDetailReport.Phonenumber': phone})
        find_book_list.update({'indiGoBookingDetailReport.RecordLocator': ''})
        find_book_list.update(
            {'indiGoBookingDetailReport_Submit': 'Find Booking'})
        url = 'https://book.goindigo.in/Agent/AgentBookingDetail'
        yield FormRequest(url, callback=self.parse_allbookings, formdata=find_book_list, dont_filter=True, meta={'auto_pnr': True})

    def parse_allbookings(self, response):
        sel = Selector(response)
        auto_pnr = response.meta['auto_pnr']

        for i in self.pnrs_checked:
            try:
                self.pnrs_tobe_checked.remove(i)
            except:
                pass
        if not self.pnrs_tobe_checked and auto_pnr:
            self.pnrs_tobe_checked = []
            current_bookings = sel.xpath(
                '//table[@id="currentBookingsTable"]//tr')
            for current in current_bookings:
                data = current.xpath('./td/text()').extract()
                if data:
                    date, org, dep = data[:3]
                    if datetime.datetime.strptime(date, '%d %b %y').strftime('%d-%b-%y') != self.booking_dict['departure_date']: continue
                    if self.booking_dict['origin_code'] == org and self.booking_dict['destination_code'] == dep:
                        pnr = ''.join(current.xpath('./@value').extract())
                        self.pnrs_tobe_checked.append(pnr)
            self.log.debug('PNRs to check %s' % self.pnrs_tobe_checked)
        #current_bookings = sel.xpath('//table[@id="currentBookingsTable"]//tr/@value').extract()

        token = ''.join(sel.xpath(
            '//form[@action="/Booking/RetrieveForMyBookings"]/input/@value').extract())
        for i in self.pnrs_checked:
            try:
                self.pnrs_tobe_checked.remove(i)
            except:
                pass
        if len(self.pnrs_tobe_checked) == 0 or auto_pnr == False:
            if not self.auto_phone_check:
                # yield to prase_login function
                url = 'https://book.goindigo.in'
                self.log.debug('No auto PNRs to check, go ahead for booking')
                yield Request(url, callback=self.prase_login, dont_filter=True)
            else:
                self.auto_phone_check = False
                url = 'https://book.goindigo.in/Agent/AgentBookingDetail'
                yield Request(url, callback=self.parse_findbooking, dont_filter=True, meta={'book_dict': self.booking_dict, 'phone_check': True})
        elif len(self.pnrs_tobe_checked) >= 5:
            # return to manual queue and ask to check manually
            self.insert_error_msg(
                err="More than 5 pnrs to check, failing to manual queue")
            self.log.debug('More than 5 pnrs to check')
            return
        else:
            # Check and yield the pnrs and if matching send pnr to HQ else return to the same function

            parse_pnr = {'retrieveBooking.IsBookingListRetrieve': 'true'}
            parse_pnr.update({'__RequestVerificationToken': token})
            parse_pnr.update(
                {'retrieveBooking.RecordLocator': self.pnrs_tobe_checked[0]})
            url = 'https://book.goindigo.in/Booking/RetrieveForMyBookings'
            yield FormRequest(url, callback=self.parse_pnrpage, formdata=parse_pnr, dont_filter=True)

    def parse_pnrpage(self, response):
        sel = Selector(response)
        token = ''.join(sel.xpath(
            '//form[@action="/Booking/RetrieveForMyBookings"]/input/@value').extract())
        # Flight number check
        # Departure time check
        # Arrival time check
        passengers_check, flight_check = False, False
        pnr = ''.join(sel.xpath(
            '//div[@class="indigo_flights"]//li/label[contains(text(),"Booking Ref")]/../h4/text()').extract()).strip()
        self.log.debug('Trying for PNR: %s' % pnr)
        #dep_date = ''.join(sel.xpath('//div[@class="itiFlightDetails flights_table"]/table[contains(@summary, "Flight details")]//tr/td[1]/text()').extract())
        
        flight_numbers = sel.xpath(
            '//div[@class="itiFlightDetails flights_table"]/table[contains(@summary, "Flight details")]//tr/td[2]/text()').extract()
        if self.booking_dict['trip_type'] == 'OW':
            #hq_flight_nos = [i[0]['flight_no'] for i in [i.values()[0]['segments'] for i in self.booking_dict['all_segments']]]
            hq_flight_nos = [i['flight_no'] for i in [
                i.values()[0]['segments'] for i in self.booking_dict['all_segments']][0]]
            #hq_dep_arr = [(x[0]['dep_time'], x[0]['arr_time']) for x in [i.values()[0]['segments']  for i in self.book_dict['all_segments']]]
        elif self.booking_dict['trip_type'] == 'RT':
            #hq_flight_nos = [i[0]['flight_no'] for i in [i.values()[0]['segments'] for i in self.booking_dict['all_segments']]]
            hq_flight_nos_ = [i.values()[0]['segments']
                              for i in self.booking_dict['all_segments']]
            all_segments = self.booking_dict['all_segments']
            segment_len = len([i.keys() for i in all_segments])
            if self.booking_dict['trip_type'] == 'RT' and segment_len == 1:
                hq_flight_nos_ = hq_flight_nos_[0]
            if len(hq_flight_nos_) == 2:
                try:
                    hq_flight_nos = [i['flight_no'] for i in hq_flight_nos_[0]]
                    hq_flight_nos.extend([i['flight_no']
                                          for i in hq_flight_nos_[1]])
                except:
                    hq_flight_nos = [i['flight_no'] for i in hq_flight_nos_]
            else:
                flight_check = True
                self.log.debug('HQ Flight number issue')
                hq_flight_nos = []
            #hq_dep_arr = [(x[0]['dep_time'], x[0]['arr_time']) for x in [i.values()[0]['segments']  for i in self.book_dict['all_segments']]]
        if hq_flight_nos:
            for index, i in enumerate(flight_numbers):
                try:
	                if i.replace('  ', ' ') != hq_flight_nos[index]:
        	            self.log.debug("flight numbers mismatch")
                	    flight_check = True
	                    break
                except:
                	self.log.debug('flight numbers mismatch on index error')
                	pass
        self.log.debug('Flight number matches')
        # Passenger names check
        # [u'1', u'Mr Manish Kumar', u'Adult']
        pass_names = sel.xpath(
            '//div[@class="passenger_views"]//li/h2/text()').extract()
        counter = 0
        hq_pass_names = [' '.join(i[1:3])
                         for i in self.booking_dict['pax_details'].values()]
        allhq_names = len(hq_pass_names)
        for i in hq_pass_names:
            for j in pass_names:
                if i.title() == ' '.join(j.title().strip().replace('  ', ' ').split()[1:]):
                    counter += 1
                    break
        sectors_check = False
        if len(flight_numbers) != len(hq_flight_nos):
            self.log.debug('Number of sectors mismatch %s %s' %
                           (flight_numbers, hq_flight_nos))
            sectors_check = True
        if counter != allhq_names:
            self.log.debug('passenger name mismatch')
            passengers_check = True
        if not passengers_check and not flight_check and not sectors_check:
            data = sel.xpath(
                '//div[@class="sumry_table"]//td//text()').extract()

            try:
                data = filter(None, map(unicode.strip, data))
            except:
                data = {}
            total_dict = {}
            if data:
                data = {data[i].strip(): data[i+1].strip()
                        for i in range(0, len(data), 2)}
                total_dict['total'] = data.pop('Total Price')
            total_dict.update({'AUTO_PNR_EXISTS': True})

            p_details = self.get_autopnr_pricingdetails(total_dict)
            self.insert_error_msg(mesg="Auto PNR Exists",
                                  pnr=pnr, p_details=json.dumps(p_details))
            self.log.debug('Auto PNR exists: %s' % pnr)
            return
        self.pnrs_checked.append(pnr)
        self.log.debug('PNRs checked : %s' % self.pnrs_checked)
        self.log.debug("Tried with PNR : %s" % (pnr))
        profile_url = 'https://book.goindigo.in/Agent/AgentBookingDetail'
        yield Request(profile_url, callback=self.parse_findbooking, dont_filter=True, meta={'auto_pnr': True})

    def prase_login(self, response):
        print 'Login works'
        sel = Selector(response)
        check_text = ''.join(
            sel.xpath('//input[@class="postLogin"]//@value').extract())
        login_status = True
        if 'LoginError' in response.url:
            login_status = False
        try:
            #book_dict = eval(self.book_dict)
            # OrderedDict(eval(self.booking_dict))
            book_dict = self.booking_dict
            #self.booking_dict = book_dict
            all_segments = self.booking_dict['all_segments']
            segment_len = len([i.keys() for i in all_segments])
            self.mb_check = True
            if self.booking_dict['trip_type'] == 'RT' and segment_len == 1:
                segments_list = []
                self.srt_check = True
                self.log.debug('Special RT Received')
                segment1 = filter(None, [
                                  i if i['seq_no'] == '1' else '' for i in all_segments[0][all_segments[0].keys()[0]]['segments']])
                segment2 = filter(None, [
                                  i if i['seq_no'] == '2' else '' for i in all_segments[0][all_segments[0].keys()[0]]['segments']])
                for index, seg in enumerate([segment1, segment2]):
                    new_all_segments = {}
                    amount = float('0')
                    if index == 0:
                        amount = all_segments[0][all_segments[0].keys()[
                            0]]['amount']
                    new_all_segments.update(
                        {all_segments[0].keys()[0]: {'amount': amount, 'segments': seg}})
                    segments_list.append(new_all_segments)
                self.booking_dict['all_segments'] = segments_list
                book_dict = self.booking_dict
                book_dict_again = self.process_input()
            pnr = book_dict.get('pnr', '')
            self.log.debug(self.booking_dict.get('trip_ref'))
            book_dict = self.process_input()
        except Exception as e:
            logging.debug(e.message)
            self.send_mail('Input Error', e.message)
            # First Error Mesg To Db
            self.insert_error_msg(err="Wrong input dict format")
            book_dict, pnr = {}, ''
            return
        if book_dict['triptype'] == 'MultiCity':
            self.send_mail(
                'Multicity triptype request received to scrapper', 'Multicity Booking Error')
            self.insert_error_msg(err="Multi-city booking")
            self.log.debug('Multicity triptype request received to scrapper')
            return
        if self.ow_meals_connection or self.rt_meals_connection:
            self.insert_error_msg(err="Meals site level issue, so not handled")
            self.log.debug('Meals multiple sectors not handled')
            return
        if self.ow_baggage_connection or self.rt_baggage_connection:
            self.insert_error_msg(
                err="Baggages site level issue, so not handled")
            self.log.debug('Baggages multiple sectors not handled')
            return
        if self.connection_check:
            #self.insert_error_msg(err="Connection Flights")
            self.log.debug('Connection flights received')
            # return
        if self.adult_fail or self.child_fail or self.infant_fail:
            self.insert_error_msg(err="Duplicate passengers")
            self.log.debug('Duplicate passengers')
            return
        oneway_date = self.get_date_format(book_dict.get('onewaydate', ''))
        return_date = self.get_date_format(book_dict.get('returndate', ''))
        self.trip_type = book_dict.get('triptype', '')
        if self.trip_type == 'OneWay':
            journey_type = 'oneWay'
        elif self.trip_type == 'RoundTrip':
            journey_type = 'roundTrip'
        else:
            return  # journey_type = 'multicity'
        pax = book_dict.get('paxdetails', {})
        adult_count, chaild_count, infant_count = pax.get(
            'adult', '0'), pax.get('child', '0'), pax.get('infant', '0')
        currency_code = book_dict.get('currencycode', '')
        self.journey.update({'destination': book_dict.get('destination', ''),
                             'origin': book_dict.get('origin', ''), 'fromDate': oneway_date,
                             'adults': adult_count, 'children': chaild_count, 'infants': infant_count,
                             'journeyType': journey_type, 'currencyCode': book_dict.get('currencycode', '')
                             })
        if self.trip_type == 'RoundTrip':
            self.journey.update({'toDate': return_date})
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
            # Currently not supported
        data = {
            'indiGoPromoAuthenticationData.CustomerNumber': '',
            'indiGoPromoAuthenticationData.PromoCode': '',
            search_trip % '.CurrencyCode': currency_code,
            search_trip % '.InfantCount': infant_count,
            search_trip % '.IsArmedForces': 'false',
            search_trip % '.IsFamilyFare': 'false',
            search_trip % '.IsSRC': 'false',
            search_trip % '.IsStudentFare': 'false',
            search_trip % '.IsUMNR': 'false',
            search_trip % '.MaxAdult': '9',
            search_trip % '.MaxChild': '4',
            search_trip % '.Origin': book_dict.get('origin', ''),
            '_Submit': '',
            'isArmedForceHiddenRT2': '0',
        }
        if chaild_count and chaild_count != '0':
            data.update({
                search_trip % '.PassengerCounts[1].Count': chaild_count,
                search_trip % '.PassengerCounts[1].PaxType': 'CHD'
            })
        if adult_count and adult_count != '0':
            data.update({
                search_trip % '.PassengerCounts[0].Count': adult_count,
                search_trip % '.PassengerCounts[0].PaxType': 'ADT',
            })
        if self.trip_type == 'OneWay' or self.trip_type == 'RoundTrip':
            data.update({
                search_trip % '.Origin': book_dict.get('origin', ''),
                search_trip % '.ReturnDate': return_date,
                search_trip % '.DepartureDate': oneway_date,
                search_trip % '.Destination': book_dict.get('destination', ''),
            })
        if login_status:
            url = 'https://book.goindigo.in/Flight/IndexAEM'
            settings.overrides['COOKIES_ENABLED'] = False
            yield FormRequest(url, callback=self.parse_search, formdata=data, meta={'book_dict': book_dict}, dont_filter=True)
        else:
            self.send_mail("Unable to login on Login ID %s" % _cfg.get(
                self.pcc_name, 'login_name'), 'Scrapper Unable to login on Login ID')
            # Second Error Msg to Db
            self.insert_error_msg(err="IndiGo Booking Scraper Login Failed")

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
                try:
                    key, val = data.split('=', 1)
                except:
                    continue
                cookies.update({key.strip(): val.strip()})
        avil_dict = json_body.get('indiGoAvailability', {})
        seg_trips = avil_dict.get('trips', [])
        seg_flights = {}
        seg_flights = self.parse_flight_segments(seg_trips)
        # pickup the flight from seg_flights
        if not seg_flights:
            self.send_mail("Flights not found %s" %
                           book_dict.get('tripid', ''), '')
            # Third Error Msg To Db
            self.insert_error_msg(err="Flights not found")
        m1_sell, m2_sell, m3_sell, m4_sell, m5_sell = ['']*5
        market1, market2, market3, market4, market5 = seg_flights.get(0, {}), seg_flights.get(1, {}),\
            seg_flights.get(2, {}), seg_flights.get(
                3, {}), seg_flights.get(4, {})
        m1_fare, m2_fare = '', ''
        if self.trip_type == 'OneWay' or self.trip_type == 'RoundTrip':
            # .replace(' ', '').replace('-', '')
            market1_ct_flight = book_dict.get('onewayflightid', '')
            m1_class = book_dict.get('onewayclass', '')
            if self.ow_farebasis_class.endswith('SALE'):
                m1_class = 'SAVERS'
            if self.ow_farebasis_class == 'SSPL':
                m1_class = 'SAVERS'
            fb_code = [i['fare_basis_code'] for i in self.ow_input_flight]
            m1_fare, m1_sell = self.get_flight_keys(
                market1, m1_class, market1_ct_flight, fb_code)
            if not m1_sell:
                fare_error = True
            if self.trip_type == 'RoundTrip':
                # .replace(' ', '').replace('-', '')
                market2_ct_flight = book_dict.get('returnflightid', '')
                m2_class = book_dict.get('returnclass', '')
                if self.rt_farebasis_class.endswith('SALE'):
                    m2_class = 'SAVERS'
                if self.rt_farebasis_class == 'SSPL':
                    m2_class = 'SAVERS'
                fb_code = [i['fare_basis_code'] for i in self.rt_input_flight]
                m2_fare, m2_sell = self.get_flight_keys(
                    market2, m2_class, market2_ct_flight, fb_code)
                if not m2_sell:
                    fare_error = True
        print m1_sell, m2_sell
        if fare_error:
            self.send_mail("Booking failed %s" % book_dict.get(
                'tripid', ''), "Flight not found in selected class")
            # Fourth Error Msg To Db
            self.insert_error_msg(err="Flight not found in selected class")
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
                # 'indiGoAvailability.MarketFareKeys[0]': sell,
            }
            if self.trip_type == 'OneWay' or self.trip_type == 'RoundTrip':
                data.update({
                    'indiGoAvailability.MarketFareKeys[0]': m1_sell,
                })
            if self.trip_type == 'RoundTrip':
                data.update({'indiGoAvailability.MarketFareKeys[1]': m2_sell})
            url = 'https://book.goindigo.in/Flight/SelectAEM'
            yield FormRequest(url, callback=self.parse_mem, formdata=data, cookies=cookies, meta={'book_dict': book_dict})

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
                try:
                    key, val = data.split('=', 1)
                except:
                    continue
                cookies.update({key.strip(): val.strip()})
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
        yield Request(url, callback=self.parse_member, headers=headers, cookies=cookies,
                      method='GET', meta={'book_dict': response.meta['book_dict']})

    def parse_member(self, response):
        print 'flight select journey works'
        sel = Selector(response)
        book_dict = response.meta['book_dict']
        price_details = {}
        res_headers = json.dumps(str(response.request.headers))
        edit_data = json.loads(response.body)
        try:
            if not edit_data['indiGoPriceBreakdown']['indigoJourneyPrice']['indigoJourneyPriceItineraryList'][0]['journeyPriceItinerary'].keys():
                self.insert_error_msg(
                    err='Try again later', mesg='indiGoPriceBreakdown not found')
                self.log.debug('indiGoPriceBreakdown list index range error')
                return
        except:
            self.log.debug('indiGoPriceBreakdown list index range error')
            self.insert_error_msg(err='Try again later',
                                  mesg='indiGoPriceBreakdown not found')
            return
        price_details, all_keys = self.process_price_details(
            edit_data, price_details, book_dict)
        if self.ow_baggage_connection or self.ow_meals_connection or self.rt_baggage_connection or self.rt_meals_connection:
            self.log.debug('Meals or Baggage Connection Issue')
            return
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
        cookies = {}
        for i in my_dict.get('Cookie', []):
            data_ = i.split(';')
            for data in data_:
                try:
                    key, val = data.split('=', 1)
                except:
                    continue
                cookies.update({key.strip(): val.strip()})
        cookies.update({'journey': self.journey})
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
            'indiGoContact.PostalCode': '',
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
        data.update({'indiGoSsr.Ssrs': all_keys})
        guests_lst = book_dict.get('guestdetails', [])
        if child_details:
            guests_lst.extend(child_details)
        for idx, i in enumerate(guests_lst):
            if i.get('gender', '') == 'Male':
                gender = '1'
            else:
                gender = '2'
            data.update({
                'indiGoPassengers[%s].Name.First' % idx: i.get('firstname', ''),
                'indiGoPassengers[%s].Name.Last' % idx: i.get('lastname', ''),
                'indiGoPassengers[%s].Name.Title' % idx: i.get('title', ''),
                'indiGoPassengers[%s].Info.Gender' % idx: gender,
                'indiGoPassengers[%s].PassengerNumber' % idx: str(idx)
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
            if gender == 'Male':
                gender_val = 1
            else:
                gender_val = 2
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
        yield FormRequest(url, callback=self.parse_pax, formdata=data, cookies=cookies, meta={'book_dict': book_dict, 'price_details': price_details})

    def parse_pax(self, response):
        print 'Passenger edit works'
        sel = Selector(response)
        #settings.overrides['COOKIES_ENABLED'] = True
        price_details = response.meta.get('price_details')
        res_headers = json.dumps(str(response.request.headers))
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
        cookies = {}
        for i in my_dict.get('Cookie', []):
            data_ = i.split(';')
            for data in data_:
                try:
                    key, val = data.split('=', 1)
                except:
                    continue
                cookies.update({key.strip(): val.strip()})
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
        yield Request(url, callback=self.parse_payment, headers=headers, cookies=cookies, meta={'book_dict': response.meta['book_dict'], 'price_details': price_details, 'cookies' : cookies, 'headers' : headers})

    def parse_payment(self, response):
        print 'Payment works'
        book_dict = response.meta['book_dict']
        open('%s.html' % self.booking_dict.get(
            'trip_ref'), 'w').write(response.body)
        sel = Selector(response)
        price_details = response.meta.get('price_details')
        #pay_summary = [i.strip() for i in sel.xpath('//div[@class="sumry_table"]//td/text()').extract()]
        res_headers = json.dumps(str(response.request.headers))
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
        cookies, journey = {}, {}
        for i in my_dict.get('Cookie', []):
            data_ = i.split(';')
            for data in data_:
                try:
                    key, val = data.split('=', 1)
                except:
                    continue
                cookies.update({key.strip(): val.strip()})
        cookies.update({'journey': json.dumps(self.journey)})
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
        token = ''.join(sel.xpath(
            '//form[@action="/Payment/Create"]/input[@name="__RequestVerificationToken"]/@value').extract())
        ac = ''.join(sel.xpath(
            '//form[@action="/Payment/Create"]/input[@id="agencyPayment_AccountNumber"]/@value').extract())
        pay_methond = ''.join(sel.xpath(
            '//form[@action="/Payment/Create"]/input[contains(@id, "agencyPayment_PaymentMethodCode")]/@value').extract())
        ac_type = ''.join(sel.xpath(
            '//form[@action="/Payment/Create"]/input[@id="agencyPayment_PaymentMethodType"]/@value').extract())
        amount = ''.join(sel.xpath(
            '//form[@action="/Payment/Create"]/input[@id="agencyPayment_QuotedAmount"]/@value').extract())
        currency_type = ''.join(sel.xpath(
            '//form[@action="/Payment/Create"]/input[@id="agencyPayment_QuotedCurrencyCode"]/@value').extract())
        is_proceed, tolerance_value = 0, 0
        if not amount:
            if response.meta.get('check', '') == '': 
                url = 'https://book.goindigo.in/Payment/New'
                try: print 'Agency Account Retried %s' % self.booking_dict.get('trip_ref')
                except: pass
                return Request(url, callback=self.parse_payment, headers=response.meta['headers'], cookies=response.meta['cookies'], meta={'book_dict': response.meta['book_dict'], 'price_details': response.meta['price_details'], 'check' : False}, dont_filter=True)
            try: open('%s_retried' % self.booking_dict.get('trip_ref'), 'w').write(response.body)
            except: pass
            self.send_mail("Agency Account not found %s" %
                           book_dict.get('tripid', ''), '')
            # Fifth Error Msg To Db
            self.insert_error_msg(err="Agency Account not found")
            return
        else:
            tolerance_value, is_proceed = self.check_tolerance(
                ct_price, amount)
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
            key_pair_list = '<>'.join(response.xpath(
                '//table[@summary="Flight details"]//tr//td[2]/text()').extract())
            infant_tuple = filter(None, [(
                key, val) if ' Infant' in key else '' for key, val in price_details.iteritems()])
            infant_value = ''
            if infant_tuple:
                try:
                    infant_count = book_dict['paxdetails']['infant']
                    infant_value = float(infant_tuple[-1]/int(infant_count))
                except:
                    infant_value = book_dict['paxdetails']['infant']
                    pass
            segments = '-'.join(sel.xpath(
                '//div[@class="price-itinerary-journey"]//div[@class="stations_name"]/span[@class="stn"]/text()').extract())
            pnr, flight_no = '', key_pair_list
            ow_date = datetime.datetime.strptime(
                book_dict.get('onewaydate', '1989-01-01'), '%Y-%m-%d')
            if book_dict.get('returndate', '1989-01-01'):
                rt_date = datetime.datetime.strptime(
                    book_dict.get('returndate', '1989-01-01'), '%Y-%m-%d')
            else:
                rt_date = default_datetime
            #self.insert_error_msg(mesg='Success', pnr=pnr, a_price=str(
            #    amount), p_details=json.dumps(price_details), tolerance=tolerance_value)
            if int(self.proceed_to_book) == 1:
                self.log.debug('Booking happening')
                return FormRequest(url, callback=self.parse_create_payment, formdata=data, cookies=cookies,
                                  headers=headers, meta={'book_dict': book_dict, 'cookies_': cookies,
                                                         'headers_': headers, "tamount": amount, 'tolerance_value': tolerance_value, 'price_details': price_details, 'key_pair_list': key_pair_list, 'data': data}, dont_filter=True)
        else:
            self.send_mail("Fare increased by IndiGo for %s by %s or response error" % (
                (book_dict.get('tripid', ''), tolerance_value)), '')
            self.insert_error_msg(err='Fare increased by IndiGo', mesg='Booking failed, price rise',
                                  p_details=json.dumps(price_details), a_price=str(amount))
            url = 'https://book.goindigo.in/Agent/Logout'
            return Request(url, callback=self.parse_logout, dont_filter=True)

    def parse_create_payment(self, response):
        print 'create payment works'
        sel = Selector(response)
        cookies = response.meta['cookies_']
        price_details = response.meta.get('price_details')
        key_pair_list = response.meta.get('key_pair_list')
        headers = response.meta['headers_']
        content = response.meta.get('content', '')
        data = response.meta['data']
        url = 'https://book.goindigo.in/Booking/PostCommit'
        time.sleep(30)
        time.sleep(20)
        yield Request(url, callback=self.parse_final_report_before, headers=headers,
                      cookies=cookies, meta={'book_dict': response.meta['book_dict'],
                                             'tamount': response.meta['tamount'], 'tolerance_value': response.meta['tolerance_value'], 'price_details': price_details, 'key_pair_list': key_pair_list, 'data': data, 'headers_': headers, 'cookies_': cookies, 'content': content}, dont_filter=True)

    def parse_final_report_before(self, response):
        time.sleep(5)
        url = 'https://book.goindigo.in/Booking/ViewAEM'
        yield Request(url, callback=self.parse_final_report, dont_filter=True, meta={'book_dict': response.meta['book_dict'], 'tamount': response.meta['tamount'], 'tolerance_value': response.meta['tolerance_value'], 'price_details': response.meta.get('price_details'), 'key_pair_list': response.meta.get('key_pair_list'), 'data': response.meta['data'], 'headers_': response.meta['headers_'], 'cookies_': response.meta['cookies_'], 'content': response.meta.get('content', '')})

    def parse_final_report(self, response):
        print 'final report payment works'
        flight_no = response.meta.get('key_pair_list')
        price_details = response.meta.get('price_details')
        cookies = response.meta['cookies_']
        try:
            detail = json.loads(response.body)
        except:
            self.insert_error_msg(err='Payment failed json body')
            self.send_mail("Indigo Booking Payment Failed Json body: %s" %
                           self.booking_dict['trip_ref'], '')
            open('jsonbodyfail.html', 'w').write(response.body)
            return
        headers = response.meta['headers_']
        data = response.meta['data']
        sel = Selector(response)
        book_dict = response.meta['book_dict']
        default_datetime = datetime.datetime.strptime('1989-01-01', '%Y-%m-%d')
        ow_date = datetime.datetime.strptime(
            book_dict.get('onewaydate', '1989-01-01'), '%Y-%m-%d')
        if book_dict.get('returndate', '1989-01-01'):
            rt_date = datetime.datetime.strptime(
                book_dict.get('returndate', '1989-01-01'), '%Y-%m-%d')
        else:
            rt_date = default_datetime
        id_price = response.meta['tamount']
        amount = response.meta['tamount']
        tolerance_value = response.meta['tolerance_value']
        #pnr = ''.join(sel.xpath('//label[contains(text(), "Booking Reference")]/following-sibling::h4/text()').extract()).strip()
        pnr = detail['indiGoBookingDetail']['recordLocator']
        try:
            content = response.meta.get('content', '')
        except:
            content = ''
        try:
            names = book_dict.get('tripid', '') + pnr + content
        except:
            names = str(book_dict.get('tripid', '')) + str(pnr) + str(content)
        open('%s.html' % names, 'w').write(response.body)
        booking_conform = detail['indiGoBookingDetail']['bookingStatusMsg']
        payment_status = detail['indiGoBookingDetail']['paymentStatus']
        if pnr and booking_conform == 'Confirmed':
            #booking_conform = ''.join(sel.xpath('//label[contains(text(), "Booking Status")]/following-sibling::h4//text()').extract()).strip()
            #payment_status = ''.join(sel.xpath('//label[contains(text(), "Payment Status")]/following-sibling::h4//text()').extract()).strip()
            if response.meta.get('content', ''):
                booking_conform = 'Retried and %s' % booking_conform
            self.insert_error_msg(pnr=pnr, mesg=booking_conform, a_price=str(
                amount), tolerance=tolerance_value, p_details=json.dumps(price_details), f_no=flight_no)
        else:
            if response.meta.get('content', ''):
                try:
                    self.send_mail("IndiGo Booking Failed: %s, Payment Status : %s, %s" % (
                        self.booking_dict['trip_ref'], payment_status, booking_conform))
                except:
                    pass
                self.insert_error_msg(err='Payment Failed', pnr=pnr, mesg='Payment Booking Failed,  Call airlines immediately', a_price=str(
                    amount), tolerance=tolerance_value, p_details=json.dumps(price_details))
            else:
                #url = 'https://book.goindigo.in/Booking/Create'
                self.log.debug(
                    'Trying again for payment booking failed case : %s' % self.booking_dict['trip_ref'])
                # try:
                #    return FormRequest(url, callback=self.parse_create_payment, meta={'book_dict':response.meta['book_dict'], 'tamount':response.meta['tamount'], 'tolerance_value':response.meta['tolerance_value'], 'price_details' : response.meta['price_details'], 'key_pair_list' : response.meta['key_pair_list'], 'content' : True, 'cookies_' : cookies, 'headers_': headers, 'data' : data}, dont_filter=True, headers=headers,cookies=cookies, formdata=data)
                # except Exception as e:
                #    self.insert_error_msg(err='Payment Failed', pnr=pnr, mesg='Payment Booking Failed,  Call airlines immediately', a_price=str(amount), tolerance=tolerance_value, p_details=json.dumps(price_details))
                #    self.log.debug('Error as follows: \n %s' % e)
                url = 'https://book.goindigo.in/Booking/ViewAEM'
                return Request(url, callback=self.parse_final_report, dont_filter=True, meta={'tamount': response.meta['tamount'], 'tolerance_value': response.meta['tolerance_value'], 'price_details': response.meta.get('price_details'), 'key_pair_list': response.meta.get('key_pair_list'), 'data': response.meta['data'], 'headers_': response.meta['headers_'], 'cookies_': response.meta['cookies_'], 'content': True, 'book_dict': book_dict})
        url = 'https://book.goindigo.in/Agent/Logout'
        return Request(url, callback=self.parse_logout, dont_filter=True)

    def parse_logout(self, response):
        sel = Selector(response)
        logout = ''.join(sel.xpath(
            '//div[@class="itiFlightDetails bookingDetails myProfile"]//p/text()').extract())
        self.log.debug(logout)
