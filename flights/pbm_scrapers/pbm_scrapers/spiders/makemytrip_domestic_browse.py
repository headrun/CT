import os
import csv
import re
import json
import md5
import MySQLdb
import hashlib
import datetime
import logging
from pbm_scrapers.utils import *
from scrapy import log
from scrapy import signals
from ast import literal_eval
from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher
#from scrapy_splash import SplashRequest


class MakemyDomesticBrowse(Spider):
    name = "makemytrip_domestic_browse"
    start_urls = ["https://www.makemytrip.com/flights"]

    def __init__(self, *args, **kwargs):
        super(MakemyDomesticBrowse, self).__init__(*args, **kwargs)
	self.source_name = 'makemytrip'
        self.log = create_logger_obj(self.source_name)
        self.crawl_type = kwargs.get('crawl_type', '')
	self.trip_type = kwargs.get('trip_type', '')
        self.limit = kwargs.get('limit', '')
        self.out_put, self.out_put_file = get_output_file(self.source_name)
        self.cr_tabe = create_crawl_table_cursor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.out_put.close()
        self.cr_tabe.close()
        move_crawlout_processing(self.out_put_file)

    def parse(self, response):
        sel = Selector(response)
	'''
	requests = terminal_requests(self.cr_tabe, self.source_name, self.crawl_type, self.trip_type, self.limit)
	for input_ in requests:
            got_sk, from_, to_, date, dx, re_date = input_
	    date_ = str(date.date())
            date = datetime.datetime.strftime(date, '%d/%m/%Y')
	    url = 'http://flights.makemytrip.com/makemytrip/search-api.json?classType=E&dcID=&deptDate=%s&deviceType=desktop&filterReq=&fromCity=%s&isDateChange=&lob=Flight&noOfAdlts=1&noOfChd=0&noOfInfnt=0&toCity=%s&tripType=O&tripTypeDup=O'%(date, from_, to_)
	    yield Request(url, callback=self.parse_next, meta={'date': date_, 'got_sk':got_sk, 'from_':from_, 'to_':to_})

	    #url = 'https://ufs.makemytrip.com/flightSOA-web/search/df?classType=E&dcID=&deptDate=15%2F12%2F2017&deviceType=desktop&filterReq=&fromCity=DXB&isDateChange=&lob=Flight&noOfAdlts=1&noOfChd=0&noOfInfnt=0&rebookFlow=false&toCity=DEL&tripType=O&tripTypeDup=O'
	'''
	date, date_, from_, to_ = '2017-12-15', '15/12/2017', 'BOM', 'CCU'
	got_sk = ''
	url = 'http://flights.makemytrip.com/makemytrip/search-api.json?classType=E&dcID=&deptDate=%s&deviceType=desktop&filterReq=&fromCity=%s&isDateChange=&lob=Flight&noOfAdlts=1&noOfChd=0&noOfInfnt=0&toCity=%s&tripType=O&tripTypeDup=O'%(date_, from_, to_)
        yield Request(url, callback=self.parse_next, meta={'date': date, 'got_sk':got_sk, 'from_':from_, 'to_':to_})
 
    def parse_next(self, response):
	sel = Selector(response)
        date = response.meta.get('date', '')
	from_ = response.meta.get('from_', '')
	to_ = response.meta.get('to_', '')
	got_sk = response.meta.get('got_sk', '')
	body = json.loads(response.body)
	flights = body.get('flights', [])
	airline_lst = []
	dep_time, ar_time = '', ''
	for idx, flt in enumerate(flights, 1):
	    price = flt.get('af', 0)
	    legs = flt.get('le', [])
	    flight_ids_lst = []
	    sk = sk = str(hashlib.md5('%s'%(str(flt))).hexdigest())
	    for f_dx, i in enumerate(legs):
		cc_id = i.get('cc', '')
		flt_no = i.get('fn', '')
		flt_lst = []
	        flt_no = flt_no.split('_')
		for k in flt_no:
		    if k.strip():
		        flt_lst.append('%s-%s'%(cc_id, k.strip()))
		airline = i.get('an', '')
		if airline: airline_lst.append(airline)
		fr_dict = i.get('fr', {})
		base_fr = fr_dict.get('bf', 0)
		fs_fare = fr_dict.get('fs', 0)
		fare = base_fr + fs_fare
		depart_time = i.get('fmtDepartureTime', '')
		arrival_time = i.get('fmtArrivalTime', '')
		if f_dx == 0: dep_time = depart_time
		ar_time = arrival_time
		dep_ = i.get('dep', '').replace('T', ' ').replace('Z', '')
		origin = i.get('o', '')
		desct = i.get('d', '')
		flight_ids_lst.extend(flt_lst)
	    
	    #vals = (sk, price, airline, '%s %s'%(date, dep_time), '%s %s'%(date, ar_time), idx, '%s-%s'%(from_,to_), '<>'.join(flight_ids_lst).strip(), sk)
	    vals = (str(sk), str(price), str(airline), str('%s %s'%(date, dep_time)), str('%s %s'%(date, ar_time)), str(idx), 'Domestic', str('%s-%s'%(from_,to_)), 'oneway', str('<>'.join(flight_ids_lst)))
	    self.out_put.write('%s\n'%'#<>#'.join(vals))
