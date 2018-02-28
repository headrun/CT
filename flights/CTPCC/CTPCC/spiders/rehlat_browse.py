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

    def spider_closed(self, spider):
	self.out_put.close()
	self.cr_tabe.close()
	move_crawlout_processing(self.out_put_file)

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
            got_sk, from_, to_, date, dx, re_date = input_
            from_ = from_.strip()
            to_ = to_.strip()
            from_cityname = self.city_details(from_)
	    to_cityname = self.city_details(to_)
	    date = str(date.date())
	    date_ = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%d %b %Y')
	    data = [
		 ('TripType', 'OneWay'),
		 ('TripType', 'RoundTrip'),
		 ('Segments[0].From', '%s' % from_),
		 ('Segments[0].To', '%s' % to_),
		 ('Segments[0].DeDate', '%s' % date_), 
		 ('Segments[0].ReDate', ''),
		 ('Adults', '1'),
		 ('Children', '0'),
		 ('Infant', '0'),
		 ('Class', 'Y'),
		 ('IsModefiedSearch', 'true'),
		 ('UrlReferrer', 'google'),
		]
	    url = 'https://www.rehlat.com/en/cheap-flights/search/%s-to-%s/%s-%s/oneway/' % (from_cityname, to_cityname, from_.lower(), to_.lower())	
	    yield SplashFormRequest(url, self.parse, formdata=data, args = {'wait': 5}, meta={'d_date':date, 'from_':from_, 'to_':to_, 'dx':dx})
    
    def parse(self, response):
	sel = Selector(response)
	date = response.meta.get('d_date', '')
	from_locaton = response.meta['from_']
	to_location = response.meta['to_']
	dx = response.meta.get('dx', '')
	temp = "".join(re.findall("var staticData = (.*)", response.body))
        data = json.loads(temp.strip(";"))
        keys = data.get('ListOfFlightVms', [{}])
        for key in keys:
            for i in key:
                    price = i.get("TotalPriceInfo", {}).get('DisPlayTotalAmountwithMarkUp', '')
		    adult = i.get("TotalPriceInfo", {}).get('DisPlayAllAdultPriceWithMarkUp', '')
                    taxes =  i.get("TotalPriceInfo", {}).get('DisPlayEffectiveTax', '')
                    details = i.get('OutBoundFlightDetails', {})
		    sk = str(hashlib.md5('%s'%(str(details))).hexdigest())
		    no_of_stops = str(len(details) -1)
		    rank = 0
		    no_pax = 1
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
				    flgt_num = ' - '.join(i)
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
		    vals = (str(sk), str(price), str(name), str(de_date), str(ar_date), str(rank), self.crawl_type.title(), str(seg), 'OneWay', str(flight_number), str(no_pax), str(no_of_stops), str(dx))
		    self.out_put.write('%s\n'%'#<>#'.join(vals))
