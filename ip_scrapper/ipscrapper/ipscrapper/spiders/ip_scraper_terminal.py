import json
import scrapy
import MySQLdb
import logging
from scrapy import log
from scrapy import signals
from scrapy.selector import Selector
from scrapy.http import Request
from ipscrapper.utils import *
from ipscrapper.items import *
from datetime import datetime, timedelta
from scrapy.xlib.pydispatch import dispatcher
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class Ipscraperterminal(scrapy.Spider):
    name = 'ipscraper_terminal'
    start_urls = ['https://www.cleartrip.com/']
    
    def __init__(self, *args,**kwargs):
        super(Ipscraperterminal,self).__init__(*args,**kwargs)
	self.log = create_logger_obj(self.name)
	self.cursor = create_ct_table_cusor()
	self.name = 'ipmeta'
        self.crawl_type = kwargs.get('crawl_type','keepup')
        self.content_type = kwargs.get('content_type','ip')
        self.limit = kwargs.get('limit', 1000)
	self.out_put_file =get_gobtrip_file(self.name)
	dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self,spider):
        self.cursor.close()
        gob_crawlout_processing(self.out_put_file)

    def parse(self, response):
	rows = terminal_ip_requests(self.cursor, 'ip_crawl', self.crawl_type, self.content_type, self.limit)
	for row in rows:
		yield Request(row[1], callback=self.parse_next, meta = {"sk":row[0]})

    def parse_next(self, response):
	sel = Selector(response)
	vs = sel.xpath('//td[@class="myipaddress"]')
	continent = ''.join(vs.xpath('.//tr[th[contains(text(), "Continent:")]]/td//text()').extract())
	country = ''.join(vs.xpath('.//tr[th[contains(text(), "Country:")]]/td//text()').extract())
	capital = ''.join(vs.xpath('.//tr[th[contains(text(), "Capital:")]]/td//text()').extract())
	city_location = ''.join(vs.xpath('.//tr[th[contains(text(), "City Location")]]/td//text()').extract())
	isp = ''.join(vs.xpath('.//tr[th[contains(text(), "ISP:")]]/td//text()').extract())
	ip_items = IpItem()
	ip_items.update({'ip':normalize_clean(response.meta.get('sk', '')),'continent':normalize_clean(continent),'country':normalize_clean(country),'capital': normalize_clean(capital),'city_location':normalize_clean(city_location),'isp':normalize_clean(isp), 'is_csvrun':'no','reference_url':normalize_clean(response.url)})
        yield ip_items
