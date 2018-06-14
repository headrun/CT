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


class CrawlCTreteriveapi(scrapy.Spider):
    name = "CLEARTRIPapi_terminal"
    handle_httpstatus_list=[400,404,500, 401]
    
    def __init__(self,*args,**kwargs):
        super(CrawlCTreteriveapi,self).__init__(*args,**kwargs)
        #settings.set('USER_AGENT_LIST', "['CTReportsFH (+http://www.cleartrip.com)']")
        #settings.set('BOT_NAME', 'CTReportsFH')
	self.check = kwargs.get('check','')
        self.name = 'Cleartrip'
	if self.check == 'dynamic':
		self.name = 'Cleartriponetime'
        self.log = create_logger_obj(self.name)
        self.crawl_type = kwargs.get('crawl_type','keepup')
        self.content_type = kwargs.get('content_type','hotels')
        self.limit = kwargs.get('limit', 1000)
        self.out_put_file =get_ctrip_file(self.name)
        self.cursor = create_crawl_table_cusor()
	self.headers = CLEARTRIP_HEADERS
        dispatcher.connect(self.spider_closed, signals.spider_closed)
    
    def spider_closed(self,spider):
        self.cursor.close()
        ct_crawlout_processing(self.out_put_file)
    
    def start_requests(self):
        headers = {'Content-Type': 'application/json'}
        rows = terminal_clear_requests(self.cursor, self.name, self.crawl_type, self.content_type, self.limit)
	if rows:
		for city_name, main_url, dx, los, pax, start_date, end_date, h_name, h_id in rows:
		    yield Request(
				  main_url, callback=self.parse_next_stage, headers = self.headers, 
				  meta = {'city_name':city_name.split('_')[0].strip(),'dx':dx,'los':los,'pax':pax,
				  'start_date':start_date,'end_date':end_date,'h_name':h_name,'h_id':h_id, 'sk_crawl':city_name, 'counter':1}
				 )

    def parse_next_stage(self,response):
	sk_crawl = response.meta.get('sk_crawl', '')
	city_name = response.meta.get('city_name','')
        dx = response.meta.get('dx','')
        los = response.meta.get('los','')
	pax = response.meta.get('pax','')
	adult = pax.split("e")[0]
	child = pax.split("e")[1]
	start_date = response.meta.get('start_date','')
	check_in = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m-%d')
	end_date = response.meta.get('end_date','')
	check_out = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y-%m-%d')
	h_name = response.meta.get('h_name','')
	h_id = response.meta.get('h_id','')
	rmtc, tax, totalamt, inclusions, b2cdiff, b2csplashed, roomtype, with_dis, without_dis,cancellation_policy ='', '', '0', '', '', '', '', '0', '0', 'NA'
            
        if response.status==200:
            data =  Selector(text=response.body)
	    hotels_check = data.xpath('//hotels//text()').extract()
	    child_node = data.xpath('//room-rate')
            if data:
		if not hotels_check:
		    if response.meta.get('counter', '') == 1:
			yield Request(response.url, callback=self.parse_next_stage, headers=self.headers, meta={'city_name': city_name,  'dx': dx, 'los': los, 'pax': pax, 'start_date': start_date, 'end_date': end_date, 'h_name': h_name, 'h_id': h_id, 'sk_crawl': city_name, 'counter': 2}, dont_filter=True)
		    else:
	        	ct_items = CTRIPItem()
        	        ct_items.update({'city':normalize(city_name),'cthotelname':normalize(h_name),'cthotelid':h_id,'check_in':check_in,
                	        'dx':dx,'los':los,'ctpax':adult,'ctroomtype':'CLOSED','ctrate':'Sold Out','ctb2cdiff':'NA','ctinclusions':'NA',
                        	'ctapprate':'NR', 'mobilediff':'NA','ctb2csplashedprice':'0','ctappsplashedprice':'0','ctb2ctaxes':'Sold Out',
	                        'ctapptaxes':'N/A','child':child, 'ctcouponcode':'N/A','ctcoupondescription':'N/A','ctcoupondiscount':'N/A',
        	                'rmtc':'CLOSED','check_out':check_out,})
                	yield ct_items
                else:
		    child_node = data.xpath('//room-rate')
                    try:
                        child_single_node= child_node[0]
                    except:
                        child_single_node = ''
		    if child_single_node:
			    rmtc = ''.join(child_single_node.xpath('.//room-type-code/text()').extract())
			    tax = ''.join(child_single_node.xpath('.//pricing-element[category[contains(text(), "TAX")]]/amount/text()').extract())
			    try:
				tax = str(int(round(float(tax))))
			    except:
				tax = '0'
			    inclusions = ', '.join(child_single_node.xpath('.//inclusion/text()').extract())
			    roomtype = ''.join(child_single_node.xpath('.//room-description/text()').extract())
			    totalamt = child_single_node.xpath('.//amount/text()').extract()
			    try:
				totalamt = str(int(round(sum([float(i) for i in data.xpath('//room-rate')[0].xpath('.//amount/text()').extract()]))))
			    except:
				totalamt = '0'
                            with_dis = child_single_node.xpath('.//pricing-element[category[contains(text(), "DIS")]]/amount/text()').extract()
                            try:
                                with_dis = str(int(round(sum([float(i) for i in with_dis])))).replace('-', '')
                            except:
                                with_dis = '0'

                            without_dis = child_single_node.xpath('.//pricing-element[category[not(contains(text(), "DIS"))]]/amount/text()').extract()
                            try:
                                without_dis = str(int(round(sum([float(i) for i in without_dis]))))
                            except:
                                without_dis = '0'
                            cancellation_policy = ', '.join(child_single_node.xpath('.//cancel-policy/text()').extract())

			
                    ct_items=CTRIPItem()
                    ct_items.update({'city':normalize(city_name),'cthotelname':normalize(h_name),'cthotelid':h_id,'check_in':check_in,
                        'dx':dx,'los':los,'ctpax':adult,'ctroomtype':normalize(roomtype), 'ctrate':totalamt,'ctb2cdiff':totalamt,
                        'ctinclusions':normalize_clean(inclusions),'ctapprate':'NR','mobilediff':'NA', 'ctb2csplashedprice':'0',
                        'ctappsplashedprice':'0','ctb2ctaxes':tax,'ctapptaxes':'N/A','child':child, 'ctcouponcode':'N/A',
                        'ctcoupondescription':'N/A','ctcoupondiscount':'N/A', 'rmtc':rmtc,'check_out':check_out, 'ctsell_price':without_dis, 'ctchmm_discount':with_dis, "cancellation_policy":normalize_clean(cancellation_policy)})
                    yield ct_items
            
            else:
                ct_items=CTRIPItem()
                ct_items.update({'city':normalize(city_name),'cthotelname':normalize(h_name),'cthotelid':h_id,'check_in':check_in,
                'dx':dx,'los':los,'ctpax':adult,'ctroomtype':'N/A','ctrate':'NR','ctb2cdiff':'NA','ctinclusions':'NA','ctapprate':'NR',
                'mobilediff':'NA','ctb2csplashedprice':'0','ctappsplashedprice':'0','ctb2ctaxes':'N/A','ctapptaxes':'N/A','child':child,
                'ctcouponcode':'N/A','ctcoupondescription':'N/A', 'ctcoupondiscount':'N/A','rmtc':'N/A', 'check_out':check_out,"cancellation_policy":normalize_clean(cancellation_policy)})
                yield ct_items

        else:
            ct_items=CTRIPItem()
            ct_items.update({'city':normalize(city_name),'cthotelname':normalize(h_name),'cthotelid':h_id,'check_in':check_in,
                'dx':dx,'los':los,'ctpax':adult,'ctroomtype':'N/A','ctrate':'NR','ctb2cdiff':'NA','ctinclusions':'NA','ctapprate':'NR',
                'mobilediff':'NA','ctb2csplashedprice':'0','ctappsplashedprice':'0','ctb2ctaxes':'N/A','ctapptaxes':'N/A','child':child,
                'ctcouponcode':'N/A','ctcoupondescription':'N/A', 'ctcoupondiscount':'N/A','rmtc':'N/A', 'check_out':check_out,"cancellation_policy":normalize_clean(cancellation_policy)})
            yield ct_items
	self.cursor.execute("update %s_crawl set crawl_status=1 where sk = '%s'" % (self.name, sk_crawl))
