import os
import re
import json
import md5
import MySQLdb
import hashlib
import datetime
import logging
import requests
from utils import *
from scrapy import log
from scrapy import signals
from CTmonitoring.items import *
from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher

class WegoSaNewBrowse(Spider):
    name = "wegosanew_browse"
    start_urls = ["https://sa.wego.com/en"]

    def __init__(self, *args, **kwargs):
        super(WegoSaNewBrowse, self).__init__(*args, **kwargs)
	self.source_name = 'wegosa'
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
	requests = terminal_requests(self.cr_tabe, self.source_name, self.crawl_type, self.trip_type, self.limit)
        for input_ in requests:
            got_sk, from_, to_, date, dx, re_date = input_
	    from_ = from_.strip()
	    to_ = to_.strip()
            date = str(date.date())
	    refer_url = 'https://sa.wego.com/en/flights/searches/%s-c%s/%s/economy/1a:0c:0i'%(from_, to_, date)
	    headers = {
			'content-type': 'application/json',
			'accept': '*/*',
			'referer': refer_url,
			'authority': 'srv.wego.com',
		      }
	    data = {"search":{	"cabin":"economy",
				"deviceType":"DESKTOP",
				"appType":"WEB_APP",
				"userLoggedIn":'false',
				"adultsCount":1,
				"childrenCount":0,
				"infantsCount":0,
				"siteCode":"SA",
				"currencyCode":"SAR",
				"locale":"en",
			"legs":[{"departureAirportCode":from_,
				"arrivalCityCode":to_,
				"outboundDate":date
				}]
			},
		"offset":0,
		"paymentMethodIds":[10,83,15],
		"providerTypes":[]
		}
	    url = "https://srv.wego.com/v2/metasearch/flights/searches"
	    yield Request(url, callback=self.parse_next, body=json.dumps(data), headers=headers, method="POST",
				meta={'headers_data':headers, 'url':url, 'got_sk':got_sk, 'dx':dx, 'ref_url':refer_url})

    def parse_next(self, response):
	res_body = response.body
	yield Request(response.meta['url'], callback=self.parse_data, \
			headers=response.meta['headers_data'],
			body=res_body, method="POST",
			meta={'got_sk':response.meta['got_sk'],
			'dx':response.meta['dx'], 'ref_url':response.meta['ref_url']})
    def parse_data(self, response):
	sel = Selector(response)
	try: body = json.loads(response.body)
	except: body = {}
	trip_list = body.get('trips', [])
	legs = body.get('legs', [])
        legs_dict = {}
        for i in legs:
            ids = i.get('id', '')
            if ids: legs_dict.update({ids:i})
	for lst in trip_list:
	    ids = lst.get('id', '')
	    l_id = lst.get('code', '').replace('-', ':')
            stopoverscount = legs_dict.get(l_id, {}).get('stopoversCount', '0')
	    url = "https://srv.wego.com/v2/metasearch/flights/trips/%s?currencyCode=SAR"%ids
	    yield Request(url, callback=self.parse_fares,
			meta={'got_sk':response.meta['got_sk'], 'stopoverscount':stopoverscount,
                        'dx':response.meta['dx'], 'ref_url':response.meta['ref_url']})
	if trip_list:
            got_page(self.cr_tabe, self.source_name, response.meta['got_sk'], 1, self.crawl_type, self.trip_type)

    def parse_fares(self, response):
	try:data = json.loads(response.body)
	except: data = {}
	aux_info = {}
        aux_info.update({'stop_count':str(response.meta['stopoverscount'])})
	if data:
	    airline, flight_id, detature, arrival, de_date = ['']*5
	    trip = data.get('trip', {})
	    flight_details = trip.get('legs', [])
	    fare_lst = trip.get('fares', [])
	    provider_dict, avail = {}, {}
	    is_avail = 0
	    if flight_details:
		f_dict = flight_details[0]
		detature = f_dict.get('departureAirportCode', '')
		arrival = f_dict.get('arrivalAirportCode', '')
		segments = f_dict.get('segments', [])
		de_date = f_dict.get('departureDateTime', '').split('T')[0].strip()
		if segments:
		    seg_dict = segments[0]
		    airline = seg_dict.get('airlineName', '')
		    flight_id = seg_dict.get('designatorCode', '')
	    if fare_lst:
		for rank, dic in enumerate(fare_lst, 1):
		    price = dic.get('price', {}).get('totalAmount', 0)
		    provider = dic.get('provider', {}).get('name', '')
		    if provider:
			if 'cleartrip' in provider:
			    is_avail = 1
			provider_dict.update({provider:{'rank':rank, 'price':price}})
	    sk_data = '%s%s%s%s%s'%(airline, flight_id, detature, arrival, de_date)
	    sk = str(hashlib.md5( str(sk_data) + str(provider_dict)).hexdigest())
	    print aux_info
	    if flight_id:
		flight_id = re.sub(flight_id[1],flight_id[1]+'-',flight_id)
		avail.update({'sk': sk, 'flight_id':flight_id, 'date': de_date, 'type': self.crawl_type, 'is_available': str(is_avail), 'airline': airline, 'departure_time': de_date, 'arrival_time': '', 'from_location': detature, 'to_location' : arrival, 'providers': json.dumps(provider_dict), 'aux_info': json.dumps(aux_info), 'reference_url':response.meta.get('ref_url', ''), 'dx':response.meta['dx'], 'no_of_passengers':'1'})
            	self.out_put.write('%s\n'%json.dumps(avail))
