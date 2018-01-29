import json
import scrapy
import MySQLdb
from scrapy.selector import Selector
from scrapy.http import Request
import datetime
import os
from Hotels.utils import *
from Hotels.auto_config import CLEARTRIP_HEADERS

def Strp_times(dx,los):
    date_=datetime.datetime.now() + datetime.timedelta(days=int(dx))
    dx = date_.strftime("%Y-%m-%d")
    los_date =date_ + datetime.timedelta(days=int(los))
    los=los_date.strftime("%Y-%m-%d")
    return dx,los

class ClearTripContent(scrapy.Spider):
    name = 'Cleartripcontentscore_browse'
    allowed_domains=['www.cleartrip.com']
    start_urls = []
    
    def __init__(self, Configfile='', *args,**kwargs):
        super(ClearTripContent,self).__init__(*args,**kwargs)
	self.check = kwargs.get('check','')
	self.city = kwargs.get('city', 'Bangalore')
	self.country = kwargs.get('country', 'IN')
        self.name ='Cleartripcontentscore'
	self.API = 'http://api.cleartrip.com/hotels/1.0/search?check-in=%s&check-out=%s&no-of-rooms=2&adults-per-room=2,1&children-per-room=1,0&city=%s&country=%s'
	self.cursor=create_crawl_table_cusor()
	self.dx, self.los = 0,1
	self.st,self.dt = Strp_times(self.dx, self.los)
	ensure_crawlct_table(self.cursor, self.name)
	drop_crawlct_table(self.cursor, self.name)
        self.metacursor=create_ct_table_cusor()
        #ensure_content_table(self.metacursor,self.name)
        drop_ct_table(self.metacursor, self.name)
	self.today_url = self.API % (self.st, self.dt, self.city, self.country)

    def start_requests(self):
	yield Request(self.today_url, callback = self.parse, headers = CLEARTRIP_HEADERS)
    
    def parse(self,response):
        data =  Selector(text=response.body)
	dict_={}
	hotels_nodes = data.xpath('//hotels/hotel')
	for hn_node in hotels_nodes:
		h_id = ''.join(hn_node.xpath('.//hotel-id/text()').extract())
		h_name = ''.join(hn_node.xpath('.//hotel-name/text()').extract())
		h_info_url = "https://api.cleartrip.com/places/hotels/info/%s" % h_id
		sk = "_".join([self.city, str(self.st), str(self.dt), str(h_id)])
		if h_id and h_name:
			dict_.update({'sk': sk,'start_date': str(self.st),'dx': str(self.dx),'los': str(self.los),'pax': '','url': h_info_url,'crawl_type': 'keepup','crawl_status': '0','content_type': 'hotels','end_date': str(self.dt),'h_name': normalize_clean(h_name),'h_id': normalize_clean(h_id),'meta_data': json.dumps({"url": self.today_url})})
		insert_crawlct_tables_data(self.cursor, self.name, dict_)
        self.cursor.close()
