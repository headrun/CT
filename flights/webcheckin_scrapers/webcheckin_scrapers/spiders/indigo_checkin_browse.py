import re
import json
import base64
import smtplib
import MySQLdb
import datetime
from ast import literal_eval
from scrapy import signals
from webcheckin_scrapers.utils import *
from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher
from ConfigParser import SafeConfigParser
from scrapy.conf import settings

class IndigoCheckinBrowse(Spider):
    name = "indigocheckin_browse"
    start_urls = ["https://www.goindigo.in/"]
    handle_httpstatus_list = [404, 500]
    def __init__(self, *args, **kwargs):
        super(IndigoCheckinBrowse, self).__init__(*args, **kwargs)
	self.log = create_logger_obj('indigo_webcheckin')
	self.check_dict = kwargs.get('jsons', {})
	self.ckeckin_dict = {}
        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('webcheckin', 'IP')
        passwd = db_cfg.get('webcheckin', 'PASSWD')
        user = db_cfg.get('webcheckin', 'USER')
        db_name = db_cfg.get('webcheckin', 'DBNAME')
        self.conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()
	self.insert_query = 'insert into indigo_webcheckin_status (sk, airline, status_message, error_message, created_at, modified_at) values(%s,%s,%s,%s,now(),now())  on duplicate key update modified_at=now(), sk=%s'
	dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()

    def get_current_ts_with_ms(self):
        dt = datetime.datetime.now().strftime("%Y%m%dT%H%M%S%f")
        return dt

    def parse(self, response):
	sel = Selector(response)
	try: check_dict = eval(self.check_dict)
	except: check_dict = {}
	if check_dict:
	    pnr = check_dict.get('pnr', '').strip()
	    last_name = check_dict.get('last_name', '').strip()
	    email = check_dict.get('email', '').strip()
	    v_token = ''.join(sel.xpath('//form[@id="retrieveBookingCheckin"]//input[@name="__RequestVerificationToken"]/@value').extract())
	    data = { 
		  '__RequestVerificationToken': v_token,
		  'indiGoRetrieveBooking.RecordLocator': pnr,
		  'indiGoRetrieveBooking.IndiGoRegisteredStrategy': 'Nps.IndiGo.Strategies.IndigoValidatePnrContactNameStrategy, Nps.IndiGo',
		  'indiGoRetrieveBooking.EmailAddress': '',
		  'indiGoRetrieveBooking.IsToEmailItinerary': 'False',
		  'indiGoRetrieveBooking.LastName': last_name,
		}
	    url = 'https://book.goindigo.in/CheckIn/CheckInInfo'
	    yield FormRequest(url, callback=self.parse_checkinfo, formdata=data, method="POST", meta={'check_dict':check_dict})
	else:
	    self.insert_error('Request not found', check_dict)

    def parse_checkinfo(self, response):
	sel = Selector(response)
	if 'CheckIN/View' in response.url: temp = True
	else: temp = False
	if 'CheckInError' in response.url: error_status = True
	else: error_status = False
	check_dict = response.meta['check_dict']
	params = {}
        nodes = sel.xpath('//form[@action="/CheckIn/View"]/input')
	for i in nodes:
	    key = ''.join(i.xpath('./@name').extract())
	    val = ''.join(i.xpath('./@value').extract())
	    params.update({key:val})
	bodingpass_key = ''.join(sel.xpath('//input[@name="indiGoPrintBoardingPasses.SellKey"]/@value').extract())
	params.update({'indiGoPrintBoardingPasses.SellKey':bodingpass_key})
	pick_seat = ''.join(sel.xpath('//div[@class="tableWrap splitTable"][1]//table/tbody//tr/td[3]/text()').extract()).strip()
	if not error_status:
	    if temp:
	        if pick_seat:
	            url = 'https://book.goindigo.in/CheckIn/View'
	            yield FormRequest(url, callback=self.parse_checkin_view, formdata=params,\
		    meta={'check_dict':check_dict})
		else: self.insert_error('Seat not selected', check_dict)
	    else: self.insert_error('IndiGo server error', check_dict)
	else:
	    message = 'Booking Retrieve Error : Details entered by you are incorrect. Please verify your Booking reference and Last name or email id you have used during booking. Please try again or contact our call centre at 0 99 10 38 38 38 or +91 124 6613838'
	    self.insert_error(message, check_dict)

    def parse_checkin_view(self, response):
	sel = Selector(response)
	data = {}
	token = ''.join(sel.xpath('//form[@id="EmailBoardingPass"]//input[@name="__RequestVerificationToken"]/@value').extract())
	email = ''.join(sel.xpath('//input[@name="indiGoEmailBoardingPasses.Email"]/@value').extract())
	indi_pnr = ''.join(sel.xpath('//input[@name="indiGoEmailBoardingPasses.PNR"]/@value').extract())
	data.update({
                        '__RequestVerificationToken':token,
                        'indiGoEmailBoardingPasses.Email':email,
                        'indiGoEmailBoardingPasses.PNR':indi_pnr
                        })
	url = 'https://book.goindigo.in/CheckIn/EmailBoardingPass'
	yield FormRequest(url, callback=self.parse_send_mail, dont_filter=True, formdata=data, meta={'pnr':indi_pnr})

    def parse_send_mail(self, response):
	sel = Selector(response)
	pnr = response.meta['pnr']
	filename = '%s_indigo_webcheckin_%s.html'%(pnr, self.get_current_ts_with_ms())
	with open(filename, 'wb') as f:
            f.write(response.body)
	vals = (pnr, 'IndiGo', 'Web checkin successful',
                        '', pnr)
        self.cur.execute(self.insert_query, vals)
        self.conn.commit()

    def insert_error(self, msg, check_dict):
	vals = (check_dict.get('pnr', ''), 'IndiGo', 'Web checkin failed',
                        msg, check_dict.get('pnr', ''))
        self.cur.execute(self.insert_query, vals)
        self.conn.commit()
