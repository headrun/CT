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
from CTmonitoring.items import *
from scrapy.spider import Spider
from scrapy.http import FormRequest
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher

class WegoBrowse(Spider):
    name = "wegoco_browse"
    start_urls = ["https://www.wego.co.in/"]

    def __init__(self, *args, **kwargs):
        super(WegoBrowse, self).__init__(*args, **kwargs)
        self.log = create_logger_obj('wego')
        self.crawl_type = kwargs.get('crawl_type', '')
        self.conn = MySQLdb.connect(host="localhost", user = "root", db = "WEGODB", charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()
	self.out_put = get_output_file('wego')
	self.cr_tabe = create_crawl_table_cursor()
	dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
	self.cur.close()
	self.conn.close()
	self.out_put.close()
	self.cr_tabe.close()
	move_crawlout_processing('wego')

    def parse(self, response):
        sel = Selector(response)
	requests = terminal_requests(self.cr_tabe, 'wego', self.crawl_type)
        if requests:
            for input_ in requests:
		got_sk, from_, to_, date = input_
		date = str(date.date())
                auth_token = ''.join(sel.xpath('//div[contains(@class, "js-search_form_hotels")]\
                        //input[@name="authenticity_token"]/@value').extract())
                formdata =  (
                        ('utf8', '\u2713'),
                        ('authenticity_token', auth_token),
                        ('departure_code', from_.strip()),
                        ('arrival_code', to_.strip()),
                        ('arrival_city', 'true'),
                        ('triptype', 'oneway'),
                        ('outbound_date', str(date)),
                        ('cabin', 'economy'),
                        ('wgz', '1d898'),
                        )
                url = 'https://www.wego.co.in/flights/search'
                yield FormRequest(url, callback=self.parse_next, formdata=formdata, meta={'date':date, 'got_sk': got_sk})

    def parse_next(self, response):
        sel = Selector(response)
        nodes = sel.xpath('//div[@class="card-list card-container js-card-container"]//section[contains(@class, "card js-card")]')
        date = response.meta.get('date', '')
	got_sk = response.meta.get('got_sk', '')
        for node in nodes:
            aux_info, provider_dict = {}, {}
            from_location, boding_time, to_location, dest_time, airline = ['']*5
            is_avail = 0
            data = ''.join(node.xpath('./@data-flight-protos').extract())
            provider_nodes = node.xpath('.//div[@class="fare-options"]//div[contains(@class, "fare-option ")]')
	    flight_id = ''.join(node.xpath('.//span[@class="flight-number"]//text()').extract())
            for index, nod in enumerate(provider_nodes, 1):
                inn_dict = {}
                provider = ''.join(nod.xpath('.//div[@class="fare-provider-info"]//span[@class="fare-provider"]//text()').extract())
                provider_price = nod.xpath('.//div[@class="fare-price-book fare-section "]\
                                //strong[@class="js-rate-price rate-price"]//text()').extract()
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
                if lst_vals:
                    from_location = lst_vals[0].get('departure_airport', {}).get('name', '')
                    boding_time = lst_vals[0].get('departure_time', '').replace('T', ' ').split('+')[0]
                    to_location = lst_vals[-1].get('arrival_airport', {}).get('name', '')
                    dest_time = lst_vals[-1].get('arrival_time', {}).replace('T', ' ').split('+')[0]
                    airline = lst_vals[0].get('airline', {}).get('name', '')

            sk = str(hashlib.md5(data+str(provider_dict)).hexdigest())
	    if sk:
                avail = {}
                avail.update({'sk': sk, 'flight_id':flight_id, 'date': date, 'type': self.crawl_type, 'is_available': str(is_avail), 'airline': airline, 'departure_time': boding_time, 'arrival_time': dest_time, 'from_location': from_location, 'to_location' : to_location, 'providers': json.dumps(provider_dict), 'aux_info': json.dumps(aux_info), 'reference_url': response.url})
                self.out_put.write('%s\n'%json.dumps(avail))
	if nodes:
	    got_page(self.cr_tabe, 'wego', got_sk, 1, self.crawl_type)


