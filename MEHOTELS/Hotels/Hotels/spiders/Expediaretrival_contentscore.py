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


class Expediacontentscore(scrapy.Spider):
    name = "Expediacontentscore_terminal"
    handle_httpstatus_list = [400, 404, 500, 401]
    start_urls = []

    def __init__(self, *args, **kwargs):
        super(Expediacontentscore, self).__init__(*args, **kwargs)
        self.name = 'Expediacontentscore'
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
        city_name = response.meta.get('city_name', '')
        sk = response.meta.get('sk', '')
        url = response.meta.get('url', '')
        h_name = response.meta.get('h_name', '')
        page_url = response.meta.get('page_url', '')
        main_url =  response.meta.get('main_url', '')
        hotel_url = response.meta.get('hotel_url', '')
        if response.status == 200:
            data = Selector(response)
            h_id = ''.join(re.findall('infosite.hotelId = \'(.*?)\';', response.body))
            h_name = normalize_clean(''.join(re.findall('infosite.hotelName = \'(.*?)\';', response.body)))
            address = normalize_clean(data.xpath('//span[@class="street-address"][not(@itemprop)]/text()').extract_first())
            city_ = normalize_clean(''.join(re.findall('infosite.hotelCityName = \'(.*?)\';', response.body)))
            latlongs = ''.join(re.findall('latLong:\"(.*?)\"', response.body))
            locality_latitude, locality_longitude = latlongs.split(',')
            rating_agency_star = ''.join(re.findall('infosite.starRatingString = \'(.*?)\';', response.body))
            if '-' in rating_agency_star:
                rating_agency_star = ''
            hotel_amenities_final = normalize_clean(', '.join(data.xpath('//div[@data-section="amenities-general"]//ul/li/text()').extract()).replace(u'\xa0', ''))
            hotel_description = ' '.join(data.xpath('//div[@class="hotel-description"]//h3[contains(text(), "Location")]/following-sibling::p[1]/text()').extract())
            hotel_description = normalize_clean(re.sub('\<.*?\>', ' ',hotel_description))
            ct_item = ContentScore()
            ct_item.update({"sk":sk, "hotel_id":h_id, "hotel_name":h_name, "address":address, "city":city_, "locality_latitude":locality_latitude, "locality_longitude":locality_longitude, "star_rating":rating_agency_star, "description":hotel_description, "amenities":hotel_amenities_final, "reference_url":response.url, "html_hotel_url":hotel_url, "main_listing_url":main_url, "navigation_url":page_url})
            yield ct_item
        self.cursor.execute(
            "update %s_crawl set crawl_status=1 where sk = '%s'" % (self.name, sk))
