import ast
from ast import literal_eval
from collections import OrderedDict
from ConfigParser import SafeConfigParser
import copy
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
from seat_finder_tool_scrapers.utils import *
from scrapy.http import FormRequest
from scrapy.http import Request
from scrapy.spiders import Spider
from scrapy import signals
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher
import sys
from scrapy.conf import settings
_cfg = SafeConfigParser()
_cfg.read('../../../seat_finder_names.cfg')


class GoAirSeatFinderBrowse(Spider):
    name = "goair_seatfinder_browse"
    start_urls = ["https://book.goair.in/Agent/Login"]
    handle_httpstatus_list = [404, 500]
    def __init__(self, *args, **kwargs):
        super(GoAirSeatFinderBrowse, self).__init__(*args, **kwargs)
        self.request_verification = ''
        self.csv_dict = ast.literal_eval(kwargs.get('jsons', '{}'))
        self.proceed_to_cancel = 0
        self.trip_type = ''
        self.log = create_logger_obj('goair_seatfinder_booking')
        self.insert_query = 'insert into seat_finder(sk,airline,pnr,pcc,ticket_number,error_message, status,remarks, request_input,aux_info,created_at,modified_at) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), pnr=%s, ticket_number=%s, status=%s, error_message=%s,remarks=%s'
        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('seatfinder', 'IP')
        passwd = db_cfg.get('seatfinder', 'PASSWD')
        user = db_cfg.get('seatfinder', 'USER')
        db_name = db_cfg.get('seatfinder', 'DBNAME')
        self.conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()

    def send_mail(self, sub, error_msg=''):
        receivers_list = ast.literal_eval(_cfg.get('goair_common', 'receivers_list'))
        if 'Login' in sub:
            receivers_list = ast.literal_eval(_cfg.get('goair_common', 'login_receivers_list'))
        sender, receivers = 'ctmonitoring17@gmail.com', ','.join(receivers_list)
        ccing = ['sathwick.katta@cleartrip.com']
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'GoAIR PROD: %s On %s'%(sub, str(datetime.datetime.now().date()))
        mas = '<p>%s</p>' % error_msg
        msg['From'] = sender
        msg['To'] = receivers
        msg['Cc'] = ','.join(ccing)
        tem = MIMEText(''.join(mas), 'html')
        msg.attach(tem)
        s = smtplib.SMTP('smtp.gmail.com:587')
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(sender, 'ctmonitoring@123')
        s.sendmail(sender, (receivers_list + ccing), msg.as_string())
        s.quit()

    def parse(self, response):
        print 'Parse function works'
        sel = Selector(response)
        details_dict = self.csv_dict
        agent_pcc = details_dict.get('agent_pcc','')
        pcc_name = 'GOAIR_'+agent_pcc
        if 'coupon' in pcc_name:
            pcc_name =  'goair_default'
        login_data_list = []
        self.log.debug('Login PCC: %s' % pcc_name)
        pnr_no = details_dict['airline_pnr']
	self.log.debug('parse function:%s'%pnr_no)
        req_token_key = ''.join(sel.xpath('//form[@action="/Agent/Login"]/input/@name').extract())
        req_token_value = ''.join(sel.xpath('//form[@action="/Agent/Login"]/input/@value').extract())
        try:
            data = [
                (req_token_key, req_token_value),
                ('starterAgentLogin.Username', _cfg.get(pcc_name, 'username')),
                ('starterAgentLogin.Password', _cfg.get(pcc_name, 'passwd'))
            ]
        except:
            self.insert_into_table(err='PCC %s not available'%pcc_name)
            self.log.debug('PCC not avaialble for scrapper:%s'%pnr_no)
            return
        url = 'https://book.goair.in/Agent/Login'
        yield FormRequest(url, callback=self.parse_login, formdata=data,meta={'pnr_no' : pnr_no})

    def parse_login(self, response):
        '''
        Login into GoAir
        '''
        print 'Login works'
        sel = Selector(response)
        pnr_no= response.meta.get('pnr_no','')
	self.log.debug("parse_login function:%s"%pnr_no)
        user_check = ''.join(sel.xpath('//span[@class="user-info-number"]//text()').extract())
        login_status = True
        if 'error' in response.url.lower():
            self.insert_into_table(err='Login Failed')
	    self.log.debug("login failed:%s"%pnr_no)
            try:
                self.send_mail("Go Air Login Failed","Login Failed")
            except:
                print "login Failed - mail not sent"
                self.log.debug("login Failed - mail not sent")
            login_status = False
            return
        url = 'https://book.goair.in/Agent/Profile'
        yield Request(url, callback=self.parse_profile,meta={'pnr_no' : pnr_no})

    def parse_profile(self, response):
        sel = Selector(response)
        pnr_no= response.meta.get('pnr_no','')
	self.log.debug('parse_profile function:%s'%pnr_no)
        self.log.debug("Search for PNR: %s" % pnr_no)
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

        yield FormRequest('https://book.goair.in/MyBookings', callback=self.parse_pnr, formdata=data, meta={'pnr_no':pnr_no})

    def parse_pnr(self, response):
        sel = Selector(response)
        pnr_no= response.meta.get('pnr_no','')
	self.log.debug("parse_pnr function:%s"%pnr_no)
        search_result = sel.xpath('//div[@class="bookings-search-results-container"]//table/tbody/tr')
        site_details = {}
        if not search_result:
            self.insert_into_table(err='PNR details not found',status='Failed',remarks='Unable to view PNR')
            self.log.debug('PNR details not found:%s'%pnr_no)
            return
        if len(search_result) > 1:
            self.insert_into_table(err='Multiple search results found with PNR-%s'%pnr_no)
            self.log.debug("Multiple search results found with PNR-%s"%pnr_no)
            return
        href = ''.join(sel.xpath('//div[@class="bookings-search-results-container"]//table/tbody/tr/td[@class="table-row-action-cell"]/form[contains(@action, "Retrieve")]/@action').extract())
        if not href:
            self.insert_into_table(err='PNR Retrieve button not present')
            self.log.debug('PNR Retrieve button not present: %s'%pnr_no)
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
        if search_pnr !=pnr_no:
            status ='Closed'
            remarks ='Unable to View PNR'
            error = "PNR details not found"
            self.insert_into_table(error,pnr_no,status,remarks)
	    self.log.debug("PNR details not found:%s"%pnr_no)
            return
        data = [
          ('__RequestVerificationToken', request_token),
          ('goairRetrieveBooking.IsBookingListRetrieve', 'true'),
        ]
        yield FormRequest(href, callback=self.parse_pnr_details, formdata=data, meta={'site_details':site_details,'prn_no':pnr_no})

    def parse_pnr_details(self, response):
        sel = Selector(response)
        pnr = response.meta.get('pnr_no','')
	self.log.debug("parse_pnr_details function:%s"%pnr)
        segment_column = sel.xpath('//div[@class="itin-flight-details-1 mdl-grid"]//text()').extract()
        src_dest =  '-'.join(sel.xpath('//div[@class="mdl-grid mdl-grid--nesting flight-date-location"]/div[@class="itin-flight-details-station mdl-cell--6-col-desktop"]/h4/text()').extract())
        seats = sel.xpath('//div[@class="itin-flight-details-seat-designator"]/h5/text()').extract()
        status=''
        remarks = ''
        if segment_column and seats:
            seats_src_dst = ','.join(seats) + ' {' + src_dest + '}'
            status = 'Flown'
            remarks = seats_src_dst
        elif segment_column and seats==[]:
            status ='Closed'
            remarks = 'No Seat Number'
        elif segment_column==[]:
            status = 'Closed'
            remarks = 'Cancelled'
        else:
            status='Failed'
            remarks='Failed'
	    self.log.debug("Not within the range of conditions. Segmemt column is: %s and seats: %s"%(segment_column,seats))
            #error_message='Not within the range of conditions'
            #self.insert_into_table(err=error_message)
            #return
        status = status
        remarks = remarks
        self.insert_into_table('',pnr,status,remarks)

    def insert_into_table(self, err='',pnr='',status='',remarks=''):
        details_dict = self.csv_dict
        sk = details_dict.get('booking_no','')
        airline = details_dict.get('airline','')
        pcc = details_dict.get('agent_pcc','')
        ticket_number = details_dict.get('ticket_no','')
        pnr = details_dict.get('airline_pnr','')
        err = err
        status = status
        remarks = remarks
        request_input = json.dumps(details_dict)
        aux_info=''
        vals = (sk,airline,pnr,pcc,ticket_number,err,status,remarks, request_input,aux_info,pnr,ticket_number,status,err,remarks)
        try:
            self.cur.execute(self.insert_query, vals)
        except Exception as e:
            print 'some insert error'
            self.log.debug('Some insert error %s\n%s\n%s' % (e, self.insert_query, vals))
        self.conn.commit()
