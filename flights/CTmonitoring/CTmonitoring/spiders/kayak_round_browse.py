import os
import re
import json
import md5
import MySQLdb
import hashlib
import datetime
import logging
from utils import *
from scrapy import log
from scrapy import signals
from ast import literal_eval
from CTmonitoring.items import *
from scrapy.spider import Spider
from scrapy.http import FormRequest
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher


class KayakRtBrowse(Spider):
    name = "kayakrt_browse"
    start_urls = ["https://www.kayak.co.in/"]

    def __init__(self, *args, **kwargs):
        super(KayakRtBrowse, self).__init__(*args, **kwargs)
	self.source_name = 'kayakrt'
	self.source_crawl_db = 'kayak'
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
	res_headers = json.dumps(str(response.headers))
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
        cookies = {}
        for i in my_dict.get('Set-Cookie', []):
            data = i.split(';')[0]
            if data:
                try : key, val = data.split('=', 1)
                except : import pdb;pdb.set_trace()
                cookies.update({key.strip():val.strip()})
	requests = terminal_requests(self.cr_tabe, self.source_crawl_db, self.crawl_type, self.trip_type, self.limit)
	for input_ in requests:
            got_sk, from_, to_, date, dx, re_date = input_
            date = str(date.date())
	    re_date = str(re_date.date())
	    url = "https://www.kayak.co.in/flights/%s-%s/%s/%s"%(from_.strip(), to_.strip(), date, re_date)
	    yield FormRequest(url, callback=self.parse_next, cookies=cookies,\
			 meta={'date':date, 'got_sk': got_sk, 'from_':from_, 'to_':to_, 'dx':dx, 're_date':re_date})

    def parse_next(self, response):
	sel = Selector(response)
	date = response.meta.get('date', '')
        got_sk = response.meta.get('got_sk', '')
	flight_nodes = sel.xpath('//div[@id="searchResultsList"]//div[@class="resultWrapper"]')
        se_ids = re.findall('\"searchId\":\"(\w+)\"', response.body)
	if se_ids: search_id = se_ids[0]
	else: search_id = ''
        script_meta = ''.join(sel.xpath('//style[@data-type="script-metadata2"]//text()').extract())
	style_meta = ''.join(sel.xpath('//style[@data-type="style-metadata2"]//text()').extract())
	for nod in flight_nodes:
	    details = {}
	    flight = nod.xpath('.//ol[@class="flights"]')
	    d_airline = ''.join(nod.xpath('.//ol[@class="flights"]//li[1]//div[@class="col-field carrier"]\
				/div[@class="bottom"]/text()').extract())
	    d_from_time = ''.join(nod.xpath('.//ol[@class="flights"]//li[1]//div[@class="col-field time depart"]\
				/div[@class="top"]/text()').extract())
	    d_from_city = ''.join(nod.xpath('.//ol[@class="flights"]//li[1]//div[@class="col-field time depart"]\
				/div[@class="bottom"]/text()').extract())
	    d_to_time = ''.join(nod.xpath('.//ol[@class="flights"]//li[1]//div[@class="col-field time return"]\
				/div[@class="top"]/text()').extract())
	    d_to_city = ''.join(nod.xpath('.//ol[@class="flights"]//li[1]//div[@class="col-field time return"]\
				/div[@class="bottom"]/text()').extract())
	    r_airline = ''.join(nod.xpath('.//ol[@class="flights"]//li[2]//div[@class="col-field carrier"]\
                                /div[@class="bottom"]/text()').extract())
            r_from_time = ''.join(nod.xpath('.//ol[@class="flights"]//li[2]//div[@class="col-field time depart"]\
                                /div[@class="top"]/text()').extract())
            r_from_city = ''.join(nod.xpath('.//ol[@class="flights"]//li[2]//div[@class="col-field time depart"]\
                                /div[@class="bottom"]/text()').extract())
            r_to_time = ''.join(nod.xpath('.//ol[@class="flights"]//li[2]//div[@class="col-field time return"]\
                                /div[@class="top"]/text()').extract())
            r_to_city = ''.join(nod.xpath('.//ol[@class="flights"]//li[2]//div[@class="col-field time return"]\
                                /div[@class="bottom"]/text()').extract())

	    details.update({'airline':d_airline, 'from_':response.meta['from_'], 'to_':response.meta['to_'],
				'return_airline':r_airline, 're_date':response.meta['re_date']})
	    result_id = ''.join(nod.xpath('./../@data-resultid').extract())
	    form_data = (
                        ('resultId', result_id),
                        ('searchId', search_id),
                        ('specificLegCounts[]', '1'),
                        ('filterState', '{}'),
                        ('legFilterEnabled', 'false'),
                        ('fspId', ''),
                        ('scriptsMetadata', script_meta),
                        ('stylesMetadata', style_meta),
                        )
            post_url = 'https://www.kayak.co.in/s/horizon/flights/results/FlightResultDetails'
	    yield FormRequest(post_url, formdata=form_data, callback=self.parse_provider, \
	    	meta={'data':details, 'date':date, 'ref_url':response.url, 'dx':response.meta['dx']})
	if flight_nodes:
	    got_page(self.cr_tabe, self.source_crawl_db, got_sk, 1, self.crawl_type, self.trip_type)

    def parse_provider(self, response):
	sel = Selector(response)
	data = response.meta['data']
	date = response.meta['date']
	provider_dict, avail = {}, {}
	is_avail, rank = 0, 0
	airline = data.get('airline', '')
	from_ = data.get('from_', '')
	to_ = data.get('to_', '')
	re_date = data.get('re_date', '')
	return_airline = data.get('return_airline', '')
	d_flight_id = ''.join(sel.xpath('//div[@class="col-content"][1]//div[@class="planeDetails"]//text()').extract())
	r_flight_id = ''.join(sel.xpath('//div[@class="col-content"][2]//div[@class="planeDetails"]//text()').extract())
	if d_flight_id:d_flight_id = re.search('\d+', d_flight_id).group()
	if r_flight_id: r_flight_id= re.search('\d+', r_flight_id).group()
	nodes = sel.xpath('//div[@class="col-content"]//table//tbody//tr')
	for idx, node in enumerate(nodes, 1):
	    provider = ''.join(node.xpath('./td[@class="logo"]/img/@title').extract())
	    price = normalize(''.join(node.xpath('./td[@class="price total"]/a/text()').extract()).replace(u'\u20b9\xa0', ''))
	    if 'cleartrip' in provider:
		is_avail = 1
	    if provider:
	        rank = rank + 1
		provider_dict.update({provider:{'rank':rank, 'price':price}})
	
	sk = str(hashlib.md5( str(data) + str(provider_dict)).hexdigest())
	if sk and d_flight_id:
            avail = {}
            avail.update({'sk': sk, 'flight_id':d_flight_id, 'date': date, 'type': self.crawl_type, 'is_available': str(is_avail), 'airline': airline, 'departure_time': date, 'arrival_time': '', 'from_location': from_, 'to_location' : to_, 'providers': json.dumps(provider_dict), 'aux_info': '', 'reference_url': response.meta.get('ref_url', ''), 'dx':response.meta['dx'], 'no_of_passengers':'1', 'return_flight_id':r_flight_id, 'return_departure_time':re_date, 'return_airline':return_airline})
            self.out_put.write('%s\n'%json.dumps(avail)) 
