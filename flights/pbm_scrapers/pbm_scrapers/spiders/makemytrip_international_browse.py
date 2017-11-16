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


class MakemyInternationalBrowse(Spider):
    name = "makemytrip_flight_international"
    start_urls = ["https://www.makemytrip.com/flights"]

    def __init__(self, *args, **kwargs):
        super(MakemyInternationalBrowse, self).__init__(*args, **kwargs)
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
	#requests = terminal_requests(self.cr_tabe, self.source_name, self.crawl_type, self.trip_type, self.limit)
	'''
	for input_ in requests:
            got_sk, from_, to_, date, dx, re_date = input_
	    seg = '%s-%s'%(from_, to_)
	    date_ = str(date.date())
            date = datetime.datetime.strftime(date, '%d%b%Y')
	    #url = 'https://air.makemytrip.com/air/screen/ifsearch?tripType=O&itinerary=DXB-BKK-D-17Dec2017&paxType=A-1&cabinClass=E&_=1510636161596'
	    url = 'https://air.makemytrip.com/air/screen/ifsearch?tripType=O&itinerary=%s-D-%s&paxType=A-1&cabinClass=E'%(seg, date)
	    yield Request(url, callback=self.parse_next, meta={'date': date_, 'got_sk':got_sk, 'seg':seg})
	    yield Request(url, callback=self.parse_next)
	'''
	seg, date, got_sk, date_ = 'DXB-Bkk', '15Dec2017', '', ''
	url = 'https://air.makemytrip.com/air/screen/ifsearch?tripType=O&itinerary=%s-D-%s&paxType=A-1&cabinClass=E'%(seg, date)
        yield Request(url, callback=self.parse_next, meta={'date': date_, 'got_sk':got_sk, 'seg':seg})
 
    def parse_next(self, response):
	sel = Selector(response)
	got_sk = response.meta.get('got_sk', '')
	seg = response.meta.get('seg', '') 
	body = json.loads(response.body)
	flights = body.get('screenModel', {}).get('intl_flight_parent', {})\
		.get('data', {}).get('intl_flights_wraper', {}).get('data', {}).get('intl_flights', {}).get('data', {})
	for rank, flt in enumerate(flights, 1):
	    flt_data = flt.get('data', {}).get('flightdetails', {}).get('data', [])
	    price = flt.get('data', {}).get('ai', {}).get('data', {}).get('df', {})
	    flight_ids, airline_lst = [], []
	    arr_datetime, dep_datetime = ['']*2
	    sk = str(hashlib.md5('%s'%(str(flt))).hexdigest())
	    for idx, f_ in enumerate(flt_data):
		flt_details = f_.get('data', {}).get('bgDtls', {})
		flt_id = f_.get('data', {}).get('alnDtls', {}).get('data', {}).get('flt_key', '')
		airline = f_.get('data', {}).get('tDtl', {}).get('data', {}).get('oANm', '').strip()
		dep_time = f_.get('data', {}).get('tDtl', {}).get('data', {}).get('dlt', '')
		if flt_id: flight_ids.append(flt_id)
		if idx == 0 : arr_datetime = dep_time.replace('T', ' ')
		dep_datetime = dep_time.replace('T', ' ')
		if airline: airline_lst.append(airline)
	    vals = (str(sk), str(price), str('<>'.join(airline_lst)), str(dep_datetime), str(arr_datetime), str(rank), 'International', str(seg), 'oneway', str('<>'.join(flight_ids)))
	    self.out_put.write('%s\n'%'#<>#'.join(vals))
