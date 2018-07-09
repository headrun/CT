import re
import ast
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
from seat_finder_tool_scrapers.utils import *
from scrapy.spiders import Spider
from collections import OrderedDict
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from scrapy.http import FormRequest, Request
from email.mime.multipart import MIMEMultipart
from scrapy.selector import Selector
from ConfigParser import SafeConfigParser
from scrapy.xlib.pydispatch import dispatcher
import csv
import codecs
from scrapy.conf import settings

_cfg = SafeConfigParser()
_cfg.read('../../../seat_finder_names.cfg')

class IndigoSeatFinderBrowse(Spider):
    name = "indigo_seatfinder_browse"
    start_urls = ["https://www.goindigo.in/"]
    handle_httpstatus_list = [404, 500]

    def __init__(self, *args, **kwargs):
        super(IndigoSeatFinderBrowse, self).__init__(*args, **kwargs)
        self.csv_dict = ast.literal_eval(kwargs.get('jsons', '{}'))
        self.log = create_logger_obj('indigo_seatfinder')
        self.multiple_pcc = False
        self.insert_query = 'insert into seat_finder(sk,airline,pnr,pcc,ticket_number,error_message, status,remarks, request_input,aux_info,created_at,modified_at) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), pnr=%s, ticket_number=%s, status=%s, error_message=%s,remarks=%s'
        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('seatfinder', 'IP')
        passwd = db_cfg.get('seatfinder', 'PASSWD')
        user = db_cfg.get('seatfinder', 'USER')
        db_name = db_cfg.get('seatfinder', 'DBNAME')
        self.conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()

    def send_mail(self, sub, error_msg=''):
        receivers_list = ast.literal_eval(_cfg.get('indigo_common', 'receivers_list'))
        if 'Login' in sub:
            receivers_list = ast.literal_eval(_cfg.get('indigo_common', 'login_receivers_list'))
        sender, receivers = 'ctmonitoring17@gmail.com', ','.join(receivers_list)
        ccing = ['sathwick.katta@cleartrip.com']
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Indigo PROD: %s On %s'%(sub, str(datetime.datetime.now().date()))
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

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()

    def parse(self, response):
        sel = Selector(response)
        print 'Parse function works'
        if not self.csv_dict:
            self.log.debug('Empty Request')
            return
        details_dict = self.csv_dict
	pnr_no = details_dict.get('airline_pnr','')
	self.log.debug("parse function:%s"%pnr_no)
        agent_pcc = details_dict.get('agent_pcc','')
        self.pcc_name = 'indigo_'+ agent_pcc
        try:self.log.debug('Finding Seat using: %s' % _cfg.get(self.pcc_name, 'login_name'))
        except:
            try:
                self.log.debug('Finding Seat using: %s' % self.pcc_name)
            except:
                pass
        if self.multiple_pcc:
            self.insert_into_table(err="Multiple PCC booking")
            self.log.debug('Multiple PCC booking')
            return
        try:
            data = [
      ('agentLogin.Username', _cfg.get(self.pcc_name, 'login_name')),
      ('agentLogin.Password', _cfg.get(self.pcc_name, 'login_pwd').strip("'")),
      ('IsEncrypted', 'true'),
                ]
        except:
            self.insert_into_table(err="PCC %s not available for scrapper" % self.pcc_name)
            self.log.debug('PCC not avaialble for scrapper')
            return
        url = 'https://book.goindigo.in/Agent/Login'
        yield FormRequest(url, callback=self.parse_next, formdata=data,dont_filter=True,meta={'details_dict':details_dict,'formdata':data})

    def parse_next(self, response):
        sel = Selector(response)
        details_dict = response.meta['details_dict']
        form_data = response.meta['formdata']
        pnr_no = details_dict['airline_pnr']
	self.log.debug("parse_next function: %s"%pnr_no)
        if response.status == 200 and 'Application/LoginError' not in response.url:
            token = ''.join(sel.xpath('//div[@class="bookingRef"]//input[@name="__RequestVerificationToken"]/@value').extract())
            url = 'https://book.goindigo.in/Agent/MyBookings'
            data = {'__RequestVerificationToken' : token}
            data.update({'indiGoMyBookings.BookingSearchRecordLocator' : pnr_no})
            data.update({'indiGoMyBookings_Submit' : 'Get Itinerary'})
            return FormRequest(url, callback=self.parse_itinerary, formdata=data, dont_filter=True, meta={'pnr_no' : pnr_no,'details_dict':details_dict})
        elif 'Application/LoginError' in response.url:
            self.log.debug('login failed')
            self.insert_into_table(err="login failed")
            self.send_mail("Indigo Unable to login on Login ID %s" %details_dict.get('agent_pcc','') , 'Scrapper Unable to login on Login ID')
            return
        else:
            self.log.debug('response.status is not 200')
            self.insert_into_table(err="response.status is not 200")
            return

    def parse_itinerary(self, response):
        sel = Selector(response)
        pnr_no = response.meta.get('pnr_no', '')
        details_dict = response.meta.get('details_dict','')
        if pnr_no and 'View' in response.url:
	    self.log.debug("parse_itinerary function:%s"%pnr_no)
            try: ref, _, pnr_status, _1, dob, payment_status = [i.strip() for i in sel.xpath('//div[@class="processStep"]/ul/li/h4//text()').extract()]
            except:
                self.log.debug("%s" % sel.xpath('//div[@class="processStep"]/ul/li/h4/text()').extract())
                self.insert_into_table(err="Xpaths changed in site, need to check" )
                return

            seats = seats_xpath = sel.xpath('//div[@id="itnServices"]//span[contains(text(),"SEAT")]/text()').extract()
            headers = sel.xpath('//div[@id="itnServices"]//th/text()').extract()
            if headers:
                headers = headers[1:]

            new_status_list = []
            seats_list =[]
            len_headers = len(headers)
            if len_headers==1:
                seats = ','.join(seats) + '{'+''.join(headers)+'}'
                new_status_list.append(seats)
            elif len_headers>1:
                seats_list = [seats[i:i+2] for i in range(0, len(seats), len_headers)]
            else:
                self.log.debug("len of headers is 0")

            for seat_list in seats_list:
                mapping = zip(headers,seat_list)
                for i in mapping:
                    loc = i[0].strip()
                    seat_no = i[1].strip()
                    new_status_list.append(seat_no +' {%s} '%loc)
            seats = seats_xpath
            status=''
            if pnr_status.upper()=='CONFIRMED' and seats==[]:
                remarks ='No Seat Numbers'
                status='Closed'

            elif pnr_status.upper()=='CONFIRMED' and seats!=[]:
                status='Flown'
                remarks = '%s'%(','.join(new_status_list).replace('SEAT ','').strip())

            elif pnr_status.upper() == 'CANCELLED':
                remarks='Cancelled'
                status = 'Closed'

            elif pnr_status.upper()=='PAYMENT DUE':
                status = 'Payment Due'
                remarks = 'Confirm'

            elif pnr_status.upper()=='FLOWN':
                status ='Flown'
                remarks='Complete'

            else:
                status='failed'
                remarks='failed'
		self.log.debug("Not within the range of conditions. Pnr status is %s and seats: %s"%(pnr_status,seats))
                #error_message='Not within the range of conditions'
                #self.insert_into_table(err=error_message)
                #return

            sk = details_dict.get('booking_no','')
            airline = details_dict.get('airline','')
            pnr = pnr_no
            pcc = details_dict.get('airline_pnr','')
            status = status
            remarks = remarks
            request_input = json.dumps(details_dict)
            aux_info = ''
            self.insert_into_table('',pnr,status,remarks)
        else:
            self.log.debug("Itinerary page not present:%s"%pnr_no)
            self.insert_into_table(err="Itinerary page not present")

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
