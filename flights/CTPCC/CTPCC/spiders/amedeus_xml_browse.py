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
from xml.etree import ElementTree as ET
from lxml import etree


class AmedeusSpider(Spider):
    name = "amedeus_xml_browse"
    start_urls = []
    handle_httpstatus_list = [500]

    def __init__(self, *args, **kwargs):
        super(AmedeusSpider, self).__init__(*args, **kwargs)
        self.source_name = 'amedeus'
        self.log = create_logger_obj(self.source_name)
        self.crawl_type = kwargs.get('crawl_type', '')
        self.trip_type = kwargs.get('trip_type', '')
        self.limit = kwargs.get('limit', '')
        if self.trip_type == 'roundtrip':
            file_name = 'amedeusrt'
        else:
            file_name = 'amedeus'
        self.out_put, self.out_put_file = get_output_file(file_name)
        self.cr_tabe = create_crawl_table_cursor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.out_put.close()
        self.cr_tabe.close()
        move_crawlout_processing(self.out_put_file)

    def start_requests(self):

        requests = terminal_requests(self.cr_tabe, self.source_name, self.crawl_type, self.trip_type, self.limit)
        for input_ in requests:
            got_sk, from_, to_, de_date, dx, re_date = input_
            from_ = from_.strip()
            to_ = to_.strip()
            re_date_ = ''
            de_date = str(de_date.date())
            de_date_ = datetime.datetime.strptime(
                de_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            if re_date:
                re_date = str(re_date.date())
                re_date_ = datetime.datetime.strptime(
                    re_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            else: re_date_ = ''
            if self.trip_type == 'roundtrip':
                trip_type = 'RoundTrip'
                url = 'http://172.23.20.18:9080/airservice/search?from=%s&to=%s&depart_date=%s&return_date=%s&adults=1&childs=0&infants=0&class=Economy&airline=&carrier=&intl=y&src=connector&suppliers=AMADEUS_INTERNATIONAL'%(from_, to_, de_date_, re_date_)
            else:
                trip_type = 'OneWay'

                url = 'http://172.21.20.61:9080/airservice/search?from=%s&to=%s&depart_date=%s&adults=1&childs=0&infants=0&class=Economy&airline=&carrier=&src=connector&suppliers=AMADEUS&sct=ae'(from_, to_, de_date_)
            yield Request(url, callback=self.parse,meta={'from_loc':from_,'to_loc':to_,'dx':dx})

    def parse(self,response):
        doc = Selector(text=response.body.strip())
        from_loc = response.meta.get('from_loc','')
        to_loc =response.meta.get('to_loc','')
        dx = response.meta.get('dx','')
        aux_info = {}
        airline_codes_dict = {}
        airlines = doc.xpath('//ancillary-data//airlines//airline')
        for airline_code in airlines :
            code = str("".join(airline_code.xpath('.//code//text()').extract()))
            name = str("".join(airline_code.xpath('.//name//text()').extract()))
            airline_codes_dict.update({code:name})
        nodes = doc.xpath('//solution')
        rank = 0
        for node in nodes :
            price_details = node.xpath('.//pax-pricing-info-list')[0]
            pax_type = price_details.xpath('./pax-pricing-info//pax-type//text()')
            price_info_dict = {}
            pricing_elements = price_details.xpath('.//pricing-info//pricing-elements//pricing-element')
            for i in pricing_elements  :
                category = "".join(i.xpath('.//category//text()').extract())
                amount = "".join(i.xpath('.//amount//text()').extract())
                code = "".join(i.xpath('.//code//text()').extract())
                if code :
                    price_info_dict.update({code:amount})
            if price_info_dict : aux_info.update({'Tax':str(price_info_dict)})
            base_fare = "".join(node.xpath('./pricing-summary/base-fare//text()').extract())
            tax = "".join(node.xpath('./pricing-summary//taxes//text()').extract())
            total_fare = "".join(node.xpath('./pricing-summary/total-fare//text()').extract())
            markup = "".join(node.xpath('./pricing-summary/markup//text()').extract())
            if markup : aux_info.update({'markup':str(markup)})
            if self.trip_type == 'roundtrip':
                flights = node.xpath('.//flights//flight')
                sector = from_loc + '-' + to_loc
                onward_segments = flights[0].xpath('.//segment')
                rank = rank + 1
                on_segments = self.get_segment_data(onward_segments,airline_codes_dict,sector)
                return_segments = flights[1].xpath('.//segment')
                ret_segments = self.get_segment_data(return_segments,airline_codes_dict,sector)

                vals = on_segments + ret_segments[2:] + [str(base_fare),str(tax),'','',str(total_fare),str(rank),str(dx),str(self.crawl_type),str(self.trip_type),str(aux_info)]
                self.out_put.write('%s\n' % '#<>#'.join(vals))

            else :
                    rank = rank + 1
                    sector = from_loc + '-' + to_loc
                    segments = node.xpath('.//segment')
                    oneway_segments = self.get_segment_data(segments,airline_codes_dict,sector)

                    vals = oneway_segments + [str(base_fare),str(tax),'','',str(total_fare),str(rank),str(dx),str(self.crawl_type),str(self.trip_type),str(aux_info)]
                    self.out_put.write('%s\n' % '#<>#'.join(vals))


    def  get_segment_data(self,segments,airline_codes_dict,sector) :
            flt_ids, opt_airline, airline_lst, airport_list = [], [], [], []
            dep_date_time, arrival_date_time = ['']*2
            for idx, segment in enumerate(segments):
                index = "".join(segment.xpath('.//index//text()').extract())
                departure = "".join(segment.xpath('.//departure-airport//text()').extract())
                depart_terminal = "".join(segment.xpath('.//departure-terminal//text()').extract())
                arrival_airport = "".join(segment.xpath('.//arrival-airport//text()').extract())
                arrival_term = "".join(segment.xpath('.//arrival-terminal//text()').extract())
                dep_time = "".join(segment.xpath('.//departure-date-time//text()').extract()).replace('T',' ').split('+')[0]
                arri_date = "".join(segment.xpath('.//arrival-date-time//text()').extract()).replace('T',' ').split('+')[0]
                flight_num = "".join(segment.xpath('.//flight-number//text()').extract())
                airline = "".join(segment.xpath('.//airline//text()').extract())
                operating_airline = "".join(segment.xpath('.//operating-airline//text()').extract())
                stops = "".join(segment.xpath('.//stops//text()').extract())

                flight_id = airline+'-'+flight_num
                flt_ids.append(flight_id)
                airport_list.append('%s-%s'%(departure, arrival_airport))
                if airline :
                    airline = airline_codes_dict.get(airline,'')
                    airline_lst.append(airline)
                duration = "".join(segment.xpath('.//duration//text()').extract())
                if idx == 0:
                    dep_date_time = dep_time
                arrival_date_time = arri_date
            sk = str(hashlib.md5(str(segments)).hexdigest())
            vals = [sk, sector, str('<>'.join(airport_list)), str(dep_date_time), str(arrival_date_time), str('<>'.join(airline_lst).strip('<>')), str(len(flt_ids)-1), str('<>'.join(flt_ids))]
            return vals
