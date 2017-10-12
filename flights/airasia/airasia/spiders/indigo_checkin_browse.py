import re
import json
import base64
import smtplib
import MySQLdb
import datetime
from ast import literal_eval
from scrapy import signals
from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher
from scrapy_splash import SplashRequest, SplashFormRequest

class IndigoCheckinBrowse(Spider):
    name = "indiocheckin_browse"
    start_urls = ["https://www.goindigo.in/"]
    handle_httpstatus_list = [404, 500]
    def __init__(self, *args, **kwargs):
        super(IndigoCheckinBrowse, self).__init__(*args, **kwargs)
	self.check_dict = kwargs.get('jsons', {})
	self.ckeckin_dict = {}
	self.conn = MySQLdb.connect(host="localhost", user = "root", db='WEBCHECKINDB', charset="utf8", use_unicode=True)
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
	    pnr = check_dict.get('pnr', '')
	    last_name = check_dict.get('last_name', '')
	    email = check_dict.get('email', '')
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

    def parse_checkinfo(self, response):
	sel = Selector(response)
	if 'CheckIN/View' in response.url: temp = True
	else: temp = False
	check_dict = response.meta['check_dict']
	params = {}
        nodes = sel.xpath('//form[@action="/CheckIn/View"]/input')
	for i in nodes:
	    key = ''.join(i.xpath('./@name').extract())
	    val = ''.join(i.xpath('./@value').extract())
	    params.update({key:val})
	bodingpass_key = ''.join(sel.xpath('//input[@name="indiGoPrintBoardingPasses.SellKey"]/@value').extract())
	params.update({'indiGoPrintBoardingPasses.SellKey':bodingpass_key})
	plash_args = {'html': 1,'png': 1}
	pick_seat = ''.join(sel.xpath('//div[@class="tableWrap splitTable"][1]//table/tbody//tr/td[3]/text()').extract())
	if pick_seat and temp:
	    url = 'https://book.goindigo.in/CheckIn/View'
	    yield SplashFormRequest(url, callback=self.parse_checkin_view, formdata=params,\
		 endpoint='render.json', args=plash_args, meta={'check_dict':check_dict})
	else:
	    vals = (check_dict.get('pnr', ''), 'IndiGo', 'Web checkin failed',
			'Seat not selected', check_dict.get('pnr', ''))
	    self.cur.execute(self.insert_query, vals)
	    self.conn.commit()

    def parse_checkin_view(self, response):
	sel = Selector(response)
	data = {}
	token = ''.join(sel.xpath('//form[@id="EmailBoardingPass"]//input[@name="__RequestVerificationToken"]/@value').extract())
	email = ''.join(sel.xpath('//input[@name="indiGoEmailBoardingPasses.Email"]/@value').extract())
	indi_pnr = ''.join(sel.xpath('//input[@name="indiGoEmailBoardingPasses.PNR"]/@value').extract())
	imgdata = base64.b64decode(response.data['png'])
        filename = '%s_%s.png'%(indi_pnr, self.get_current_ts_with_ms())
        with open(filename, 'wb') as f:
            f.write(imgdata)
	data.update({
                        '__RequestVerificationToken':token,
                        'indiGoEmailBoardingPasses.Email':email,
                        'indiGoEmailBoardingPasses.PNR':indi_pnr
                        })
	url = 'https://book.goindigo.in/CheckIn/EmailBoardingPass'
	yield FormRequest(url, callback=self.parse_send_mail, formdata=data, meta={'pnr':indi_pnr})

    def parse_send_mail(self, response):
	sel = Selector(response)
	pnr = response.meta['pnr']
	filename = '%s_%s.html'%(pnr, self.get_current_ts_with_ms())
	with open(filename, 'wb') as f:
            f.write(response.body)
	vals = (pnr, 'IndiGo', 'Web checkin successfull',
                        '', pnr)
        self.cur.execute(self.insert_query, vals)
        self.conn.commit()
