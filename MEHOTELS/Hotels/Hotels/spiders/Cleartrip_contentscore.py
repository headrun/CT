import json
import scrapy
import MySQLdb
from scrapy.selector import Selector
from scrapy.http import Request
import datetime
import os
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from Hotels.utils import *
from Hotels.auto_config import CLEARTRIP_HEADERS

class ClearTripContent(scrapy.Spider):
    name = 'Cleartripcontentscore_browse'
    allowed_domains = ['www.cleartrip.com']
    handle_httpstatus_list = [400]
    start_urls = []

    def __init__(self, Configfile='', *args, **kwargs):
        super(ClearTripContent, self).__init__(*args, **kwargs)
        self.check = kwargs.get('check', '')
        self.today_url_list = [('https://www.cleartrip.com/hotels/united-arab-emirates/dubai/', 'Dubai'), ('https://www.cleartrip.com/hotels/turkey/istanbul/', 'Istanbul'), ('https://www.cleartrip.com/hotels/united-arab-emirates/abu-dhabi/', 'Abu Dhabi'), ('https://www.cleartrip.com/hotels/saudi-arabia/mecca/', 'Mecca'), ('https://www.cleartrip.com/hotels/saudi-arabia/medina/', 'Medina'), ('https://www.cleartrip.com/hotels/bahrain/manama/', 'Manama'), ('https://www.cleartrip.com/hotels/singapore/singapore/', 'Singapore'),('https://www.cleartrip.com/hotels/saudi-arabia/jeddah/', 'Jeddah'), ('https://www.cleartrip.com/hotels/oman/muscat/', 'Muscat'), ('https://www.cleartrip.com/hotels/oman/salalah/', 'Salalah'), ('https://www.cleartrip.com/hotels/qatar/doha/', 'Doha'), ('https://www.cleartrip.com/hotels/saudi-arabia/riyadh/', 'Riyadh')]
        self.name = 'Cleartripcontentscore'
        self.cursor = create_crawl_table_cusor()
        ensure_crawlct_table(self.cursor, self.name)
        drop_crawlct_table(self.cursor, self.name)
        self.metacursor = create_ct_table_cusor()
        ensure_content_table(self.metacursor,self.name)
        drop_ct_table(self.metacursor, self.name)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self,spider):
        self.cursor.close()

    def start_requests(self):
        for tda in self.today_url_list:
            yield Request(tda[0], callback=self.parse, headers=CLEARTRIP_HEADERS, meta = {"city_name":tda[1], "hotel_main_url":tda[0]})

    def parse(self, response):
        city_name = response.meta.get('city_name', '')
        hotel_main_url = response.meta.get('hotel_main_url', '')
        dict_ = {}
        sel = Selector(response)
        nodes = sel.xpath('//div[@id="hotelsList"]/div[contains(@class, "hotelUnit normal-view ")]')
        for nod in nodes:
            hotel_url = nod.xpath('.//li[@class="hotelNamelink"]//a/@href').extract_first()
            if hotel_url:
                hotel_url = "%s%s" % ("https://www.cleartrip.com", hotel_url)
            h_name = nod.xpath('.//li[@class="hotelNamelink"]//a/@title').extract_first()
            h_id = hotel_url.split('-')[-1].replace('/', '')
            h_info_url = "https://api.cleartrip.com/places/hotels/info/%s" % h_id
            if h_id and h_name:
                dict_.update(
                    {'sk': str(h_id), 'start_date': '', 'dx': '', 'los': '', 'pax': '', 'url': h_info_url, 'crawl_type': 'keepup', 'crawl_status': '0',
                     'content_type': 'hotels', 'end_date': '', 'h_name': normalize_clean(h_name), 'h_id': normalize_clean(h_id), 'meta_data': json.dumps({"main_url": hotel_main_url, "hotel_url":hotel_url, "page_url":response.url, "city_name":city_name})})
            insert_crawlct_tables_data(self.cursor, self.name, dict_)
        next_page = sel.xpath('//a[@class="next_page"]/@href').extract_first()
        if next_page:
            next_page = "%s%s" % ("https://www.cleartrip.com", next_page)
            yield Request(next_page, callback=self.parse, headers=CLEARTRIP_HEADERS, meta = {"city_name":city_name, "hotel_main_url":hotel_main_url})
