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


class MakemyBrowse(Spider):
    name = "makemytrip_flight_international"
    start_urls = ["https://www.makemytrip.com/flights"]

    def __init__(self, *args, **kwargs):
        super(MakemyBrowse, self).__init__(*args, **kwargs)
	self.source_name = 'makemytrip'
        self.log = create_logger_obj(self.source_name)
        self.crawl_type = kwargs.get('crawl_type', '')
	self.trip_type = kwargs.get('trip_type', '')
        self.limit = kwargs.get('limit', '')
        self.out_put, self.out_put_file = get_output_file(self.source_name)
        self.cr_tabe = create_crawl_table_cursor()
        self.insert_query = "insert into mmt_availability (sk, price, airline, depature_datetime, arrival_datetime, rank, segments, flight_id, created_at, modified_at) values(%s, %s, %s, %s, %s, %s, %s, %s, now(), now()) on duplicate key update modified_at=now(), sk=%s"
	self.headers = ["Airline", "Flight_Number", "From Location", "To Location", "Departure_Date", "MMT Price", "MMT Rank"]
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.out_put.close()
        self.cr_tabe.close()
        #move_crawlout_processing(self.out_put_file)

    def open_excel_files(self):
        excel_file_name = 'mmt_%s_avail.csv'%(str(datetime.datetime.now().date()))
        oupf = open(excel_file_name, 'ab+')
        todays_excel_file  = csv.writer(oupf)
        return (todays_excel_file, excel_file_name)

    def parse(self, response):
        sel = Selector(response)
	'''
	requests = terminal_requests(self.cr_tabe, self.source_name, self.crawl_type, self.trip_type, self.limit)
	if requests:
	    excel_file, ex_file_name = self.open_excel_files()
	for input_ in requests:
            got_sk, from_, to_, date, dx, re_date = input_
	    date_ = str(date.date())
            date = datetime.datetime.strftime(date, '%d/%m/%Y')
	    url = 'http://flights.makemytrip.com/makemytrip/search-api.json?classType=E&dcID=&deptDate=%s&deviceType=desktop&filterReq=&fromCity=%s&isDateChange=&lob=Flight&noOfAdlts=1&noOfChd=0&noOfInfnt=0&toCity=%s&tripType=O&tripTypeDup=O'%(date, from_, to_)
	    yield Request(url, callback=self.parse_next, meta={'date': date_, 'got_sk':got_sk, 'excel_file':excel_file})'''

	url = 'https://air.makemytrip.com/air/screen/ifsearch?tripType=O&itinerary=DXB-BKK-D-17Dec2017&paxType=A-1&cabinClass=E&_=1510636161596'
	yield Request(url, callback=self.parse_next)
 
    def parse_next(self, response):
	sel = Selector(response)
        #date = response.meta.get('date', '')
	date = '2017-12-17'
	from_, to_ = "DXB", "BKK"
	#got_sk = response.meta.get('got_sk', '')
	#excel_file = response.meta['excel_file']
	body = json.loads(response.body)
	import pdb;pdb.set_trace()
