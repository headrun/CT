import scrapy
from scrapy.selector import Selector
from scrapy.http import Request
import datetime
import json
import os
import time
import re
import MySQLdb
import logging
from scrapy import log
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from Hotels.utils import *
from Hotels.items import *
from Hotels.auto_config import CLEARTRIP_HEADERS
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class Bookingcontentscore(scrapy.Spider):
    name = "Bookingcontentscore_terminal"
    handle_httpstatus_list = [400, 404, 500, 401]
    start_urls = []

    def __init__(self, *args, **kwargs):
        super(Bookingcontentscore, self).__init__(*args, **kwargs)
        self.name = 'Bookingcontentscore'
        self.log = create_logger_obj(self.name)
        self.crawl_type = kwargs.get('crawl_type', 'keepup')
        self.content_type = kwargs.get('content_type', 'hotels')
        self.limit = kwargs.get('limit', 1000)
        self.out_put_file = get_ctrip_file(self.name)
        self.cursor = create_crawl_table_cusor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.cursor.close()
        ct_crawlout_processing(self.out_put_file)

    def start_requests(self):
        rows = terminal_contentclear_requests(
            self.cursor, self.name, self.crawl_type, self.content_type, self.limit)
        if rows:
            for sk, url, h_name, meta_data in rows:
                meta_data = json.loads(meta_data)
                city_name = meta_data.get('city_name', '')
                page_url = meta_data.get('page_url', '')
                main_url = meta_data.get('main_url', '')
                hotel_url = meta_data.get('hotel_url', '')
                yield Request(
                    url, callback=self.parse,
                    meta={'city_name': city_name, "sk":sk, 'url':url, 'h_name':h_name, 'page_url':page_url, 'main_url':main_url, 'hotel_url':hotel_url})

    def parse(self, response):
        sel = Selector(response)
        city_name = response.meta.get('city_name', '')
        sk = response.meta.get('sk', '')
        url = response.meta.get('url', '')
        h_name = response.meta.get('h_name', '')
        page_url = response.meta.get('page_url', '')
        main_url =  response.meta.get('main_url', '')
        hotel_url = response.meta.get('hotel_url', '')
        if response.status == 200:
            h_id = normalize_clean(sel.xpath('//input[@type="hidden"][@name="hotel_id"]/@value').extract_first())
            h_name = normalize_clean(''.join(re.findall("b_hotel_name: \'(.*)\'", response.body))).replace('\\', '')
            address = normalize_clean(''.join(re.findall('\"streetAddress\" : \"(.*)\"', response.body))).replace('\\', '')
            city_ = normalize_clean(''.join(re.findall("city_name: \'(.*?)\'", response.body)))
            locality_latitude, locality_longitude = ['']*2
            cvs = ''.join(sel.xpath('//a[@data-title="Check location"]/@style').extract())
            csv_la = re.findall('&center=(\d+.\d+),(\d+.\d+)&', cvs)
            if csv_la:
                    locality_latitude, locality_longitude = csv_la[0]
            cvss = ''.join(sel.xpath('//span[@class="hp__hotel_ratings"]//svg[contains(@class, "ratings_stars")]/@class').extract())
            rating_agency_star = ''.join(re.findall('\d+', cvss))
            fac_nods = sel.xpath('//div[contains(@class, "hp_hotel_description")]//div[contains(@class, "hp_desc_important_facilities")]//div[@class="important_facility "]')
            hotel_amenities_final = ', '.join([normalize_clean(''.join(nod.xpath('.//text()').extract())) for nod in fac_nods])
            hotel_description = ' '.join(sel.xpath('//div[@id="summary"]//text()').extract())
            hotel_description = normalize_clean(re.sub('\<.*?\>', ' ',hotel_description))
            import pdb;pdb.set_trace()
            ct_item = ContentScore()
            ct_item.update({"sk":sk, "hotel_id":h_id, "hotel_name":h_name, "address":address, "city":city_, "locality_latitude":locality_latitude, "locality_longitude":locality_longitude, "star_rating":rating_agency_star, "description":hotel_description, "amenities":hotel_amenities_final, "reference_url":response.url, "html_hotel_url":hotel_url, "main_listing_url":main_url, "navigation_url":page_url})
            yield ct_item
        self.cursor.execute(
            "update %s_crawl set crawl_status=1 where sk = '%s'" % (self.name, sk))
