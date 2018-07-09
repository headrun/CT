from ast import literal_eval
from collections import OrderedDict
from ConfigParser import SafeConfigParser
import copy
import datetime
from datetime import timedelta
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

from splitcancellation_scrapers.utils import *
from goairsplit_cancel_utils import *

from scrapy.conf import settings

import sys
sys.path.append(settings['ROOT_PATH'])

from root_utils import Helpers

_cfg = SafeConfigParser()
_cfg.read(settings['BOOK_PCC_PATH'])

class GoAirSplitCancelBrowse(Spider, GoAirCancelUtils, Helpers):
    name = "goair_splitcancel_browse"
    start_urls = ["https://book.goair.in/Agent/Login"]
    handle_httpstatus_list = [404, 500]

    def __init__(self, *args, **kwargs):
        super(GoAirSplitCancelBrowse, self).__init__(*args, **kwargs)
        self.request_verification = ''
        self.cancel_dict = kwargs.get('jsons', {})
        self.proceed_to_cancel = 0
        self.trip_type = ''
        self.new_pnr = ''
        self.split_check = False
        self.log_cookies = {}
        self.log = create_logger_obj('goair_splitcancel_booking')
        self.insert_query = 'insert into goairsplit_cancellation_report(sk, airline, pnr, new_pnr, pcc, flight_number, error_message, status, cancel_amount, pricing_details, request_input, aux_info, created_at, modified_at) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now()) on duplicate key update modified_at=now(), error_message=%s, pricing_details=%s, request_input=%s, cancel_amount=%s, status=%s, new_pnr=%s'
        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('splitcancel', 'IP')
        passwd = db_cfg.get('splitcancel', 'PASSWD')
        user = db_cfg.get('splitcancel', 'USER')
        db_name = db_cfg.get('splitcancel', 'DBNAME')
        self.conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()
        headers = { 
               'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
                'Upgrade-Insecure-Requests': '1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Referer': 'https://book.goair.in/Booking',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }   
        res = requests.get('https://book.goair.in/Agent/Logout', headers=headers, cookies=self.log_cookies)

    def parse(self, response):
        print 'Parse function works'
        sel = Selector(response)
        try:
            self.pcc_name = self.get_pcc_name()
            err_msg = self.cancel_dict.get('error', '')
        except Exception as e:
            cancel_dict = copy.copy(self.cancel_dict)
            self.insert_into_table("Cancel Failed", e.message)
            self.send_mail("Split Cancel Failed", e.message, "splitcancel", "GoAir", "goair_common")
            return
        if 'coupon' in self.pcc_name:
             self.pcc_name =  'goair_default'
        login_data_list = []
        if len(self.cancel_dict['details']) == 2:
            self.log.debug('Multiple PNR Cancellation')
            self.insert_into_table("Split Cancel Failed",'Multiple PNR Cancellation')
            return
        print self.pcc_name
        cancellation_type = self.cancel_dict.get('cancel_type', '')
        pnr_no = self.cancel_dict['details'][0].get('pnr', '')
        self.log.debug("Search for PNR: %s" % pnr_no)
        if not cancellation_type:
            self.log.debug('Cancellation type is Empty')
            self.insert_into_table("Split Cancel Failed", 'Cancellation type is Empty')
        if len(self.cancel_dict['details'][0]['all_segment_details']) != len(self.cancel_dict['details'][0]['cancelled_segment_details']):
            self.insert_into_table('Split Cancel Failed', 'Failing as Partial segment cancellation')
            self.log.debug('Partial segment cancellation error')
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
            self.insert_into_table("Split Cancel Failed", "PCC %s not available"%self.pcc_name)
            logging.debug('PCC %s not avaialble for scrapper' % self.pcc_name)
            self.send_mail("Split Cancel Failed", "PCC %s not avaialble for scrapper" % self.pcc_name, "splitcancel", "GoAir", "goair_common")
            return
        url = 'https://book.goair.in/Agent/Login'
        yield FormRequest(url, callback=self.prase_login, formdata=data)

    def prase_login(self, response):
        '''
        Login into Indigo
        '''
        print 'Login works'
        sel = Selector(response)
        user_check = ''.join(sel.xpath('//span[@class="user-info-number"]//text()').extract())
        login_status = True
        if 'error' in response.url.lower():
            self.insert_into_table("Split Cancel Failed", "Login Failed")
            self.send_mail("Split Cancel Failed", "Login Failed", "Splitcancel", "GoAir", "goair_common")
            login_status = False
            return
        url = 'https://book.goair.in/Agent/Profile'
        yield Request(url, callback=self.parse_profile, dont_filter=True)

    def parse_profile(self, response):
        sel = Selector(response)
        if not self.split_check:
		    pnr_no = self.cancel_dict['details'][0].get('pnr', '')
        else:
            pnr_no = self.new_pnr
        self.log.debug("Search for PNR: %s" % pnr_no)
        if not pnr_no:
            self.insert_into_table("Split Cancel Failed", "Received Empty PNR")
            logging.debug('No PNR avail for search')
            return

        logout_cookies = response.request.headers.get('Cookie', '').split(';')
        for i in logout_cookies:
            try: key, val = i.split('=', 1)
            except: continue
            self.log_cookies[key] = val

        request_token = ''.join(sel.xpath('//form[@id="RetrieveByPnr"]/input[@name="__RequestVerificationToken"]/@value').extract())
        data = [
		  ('__RequestVerificationToken', request_token),
		  ('goAirRetrieveBookingsByRecordLocator.RecordLocator', pnr_no),
		  ('goAirRetrieveBookingsByRecordLocator.SearchArchive', 'false'),
		  ('goAirRetrieveBookingsByRecordLocator.SourceOrganization', ''),
		  ('goAirRetrieveBookingsByRecordLocator.OrganizationGroupCode', ''),
		  ('goAirRetrieveBookingsByRecordLocator.PageSize', '10'),
		  ('goAirRetrieveBookingsByRecordLocator.PerformSearch', 'True'),
        ]
        yield FormRequest('https://book.goair.in/MyBookings', callback=self.parse_pnr, formdata=data, dont_filter=True)

    def parse_pnr(self, response):
        sel = Selector(response)
        search_result = sel.xpath('//div[@class="bookings-search-results-container"]//table/tbody/tr')
        site_details = {}
        if not search_result:
            error = "PNR details not found"
            self.insert_into_table('Cancel Failed', error)
            print error
            return
        if len(search_result) > 1:
            error = "Multiple search results found with PNR-%s"
            self.insert_into_table('Cancel Failed', error)
            print error
            return
        href = ''.join(sel.xpath('//div[@class="bookings-search-results-container"]//table/tbody/tr/td[@class="table-row-action-cell"]/form[contains(@action, "Retrieve")]/@action').extract())
        checkin_href = ''.join(sel.xpath('//div[@class="bookings-search-results-container"]//table/tbody/tr/td[@class="table-row-action-cell"]/form[contains(@action, "CheckIn")]/@action').extract())
        if not checkin_href:
            error = "Already cancelled"
            self.insert_into_table('Cancel Failed', error)
            return
        if not href:
            error = "PNR Retrieve button not presented"
            self.insert_into_table('Cancel Failed', error)
            print error
            return
        else:
            href = 'https://book.goair.in%s'%href
        request_token = sel.xpath('//div[@class="bookings-search-results-container"]//table/tbody/tr/td[@class="table-row-action-cell"]/form[contains(@action, "Retrieve")]/input[@name="__RequestVerificationToken"]/@value').extract()
        search_pnr = ''.join(sel.xpath('//div[@class="bookings-search-results-container"]//table/tbody/tr/td[4]/text()').extract())
        depart_date = ''.join(sel.xpath('//div[@class="bookings-search-results-container"]//table/tbody/tr/td[1]/text()').extract())
        site_origin = ''.join(sel.xpath('//div[@class="bookings-search-results-container"]//table/tbody/tr/td[2]/text()').extract())
        site_dest = ''.join(sel.xpath('//div[@class="bookings-search-results-container"]//table/tbody/tr/td[3]/text()').extract())
        site_details['site_origin'] = site_origin
        site_details['site_dest'] = site_dest
        if not self.split_check:
            if search_pnr != self.cancel_dict['details'][0].get('pnr', ''):
                error = "PNR details not found"
                self.insert_into_table('Cancel Failed', error)
                print error
                return
            self.cancel_dict['site_details'] = site_details
        data = [
                    ('__RequestVerificationToken', request_token),
                    ('goairRetrieveBooking.IsBookingListRetrieve', 'true'),
        ]
        yield FormRequest(href, callback=self.parse_pnr_details, formdata=data, dont_filter=True)

    def parse_pnr_details(self, response):
        sel = Selector(response)
        cancellation_type = self.cancel_dict.get('cancel_type', '')
        outbound_date = ''.join(sel.xpath('//h4[contains(text(), "Outbound")][1]//text()').extract())
        outbound_date = ''.join(re.findall('\d+ \w+ \d{4}$', outbound_date.strip()))
        ow_flight_details = sel.xpath('//h4[contains(text(), "Outbound")]/../following-sibling::div[1]//h4/text()').extract()
        flight_check, passengers_check, dep_arr_check = False, False, False
        flight_numbers = sel.xpath('//div[@class="itin-flight-details-1 mdl-grid"]/div[contains(@class, "itin-flight-details-carrier")]/h4/text()').extract()
        flight_check = self.check_flight_ids(flight_numbers)
        g8_pass_names = sel.xpath('//div[@class="itin-passengers-content group"]/div[2]/h5/text()').extract()
        g8_infants = [i.strip('Traveling with ') for i in sel.xpath('//div[@class="itin-infant-name"]/h5/text()').extract()]
        site_pass_names = g8_pass_names + g8_infants
        passengers_check, duplicate_pax = self.check_pax_details(site_pass_names)
        if not self.split_check:
            if passengers_check:
                self.insert_into_table('Cancel Failed', "Pax name not matched")
                return
            if flight_check:
                self.insert_into_table('Cancel Failed', "Flight ids not matched")
                return
            if duplicate_pax:
                self.insert_into_table('Cancel Failed', "Duplicate pax presented")
                return
            segments_check, depart_date_check = self.check_segments(outbound_date, ow_flight_details)
            if segments_check:
                self.insert_into_table('Cancel Failed', "Sigments missmatched")
                return
            if depart_date_check:
                self.insert_into_table('Cancel Failed', "Travel date missmatched")
                return
        cancel_button_check = sel.xpath('//div[@class="mdl-grid itin-sub-header itin-sub-header-tablet"]//div//a[contains(@href, "Booking/Manage?state=Cancel")]/@href').extract()
        split_button_check = sel.xpath('//div[@class="mdl-grid itin-sub-header itin-sub-header-tablet"]//div//a[@data-target="#split-pnr"]').extract()
        if cancellation_type == "PARTIAL":
            print "go to partial cancel"
            dupe_pax = self.check_dup_pax()
            if dupe_pax:
                self.insert_into_table('Cancel Failed', "Duplicate pax presented")
                return
            if not self.split_check:
                if not split_button_check:
                    self.insert_into_table('Cancel Failed', "Split PNR button not presented")
                    return
                split_pax_dict = {}
                clean_pax_patt = re.compile('\(.*\)')
                split_pax_nodes = sel.xpath('//div[@class="available-passengers"]//div[@class="passengers-list"]/input')
                for node in split_pax_nodes:
                    pax_val = ''.join(node.xpath('./@value').extract())
                    pax_name = normalize(''.join(node.xpath('./../text()').extract()))
                    pax_name = clean_pax_patt.sub('', pax_name)
                    if pax_name: pax_name = pax_name.split('.')[-1]
                    split_pax_dict[pax_name.replace(' ', '').lower()] = pax_val

                split_pax_list = self.split_pax_value(split_pax_dict)
                data = []
                split_value = '#'.join(split_pax_list).strip('#')
                data.append(('goAirSplitBooking.SplitKeys', '%s#'%split_value))
                url = 'https://book.goair.in/Booking/Split'
                yield FormRequest(url, callback=self.parse_split_cancel, formdata=data, dont_filter=True)
            else:
                url = 'https://book.goair.in/Booking/Manage?state=Cancel'
                yield Request(url, callback=self.parse_cancel, dont_filter=True)
        else:
            if not cancel_button_check:
                self.insert_into_table('Cancel Failed', "cancel button not presented")
                return
            url = 'https://book.goair.in/Booking/Manage?state=Cancel'
            print "go to full cancel"
            yield Request(url, callback=self.parse_cancel, dont_filter=True)

    def parse_split_cancel(self, response):
        sel = Selector(response)
        error = normalize(''.join(sel.xpath('//div[@class="error-msg alert alert-error"]//ul//li//text()').extract()))
        if error:
            self.insert_into_table('Cancel Failed', error)
            return
        self.new_pnr = ''.join(sel.xpath('//h5[contains(text(), "Child PNR")]//text()').extract())
        print self.new_pnr
        self.log.debug("Split PNR: %s" % self.new_pnr)
        if self.new_pnr: self.new_pnr = normalize(self.new_pnr.split(':')[-1])
        with open('g8_split_%s.html'%self.cancel_dict.get('trip_ref', ''), 'w+') as f:
            f.write('%s'%response.body)
        url = 'https://book.goair.in/Booking/Manage?state=Cancel'
        if self.new_pnr:
            self.split_check = True
            url = 'https://book.goair.in/Agent/Profile'
            yield Request(url, callback=self.parse_profile, dont_filter=True)
        else:
            self.insert_into_table('Cancel Failed', "Child PNR not found")

    def parse_cancel(self, response):
        sel = Selector(response)
        error = normalize(''.join(sel.xpath('//div[@class="error-msg alert alert-error"]//ul//li//text()').extract()))
        if error:
            self.insert_into_table('Cancel Failed', error)
            return
        token = ''.join(sel.xpath('//form[@action="/Payment/Refund"]/input[@name="__RequestVerificationToken"]/@value').extract())
        keys_nodes = sel.xpath('//form[@action="/Payment/Refund"]/input')
        balance_due = ''.join(sel.xpath('//span[contains(text(), "Balance due")]/following-sibling::span[1]//text()').extract())
        total_refund = ''.join(sel.xpath('//span[contains(text(), "Refund total")]/following-sibling::span[1]//text()').extract())
        form_data = {}
        for node in keys_nodes:
            key = ''.join(node.xpath('./@id').extract())
            value = ''.join(node.xpath('./@value').extract())
            if key and value:
                form_data[key] = value
        form_data['__RequestVerificationToken'] = token
        url = 'https://book.goair.in/Payment/Refund'
        yield FormRequest(url, callback=self.parse_refund, formdata=form_data, method="POST", dont_filter=True)

    def parse_refund(self, response):
        sel = Selector(response)
        url = 'https://book.goair.in/Booking/Commit'
        yield Request(url, callback=self.parse_post_cancel, method="POST", dont_filter=True)

    def parse_post_cancel(self, response):
        sel = Selector(response)
        time.sleep(10)
        with open('g8_post_cancel_%s.html'%self.cancel_dict.get('trip_ref', ''), 'w+') as f:
        	f.write('%s'%response.body)
        url = 'https://book.goair.in/Booking/PostCommit'
        yield Request(url, callback=self.parse_final, dont_filter=True)

    def parse_final(self, response):
        sel = Selector(response)
        print "final"
        pax_names = normalize(','.join(sel.xpath('//div[@class="itin-passengers-content group"]//div[not(contains(@class, "index"))]//h5//text()').extract()))
        try:
            bal_nodes = sel.xpath('//div[@class="price-display-content"]//div[@id="price_display_total"]')
            bal_price = ''.join(sel.xpath('//div[@class="price-display-content"]//div[@id="price_display_total"]//span[@class="js-total-price hidden"]//text()').extract()).strip('()')
        except:
            print "xpath error"
        nodes = sel.xpath('//div[@class="itin-payment-content group mdl-grid"]')
        pricing_details = {}
        for idx, node in enumerate(nodes):
            pricing_details[idx] = node.xpath('.//div//h5//text()').extract()
        pricing_details['pax_names'] = pax_names
        self.cancel_dict['pricing_details'] = [pricing_details]
        if self.split_check: cn_msg = "Split and Cancel Success"
        else: cn_msg = "Full Cancel Success"
        self.insert_into_table(cn_msg, '')
        with open('g8_cancel_%s.html'%self.cancel_dict.get('trip_ref', ''), 'w+') as f:
            f.write('%s'%response.body)
