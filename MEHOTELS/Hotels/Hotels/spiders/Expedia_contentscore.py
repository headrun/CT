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

class ExpediaContent(scrapy.Spider):
    name = 'Expediacontentscore_browse'
    start_urls = []

    def __init__(self, Configfile='', *args, **kwargs):
        super(ExpediaContent, self).__init__(*args, **kwargs)
        self.check = kwargs.get('check', '')
        self.today_url_list = [('https://www.expedia.com/All-Dubai-Hotels.d1079.Travel-Guide-City-All-Hotels', 'Dubai'),('https://www.expedia.com/All-Istanbul-Hotels.d178267.Travel-Guide-City-All-Hotels', 'Istanbul'), ('https://www.expedia.com/All-Abu-Dhabi-Hotels.d6053838.Travel-Guide-City-All-Hotels', 'Abu Dhabi'), ('https://www.expedia.com/All-Mecca-Hotels.d178043.Travel-Guide-City-All-Hotels', 'Mecca'), ('https://www.expedia.com/All-Medina-Hotels.d602705.Travel-Guide-City-All-Hotels', 'Medina'), ('https://www.expedia.com/All-Manama-Hotels.d490.Travel-Guide-City-All-Hotels', 'Manama'), ('https://www.expedia.com/All-Singapore-Hotels.d180027.Travel-Guide-City-All-Hotels', 'Singapore'), ('https://www.expedia.com/All-Jeddah-Hotels.d1680.Travel-Guide-City-All-Hotels', 'Jeddah'), ('https://www.expedia.com/All-Muscat-Hotels.d2238.Travel-Guide-City-All-Hotels', 'Muscat'), ('https://www.expedia.com/All-Salalah-Hotels.d6132442.Travel-Guide-City-All-Hotels', 'Salalah'), ('https://www.expedia.com/All-Doha-Hotels.d1048.Travel-Guide-City-All-Hotels', 'Doha'), ('https://www.expedia.com/All-Riyadh-Hotels.d3051.Travel-Guide-City-All-Hotels', 'Riyadh')]
        self.name = 'Expediacontentscore'
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
            yield Request(tda[0], callback=self.parse, meta = {"city_name":tda[1], "hotel_main_url":tda[0]})

    def parse(self, response):
        city_name = response.meta.get('city_name', '')
        hotel_main_url = response.meta.get('hotel_main_url', '')
        dict_ = {}
        sel = Selector(response)
        nodes = sel.xpath('//ul[contains(@id, "links-container")]//li')
        for nod in nodes:
            hotel_url = nod.xpath('.//a/@href').extract_first()
            if hotel_url:
                hotel_url = "%s%s" % ("https://www.expedia.com", hotel_url)
            h_name = nod.xpath('./self::li/@data-name').extract_first()
            h_id = ''.join(re.findall('\d+', hotel_url))
            if h_id and h_name:
                dict_.update(
                    {'sk': str(h_id), 'start_date': '', 'dx': '', 'los': '', 'pax': '', 'url': hotel_url, 'crawl_type': 'keepup', 'crawl_status': '0',
                     'content_type': 'hotels', 'end_date': '', 'h_name': normalize_clean(h_name), 'h_id': normalize_clean(h_id), 'meta_data': json.dumps({"main_url": hotel_main_url, "hotel_url":hotel_url, "page_url":response.url, "city_name":city_name})})
            insert_crawlct_tables_data(self.cursor, self.name, dict_)
        next_page = sel.xpath('//nav/a[contains(text(), "Next")]/@href').extract_first()
        if next_page:
            next_page = "%s%s" % ("https://www.expedia.com", next_page)
            yield Request(next_page, callback=self.parse, meta = {"city_name":city_name, "hotel_main_url":hotel_main_url})
