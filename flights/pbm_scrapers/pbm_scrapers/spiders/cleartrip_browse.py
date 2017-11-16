import os
import re
import json
import csv
import sys
import md5
import MySQLdb
import hashlib
import datetime
import operator
import logging
import requests
from pbm_scrapers.utils import *
from scrapy import log
from scrapy import signals
from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher

class CleartripBrowse(Spider):
    name = "cleartrip_browse"
    start_urls = ["https://www.cleartrip.com/flights/"]

    def __init__(self, *args, **kwargs):
        super(CleartripBrowse, self).__init__(*args, **kwargs)
	self.source_name = 'cleartrip'
        self.log = create_logger_obj(self.source_name)
        self.crawl_type = kwargs.get('crawl_type', '')
	self.trip_type = kwargs.get('trip_type', '')
        self.limit = kwargs.get('limit', '')
        self.out_put, self.out_put_file = get_output_file(self.source_name)
        self.cr_tabe = create_crawl_table_cursor()
	self.headers = ["Airline", "Flight_Number with Segnemts", "Departure_Date", "Cleartrip_Price"]
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
	self.out_put.close()
	self.cr_tabe.close()
	move_crawlout_processing(self.out_put_file)

    def open_excel_files(self):
        excel_file_name = 'cleartrip_%s_avail.csv'%(str(datetime.datetime.now().date()))
        oupf = open(excel_file_name, 'ab+')
        todays_excel_file  = csv.writer(oupf)
        return (todays_excel_file, excel_file_name)
	
    def parse(self, response):
        sel = Selector(response)
	'''
	requests = terminal_requests(self.cr_tabe, self.source_name, self.crawl_type, self.trip_type, self.limit)
	
	for input_ in requests:
            got_sk, from_, to_, date, dx, re_date = input_
            from_ = from_.strip()
            to_ = to_.strip()
	    date = datetime.datetime.strftime(date, '%d/%m/%Y')
	from_, to_, date = 'CCU', 'DEL', '04/12/2017'
	params = (
		    ('trip_type', 'OneWay'),
		    ('origin', from_),
		    ('from', from_),
		    ('destination', to_),
		    ('to', to_),
		    ('depart_date', date),
		    ('adults', '1'),
		    ('childs', '0'),
		    ('infants', '0'),
		    ('class', 'Economy'),
		    ('airline', ''),
		    ('carrier', ''),
		    ('ver', 'V2'),
		    ('type', 'json'),
		    ('intl', 'n'),
		    ('page', ''),
		    ('search_ver', 'V2'),
		    ('cc', '1'),
		    ('rhc', '1'),
		    ('timeout', '3000'),
		)
	url = 'https://www.cleartrip.com/flights/results/airjson'
	yield FormRequest(url, callback=self.parse_next, formdata=params, meta={'d_date':date, 'from_':from_, 'to_':to_})
	'''
	date = '2017-12-15'; from_ = 'BOM'; to_ = 'DEL'
	url = 'https://api.cleartrip.com/air/1.0/search?from=BOM&to=DEL&depart-date=2017-12-15&adults=1&country=IN&currency=INR&jsonVersion=1.0'
	headers = {
		'X-CT-API-KEY' : 'bce875d513bab5fa2cba6371f7b1ea58',
		'X-CT-SOURCETYPE' : 'B2C'
		}
	yield Request(url, callback=self.parse_next, headers=headers, meta={'d_date':date, 'from_':from_, 'to_':to_})

    def parse_next(self, response):
	sel = Selector(response)
	date = response.meta.get('d_date', '')
	#date = datetime.datetime.strptime(d_date, '%d/%m/%Y').date()
	from_ = response.meta['from_']
	to_ = response.meta['to_']
	body = json.loads(response.body)
	content = body.get('content', {})
	mapping = body.get('mapping', {})
	fares = body.get('fare', {})
	oneway_mapping = mapping.get('onward', [])
	segments_lst, seg_price_order = [], []
	excel_file, ex_file_name = self.open_excel_files()
	temp_dict = {}
	for rank, ow in enumerate(oneway_mapping, 1):
	    seg_details, status = {}, False
	    cont_code_lst = ow.get('c', [])
	    fare_code = ow.get('f', '')
	    fare_dict = fares.get(fare_code, {})
	    fr_ = fare_dict.get('dfd', '')
	    fare_ = fare_dict.get('HBAG', {}).get('dfd', {})
	    if fare_: fare_ = fare_dict.get('HBAG', {}).get(fare_, {}).get('pr', '')
	    if not fare_:
	        fare_ = fare_dict.get(fr_, {}).get('pr', '')
	    flts_lst, air_name = [], []
	    sk = str(hashlib.md5('%s'%(str(cont_code_lst))).hexdigest())
	    ar_seg_time, de_seg_time = '', ''
	    for seg_idx, i in enumerate(cont_code_lst):
		i = content.get(i, {})
		flt_dict = {}
		ar_date = i.get('ad', '')
		ar_time = i.get('a', '')
		if seg_idx == 0:
		    ar_seg_time = ar_time
		    de_seg_time = ''
		ar_ori = i.get('fr', '')
		ar_dest = i.get('to', '')
		flt_key = i.get('fk', '').split('_')
		try: airline, flight_no = flt_key[0], flt_key[1]
		except: airline, flight_no = ['']*2
		if 'ASIA' in flight_no:
		    airline, flight_no = '%s%s'%(flt_key[0],flt_key[1]), flt_key[2]
		if 'AMADEUS' in airline:
		    airline = 'JET AIRWAYS'
		air_name.append(airline)
		flts_lst.append(flight_no)
	    ar_dat = '%s %s'%(date, ar_seg_time)
	    seg_price_order.append([sk, fare_, '<>'.join(air_name), '', ar_dat, '0', '%s-%s'%(from_, to_), '<>'.join(flts_lst), sk])
	    #vals = (sk, fare_, '<>'.join(air_name), '', ar_dat, '0', '%s-%s'%(from_, to_), '<>'.join(flts_lst), sk)
	    #self.db_cur.execute(self.insert_query, vals)
	rank, price_, lst_, lst = 0, 0, {}, {}
	lsss = []
	for idx, i in enumerate(seg_price_order):
	    price = i[1]
	    try:nex_price = seg_price_order[idx+1][1]
	    except: nex_price = 0
	    lsss.append(i)
	    lst.update({rank:lsss})
	    if price != nex_price:
		rank = rank + 1; lsss = []
	fin_dict = {}
	for key, val in lst.iteritems():
	    price = val[0][1]
	    fin_dict.update({price:val})
	sorted_x = sorted(fin_dict.items(), key=operator.itemgetter(0))
	fin_rank = 1
	for i in sorted_x:
	    lsttt = sorted(i[1], key=lambda x: (x[4]))
	    for k in lsttt:
		sk, fare, air_name, de_dat, ar_dat, rank, seg, flts_, sk = k
		vals = (str(sk), str(fare), str(air_name), str(de_dat), str(ar_dat), str(fin_rank), 'Domestic', str(seg), 'oneway', str(flts_))
		self.out_put.write('%s\n'%'#<>#'.join(vals))
		#self.db_cur.execute(self.insert_query, vals)
		fin_rank = fin_rank + 1
