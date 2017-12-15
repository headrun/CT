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
from operator import itemgetter
from scrapy import signals
from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher

class GoibiboDomesticBrowse(Spider):
    name = "goibibo_domestic_browse"
    start_urls = ["https://www.goibibo.com/flights/"]

    def __init__(self, *args, **kwargs):
        super(GoibiboDomesticBrowse, self).__init__(*args, **kwargs)
	self.source_name = 'goibibo'
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
            from_ = from_.strip()
            to_ = to_.strip()
	    date = str(date.date())
	    date_ = datetime.datetime.strptime(date, '%d/%m/%Y')
	    yield Request(url, callback=self.parse_next, headers=headers, meta={'d_date':date, 'from_':from_, 'to_':to_})
	'''
	params = (
    			('userid', 'asd'),
    			('application', 'fbs'),
  			('flavour', 'v2'),
    			('mime', 'html'),
  			('script', 'y'),
    			('actionData', '[{"query":"air-BOM-CCU-20171215--1-0-0-E-100--"}]'),
			('bookability', 'n'),
		)
	from_, to_, date, re_date = 'BOM', 'CCU', '15/12/2017', '2017-12-15'
	url = 'https://thor.goibibo.com/v2/thor/rest/flight/search/'
	date = '2017-12-15'
        yield FormRequest(url, callback=self.parse_next, formdata=params, meta={'d_date':date, 'from_':from_, 'to_':to_}, method='GET')

    def parse_next(self, response):
	sel = Selector(response)
	date = response.meta.get('d_date', '')
	from_ = response.meta['from_']
	to_ = response.meta['to_']
	seg = '%s-%s'%(from_, to_)
	row_data_lst = []
	data_lst = sel.xpath('//script[@type="text/javascript"]//text()').extract()
	for i in data_lst:
	    data_ = re.findall("window.parent.postMessage\((.*), \'*\'", i)
	    try:
	        if len(data_) == 1: row_data_lst.append(json.loads(data_[0]))
	    except Exception as e: print e.message
	unorder_lst = []
	for dit in row_data_lst:
	    carrier_dict = {}
	    for c_di in dit.get('c', []):
		key = c_di.get('c', '')
		val = c_di.get('n', '')
		if key: carrier_dict.update({key:val})
	    flt_lst = dit.get('o', [])
	    for flt_ in flt_lst:
		sk = str(hashlib.md5('%s'%(str(flt_))).hexdigest())
		aux_info = {}
	        ids = flt_.get('id', '')
		flight_ids = ''.join(re.findall(':(.*)', ids))
	        price = flt_.get('p', '0')
		base_fare = flt_.get('b', '0')
                taxs = flt_.get('x', '0')
                aux_info.update({'base_fare':base_fare, 'tax':taxs})
		ar_date_time, de_date_time = ['']*2
	        for idx, flt in enumerate(flt_.get('f', [])):
		    ar_time = str(flt.get('a', ''))
		    de_time = str(flt.get('d', ''))
		    if len(ar_time) == 3:
		        ar_time = '0%s'%ar_time
		    elif len(ar_time) == 2:
			ar_time = '00%s'%ar_time
		    if len(de_time) == 3:
			de_time = '0%s'%de_time
		    elif len(de_time) == 2:
			de_time = '00%s'%de_time
		    de_time_ = re.findall('(.*)(\d{2}$)', de_time)
		    if de_time_ : de_time_ = ':'.join(de_time_[0])
		    ar_time_ = re.findall('(.*)(\d{2}$)', ar_time)
		    if ar_time_ : ar_time_ = ':'.join(ar_time_[0])
		    if idx == 0: de_date_time = de_time_ 
		    ar_date_time=ar_time_
		ar_date_time = '%s %s'%(date, ar_date_time)
		de_date_time = '%s %s'%(date, de_date_time)
		val = [sk, price, '',  de_date_time.strip(), ar_date_time.strip(), 'Domestic', seg, 'oneway', flight_ids, json.dumps(aux_info)]
                unorder_lst.append(val)
	price_order_lst = sorted(unorder_lst, key=itemgetter(1))
	f_list = self.get_sorted_values(price_order_lst)
	fin_dict = self.get_finalranking(f_list)
	for key, vals in fin_dict.iteritems():
	    self.out_put.write('%s\n'%'#<>#'.join(vals))

    def get_finalranking(self, sorted_x):
	fin_rank, dict_ = 1, {}
	for i in sorted_x:
            lsttt = sorted(i[1], key=lambda x: (x[3]))
            for k in lsttt:
		sk, fare, air_name, de_dat, ar_dat, seg_type, seg, trip_type, flts_ids, aux_ = k
                vals = (str(sk), str(fare), str(air_name), str(de_dat), \
			str(ar_dat), str(fin_rank), 'Domestic', str(seg), 'oneway', str(flts_ids), aux_)
		dict_.update({fin_rank:vals})
		fin_rank = fin_rank + 1
	return dict_

    def get_sorted_values(self, seg_price_order):
	rank, price_, lst_, lst, fin_dict = 0, 0, {}, {}, {}
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
	return sorted_x
