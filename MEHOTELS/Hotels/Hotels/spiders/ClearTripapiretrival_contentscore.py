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


class CrawlCTreteriveapicontentscore(scrapy.Spider):
    name = "CLEARTRIPapicontentscore_terminal"
    handle_httpstatus_list = [400, 404, 500, 401]
    start_urls = []

    def __init__(self, *args, **kwargs):
        super(CrawlCTreteriveapicontentscore, self).__init__(*args, **kwargs)
        self.name = 'Cleartripcontentscore'
        self.log = create_logger_obj(self.name)
        self.crawl_type = kwargs.get('crawl_type', 'keepup')
        self.content_type = kwargs.get('content_type', 'hotels')
        self.limit = kwargs.get('limit', 1000)
        self.out_put_file = get_ctrip_file(self.name)
        self.cursor = create_crawl_table_cusor()
        self.headers = CLEARTRIP_HEADERS
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
                    url, callback=self.parse, headers=self.headers,
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
            data = Selector(text=response.body)
            h_id = ''.join(data.xpath('//hotel-id/text()').extract())
            h_name = normalize_clean(''.join(data.xpath('//hotel-name/text()').extract()))
            address = normalize_clean(''.join(data.xpath('//address/text()').extract()))
            city_ = normalize_clean(''.join(data.xpath('//city/text()').extract()))
            locality_latitude = normalize_clean(''.join(data.xpath(
                '//locality-latitude/text()').extract()))
            locality_longitude = normalize_clean(''.join(data.xpath(
                '//locality-longitude/text()').extract()))
            star_rating = ''.join(data.xpath('//star-rating/text()').extract())
            rating_agency_star = ''.join(data.xpath(
                '//hotel-rating[rating-agency[contains(text(), "SUPPLIER")]]/rating/text()').extract())
            hotel_amenities_final = []
            hotel_amenities = data.xpath('//hotel-amenities/hotel-amenity')
            for hame in hotel_amenities:
                h_name_category = ''.join(
                    hame.xpath('./category/text()').extract())
                h_name_amenity = ', '.join(hame.xpath(
                    './amenities/amenity/text()').extract())
                h_final_ac = '%s%s%s' % (
                    h_name_category, ' : ', h_name_amenity)
                hotel_amenities_final.append(h_final_ac)
            hotel_amenities_final = normalize_clean('<>'.join(hotel_amenities_final))
            hotel_description = ''.join(data.xpath(
                '//other-info/description/text()').extract())
            hotel_description = normalize_clean(re.sub('\<.*?\>', ' ',hotel_description))
            ct_item = ContentScore()
            ct_item.update({"sk":sk, "hotel_id":h_id, "hotel_name":h_name, "address":address, "city":city_, "locality_latitude":locality_latitude, "locality_longitude":locality_longitude, "star_rating":rating_agency_star, "description":hotel_description, "amenities":hotel_amenities_final, "reference_url":response.url, "html_hotel_url":hotel_url, "main_listing_url":main_url, "navigation_url":page_url})
            yield ct_item
        self.cursor.execute(
            "update %s_crawl set crawl_status=1 where sk = '%s'" % (self.name, sk))
