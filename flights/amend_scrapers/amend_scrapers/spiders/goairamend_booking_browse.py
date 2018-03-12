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
from goair_amend_utils import *

import sys
sys.path.append('/root/scrapers/flights/')

from root_utils import *

_cfg = SafeConfigParser()
_cfg.read('/root/scrapers/flights/amend_airline_names.cfg')


class GoAirAmendBrowse(Spider, GoairAmendUtils, Helpers):
    name = "goair_amendbooking_browse"
    start_urls = ["https://book.goair.in/Agent/Login"]
    handle_httpstatus_list = [404, 500]
    def __init__(self, *args, **kwargs):
        super(GoAirAmendBrowse, self).__init__(*args, **kwargs)
        self.request_verification = ''
        self.amend_dict = kwargs.get('jsons', {})
        self.proceed_to_book = 0
        self.trip_type = ''
        self.rt_round_amendment = False
        self.ow_amendment = False
        self.rt_amendment = False
        self.price_patt = re.compile('\d+')
        self.log = create_logger_obj('goair_amend_booking')
        self.insert_query = 'insert into goairamend_booking_report (sk, airline, pnr, flight_number, from_location, to_location, triptype, cleartrip_price, airline_price, status_message, tolerance_amount, oneway_date, return_date, error_message, request_input, price_details, created_at, modified_at) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), sk=%s, airline=%s, pnr=%s, flight_number=%s, from_location=%s, to_location=%s, triptype=%s, cleartrip_price=%s, airline_price=%s, status_message=%s, tolerance_amount=%s, oneway_date=%s, return_date=%s, error_message=%s, request_input=%s, price_details=%s'
        self.conn = MySQLdb.connect(host='localhost', user = 'root', passwd='', db='AMENDBOOKINGDB', charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()

    def insert_values_into_db(self, amend_dict, status_message, error_message):
        request = ast.literal_eval(self.amend_dict)
        sk = request.get('trip_ref', '')
        pnr = amend_dict.get('pnr', '')
        flight_number = str(amend_dict.get('new_flight_ids', []))
        from_location = amend_dict.get('origin_code', '')
        to_location = amend_dict.get('destination_code', '')
        triptype = self.trip_type
        cleartrip_price = request.get('cleartrip_price', '')
        airline_price = amend_dict.get('Total Price', '').strip()
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
        cancel_details['Total Price'] = airline_price
        booking_details = json.dumps(amend_dict.get('booking_price', {}))
        price_details = json.dumps({'cancel_charges':json.dumps(cancel_details), 'booking_charges':booking_details})
        values = (
            sk, 'GoAir', pnr, flight_number, from_location,
            to_location, triptype, cleartrip_price, airline_price,
            status_message, tolerance_amount, oneway_date, return_date,
            error_message, paxdetails, price_details,
            sk, 'GoAir', pnr, flight_number, from_location, to_location,
            triptype, cleartrip_price, airline_price, status_message, tolerance_amount,
            oneway_date, return_date, error_message, paxdetails, price_details
        )
        self.cur.execute(self.insert_query, values)

    def parse(self, response):
        print 'Parse function works'
        sel = Selector(response)
        try:
            self.pcc_name, amend_dict, err_msg = self.get_pcc_name()
        except Exception as e:
            amend_dict = self.amend_dict
            self.insert_values_into_db(amend_dict, "Amend Failed", e.message)
            self.send_mail("Amend Failed", e.message, "amend", "GoAir", "goair_common")
        if 'coupon' in self.pcc_name:
            self.pcc_name =  'goair_default'
        if err_msg:
            self.insert_values_into_db(amend_dict, "Amend Failed", err_msg)
            logging.debug(err_msg)
            return
        req_token_key = ''.join(sel.xpath('//form[@action="/Agent/Login"]/input/@name').extract())
        req_token_value = ''.join(sel.xpath('//form[@action="/Agent/Login"]/input/@value').extract())
        try:
            data = [
                (req_token_key, req_token_value),
                ('starterAgentLogin.Username', _cfg.get(self.pcc_name, 'username')),
                ('starterAgentLogin.Password', _cfg.get(self.pcc_name, 'passwd'))
            ]
        except:
            self.insert_values_into_db(amend_dict, "Amend Failed", "PCC %s not available"%self.pcc_name)
            logging.debug('PCC not avaialble for scrapper')
            self.send_mail("Amend Failed", "PCC not avaialble for scrapper", "amend", "GoAir", "goair_common")
            return
        url = 'https://book.goair.in/Agent/Login'
        yield FormRequest(url, callback=self.prase_login, formdata=data, meta={'amend_dict':amend_dict})

    def prase_login(self, response):
        '''
        Login into Indigo
        '''
        print 'Login works'
        sel = Selector(response)
        amend_dict = response.meta['amend_dict']
        user_check = ''.join(sel.xpath('//span[@class="user-info-number"]//text()').extract())
        login_status = True
        if 'error' in response.url.lower():
            self.insert_values_into_db(amend_dict, "Amend Failed", "Login Failed")
            self.send_mail("Amend Failed", "Login Failed", "amend", "GoAir", "goair_common")
            login_status = False
            return
        url = 'https://www.goair.in/plan-my-trip/manage-booking/'
        yield Request(url, callback=self.parse_manage_booking, meta={'amend_dict':amend_dict})

    def parse_manage_booking(self, response):
        sel = Selector(response)
        amend_dict = response.meta['amend_dict']
        pax_last_name = amend_dict.get('pax_last_name', '')
        pnr = amend_dict.get('pnr', '')
        url = 'https://book.goair.in/Booking/Index'
        headers = {
            'Pragma': 'no-cache',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://www.goair.in/plan-my-trip/manage-booking/',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
        }
        params = (
            ('rl', pnr),
            ('ln', pax_last_name),
        )
        yield FormRequest(url, callback=self.parse_booking_index, headers=headers, formdata=params, method="GET", meta={'amend_dict':amend_dict})
    def parse_booking_index(self, response):
        sel = Selector(response)
        amend_dict = response.meta.get('amend_dict', {})
        pnr_error = normalize(''.join(sel.xpath('//div[@class="error-msg alert alert-error"]//text()').extract()))
        if 'Errors' in pnr_error:
            error = "PNR %s details not find with %s(pax last name)"%(amend_dict.get('pnr', ''), amend_dict.get('pax_last_name', ''))
            self.insert_values_into_db(amend_dict, "Amend Failed", error)
            self.send_mail("Amend Failed", error, "amend", "GoAir", "goair_common")
            print error
            return
        site_pnr = ''.join(sel.xpath('//h3[@class="pull-right itin-pnr"]/text()').extract())
        cancel_rebook_button = ''.join(sel.xpath('//div[@class="mdl-grid itin-sub-header"]//a[contains(@href, "state=CancelRebook")]/@href').extract())
        if amend_dict.get('pnr', '') != site_pnr:
            error = "Scraper failed to fetch pnr %s"%amend_dict.get('pnr', '')
            self.insert_values_into_db(amend_dict, "Amend Failed", error)
            print error
            return
        if not cancel_rebook_button:
            error = "Change Booking button not presented"
            self.insert_values_into_db(amend_dict, "Amend Failed", error)
            self.send_mail("Amend Failed", error, "amend", "GoAir", "goair_common")
            print error
            #insert error
            return
        headers = {
                'Pragma': 'no-cache',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Upgrade-Insecure-Requests': '1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Referer': 'https://book.goair.in/Booking/Index',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
        }
        params = (
            ('state', 'CancelRebook'),
        )
        url = 'https://book.goair.in/Flight/Rebook'
        yield FormRequest(url, callback=self.parse_rebook, headers=headers, formdata=params, method="GET", meta={'amend_dict':amend_dict})

    def parse_rebook(self, response):
        sel = Selector(response)
        amend_dict = response.meta.get('amend_dict', {})
        request_verification = ''.join(sel.xpath('//form[@id="rebookForm"]/input[@name="__RequestVerificationToken"]/@value').extract())
        starter_key = ''.join(sel.xpath('//form[@id="rebookForm"]/input[contains(@id, "starterCancelRebook_")]/@name').extract())
        starter_value = ''.join(sel.xpath('//form[@id="rebookForm"]/input[contains(@id, "starterCancelRebook_")]/@value').extract())
        journey_form_key = ''.join(sel.xpath('//form[@id="rebookForm"]//input[@name="starterCancelRebook.SelectedCancelRebookFlights[0].FromJourney"]/@value').extract())

        rt_journey_form_key = ''.join(sel.xpath('//form[@id="rebookForm"]//input[@name="starterCancelRebook.SelectedCancelRebookFlights[1].FromJourney"]/@value').extract())
        #rt form_key
        self.trip_type = self.get_trip_type(amend_dict)
        self.rt_round_amendment, self.ow_amendment, self.rt_amendment = self.get_amend_type(amend_dict)
        search_keys_dict = self.get_segment_details(amend_dict)
        ow_depart_date = search_keys_dict.get('amd_ow_depature_date', '')
        ori_return_dep_date = search_keys_dict.get('rt_depature_date', '')
        return_dapart_date = search_keys_dict.get('amd_rt_depature_date', '')
        if return_dapart_date:
            try: return_dapart_date = return_dapart_date.strftime('%d/%m/%Y')
            except: return_dapart_date = ''
        if ow_depart_date:
            try: ow_depart_date = ow_depart_date.strftime('%d/%m/%Y')
            except: ow_depart_date = ''
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
        ow_depat_date_hash = search_keys_dict.get('depature_date', '')
        rt_depat_date_hash = search_keys_dict.get('rt_depature_date', '')
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
        if self.ow_amendment:
            data = [
                ('__RequestVerificationToken', request_verification),
                (starter_key, starter_value),
                ('starterCancelRebook.SelectedCancelRebookFlights[0].FromJourney', journey_form_key),
                ('goAirRebook.fromInput', origin),
                ('goAirRebook.fromInput', dest),
                ('starterCancelRebook.SelectedCancelRebookFlights[0].Origin', ow_amend_origin),
                ('starterCancelRebook.SelectedCancelRebookFlights[0].Destination', ow_amend_dest),
                ('starterCancelRebook.SelectedCancelRebookFlights[0].DepartureDate', ow_depart_date),
            ]
        elif self.rt_amendment:
            data = [
                ('__RequestVerificationToken', request_verification),
                (starter_key, starter_value),
                ('starterCancelRebook.SelectedCancelRebookFlights[1].FromJourney', rt_journey_form_key),
                ('starterCancelRebook.SelectedCancelRebookFlights[0].Origin', request_origin),
                ('starterCancelRebook.SelectedCancelRebookFlights[0].Destination', request_destination),
                ('starterCancelRebook.SelectedCancelRebookFlights[1].Origin', request_destination),
                ('starterCancelRebook.SelectedCancelRebookFlights[1].Destination', request_origin),
                ('starterCancelRebook.SelectedCancelRebookFlights[1].DepartureDate', return_dapart_date),

            ]
        elif self.rt_round_amendment:
           data = [
              ('__RequestVerificationToken', request_verification),
              (starter_key, starter_value),
              ('starterCancelRebook.SelectedCancelRebookFlights[0].FromJourney', journey_form_key),
              ('starterCancelRebook.SelectedCancelRebookFlights[1].FromJourney', rt_journey_form_key),
              ('starterCancelRebook.SelectedCancelRebookFlights[0].Origin', ow_amend_origin),
              ('starterCancelRebook.SelectedCancelRebookFlights[0].Destination', ow_amend_dest),
              ('starterCancelRebook.SelectedCancelRebookFlights[0].DepartureDate', ow_depart_date),
              ('starterCancelRebook.SelectedCancelRebookFlights[1].Origin', ow_amend_dest),
              ('starterCancelRebook.SelectedCancelRebookFlights[1].Destination', ow_amend_origin),
              ('starterCancelRebook.SelectedCancelRebookFlights[1].DepartureDate', return_dapart_date),
            ]
        else:
            self.insert_values_into_db(amend_dict, "Amend Failed", "No details for amend")
            return
        url = 'https://book.goair.in/Flight/Rebook'
        yield FormRequest(url, callback=self.parse_fetch_flight, formdata=data, meta={'amend_dict':amend_dict})

    def parse_fetch_flight(self, response):
        sel = Selector(response)
        amend_dict = response.meta.get('amend_dict', {})
        ow_nodes  = sel.xpath('//div[@class="overflow-auto"][1]/table[1]/tbody/tr')
        rt_nodes = sel.xpath('//div[@class="overflow-auto"][2]/table[1]/tbody/tr')
        ow_avil_flight_dict, rt_avil_flight_dict = {}, {}
        nodes_dict = {}
        nodes_dict['ow_nodes'] = ow_nodes
        nodes_dict['rt_nodes'] = rt_nodes
        for type_node, nodes in nodes_dict.iteritems():
            for node in nodes:
                cabin_class_dict = {}
                flight_id_path = normalize(''.join(node.xpath('./td[1]/div/text()').extract()))
                flight_id_path2 = normalize('<>'.join(node.xpath('./td[2]//h5//text()').extract()))
                economy_fares_key_name = normalize(''.join(node.xpath('./td[4]//div[contains(@class, "fare-price-text")]/input/@name').extract()))
                economy_fares_key_value = normalize(''.join(node.xpath('./td[4]//div[contains(@class, "fare-price-text")]/input/@value').extract()))
                economy_price_val = normalize(''.join(node.xpath('./td[4]//div[contains(@class, "fare-price-text")]//span[@class="price-text"]/span[@class="js-extract-text"]/text()').extract()))
                business_fares_key_name = normalize(''.join(node.xpath('./td[5]//div[contains(@class, "fare-price-text")]/input/@name').extract()))
                business_fares_key_value = normalize(''.join(node.xpath('./td[5]//div[contains(@class, "fare-price-text")]/input/@value').extract()))
                business_price_val = normalize(''.join(node.xpath('./td[5]//div[contains(@class, "fare-price-text")]//span[@class="price-text"]/span[@class="js-extract-text"]/text()').extract()))
                cabin_class_dict.update({'economy':[economy_fares_key_name, economy_fares_key_value, economy_price_val]})
                cabin_class_dict.update({'business':[business_fares_key_name, business_fares_key_value, business_price_val]})
                if type_node == 'ow_nodes':
                    if flight_id_path2:
                        flight_id_path2 = re.sub('(\(.*\))', '', flight_id_path2).strip()
                        ow_avil_flight_dict.update({flight_id_path2.replace(' ', ''):cabin_class_dict})
                else:
                    if flight_id_path2:
                        flight_id_path2 = re.sub('(\(.*\))', '', flight_id_path2).strip()
                        rt_avil_flight_dict.update({flight_id_path2.replace(' ', ''):cabin_class_dict})
        cabin_class = amend_dict.get('cabin_class', '')
        seg_key, sell_key, ow_flight = self.get_amend_sell_keys(amend_dict, ow_avil_flight_dict, cabin_class, False)
        rt_seg_key, rt_sell_key, rt_flight = self.get_amend_sell_keys(amend_dict, rt_avil_flight_dict, cabin_class, True)
        if self.ow_amendment or self.rt_amendment:
            if not sell_key:
                self.insert_values_into_db(amend_dict, "Amend Failed", "Flights not found")
                self.send_mail("Amend Failed", "Flights not found", "amend", "GoAir", "goair_common")
                return
        if self.rt_round_amendment:
            if not rt_sell_key:
                self.insert_values_into_db(amend_dict, "Amend Failed", "Flights not found")
                self.send_mail("Amend Failed", "Flights not found", "amend", "GoAir", "goair_common")
                return
        new_flights = []
        if self.ow_amendment:
            new_flights = ['<>'.join(ow_flight), '']
        elif self.rt_amendment:
            new_flights = ['', '<>'.join(ow_flight)]
        elif self.rt_round_amendment:
            new_flights = ['<>'.join(ow_flight), '<>'.join(rt_flight)]
        amend_dict['new_flight_ids'] = new_flights
        #ow_avil_flight_dict, rt_avil_flight_dict
        data = [
            ('goAirAvailability.BundleCodes[0]', ''),
            ('goAirAvailability.MarketFareKeys[0]', sell_key),
        ]
        if rt_sell_key:
            data.append((rt_seg_key, rt_sell_key))
        url = 'https://book.goair.in/Flight/ChangeFlightSelect'
        yield FormRequest(url, callback=self.parse_change_flight, formdata=data, meta={'amend_dict':amend_dict}, dont_filter=True)

    def parse_change_flight(self, response):
        sel = Selector(response)
        amend_dict = response.meta.get('amend_dict', {})
        data = [
            ('goAirInsuranceQuote.IsBuyInsurance', 'False'),
            ('goAirInsuranceQuote.Address.LineOne.Data', ''),
            ('goAirInsuranceQuote.Address.PostalCode.Data', ''),
            ('goAirInsuranceQuote.Address.LineTwo.Data', ''),
            ('goAirInsuranceQuote.Address.City.Data', ''),
            ('goAirInsuranceQuote.Address.Country.Data', ''),
            ('goAirInsuranceQuote.Address.EmailAddress.Data', ''),
        ]
        url = 'https://book.goair.in/Extras/Add'
        yield FormRequest(url, callback=self.parse_conform_change, formdata=data, meta={'amend_dict':amend_dict}, dont_filter=True)

    def parse_conform_change(self, response):
        sel = Selector(response)
        amend_dict = response.meta.get('amend_dict', {})
        price_dict, ow_price_dict = {}, {}
        tax_free = ''.join(sel.xpath('//div[@id="price_itinerary_taxes"]//div[@class="price-display-summary-line-item"]//div[@class="pull-right strong"]/text()').extract())
        if tax_free:
            ow_price_dict.update({'taxes_free':tax_free})
        total_price = ''.join(sel.xpath('//div[@class="price-display-content"]//div[@id="price_display_total"]/span[@class="js-total-price hidden"]/text()').extract())
        if total_price:
            ow_price_dict.update({'total':total_price})
        all_tax_nodes = sel.xpath('//div[@id="price_itinerary_taxes"]//div[@id="price_itinerary_expand_body"]/div')
        for node in all_tax_nodes:
            tax_name = ''.join(node.xpath('./div[@class="pull-left"]/text()').extract())
            tax_value = ''.join(node.xpath('./div[@class="pull-right"]/text()').extract())
            ow_price_dict.update({tax_name:tax_value})
        pax_base_price_nodes = sel.xpath('//div[@id="price_display_container"]/div[@class="price-display-content"]/div[@id="price_itinerary_expand_body"]//div[@class="price-display-summary-line-item"]')
        for pax_base in pax_base_price_nodes:
            name = normalize(''.join(pax_base.xpath('./div[@class="pull-left"]/text()').extract()))
            val = normalize(''.join(pax_base.xpath('./div[contains(@class, "pull-right")]/text()').extract()))
            ow_price_dict.update({name:val})
        amend_dict['price_dict'] = ow_price_dict
        amend_dict['Total Price'] = total_price
        tolerance_amount = amend_dict.get('tolerance_amount', 0)
        cleartrip_price = amend_dict.get('pax_paid_amount', 0)
        total_price = total_price.split(' ')[0].replace(',', '').strip()
        if not  total_price:
            self.insert_values_into_db(amend_dict, "Amend Failed", "Total price not found")
            return
        elif total_price == '0' or total_price == 0:
            self.insert_values_into_db(amend_dict, "Amend Failed", "Total price not found")
            return
        try:
            tolerance = float(total_price) - float(cleartrip_price)
            amend_dict['price_diff'] = str(tolerance)
            if tolerance <= float(tolerance_amount):
                tolerance_check = True
            else:
                tolerance_check = False
                self.insert_values_into_db(amend_dict, "Amend Failed", "Fare increased by Airline")
                return
        except:
            tolerance_check = False
            tolerance = 0
            print "Total amount not found"
            self.insert_values_into_db(amend_dict, "Amend Failed", "Total price not found")
            return
        amend_dict['price_diff'] = tolerance
        proceed_to_book = amend_dict.get('proceed_to_book', 0)
        print ow_price_dict
        request_token = sel.xpath('//input[@name="__RequestVerificationToken"]/@value').extract()
        if request_token:
            request_token = request_token[0]
        else:
            request_token = ''
            self.insert_values_into_db(amend_dict, "Amend Failed", "RequestVerificationToken not found in source page")
            return
        cookies = {
            '__RequestVerificationToken': request_token
        }
        headers = {
        'Pragma': 'no-cache',
        'Origin': 'https://book.goair.in',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Upgrade-Insecure-Requests': '1',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Cache-Control': 'no-cache',
        'Referer': 'https://book.goair.in/Booking/Confirm',
        'Connection': 'keep-alive',
        'Content-Length': '0',
        }
        if proceed_to_book == 1:
            url = 'https://book.goair.in/Payment/New'
            yield Request(url, callback=self.payment_new, headers=headers, cookies=cookies, meta={'amend_dict':amend_dict})
        else:
            self.insert_values_into_db(amend_dict, "Amend Failed", "Test Booking")

    def payment_new(self, response):
        sel = Selector(response)
        amend_dict = response.meta.get('amend_dict', {})
        request_token = sel.xpath('//input[@name="__RequestVerificationToken"]/@value').extract()
        if request_token: request_token = request_token[0]
        else:
            request_token = ''
            self.insert_values_into_db(amend_dict, "Amend Failed", "RequestVerificationToken not found in source page")
            return
        amount = ''.join(sel.xpath('//input[@name="AgencyPayment.QuotedAmount"]/@value').extract())
        ac_number = ''.join(sel.xpath('//input[@name="AgencyPayment.AccountNumber"]/@value').extract())
        payment_method = ''.join(sel.xpath('//input[@name="AgencyPayment.PaymentMethodCode"]/@value').extract())
        payment_type = ''.join(sel.xpath('//input[@name="AgencyPayment.PaymentMethodType"]/@value').extract())
        currency_code = ''.join(sel.xpath('//input[@name="AgencyPayment.QuotedCurrencyCode"]/@value').extract())
        if not amount or not ac_number or not payment_method:
            self.insert_values_into_db(amend_dict, "Amend Failed", "Failed to navigate payment page")
            return
        data = [
            ('__RequestVerificationToken', request_token),
            ('AgencyPayment.QuotedAmount', amount),
            ('AgencyPayment.AccountNumber', ac_number),
            ('AgencyPayment.PaymentMethodCode', payment_method),
            ('AgencyPayment.PaymentMethodType', payment_type),
            ('AgencyPayment.QuotedCurrencyCode', currency_code),
        ]
        headers = {
            'Pragma': 'no-cache',
            'Origin': 'https://book.goair.in',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Cache-Control': 'no-cache',
            'Referer': 'https://book.goair.in/Payment/New',
            'Connection': 'keep-alive',
        }
        print "Submit payment"
        url = 'https://book.goair.in/Booking/Commit'
        yield FormRequest(url, callback=self.parse_booking_commit, formdata=data, headers=headers, meta={'amend_dict':amend_dict})

    def parse_booking_commit(self, response):
        sel = Selector(response)
        amend_dict = response.meta.get('amend_dict', {})
        time.sleep(20)
        self.insert_values_into_db(amend_dict, "Amend Failed", "Payment failed whereas payment is successful")
        url = 'https://book.goair.in/Booking/PostCommit'
        headers = {
            'Pragma': 'no-cache',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://book.goair.in/Payment/New',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
        }
        yield Request(url, callback=self.parse_post_payment, headers=headers, meta={'amend_dict':amend_dict}, dont_filter=True)

    def parse_post_payment(self, response):
        sel = Selector(response)
        amend_dict = response.meta.get('amend_dict', {})
        self.insert_values_into_db(amend_dict, "Confirmed", "")
        with open('G8_amend_%s.html'%amend_dict.get('trip_ref', ''), 'w+') as f:
            f.write('%s'%response.body)
