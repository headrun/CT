from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy import signals
from scrapy.spider import Spider

from ast import literal_eval
import datetime
import hashlib
import json
import logging
import os
import re

import md5
import MySQLdb

from utils import *

class SkyBrowse(Spider):
    name = "skyscannerall_browse"
    start_urls = []

    def __init__(self, *args, **kwargs):
        super(SkyBrowse, self).__init__(*args, **kwargs)
	self.domain = kwargs.get('domain', '')
	self.source_name = 'skyscanner%s'%self.domain
	st_url_dict = {
			'sg':'https://www.skyscanner.com.sg',
			'au': 'https://www.skyscanner.com.au',
			'us': 'https://www.skyscanner.com',
			'uk': 'https://www.skyscanner.net',
			}
	self.log = create_logger_obj(self.source_name)
        self.crawl_type = kwargs.get('crawl_type', '')
        self.trip_type = kwargs.get('trip_type', '')
        self.limit = kwargs.get('limit', '')
	self.start_urls.append(st_url_dict.get(self.domain, ''))
        self.out_put, self.out_put_file = get_output_file(self.source_name)
        self.cr_tabe = create_crawl_table_cursor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.out_put.close()
        self.cr_tabe.close()
        move_crawlout_processing(self.out_put_file)

    def parse(self, response):
        sel = Selector(response)
	res_headers = json.dumps(str(response.headers))
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
        cookies = {}
        for i in my_dict.get('Set-Cookie', []):
            data = i.split(';')[0]
            if data:
                try : key, val = data.split('=', 1)
                except : continue
                cookies.update({key.strip():val.strip()})
	data_inputs = {
			'sg':[
				'https://www.skyscanner.com.sg',
				'www.skyscanner.com.sg',
				'SG',
				'SGD'
				],
			'us':[
				'https://www.skyscanner.com',
				'www.skyscanner.com',
				'US',
				'USD'
				],
			'au':[
				'https://www.skyscanner.com.au',
				'www.skyscanner.com.au',
				'AU',
				'AUD'
				],
			'uk':[
				'https://www.skyscanner.net',
				'www.skyscanner.net',
				'UK',
				'GBP'
				]
			}
	origin_url, authority_url, market, currency = data_inputs.get(self.domain, '')
	requests = terminal_requests(self.cr_tabe, self.source_name, \
			self.crawl_type, self.trip_type, self.limit)
	for input_ in requests:
            got_sk, from_, to_, date, dx, re_date = input_
	    refer_date = str(date.strftime("%y%m%d"))
            date = str(date.date())
	    from_ = from_.strip()
	    to_ = to_.strip()
	    referer_url = '%s/transport/flights/%s/%s/%s'\
			%(origin_url, from_.lower(), to_.lower(), refer_date)
	    headers = {
			'x-skyscanner-devicedetection-istablet': 'false',
                        'origin': origin_url,
                        'accept-encoding': 'gzip, deflate, br',
                    	'accept-language': 'en-US,en;q=0.8',
                    	'x-requested-with': 'XMLHttpRequest',
                    	'pragma': 'no-cache',
                    	'x-skyscanner-channelid': 'website',
                    	'x-skyscanner-devicedetection-ismobile': 'false',
                    	'content-type': 'application/json; charset=UTF-8',
                    	'accept': 'application/json, text/javascript, */*; q=0.01',
                    	'cache-control': 'no-cache',
                    	'authority': authority_url,
                    	'referer': referer_url,

		}
	
	    data = {
			"market":market,
			"currency":currency,
			"locale":"en-GB",
			"cabin_class":"economy",
			"prefer_directs":'false',
			"trip_type":"one-way",
			"legs":[
					{
					"origin":from_,
					"destination":to_,
					"date":date
					}
				],
			"adults":1,
			"child_ages":[],
			"options":{
				"include_unpriced_itineraries":'true',
				"include_mixed_booking_options":'true'
				}
		}
	    print from_, to_, date
	    url = origin_url + '/dataservices/flights/pricing/v3.0/search/?geo_schema=skyscanner&\
			carrier_schema=skyscanner&response_include=query%3Bdeeplink%\
				3Bsegment%3Bstats%3Bfqs%3Bpqs%3B_flights_availability'
	    yield Request(url, callback=self.parse_next, headers=headers,
				cookies=cookies, body=json.dumps(data), method="POST",
				meta={'dx':dx, 'got_sk':got_sk})

    def parse_next(self, response):
	try: data = json.loads(response.body)
	except: data = {}
	if data:
	    places_dict, carriers_dict, prices_dict, \
			agents_dict, segments_dict = {}, {}, {}, {}, {}
	    flights_lst = data.get('legs', [])
	    segments = data.get('segments', [])
	    prices_lst = data.get('itineraries', [])
	    places = data.get('places', [])
	    carriers = data.get('carriers', [])
	    agents = data.get('agents', [])
	    for ci in carriers:
    		ids = ci.get('id', '')
    		if ids: carriers_dict.update({ids:ci})
	    for pri in prices_lst:
    		ids = pri.get('id', '')
    		pricing_options = pri.get('pricing_options', [])
    		if ids: prices_dict.update({ids:pricing_options})
	    for pl in places:
    		ids = pl.get('id', '')
    		if ids: places_dict.update({ids:pl})
	    for ag in agents:
		ids = ag.get('id', '')
		if ids: agents_dict.update({ids:ag})
	    for sg in segments:
		ids = sg.get('id', '')
		if ids: segments_dict.update({ids:sg})
	    for flg in flights_lst:
		providers_dict, aux_info = {}, {}
		provider_lst = prices_dict.get(flg.get('id', ''), '')
		aux_info.update({'stop_count': str(flg.get('stop_count', ''))})
		cu = flg.get('stop_count', 0)
		seg_ids = flg.get('segment_ids', [])
		flight_id_lst, airline_lst = [], []
		origin, desct = ['']*2
		departure_, arrival_  = ['']*2
		for idx, id_ in enumerate(seg_ids):
		    segments_data = segments_dict.get(id_, {})
		    flight_id = segments_data.get('marketing_flight_number', '')
		    flight_id_ = segments_data.get('operating_flight_number', '')
		    arrival = segments_data.get('arrival', '').split('T')[0]
		    departure = segments_data.get('departure', '').split('T')[0]
		    origin_ = places_dict.get(segments_data.get('origin_place_id', ''), {})\
				.get('display_code', '')
		    desct_ = places_dict.get(segments_data.get('destination_place_id', ''), {})\
				.get('display_code', '')
		    airline_ = carriers_dict.get(segments_data.get('marketing_carrier_id', ''), {})\
				.get('name', '')
		    air_code = carriers_dict.get(segments_data.get('marketing_carrier_id', ''), {})\
				.get('display_code', '')
		    flight_id = '%s-%s'%(air_code, flight_id)
		    operating_airline = carriers_dict.get(segments_data.\
				get('operating_carrier_id', ''), '').get('name','')
		    aux_info.update({'operating_airline':operating_airline})
		    rank, is_avail = 0, 0
		    for prv in provider_lst:
			item = prv.get('items', [])
			if item:
			    item = item[0]
			    agent = agents_dict.get(item.get('agent_id', ''), {}).get('name', '')
			    price = item.get('price', {}).get('amount', '')
			    if agent:
			       rank = rank + 1
			       if 'cleartrip' in agent.lower():is_avail = 1
			       providers_dict.update({agent:{'rank':rank, 'price':str(price)}})
		    if idx == 0:
			origin = origin_
			departure_ = departure
		    desct = desct_
		    arrival_ = arrival
		    flight_id_lst.append(flight_id)
		    airline_lst.append(airline_)
		    sk_date = str(datetime.datetime.now())
		    sk = str(hashlib.md5(str(segments_data)+str(sk_date)).hexdigest())
                if sk and flight_id:
			vals = (
				sk, str(departure_),
				self.crawl_type,
				str(response.meta['dx']),
				'1',
				str(is_avail),
				'<>'.join(airline_lst),
				str('<>'.join(flight_id_lst)),
				str(departure_), str(arrival_),
				origin,
				desct,
				json.dumps(providers_dict),
				json.dumps(aux_info),
				response.url
			)
			self.out_put.write('%s\n'%'#<>#'.join(vals))
	    		got_page(self.cr_tabe, self.source_name, response.meta['got_sk'],\
				 1, self.crawl_type, self.trip_type)	    