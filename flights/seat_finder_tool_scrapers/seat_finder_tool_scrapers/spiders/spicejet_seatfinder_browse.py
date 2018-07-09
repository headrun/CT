import re
import ast
import json
import md5
import time
import MySQLdb
import smtplib
import datetime
import inspect
import smtplib, ssl
from email import encoders
from scrapy import signals
from ast import literal_eval
from scrapy.spider import Spider
from scrapy.selector import Selector
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from seat_finder_tool_scrapers.utils import *
from ConfigParser import SafeConfigParser
from scrapy.http import FormRequest, Request
from scrapy.xlib.pydispatch import dispatcher
from email.mime.multipart import MIMEMultipart
from scrapy.conf import settings
import sys
sys.path.append('/root/scrapers/flights')
_cfg = SafeConfigParser()
_cfg.read('../../../seat_finder_names.cfg')


class SpicejetSeatFinderBrowse(Spider):
    name = "spicejet_seatfinder_browse"
    start_urls = ["https://book.spicejet.com/LoginAgent.aspx"]

    def __init__(self, *args, **kwargs):
        super(SpicejetSeatFinderBrowse, self).__init__(*args, **kwargs)
        self.source_name = 'spicejet'
        pnr_no = ''
        self.new_pnr = ''
        self.cancel = False
        self.log = create_logger_obj('spicejet_seatfinder')
        self.csv_dict = ast.literal_eval(kwargs.get('jsons', '{}'))
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
        receivers_list = ast.literal_eval(_cfg.get('spicejet_common', 'receivers_list'))
        if 'Login' in sub:
            receivers_list = ast.literal_eval(_cfg.get('spicejet_common', 'login_receivers_list'))
        sender, receivers = 'ctmonitoring17@gmail.com', ','.join(receivers_list)
        ccing = ['sathwick.katta@cleartrip.com']
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'SpiceJet PROD: %s On %s'%(sub, str(datetime.datetime.now().date()))
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
        '''Parse Login'''
        if not self.csv_dict:
            self.log.debug('Empty Request')
            self.insert_into_table('', 'Empty request')
            return
        login_data_list = []
        details_dict = self.csv_dict
        agent_pcc = details_dict.get('agent_pcc','')
        pcc_name = 'spicejet_'+ agent_pcc
        self.log.debug('Login PCC: %s' % pcc_name)
        pnr_no = details_dict['airline_pnr']
	self.log.debug("parse function:%s"%pnr_no)
        self.log.debug("Search for PNR: %s" % pnr_no)
        sel = Selector(response)
        view_state = ''.join(sel.xpath('//input[@id="viewState"]/@value').extract())
        login_data_list.append(('__VIEWSTATE', view_state))
        try:
            user_name = _cfg.get(pcc_name, 'username')
            user_psswd = _cfg.get(pcc_name, 'password')
        except:
            self.insert_into_table(err="PCC %s not available for scrapper" % pcc_name)
            self.log.debug('PCC not avaialble for scrapper')
            return
        self.log.debug('Login using %s' % user_name)
        login_data_list.append(('ControlGroupLoginAgentView$AgentLoginView$ButtonLogIn', 'Log In'))
        login_data_list.append(('ControlGroupLoginAgentView$AgentLoginView$TextBoxUserID', str(user_name)))
        login_data_list.append(('ControlGroupLoginAgentView$AgentLoginView$PasswordFieldPassword', str(user_psswd)))
        yield FormRequest('https://book.spicejet.com/LoginAgent.aspx', \
                formdata=login_data_list, callback=self.parse_next, meta={'pnr_no' : pnr_no, 'user_name' : user_name})

    def parse_next(self, response):
        sel = Selector(response)
        pnr_no = response.meta['pnr_no']
        if response.status == 200:
	    self.log.debug("parse_next function:%s"%pnr_no)
            url = 'https://book.spicejet.com/BookingList.aspx'
            return Request(url, callback=self.parse_search, dont_filter=True, meta={'pnr_no' : pnr_no})
        else:
            self.send_mail("SpiceJet Unable to login on Login ID %s" % response.meta.get('username', '') , 'Scrapper Unable to login on Login ID')
            self.insert_into_table(err='Unable to login on LOGIN ID %s' % response.meta.get('username', ''))
	    self.log.debug('Unable to login on LOGIN ID %s' % response.meta.get('username', ''))

    def parse_search(self, response):
        sel = Selector(response)
        pnr_no = response.meta.get('pnr_no', '')
	self.log.debug("parse_search function:%s"%pnr_no)
        view_state = ''.join(sel.xpath('//input[@id="viewState"]/@value').extract())
        search_data_list = {}
        search_data_list.update({'__VIEWSTATE': str(view_state)})
        if pnr_no:
            agp_key = ''.join(sel.xpath('//input[@id="AGPKey"]/@value').extract())
            agp_returnurl = ''.join(sel.xpath('//input[@id="AGPRETURNURL"]/@value').extract())
            qp_Key = ''.join(sel.xpath('//input[@id="QPKey"]/@value').extract())
            reports_key = ''.join(sel.xpath('//input[@id="ReportsKey"]/@value').extract())
            search_data_list.update({'ControlGroupBookingListView$BookingListBookingListView$TextBoxKeyword': pnr_no})
            search_data_list.update({'__EVENTTARGET' : 'ControlGroupBookingListView$BookingListBookingListView$LinkButtonFindBooking'})
            search_data_list.update({'ControlGroupBookingListView$BookingListBookingListView$Search' : 'ForAgency'})
            search_data_list.update({'ControlGroupBookingListView$BookingListBookingListView$DropDownListTypeOfSearch' : '1'})
            search_data_list.update({'AGPKey' : agp_key})
            search_data_list.update({'AGPRETURNURL' : agp_returnurl})
            search_data_list.update({'QPKey' : qp_Key})
            search_data_list.update({'ReportsKey' : reports_key})
            search_data_list.update({'pageToken' : ''})
            search_data_list.update({'__EVENTARGUMENT' : ''})
            url = "https://book.spicejet.com/BookingList.aspx"
            return FormRequest(url, formdata=search_data_list, callback=self.parse_pnr_details, meta={'pnr_no' : pnr_no, 'search_data_list': search_data_list}, dont_filter=True)

    def parse_pnr_details(self, response):
        sel = Selector(response)
	self.log.debug("parse_pnr_details")
        pnr_no = response.meta.get('pnr_no', '')
	self.log.debug("parse_pnr_details:%s"%pnr_no)
        search_data_list = response.meta['search_data_list']
        view_state = ''.join(sel.xpath('//input[@id="viewState"]/@value').extract())
        eventarg = 'Edit:%s' % pnr_no
        self.log.debug("%s editing..." % pnr_no)
        search_data_list.update({'__EVENTARGUMENT' : eventarg})
        search_data_list.update({'__VIEWSTATE': str(view_state)})
        search_data_list.update({'__EVENTTARGET' : 'ControlGroupBookingListView$BookingListBookingListView'})
        url = "https://book.spicejet.com/BookingList.aspx"
        return FormRequest(url, callback=self.parse_modify, dont_filter=True, formdata=search_data_list, meta={'pnr_no' : pnr_no})

    def parse_modify(self, response):
        sel = Selector(response)
        details_dict = self.csv_dict
	pnr_no = response.meta.get('pnr_no', '')
        if 'Itinerary.aspx' in response.url:
	    self.log.debug("Itinerary page - parse_modify function:%s"%pnr_no)
            booking_detail = sel.xpath('//table[@id="bookingDetail"]//tr/td/span//strong/text()').extract()
            pnr_, pnr_status, dobooking,payment_status=booking_detail
            seats =''
            seats_ = sel.xpath('//span[@class="MMB-table-ssr-icon"]')
            status =''
            if seats_:
                seats = ','.join(seats_.xpath('./span[@class="grid-SpiceMax-icon"]/../text()').extract()) + ','+','.join(seats_.xpath('./span[@class="grid-seat-icon"]/../text()').extract())
                seats = seats.strip(',')
            if pnr_status.upper()=='CONFIRMED' and seats=='':
                remarks ='No Seat Number'
                status='Closed'
            elif pnr_status.upper() =='CANCELLED':
                remarks='Cancelled'
                status ='Closed'
            elif (pnr_status.upper() == 'CLOSED' or pnr_status.upper() == 'CONFIRMED') and seats!='':
                status='Flown'
                src_dst = sel.xpath('//div[@class="flight-destination-name"]/text()').extract()
                if len(src_dst)==2:
                    remarks = '%s'%(''.join(seats)+' {%s}'%'-'.join(src_dst))
                elif len(src_dst)==4:
                    flight1_route = '-'.join(src_dst[:2])
                    flight2_route = '-'.join(src_dst[2:])
                    seats = seats_.xpath('./span[@class="grid-SpiceMax-icon"]/../text()').extract() + seats_.xpath('./span[@class="grid-seat-icon"]/../text()').extract()
                    flight1_seats , flight2_seats= [],[]
		    try:
			for seat in seats:
                                f1,f2 = seat.split(',')
		    except:
			if len(seats)==2:
                                f1,f2= seats
                    flight1_seats.append(f1)
                    flight2_seats.append(f2)
                    remarks = '%s, %s'%(','.join(flight1_seats) + ' {%s}'%flight1_route,','.join(flight2_seats) + ' {%s}'%flight2_route)
                else:
                    remarks = '%s'%seats
                    status = status
                    self.insert_into_table('connecting flights scenario',pnr_no,status,remarks)
                    return

            elif pnr_status.upper()=='PAYMENT DUE':
                status = 'Payment Due'
                remarks = 'Confirm'

            else:
                remarks='Confirm'
                status = 'Closed'

            sk = details_dict.get('booking_no','')
            airline = details_dict.get('airline','')
            pnr = pnr_no
            pcc = details_dict.get('airline_pnr','')
            status = status.replace('SEAT','').strip()
            remarks = remarks
            request_input = json.dumps(details_dict)
            aux_info = ''
            self.insert_into_table('',pnr,status,remarks)

        else:
            self.log.debug("Itinerary page not present:%s"%pnr_no)
            self.insert_into_table(err="Itinerary page not present")
            return


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
