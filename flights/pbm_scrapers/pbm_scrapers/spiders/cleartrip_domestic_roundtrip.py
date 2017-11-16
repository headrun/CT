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

class CleartripDomesticRtBrowse(Spider):
    name = "cleartrip_domestic_roundtrip"
    start_urls = ["https://www.cleartrip.com/flights/"]

    def __init__(self, *args, **kwargs):
        super(CleartripDomesticRtBrowse, self).__init__(*args, **kwargs)
	self.source_name = 'cleartriprt'
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
	    #url = 'https://api.cleartrip.com/air/1.0/search?from=BOM&to=DEL&depart-date=2017-12-15&adults=1&country=IN&currency=INR&jsonVersion=1.0'
	    url = 'https://api.cleartrip.com/air/1.0/search?from=%s&to=%s&depart-date=%s&adults=1&country=IN&currency=INR&jsonVersion=1.0'%(from_, to_, date)
	    headers = {
		'X-CT-API-KEY' : 'bce875d513bab5fa2cba6371f7b1ea58',
		'X-CT-SOURCETYPE' : 'B2C'
		}
	    yield Request(url, callback=self.parse_next, headers=headers, meta={'d_date':date, 'from_':from_, 'to_':to_})
	'''
	from_, to_, date, re_date = 'BOM', 'CCU', '2017-12-15', '2017-12-25'
	#url = 'https://api.cleartrip.com/air/1.0/search?from=%s&to=%s&depart-date=%s&adults=1&country=IN&currency=INR&jsonVersion=1.0'%(from_, to_, date)
	url = 'https://api.cleartrip.com/air/1.0/search?from=%s&to=%s&depart-date=%s&return-date=%s&adults=1&country=IN&currency=INR&jsonVersion=1.0'%(from_, to_, date, re_date)
        headers = {
                'X-CT-API-KEY' : 'bce875d513bab5fa2cba6371f7b1ea58',
                'X-CT-SOURCETYPE' : 'B2C'
                }
        yield Request(url, callback=self.parse_next, headers=headers, meta={'d_date':date, 'from_':from_, 'to_':to_})

    def parse_next(self, response):
	sel = Selector(response)
	date = response.meta.get('d_date', '')
	from_ = response.meta['from_']
	to_ = response.meta['to_']
	seg = '%s-%s'%(from_, to_)
	body = json.loads(response.body)
	content = body.get('content', {})
	mapping = body.get('mapping', {})
	fares = body.get('fare', {})
	oneway_mapping = mapping.get('onward', [])
	return_mapping = mapping.get('return', [])
	seg_price_order = self.get_price_order_dict(oneway_mapping, content, fares, date, seg)
	return_price_order = self.get_price_order_dict(return_mapping, content, fares, date, seg)
	import pdb;pdb.set_trace()
	ow_sorted = self.get_sorted_values(seg_price_order)
	rt_sorted = self.get_sorted_values(return_price_order)
	ow_fin_dict = self.get_finalranking(ow_sorted)
	rt_fin_dict = self.get_finalranking(rt_sorted)
	import pdb;pdb.set_trace()

    def get_finalranking(self, sorted_x):
	fin_rank, dict_ = 1, {}
	for i in sorted_x:
            lsttt = sorted(i[1], key=lambda x: (x[4]))
            for k in lsttt:
                sk, fare, air_name, de_dat, ar_dat, rank, seg, flts_, sk = k
                vals = (str(sk), str(fare), str(air_name), str(de_dat), str(ar_dat), str(fin_rank), 'Domestic', str(seg), 'oneway', str(flts_))
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

    def get_price_order_dict(self, oneway_mapping, content, fares, date, seg):
	segments_lst, seg_price_order = [], []
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
	    if len(cont_code_lst) > 1: continue
            for seg_idx, i in enumerate(cont_code_lst):
                i = content.get(i, {})
                flt_dict = {}
                ar_date = i.get('ad', '') 
                ar_time = i.get('a', '') 
                ar_seg_time = ar_time
                ar_ori = i.get('fr', '')
                ar_dest = i.get('to', '')
                flt_key = i.get('fk', '')
                flight_no = ''.join(re.findall('_(\w{2}-\d+)_', flt_key))
                airline = ''.join(re.findall('(.*)_\w{2}-\d+_', flt_key)).replace('_', ' ')
                de_seg_t = ''.join(re.findall('_(\d+:\d+)_', flt_key))
                if seg_idx == 0: de_seg_time = de_seg_t
                air_name.append(airline)
                flts_lst.append(flight_no)
            ar_dat = '%s %s'%(date, ar_seg_time)
            de_dat = '%s %s'%(date, de_seg_time)
            seg_price_order.append([sk, fare_, '<>'.join(air_name), de_dat, ar_dat, '0', seg, '<>'.join(flts_lst), sk])
	return seg_price_order
