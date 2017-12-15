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
    name = "makemytrip_flight_round"
    start_urls = ["https://www.makemytrip.com/flights"]

    def __init__(self, *args, **kwargs):
        super(MakemyInternationalBrowse, self).__init__(*args, **kwargs)
        self.crawl_type = kwargs.get('crawl_type', '')
	self.trip_type = kwargs.get('trip_type', '')
	if self.trip_type == 'oneway':
	    self.source_name = 'makemytrippbs'
	elif self.trip_type == 'roundtrip':
	    self.source_name = 'makemytrippbsrt'
	else: return
	self.log = create_logger_obj(self.source_name)
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
	got_sk = ''
	if self.crawl_type == 'domestic':
	    date, date_, from_, to_ = '2018-01-15', '15/01/2018', 'BOM', 'CCU'
	    re_date = '25/01/2018'
	    seg, re_seg = 'BOM-CCU', 'CCU-BOM'
	    if self.trip_type == 'oneway':
		url = 'http://flights.makemytrip.com/makemytrip/search-api.json?classType=E&dcID=&deptDate=%s&deviceType=desktop&filterReq=&fromCity=%s&isDateChange=&lob=Flight&noOfAdlts=1&noOfChd=0&noOfInfnt=0&toCity=%s&tripType=O&tripTypeDup=O'%(date_, from_, to_)
	    else:
		url = 'http://flights.makemytrip.com/makemytrip/search-api.json?classType=E&dcID=&deptDate=%s&deviceType=desktop&filterReq=&fromCity=%s&isDateChange=&lob=Flight&noOfAdlts=1&noOfChd=0&noOfInfnt=0&returnDate=%s&toCity=%s&tripType=R&tripTypeDup=R'%(date_, from_, re_date, to_)
	else:
	    seg, date, got_sk, date_ = 'DXB-Bkk', '15Jan2018', '', ''
            re_seg, re_date = 'BKK-DXB', '25Jan2018'
	    if self.trip_type == 'oneway':
	        url = 'https://air.makemytrip.com/air/screen/ifsearch?tripType=O&itinerary=%s-D-%s&paxType=A-1&cabinClass=E'%(seg, date)
	    else:
	        url = 'https://air.makemytrip.com/air/screen/ifsearch?tripType=R&itinerary=%s-D-%s_%s-D-%s&paxType=A-1&cabinClass=E'%(seg, date, re_seg, re_date)
        yield Request(url, callback=self.parse_next, meta={'date': date_, 'got_sk':got_sk, 'seg':seg, 're_seg':re_seg})

    def parse_next(self, response):
	sel = Selector(response)
	got_sk = response.meta.get('got_sk', '')
	seg = response.meta.get('seg', '')
	re_seg = response.meta.get('re_seg', '')
	body = json.loads(response.body)
	if self.crawl_type == 'domestic':
	    self.get_domestic_flights(body, seg, re_seg)
	else:
	    flights = body.get('screenModel', {}).get('intl_flight_parent', {})\
		.get('data', {}).get('intl_flights_wraper', {}).get('data', {}).get('intl_flights', {}).get('data', {})
	    for rank, flt in enumerate(flights, 1):
	        aux_info, return_details = {}, {}
	        flt_data = flt.get('data', {}).get('flightdetails', {}).get('data', [])
	        price = flt.get('data', {}).get('ai', {}).get('data', {}).get('df', {})
	        flight_ids, airline_lst = [], []
	        arr_datetime, dep_datetime = ['']*2
	        sk_date = str(datetime.datetime.now())
	        sk = str(hashlib.md5('%s%s'%(str(flt), sk_date)).hexdigest())
	        if self.trip_type == 'oneway':
		    flight_ids, airline_lst, depature_time, arr_time = self.get_oneway_flt_details(flt_data)
	        else:
	            rt_flts = flt.get('data', {}).get('aDtlWoG', {}).get('data', [])
	            ow_flts = flt.get('data', {}).get('dDtlWoG', {}).get('data', [])
	            flight_ids, airline_lst, depature_time, arr_time = self.get_flight_details(ow_flts)
	            re_flight_ids, re_airline_lst, re_depature_time, re_arr_time = self.get_flight_details(rt_flts)
	            return_details.update({'flight_no':'<>'.join(re_flight_ids),
				'airline':'<>'.join(re_airline_lst),
				'depature':re_depature_time,
				'arrival':re_arr_time})
	            aux_info.update({'return_details':return_details})
	        vals = (str(sk), str(price), str('<>'.join(airline_lst)), str(depature_time), str(arr_time), \
		    str(rank), self.crawl_type.capitalize(), str(seg), self.trip_type.capitalize(),\
		    str('<>'.join(flight_ids)), json.dumps(aux_info))
	        self.out_put.write('%s\n'%'#<>#'.join(vals))

    def get_flight_details(self, flt_list):
	flight_ids, airline_lst = [], []
	arr_time, depature_time = '', ''
	for idx, dt in enumerate(flt_list):
	    air_code = dt.get('data', {}).get('tDtl', {}).get('data', {}).get('oACd', '')
	    flt_no = dt.get('data', {}).get('tDtl', {}).get('data', {}).get('fNum', '')
	    airline = dt.get('data', {}).get('tDtl', {}).get('data', {}).get('oANm', '')
	    arrival =  dt.get('data', {}).get('tDtl', {}).get('data', {}).get('alt', '').replace('T', ' ')
	    depature = dt.get('data', {}).get('tDtl', {}).get('data', {}).get('dlt', '').replace('T', ' ')
	    if idx == 0:
		depature_time = depature
	    arr_time = arrival
            flight_ids.append('%s-%s'%(air_code, flt_no))
	    airline_lst.append(airline)
	return (flight_ids, airline_lst, depature_time, arr_time)

    def get_oneway_flt_details(self, flt_data):
	flight_ids, airline_lst = [], []
        arr_datetime, dep_datetime = ['']*2
	for idx, f_ in enumerate(flt_data):
                flt_details = f_.get('data', {}).get('bgDtls', {})
                flt_id = f_.get('data', {}).get('alnDtls', {}).get('data', {}).get('flt_key', '')
                airline = f_.get('data', {}).get('tDtl', {}).get('data', {}).get('oANm', '').strip()
                dep_time = f_.get('data', {}).get('tDtl', {}).get('data', {}).get('dlt', '')
                if flt_id: flight_ids.append(flt_id)
                if idx == 0 : arr_datetime = dep_time.replace('T', ' ')
                dep_datetime = dep_time.replace('T', ' ')
                if airline: airline_lst.append(airline)
	return (flight_ids, airline_lst, arr_datetime, dep_datetime)

    def get_domestic_flights(self, body, seg, re_seg):
	if self.trip_type == 'oneway':
	    flights = body.get('flights', [])
	    self.get_domestic_details(flights, seg)
	else:
	    flights = body.get('fd', {})
	    ow_flight = flights.get('departureFlights', [])
	    rt_flight = flights.get('returnFlights', [])
	    self.get_domestic_details(ow_flight, seg)
	    self.get_domestic_details(rt_flight, re_seg)

    def get_domestic_details(self, flights, seg):
        airline_lst = []
        dep_time, ar_time = '', ''
        for idx, flt in enumerate(flights, 1):
            price = flt.get('af', 0)
            legs = flt.get('le', [])
            flight_ids_lst = []
            sk_date = str(datetime.datetime.now())
            sk = sk = str(hashlib.md5('%s%s'%(str(flt), sk_date)).hexdigest())
            base_fare, taxs, aux_info = [], [], {}
	    depature_time , arrival_time = '', ''
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
                base_fare.append(str(fr_dict.get('bf', 0)))
                taxs.append(str(fr_dict.get('fs', 0)))
                depart_time = i.get('fmtDepartureTime', '')
                arrival_time = i.get('fmtArrivalTime', '')
		dep_ = i.get('dep', '').replace('T', ' ').replace('Z', '')
                if f_dx == 0:
		    depature_time = dep_
                #ar_time = arrival_time
                origin = i.get('o', '')
                desct = i.get('d', '')
                flight_ids_lst.extend(flt_lst)
	    aux_info.update({'base_fare':'<>'.join(base_fare), 'tax':'<>'.join(taxs)})
            vals = (str(sk), str(price), str(airline), str(depature_time), '', str(idx), self.crawl_type.capitalize(),
			 str(seg), self.trip_type.capitalize(), str('<>'.join(flight_ids_lst)), json.dumps(aux_info))
            self.out_put.write('%s\n'%'#<>#'.join(vals))
