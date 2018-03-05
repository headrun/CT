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
from CTPCC.utils import *
from scrapy import log
from scrapy import signals
from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher
from scrapy_splash import SplashRequest, SplashFormRequest

class RehlatBrowse(Spider):
    name = "rehlat_browse"
    start_urls = ['https://www.rehlat.com/']

    def __init__(self, *args, **kwargs):
        super(RehlatBrowse, self).__init__(*args, **kwargs)
	self.source_name = 'rehlat'
        self.log = create_logger_obj(self.source_name)
        self.crawl_type = kwargs.get('crawl_type', '')
	self.trip_type = kwargs.get('trip_type', '')
        self.limit = kwargs.get('limit', '')
        self.out_put, self.out_put_file = get_output_file(self.source_name)
        self.cr_tabe = create_crawl_table_cursor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)
	self.pattern = re.compile(r'var staticData = (.*)')

    def spider_closed(self, spider):
	self.out_put.close()
	self.cr_tabe.close()
	move_crawlout_processing(self.out_put_file)

    def flight_details(sel, flgt_deatils):
	inbound_details, outbound_details = {}, {}
	key = ''.join(flgt_deatils.keys())
	details = flgt_deatils.get(key, {})
	no_of_stops = str(len(details) -1)
	if len(details) > 1:
	    flt_no, city_seg = [], []
	    for indx, list_ in enumerate(details):
		if indx == 0:
		    names = [i.get('AirlineName', '') for i in details]
		    name = '<>'.join(names).strip('<>').strip()
		    departure_date = list_.get('DepartureDate', '').strip()
		    start_time = list_.get('StartTm', '').strip()
		    code = [i.get('AirV', '').strip() for i in details]
		    flt_nu = [i.get('FltNum', '').strip() for i in details]
		    arrival_date = details[-1].get('ArrivalDate', '').strip()
		    end_time = details[-1].get('EndTm', '').strip()
		    start_city = [i.get('StartAirp', '').strip() for i in details]
		    end_city = [i.get('EndAirp', '').strip() for i in details]
		    for i in zip(start_city, end_city):
		        city = '-'.join(i)
		        city_seg.append(city)
		        seg = '<>'.join(city_seg).strip()
		    for i in zip(code, flt_nu):
		        flgt_num = '-'.join(i)
		        flt_no.append(flgt_num)
		        flight_number = '<>'.join(flt_no).strip()
	else:
	    for i in details:
		name = i.get('AirlineName', '').strip()
		airline_code = i.get('AirV', '').strip()
		flt_number = i.get('FltNum', '').strip()
	    	flight_number = airline_code + '-' + flt_number
	    	start_trip = i.get('StartAirp', '').strip()
	    	departure_date = i.get('DepartureDate', '').strip()
	    	start_time = i.get('StartTm', '').strip()
	    	arrival_date = i.get('ArrivalDate', '').strip()
	    	end_time = i.get('EndTm', '').strip()
	    	start_city = i.get('StartAirp', '').strip()
	   	end_city = i.get('EndAirp', '').strip()
	    	seg = start_city + '-' + end_city
	de_time = departure_date+', '+ start_time
	ar_time = arrival_date+', '+end_time
	year = str(datetime.date.today().year)
	de_date = year+'-'+str(datetime.datetime.strptime(de_time, '%a %d %b, %H%M').strftime('%m-%d %H:%M'))
	ar_date = year+'-'+str(datetime.datetime.strptime(ar_time, '%a %d %b, %H%M').strftime('%m-%d %H:%M'))
	if key == 'inbound':
	    inbound_details.update({key+'_'+'name':name, key+'_'+'flight_number':flight_number, key+'_'+'de_date':de_date, key+'_'+'ar_date':ar_date, key+'_'+'seg':seg, key+'_'+'no_of_stops':no_of_stops})
	    return inbound_details
        else:
	    outbound_details.update({key+'_'+'name':name, key+'_'+'flight_number':flight_number, key+'_'+'de_date':de_date, key+'_'+'ar_date':ar_date, key+'_'+'seg':seg, key+'_'+'no_of_stops':no_of_stops})
	    return outbound_details

    def city_details(self, code):
        data = [
                ('term', code),
                ('url', 'https://www.rehlat.com/'),
                ]
        response = requests.post('https://www.rehlat.com/Home/LodeFlyingFrom', data=data).text
        json_data = json.loads(response)
        for i in json_data:
            airport_code = i.get('AirportCode', '')
            if code == airport_code:
                city_name = i.get('CityName', '')
                return city_name
        if not json_data:
            return ''

    def start_requests(self):
	requests = terminal_requests(self.cr_tabe, self.source_name, self.crawl_type, self.trip_type, self.limit)
	for input_ in requests:
            got_sk, from_, to_, de_date, dx, re_date = input_
            from_ = from_.strip()
            to_ = to_.strip()
            from_cityname = self.city_details(from_)
	    to_cityname = self.city_details(to_)
	    re_date_ = ''
	    de_date = str(de_date.date())
	    de_date_ = datetime.datetime.strptime(de_date, '%Y-%m-%d').strftime('%d %b %Y')
	    if re_date:
	    	re_date = str(re_date.date())
	    	re_date_ = datetime.datetime.strptime(re_date, '%Y-%m-%d').strftime('%d %b %Y')
	    if self.trip_type == 'roundtrip':
		trip_type = 'RoundTrip'
	    else:
		trip_type = 'OneWay'
	    data = [
		 ('TripType', trip_type),
		 ('TripType', 'RoundTrip'),
		 ('Segments[0].From', str(from_)),
		 ('Segments[0].To', str(to_)),
		 ('Segments[0].DeDate', de_date_), 
		 ('Segments[0].ReDate', re_date_),
		 ('Adults', '1'),
		 ('Children', '0'),
		 ('Infant', '0'),
		 ('Class', 'Y'),
		 ('IsModefiedSearch', 'true'),
		 ('UrlReferrer', ''),
		]
	    url = 'https://www.rehlat.com/en/cheap-flights/search/%s-to-%s/%s-%s/%s/' % (str(from_cityname.lower()), str(to_cityname.lower()), str(from_.lower()), str(to_.lower()), str(self.trip_type))
	    yield SplashFormRequest(url, self.parse, formdata=data, args={'timeout':180}, meta={'d_date':de_date_, 're_date':re_date_, 'from_':from_, 'to_':to_, 'dx':dx})
   
 
    def parse(self, response):
	sel = Selector(response)
	de_date = response.meta.get('d_date', '')
	re_date = response.meta.get('re_date', '')
	from_locaton = response.meta['from_']
	to_location = response.meta['to_']
	dx = response.meta.get('dx', '')
	temp = "".join(self.pattern.findall(response.body))
        data = json.loads(temp.strip(";"))
        keys = data.get('ListOfFlightVms', [{}])
	inbound_details, inbound_name_, inbound_de_date_, \
	inbound_ar_date_, inbound_seg_, inbound_flight_number_, \
	inbound_no_of_stops_ = '', '', '', '', '', '', ''
        for key in keys:
            for i in key:
		    in_dict, out_dict = {}, {}
                    price = i.get("TotalPriceInfo", {}).get('DisPlayTotalAmountwithMarkUp', '')
		    adult = i.get("TotalPriceInfo", {}).get('DisPlayAllAdultPriceWithMarkUp', '')
                    taxes =  i.get("TotalPriceInfo", {}).get('DisPlayEffectiveTax', '')
		    in_details = i.get('InBoundFlightDetails', {})
                    out_details = i.get('OutBoundFlightDetails', {})
		    sk = str(hashlib.md5('%s'%(str(i))).hexdigest())
		    rank = 0
		    no_pax = 1
		    if in_details:
			in_dict.update({'inbound':in_details})
			inbound_details = self.flight_details(in_dict)
			inbound_name_ = inbound_details.get('inbound_name', '').strip()
			inbound_de_date_ = inbound_details.get('inbound_de_date', '').strip()
			inbound_ar_date_ = inbound_details.get('inbound_ar_date', '').strip()
			inbound_seg_ = inbound_details.get('inbound_seg', '').strip()
			inbound_flight_number_ = inbound_details.get('inbound_flight_number', '').strip()
			inbound_no_of_stops_ = inbound_details.get('inbound_no_of_stops', '').strip()
		    if out_details:
			out_dict.update({'outbound':out_details})
			outbound_details = self.flight_details(out_dict)
			outbound_name_ = outbound_details.get('outbound_name', '').strip()
                        outbound_de_date_ = outbound_details.get('outbound_de_date', '').strip()
                        outbound_ar_date_ = outbound_details.get('outbound_ar_date', '').strip()
                        outbound_seg_ = outbound_details.get('outbound_seg', '').strip()
                        outbound_flight_number_ = outbound_details.get('outbound_flight_number', '').strip()
                        outbound_no_of_stops_ = outbound_details.get('outbound_no_of_stops', '').strip()
		    vals = (str(sk), str(price), str(outbound_name_), str(outbound_de_date_), str(outbound_ar_date_), str(rank), self.crawl_type.title(), str(outbound_seg_), self.trip_type.title(), str(outbound_flight_number_), str(no_pax), str(outbound_no_of_stops_), str(inbound_name_), str(inbound_de_date_), str(inbound_ar_date_), str(inbound_seg_), str(inbound_flight_number_), str(inbound_no_of_stops_), str(dx))
		    self.out_put.write('%s\n'%'#<>#'.join(vals))
