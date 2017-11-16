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

class YatraDomesticRtBrowse(Spider):
    name = "yatra_domestic_browse"
    start_urls = ["https://www.yatra.com/"]

    def __init__(self, *args, **kwargs):
        super(YatraDomesticRtBrowse, self).__init__(*args, **kwargs)
	self.source_name = 'yatra'
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
	from_, to_, date, re_date = 'BOM', 'CCU', '15/12/2017', '2017-12-25'
	url = 'https://flight.yatra.com/air-search-ui/dom2/trigger?ADT=1&CHD=0&INF=0&class=Economy&destination=%s&flexi=0&flight_depart_date=%s&noOfSegments=1&origin=%s&source=fresco-home&type=O'%(to_, date, from_)
	date = '2017-12-15'
        yield Request(url, callback=self.parse_next, meta={'d_date':date, 'from_':from_, 'to_':to_})

    def parse_next(self, response):
	sel = Selector(response)
	date = response.meta.get('d_date', '')
	from_ = response.meta['from_']
	to_ = response.meta['to_']
	seg = '%s-%s'%(from_, to_)
	data = sel.xpath('//script[@type="text/javascript"]//text()[contains(., "resultData")]').extract()
	body = json.loads(''.join(re.findall('=(.*resultData.*)=?', ''.join(data))).strip('\r;'))
	resultdata = body.get('resultData', [])
	flt_lst_key = '%s%s%s'%(from_, to_, date.replace('-', ''))
	unorder_lst = []
	for res in resultdata:
	    schedule_lst = res.get('fltSchedule', {}).get(flt_lst_key, [])
	    airlinenames = res.get('fltSchedule', {}).get('airlineNames', {})
	    fare_dict = {}
	    fare_details = res.get('fareDetails', {}).get(flt_lst_key, {})
	    fr_keys = fare_details.keys()
	    sk = str(hashlib.md5('%s'%(str())).hexdigest())
	    for fr in fr_keys:
		fr_ = fare_details.get(fr, {}).get('O', {}).get('ADT', {}).get('tf', '')
		fare_dict.update({fr:fr_})
	    for ele in schedule_lst:
		sk = str(hashlib.md5('%s'%(str(ele))).hexdigest())
		id_ = ele.get('ID', '')
		flt_od_ = ele.get('OD', [{}])[0].get('FS', [{}])
		de_dat, ar_dat = ['']*2
		flt_ids, airline_lst = [], []
		for idx, flt_od in enumerate(flt_od_):
		    air_code = flt_od.get('ac', '')
		    flt_id = flt_od.get('fl', '')
		    ddt = flt_od.get('ddt', '')
		    adt = flt_od.get('adt', '')
		    dd = flt_od.get('dd', '')
		    ad = flt_od.get('ad', '')
		    airline = airlinenames.get(air_code, '')
		    airline_lst.append(airline)
		    if idx == 0:
		        de_dat = '%s %s'%(ddt, dd)
                    ar_dat = '%s %s'%(adt, ad)
                    flt_id = '%s-%s'%(air_code, flt_id)
		    flt_ids.append(flt_id)
		try: fare_val = float(fare_dict.get(id_, ''))
		except: fare_val = ''
		val = [sk, fare_val, '<>'.join(airline_lst), de_dat, ar_dat, 'Domestic', seg, 'oneway', '<>'.join(flt_ids)]
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
		sk, fare, air_name, de_dat, ar_dat, seg_type, seg, trip_type, flts_ids = k
                vals = (str(sk), str(fare), str(air_name), str(de_dat), \
			str(ar_dat), str(fin_rank), 'Domestic', str(seg), 'oneway', str(flts_ids))
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
