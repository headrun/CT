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

class BookingContent(scrapy.Spider):
    name = 'Bookingcontentscore_browse'
    start_urls = []

    def __init__(self, Configfile='', *args, **kwargs):
        super(BookingContent, self).__init__(*args, **kwargs)
        self.check = kwargs.get('check', '')
        self.today_url_list = [('https://www.booking.com/searchresults.en-gb.html?label=gen173nr-1DCAIobEICaW5ICVgEaGyIAQGYAS7CAQN4MTHIAQzYAQPoAQH4AQKSAgF5qAID;sid=5bfeee87b8bf9510a0a35115add5729c;city=-782831', 'Dubai'),('https://www.booking.com/searchresults.en-gb.html?aid=357026;label=gog235jc-city-XX-tr-istanbul-unspec-in-com-L%3Aen-O%3Ax11-B%3Achrome-N%3Ayes-S%3Abo-U%3Asalo-H%3As;sid=5bfeee87b8bf9510a0a35115add5729c;city=-755070', 'Istanbul'), ('https://www.booking.com/searchresults.en-gb.html?label=gen173nr-1DCAIobEICaW5ICVgEaGyIAQGYAS7CAQN4MTHIAQzYAQPoAQH4AQKSAgF5qAID;sid=5bfeee87b8bf9510a0a35115add5729c;city=-782066', 'Abu Dhabi'), ('https://www.booking.com/searchresults.en-gb.html?aid=357026;label=gog235jc-city-XX-sa-mecca-unspec-in-com-L%3Aen-O%3Ax11-B%3Achrome-N%3Ayes-S%3Abo-U%3Asalo-H%3As;sid=5bfeee87b8bf9510a0a35115add5729c;city=-3096949', 'Mecca'), ('https://www.booking.com/searchresults.en-gb.html?aid=357026;label=gog235jc-searchresults-XX-XX-city_N3092186-unspec-in-com-L%3Aen-O%3Ax11-B%3Achrome-N%3AXX-S%3Abo-U%3Ao-H%3As;sid=5bfeee87b8bf9510a0a35115add5729c;city=-3092186&class_interval=1&dest_id=-3092186&dest_type=city&dtdisc=0&inac=0&index_postcard=0&label_click=undef&offset=0&postcard=0&room1=A%2CA&sb_price_type=total&ss_all=0&ssb=empty&sshis=0&', 'Medina'), ('https://www.booking.com/searchresults.en-gb.html?aid=357026;label=gog235jc-city-XX-bh-manama-unspec-in-com-L%3Aen-O%3Ax11-B%3Achrome-N%3Ayes-S%3Abo-U%3Asalo-H%3As;sid=5bfeee87b8bf9510a0a35115add5729c;city=-784833', 'Manama'), ('https://www.booking.com/searchresults.en-gb.html?aid=357026;label=gog235jc-searchresults-XX-XX-city_N73635-unspec-in-com-L%3Aen-O%3Ax11-B%3Achrome-N%3AXX-S%3Abo-U%3Ao-H%3As;sid=5bfeee87b8bf9510a0a35115add5729c;city=-73635&class_interval=1&dest_id=-73635&dest_type=city&dtdisc=0&inac=0&index_postcard=0&label_click=undef&offset=0&postcard=0&room1=A%2CA&sb_price_type=total&ss_all=0&ssb=empty&sshis=0&', 'Singapore'), ('https://www.booking.com/searchresults.en-gb.html?aid=357026;label=gog235jc-landmark-XX-sa-jeddahNcorniche-unspec-in-com-L%3Aen-O%3Ax11-B%3Achrome-N%3Ayes-S%3Abo-U%3Asalo-H%3As;sid=5bfeee87b8bf9510a0a35115add5729c;dest_id=-3096108;dest_type=city;ss=Jeddah&', 'Jeddah'), ('https://www.booking.com/searchresults.en-gb.html?aid=357026;label=gog235jc-city-XX-om-muscat-unspec-in-com-L%3Aen-O%3Ax11-B%3Achrome-N%3Ayes-S%3Abo-U%3Asalo-H%3As;sid=5bfeee87b8bf9510a0a35115add5729c;city=-787987', 'Muscat'), ('https://www.booking.com/searchresults.en-gb.html?aid=357026;label=gog235jc-city-XX-om-salalah-unspec-in-com-L%3Aen-O%3Ax11-B%3Achrome-N%3Ayes-S%3Abo-U%3Asalo-H%3As;sid=5bfeee87b8bf9510a0a35115add5729c;city=-788664', 'Salalah'), ('https://www.booking.com/searchresults.en-gb.html?aid=357026;label=gog235jc-city-XX-qa-doha-unspec-in-com-L%3Aen-O%3Ax11-B%3Achrome-N%3Ayes-S%3Abo-U%3Asalo-H%3As;sid=5bfeee87b8bf9510a0a35115add5729c;city=-785169', 'Doha'), ('https://www.booking.com/searchresults.en-gb.html?aid=357026;label=gog235jc-city-XX-sa-riyadhNsa-unspec-in-com-L%3Aen-O%3Ax11-B%3Achrome-N%3Ayes-S%3Abo-U%3Asalo-H%3As;sid=5bfeee87b8bf9510a0a35115add5729c;city=900040280', 'Riyadh')]
        self.name = 'Bookingcontentscore'
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
        sel = Selector(response)
        city_name = response.meta.get('city_name', '')
        hotel_main_url = response.meta.get('hotel_main_url', '')
        dict_ = {}
        City_Hotels = sel.xpath('//div[@data-block-id="hotel_list"]//div[@data-hotelid]')
        for hotels in City_Hotels:
            h_id = ''.join(hotels.xpath('.//self::div/@data-hotelid').extract())
            h_name = ''.join(hotels.xpath('.//span[contains(@class, "sr-hotel__name")]//text()').extract()).replace('\n', '').strip()
            hotel_url = ''.join(hotels.xpath('.//a[@class="hotel_name_link url"]/@href').extract()).replace('\n', '')
            if hotel_url:
                hotel_url = "%s%s" % ('https://www.booking.com', hotel_url)
            if h_id and h_name:
                dict_.update(
                    {'sk': str(h_id), 'start_date': '', 'dx': '', 'los': '', 'pax': '', 'url': hotel_url, 'crawl_type': 'keepup', 'crawl_status': '0',
                     'content_type': 'hotels', 'end_date': '', 'h_name': normalize_clean(h_name), 'h_id': normalize_clean(h_id), 'meta_data': json.dumps({"main_url": hotel_main_url, "hotel_url":hotel_url, "page_url":response.url, "city_name":city_name})})
            insert_crawlct_tables_data(self.cursor, self.name, dict_)
        next_page = sel.xpath('//li[@class="sr_pagination_item current"]/following-sibling::li[1]/a/@href').extract_first()
        if next_page:
            if 'booking.com' not in next_page:
                next_page = "%s%s" % ("https://www.booking.com", next_page)
            yield Request(next_page, callback=self.parse, meta = {"city_name":city_name, "hotel_main_url":hotel_main_url})
