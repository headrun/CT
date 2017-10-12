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
from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher


class SkyBrowse(Spider):
    name = "skyscannerrt_browse"
    start_urls = ["https://www.skyscanner.co.in/"]

    def __init__(self, *args, **kwargs):
        super(SkyBrowse, self).__init__(*args, **kwargs)
        self.source_name = 'skyscannerrt'
        self.crawl_table_name = 'skyscanner'
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
        requests = terminal_requests(self.cr_tabe, self.crawl_table_name, self.crawl_type, self.trip_type, self.limit)
        for input_ in requests:
            got_sk, from_, to_, date, dx, re_date = input_
            refer_date = str(date.strftime("%y%m%d"))
            date = str(date.date())
            re_date = str(re_date.date())
            from_ = from_.strip()
            to_ = to_.strip()
            
            headers = {
                'x-skyscanner-devicedetection-istablet': 'false',
                'origin': 'https://www.skyscanner.co.in',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'en-US,en;q=0.8',
                'x-requested-with': 'XMLHttpRequest',
                'pragma': 'no-cache',
                'x-skyscanner-channelid': 'website',
                'x-skyscanner-devicedetection-ismobile': 'false',
                'content-type': 'application/json; charset=UTF-8',
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'cache-control': 'no-cache',
                'authority': 'www.skyscanner.co.in',
                'referer': 'https://www.skyscanner.co.in/transport/flights/%s/%s/%s'%(from_.lower(), to_.lower(), refer_date),
		        }
            
            data = {
                "market":"IN",
                "currency":"INR",
                "locale":"en-GB",
                "cabin_class":"economy",
                "prefer_directs":'false',
                "trip_type":"one-way",
                "legs":[{"origin":from_,"destination":to_,"date":date,"return_date":re_date}],
                "adults":1,
                "child_ages":[],
                "options":{
                    "include_unpriced_itineraries":'true',
                    "include_mixed_booking_options":'true'
                    },
                "prefer_directs":"false",
                "trip_type":"return"
		        }
        
            url = 'https://www.skyscanner.co.in/dataservices/flights/pricing/v3.0/search/?geo_schema=skyscanner&carrier_schema=skyscanner&response_include=query%3Bdeeplink%3Bsegment%3Bstats%3Bfqs%3Bpqs%3B_flights_availability'
            yield Request(url, callback=self.parse_next, headers=headers, cookies=cookies, body=json.dumps(data), method="POST",
				meta={'dx':dx, 'got_sk':got_sk, 'date':date, 're_date':re_date})

    def parse_next(self, response):
        try: data = json.loads(response.body)
        except: data = {}
        if data:
            date = response.meta['date']
            re_date = response.meta['re_date']
            places_dict, carriers_dict, prices_dict, agents_dict, segments_dict,  = {}, {}, {}, {}, {}
            oneway_list, return_list = [], []
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
            
            price_keys = prices_dict.keys()
            for key in price_keys:
                oneway_key, return_key = key.split('|')[0], key.split('|')[-1]
            	for flg in flights_lst:
		    if oneway_key == flg.get('id', ''):oneway_list.append(flg)
                    if return_key == flg.get('id', ''):return_list.append(flg)
        
            for i,k in zip(oneway_list, return_list):
                providers_dict, aux_info = {}, {}
                provider_lst = prices_dict.get(key, '')
                oneway_seg_ids = i.get('segment_ids', [])
                return_seg_ids = k.get('segment_ids', [])
                if len(oneway_seg_ids) > len(return_seg_ids): return_seg_ids.extend([return_seg_ids[-1]]*abs(len(oneway_seg_ids)-len(return_seg_ids)))
                if len(return_seg_ids) > len(oneway_seg_ids): oneway_seg_ids.extend([oneway_seg_ids[-1]]*abs(len(oneway_seg_ids)-len(return_seg_ids)))
                for oneway_id, return_id in zip(oneway_seg_ids, return_seg_ids):
                    oneway_segments_data = segments_dict.get(oneway_id, {})
                    return_segments_data = segments_dict.get(return_id, {})
                    oneway_flight_id = oneway_segments_data.get('marketing_flight_number', '')
                    return_flight_id = return_segments_data.get('marketing_flight_number', '')
                    oneway_date, return_date = oneway_segments_data.get('departure', '').split('T')[0], return_segments_data.get('departure', '').split('T')[0]
                    origin_ = places_dict.get(oneway_segments_data.get('origin_place_id', ''), {}).get('display_code', '')
                    desct_ = places_dict.get(oneway_segments_data.get('destination_place_id', ''), {}).get('display_code', '')
                    oneway_airline = carriers_dict.get(oneway_segments_data.get('marketing_carrier_id', ''), '').get('name', '')
                    return_airline = carriers_dict.get(return_segments_data.get('marketing_carrier_id', ''), '').get('name', '')
                    rank, is_avail = 0, 0
                    for prv in provider_lst:
                        item = prv.get('items', [])
                        if item:
                            item = item[0]
                            agent = agents_dict.get(item.get('agent_id', ''), {}).get('name', '')
                            price = item.get('price', {}).get('amount', '')
                            if agent:
                                rank = rank + 1
                                if 'cleartrip' in agent.lower(): is_avail = 1
                                providers_dict.update({agent:{'rank':rank, 'price':str(price)}})
                
                    sk = str(hashlib.md5(str(oneway_segments_data) + str(return_segments_data) + str(provider_lst)).hexdigest())
                    if sk and oneway_flight_id and return_flight_id:
                        avail = {}
                        avail.update({'sk': sk, 'flight_id':oneway_flight_id, 'date': oneway_date, 'type': self.crawl_type, 'is_available': str(is_avail), 'airline': oneway_airline, 'departure_time': oneway_date, 'arrival_time': oneway_date, 'from_location': origin_, 'to_location' : desct_, 'providers': json.dumps(providers_dict), 'aux_info': json.dumps(aux_info), 'reference_url': response.url, 'dx':response.meta['dx'], 'no_of_passengers':'1', 'return_flight_id':return_flight_id, 'return_date':return_date, 'return_airline':return_airline, 'return_departure_time':return_date})
                        self.out_put.write('%s\n'%json.dumps(avail))
                        got_page(self.cr_tabe, self.crawl_table_name, response.meta['got_sk'], 1, self.crawl_type, self.trip_type)
