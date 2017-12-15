import csv
import datetime
import hashlib
import json
import logging
import md5
import operator
import os
import re
import requests
import sys

from scrapy.xlib.pydispatch import dispatcher
from operator import itemgetter
from scrapy.http import FormRequest
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy import signals
from scrapy.spider import Spider
from scrapy import log

import MySQLdb

from pbm_scrapers.utils import *


class YatraRoundTripBrowse(Spider):
    name = "yatra_roundtrip_browse"
    start_urls = ["https://www.yatra.com/"]

    def __init__(self, *args, **kwargs):
        super(YatraRoundTripBrowse, self).__init__(*args, **kwargs)
	self.source_name = 'yatrapbsrt'
        self.log = create_logger_obj(self.source_name)
        self.crawl_type = kwargs.get('crawl_type', '')
	self.trip_type = kwargs.get('trip_type', '')
        self.limit = kwargs.get('limit', '')
        self.out_put, self.out_put_file = get_output_file(self.source_name)
        self.cr_tabe = create_crawl_table_cursor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
	stats = self.crawler.stats.get_stats()
	get_crawler_stats(self.cr_tabe, stats, self.name)
	import pdb;pdb.set_trace()
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
	if self.crawl_type == 'international':
	    from_, to_, date, re_date = 'DXB', 'BKK', '15/01/2018', '25/01/2018'
	    #url = 'https://flight.yatra.com/air-search-ui/int2/trigger?ADT=1&CHD=0&INF=0&class=Economy&destination=%s&flexi=0&flight_depart_date=%s&noOfSegments=1&origin=%s&source=fresco-home&type=O'%(to_, date, from_)
	    url = 'https://flight.yatra.com/air-search-ui/int2/trigger?ADT=1&CHD=0&INF=0&arrivalDate=%s&class=Economy&destination=%s&flexi=0&flight_depart_date=%s&noOfSegments=2&origin=%s&source=fresco-home&type=R&viewName=normal'%(re_date, to_, date, from_)
	    date, re_date = '2018-01-15', '2018-01-25'
	else:
	    from_, to_, date, re_date = 'BOM', 'CCU', '15/01/2018', '25/01/2018'
	    url = 'https://flight.yatra.com/air-search-ui/dom2/trigger?ADT=1&CHD=0&INF=0&arrivalDate=%s&class=Economy&destination=%s&flexi=0&flight_depart_date=%s&noOfSegments=2&origin=%s&source=fresco-home&type=R&viewName=normal'%(re_date, to_, date, from_)
	    date, re_date = '2018-01-15', '2018-01-25'
        yield Request(url, callback=self.parse_next, meta={'d_date':date, 'from_':from_, 'to_':to_, 're_date':re_date})

    def parse_next(self, response):
	sel = Selector(response)
	date = response.meta.get('d_date', '')
	re_date = response.meta.get('re_date', '')
	from_ = response.meta['from_']
	to_ = response.meta['to_']
	seg = '%s-%s'%(from_, to_)
	re_seg = '%s-%s'%(to_, from_)
	data = sel.xpath('//script[@type="text/javascript"]//text()[contains(., "resultData")]').extract()
	body = json.loads(''.join(re.findall('=(.*resultData.*)=?', ''.join(data))).strip('\r;'))
	resultdata = body.get('resultData', [])
	flt_lst_key = '%s%s%s'%(from_, to_, date.replace('-', ''))
	re_flt_lst_key = '%s%s%s'%(to_, from_, re_date.replace('-', ''))
	unorder_lst = self.get_flight_details(flt_lst_key, resultdata, seg)
	if self.crawl_type == 'domestic':
	    re_unorder_lst = self.get_flight_details(re_flt_lst_key, resultdata, re_seg)
	else: re_unorder_lst = []
	self.write_datainto_file(unorder_lst)
	self.write_datainto_file(re_unorder_lst)


    def get_flight_details(self, flt_lst_key, resultdata, seg):
	unorder_lst = []
	for res in resultdata:
	    schedule_lst = res.get('fltSchedule', {}).get(flt_lst_key, {})
	    airlinenames = res.get('fltSchedule', {}).get('airlineNames', {})
	    fare_dict = {}
	    fare_details = res.get('fareDetails', {}).get(flt_lst_key, {})
	    fr_keys = fare_details.keys()
	    sk = str(hashlib.md5('%s'%(str())).hexdigest())
	    for fr in fr_keys:
		fr_ = fare_details.get(fr, {}).get('O', {}).get('ADT', {}).get('tf', '')
		fare_dict.update({fr:[fr_, fare_details.get(fr, {}).get('O', {})]})
	    if isinstance(schedule_lst, dict):
	        for key, ele in schedule_lst.iteritems():
		    return_details = {}
		    sk_date = str(datetime.datetime.now())
		    sk = str(hashlib.md5('%s%s'%(str(ele), sk_date)).hexdigest())
		    id_ = ele.get('ID', '')
		    flt_od_ = ele.get('OD', [{}])[0].get('FS', [{}])
		    try: re_flt_od_ = ele.get('OD', [{}, {}])[1].get('FS', [{}])
		    except: re_flt_od_ = []
		    fare_val, airline_names, depart_date, arrival_date, \
			flight_ids, aux_info = self.get_flt_details(flt_od_, fare_dict, airlinenames, id_)
		    if re_flt_od_:
		        re_fare_val, re_airline_names, re_depart_date, re_arrival_date, \
                        	re_flight_ids, re_aux_info = self.get_flt_details(re_flt_od_, fare_dict, airlinenames, id_)
		        return_details.update({'arrival':re_arrival_date, 'flight_no':re_flight_ids,
				'airline':re_airline_names, 'depature':re_depart_date})
		    aux_info.update({'return_details':return_details})
		    val = [sk, fare_val, airline_names, depart_date, arrival_date,
			self.crawl_type.capitalize(), seg, self.trip_type.capitalize(),
			flight_ids, json.dumps(aux_info)]
                    unorder_lst.append(val)
	    else:
		for ele in schedule_lst:
                    return_details = {}
                    sk_date = str(datetime.datetime.now())
                    sk = str(hashlib.md5('%s%s'%(str(ele), sk_date)).hexdigest())
                    id_ = ele.get('ID', '')
                    flt_od_ = ele.get('OD', [{}])[0].get('FS', [{}])
                    try: re_flt_od_ = ele.get('OD', [{}, {}])[1].get('FS', [{}])
                    except: re_flt_od_ = []
                    fare_val, airline_names, depart_date, arrival_date, \
                        flight_ids, aux_info = self.get_flt_details(flt_od_, fare_dict, airlinenames, id_)
                    if re_flt_od_:
                        re_fare_val, re_airline_names, re_depart_date, re_arrival_date, \
                                re_flight_ids, re_aux_info = self.get_flt_details(re_flt_od_, fare_dict, airlinenames, id_)
                        return_details.update({'arrival':re_arrival_date, 'flight_no':re_flight_ids,
                                'airline':re_airline_names, 'depature':re_depart_date})
                    aux_info.update({'return_details':return_details})
                    val = [sk, fare_val, airline_names, depart_date, arrival_date,
                        self.crawl_type.capitalize(), seg, self.trip_type.capitalize(),
                        flight_ids, json.dumps(aux_info)]
                    unorder_lst.append(val)
	return unorder_lst

    def get_flt_details(self, flt_od_, fare_dict, airlinenames, id_):
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
	aux_info = {}
	try: fare_val, fare_dict_ = fare_dict.get(id_, '')
	except:
		fare_val, fare_dict_ = 0, {}
	base_fare = str(fare_dict_.get('ADT', {}).get('bf', ''))
	pax_service_fare = str(fare_dict_.get('ADT', {}).get('PSF', ''))
	udf = str(fare_dict_.get('ADT', {}).get('UDF', ''))
	yt_cute = str(fare_dict_.get('ADT', {}).get('YQ', ''))
	aux_info.update({'base_fare':base_fare, 'tax':'PSF:%s, UDF:%s, YQ:%s'%(pax_service_fare, udf, yt_cute)})
	return (float(fare_val), '<>'.join(airline_lst), de_dat, ar_dat, '<>'.join(flt_ids), aux_info)

    def write_datainto_file(self, unorder_lst):
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
			str(ar_dat), str(fin_rank), seg_type, str(seg), trip_type, str(flts_ids), aux_)
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
