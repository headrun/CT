import os
import re
import json
import md5
import MySQLdb
import hashlib
import datetime
import logging
#from utils import *
from scrapy import log
from scrapy import signals
#from CTmonitoring.items import *
from scrapy.spider import Spider
from scrapy.http import FormRequest
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher

class WegoBrowse(Spider):
    name = "wego_browse"
    start_urls = ["https:wego.co.in"]

    def __init__(self, *args, **kwargs):
        super(WegoSaRoundTripBrowse, self).__init__(*args, **kwargs)
	self.source_name = 'wego'
	self.conn = MySQLdb.connect(host="localhost", user = "root", db = "WEGODB", charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()

    def parse(self, response):
        sel = Selector(response)
	auth_token = ''.join(sel.xpath('//div[contains(@class, "js-search_form_hotels")]\
		//input[@name="authenticity_token"]/@value').extract())
	formdata =  (
		('utf8', '\u2713'),
		('authenticity_token', auth_token),
		('departure_code', 'BLR'),
		('arrival_code', 'CCU'),
		('triptype', 'roundtrip'),
		('outbound_date', '2017-08-02'),
		('inbound_date', '2017-08-28'),
		('cabin', 'economy'),
		('wgz', '1d898'),
		)
	url = 'https://sa.wego.com/en/flights/search'
	yield FormRequest(url, callback=self.parse_next, formdata=formdata)

    def parse_next(self, response):
        sel = Selector(response)
        nodes = sel.xpath('//div[@class="card-list card-container js-card-container"]//section[contains(@class, "card js-card")]')
        for node in nodes:
            aux_info, provider_dict = {}, {}
            from_location, boding_time, to_location, dest_time, airline = ['']*5
	    re_from_location, re_boding_time, re_to_location, re_dest_time, re_airline = ['']*5
            is_avail = 0
            data = ''.join(node.xpath('./@data-flight-protos').extract())
            provider_nodes = node.xpath('.//div[@class="fare-options"]//div[contains(@class, "fare-option ")]')
	    flight_id, re_flight_id = '', ''
            for index, nod in enumerate(provider_nodes, 1):
                inn_dict = {}
                provider = ''.join(nod.xpath('.//div[@class="fare-provider-info"]//span[@class="fare-provider"]//text()').extract())
		provider_price = nod.xpath('.//strong[@class="js-rate-price rate-price rate-price-three-letter-code-symbol-first"]//text()').extract() 
                if provider_price:
                    inn_dict.update({'rank':index, 'price':provider_price[0]})
                if provider:
                    provider_dict.update({'%s_%s'%(provider,str(index)):inn_dict})
                    if 'cleartrip' in provider:
                        is_avail = 1
            if data:
                aux_info.update({'avail_data':data})
            if data:
                json_data = json.loads(data)
                lst_vals = json_data.get('outbound_segments', [])
		return_segments = json_data.get('inbound_segments', [])
                if lst_vals:
                    from_location = lst_vals[0].get('departure_airport', {}).get('name', '')
                    boding_time = lst_vals[0].get('departure_time', '').replace('T', ' ').split('+')[0]
                    to_location = lst_vals[-1].get('arrival_airport', {}).get('name', '')
                    dest_time = lst_vals[-1].get('arrival_time', '').replace('T', ' ').split('+')[0]
                    airline = lst_vals[0].get('airline', {}).get('name', '')
		    flight_id = lst_vals[0].get('designator_code', '')
		if return_segments:
		    re_from_location = lst_vals[0].get('departure_airport', {}).get('name', '')
                    re_boding_time = lst_vals[0].get('departure_time', '').replace('T', ' ').split('+')[0]
                    re_to_location = lst_vals[-1].get('arrival_airport', {}).get('name', '')
                    re_dest_time = lst_vals[-1].get('arrival_time', '').replace('T', ' ').split('+')[0]
                    re_airline = lst_vals[0].get('airline', {}).get('name', '')
		    re_flight_id = lst_vals[0].get('designator_code', '')

            sk = str(hashlib.md5(data+str(provider_dict)).hexdigest())
	    if sk:
		vals = (sk, date, self.crawl_type, is_avail, airline, boding_time,
                        dest_time, from_location, to_location, json.dumps(provider_dict),
                                json.dumps(aux_info), response.url, sk, json.dumps(provider_dict))
                self.cur.execute(self.insert_query, vals)

