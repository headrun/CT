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

class CrawlCTreterive(scrapy.Spider):
    name = "CLEARTRIP_terminal"
    handle_httpstatus_list=[400,404,500]
    start_urls=['https://www.cleartrip.com/hotels']
    
    def __init__(self,*args,**kwargs):
        super(CrawlCTreterive,self).__init__(*args,**kwargs)
        self.name = 'Cleartrip'
        self.log = create_logger_obj(self.name)
        self.crawl_type = kwargs.get('crawl_type','keepup')
        self.content_type = kwargs.get('content_type','hotels')
        self.limit = kwargs.get('limit', 1000)
        self.out_put_file =get_ctrip_file(self.name)
        self.cursor = create_crawl_table_cusor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)
    
    def spider_closed(self,spider):
        self.cursor.close()
        ct_crawlout_processing(self.out_put_file)
    
    def parse(self,response):
        headers = {'Content-Type': 'application/json'}
        rows = terminal_clear_requests(self.cursor, self.name, self.crawl_type, self.content_type, self.limit)
        for city_name, main_url, dx, los, pax, start_date, end_date, h_name, h_id in rows:
            yield Request(
                          main_url, callback=self.parse_next_stage, headers = headers, 
                          meta = {'city_name':city_name.split('_')[0].strip(),'dx':dx,'los':los,'pax':pax,
                          'start_date':start_date,'end_date':end_date,'h_name':h_name,'h_id':h_id}
                         )

    def parse_next_stage(self,response):
	city_name = response.meta.get('city_name','')
        dx = response.meta.get('dx','')
        los = response.meta.get('los','')
	pax = response.meta.get('pax','')
	adult = pax.split("e")[0]
	child = pax.split("e")[1]
	start_date = response.meta.get('start_date','')
	check_in = datetime.datetime.strptime(start_date, '%d/%m/%Y').strftime('%Y-%m-%d')
	end_date = response.meta.get('end_date','')
	check_out = datetime.datetime.strptime(end_date, '%d/%m/%Y').strftime('%Y-%m-%d')
	h_name = response.meta.get('h_name','')
	h_id = response.meta.get('h_id','')
	rmtc, tax, totalamt, inclusions, b2cdiff, b2csplashed, roomtype='', '', '0', '', '', '', ''
            
        if response.status==200:
            data = json.loads(response.body)
            if data and data!='':
                soldout = "".join(data.keys())
                if "sold_out" in soldout:
                    ct_items = CTRIPItem()
                    ct_items.update({'city':normalize(city_name),'cthotelname':normalize(h_name),'cthotelid':h_id,'check_in':check_in,
                        'dx':dx,'los':los,'ctpax':adult,'ctroomtype':'CLOSED','ctrate':'Sold Out','ctb2cdiff':'NA','ctinclusions':'NA',
                        'ctapprate':'NR', 'mobilediff':'NA','ctb2csplashedprice':'0','ctappsplashedprice':'0','ctb2ctaxes':'Sold Out',
                        'ctapptaxes':'N/A','child':child, 'ctcouponcode':'N/A','ctcoupondescription':'N/A','ctcoupondiscount':'N/A',
                        'rmtc':'CLOSED','check_out':check_out,})
                    yield ct_items

                elif 'error' in data.keys():
                    ct_items = CTRIPItem()
                    ct_items.update({'city':normalize(city_name),'cthotelname':normalize(h_name),'cthotelid':h_id,'check_in':check_in,
                        'dx':dx,'los':los,'ctpax':adult,'ctroomtype':'N/A','ctrate':'NR','ctb2cdiff':'NA','ctinclusions':'NA',
                        'ctapprate':'NR', 'mobilediff':'NA','ctb2csplashedprice':'0','ctappsplashedprice':'0','ctb2ctaxes':'N/A',
                        'ctapptaxes':'N/A','child':child, 'ctcouponcode':'N/A','ctcoupondescription':'N/A','ctcoupondiscount':'N/A',
                        'rmtc':'N/A','check_out':check_out,})
                    yield ct_items

                else:
                    main_node = data.get("rc",{})
                    parent_node = main_node.get("d0",{})
                    child_node = parent_node.get("rms",{})
                    try:
                        child_single_node= child_node[0]
                    except:
                        import pdb;pdb.set_trace()
                    rmtc = child_single_node.get('rmtc','')
                    tax = child_single_node.get('t','')
                    inclusions = child_single_node.get('i','')
                    roomtype = child_single_node.get('rm','')
                    b2cdiff = child_single_node.get('d','')
                    b2csplashed = child_single_node.get('agvo','')
                    totalamt = child_single_node.get('tot','')

                    ct_items=CTRIPItem()
                    ct_items.update({'city':normalize(city_name),'cthotelname':normalize(h_name),'cthotelid':h_id,'check_in':check_in,
                        'dx':dx,'los':los,'ctpax':adult,'ctroomtype':normalize(roomtype), 'ctrate':totalamt,'ctb2cdiff':totalamt,
                        'ctinclusions':normalize(inclusions),'ctapprate':'NR','mobilediff':'NA', 'ctb2csplashedprice':'0',
                        'ctappsplashedprice':'0','ctb2ctaxes':tax,'ctapptaxes':'N/A','child':child, 'ctcouponcode':'N/A',
                        'ctcoupondescription':'N/A','ctcoupondiscount':'N/A', 'rmtc':rmtc,'check_out':check_out,})
                    yield ct_items
            
            else:
                ct_items=CTRIPItem()
                ct_items.update({'city':normalize(city_name),'cthotelname':normalize(h_name),'cthotelid':h_id,'check_in':check_in,
                'dx':dx,'los':los,'ctpax':adult,'ctroomtype':'N/A','ctrate':'NR','ctb2cdiff':'NA','ctinclusions':'NA','ctapprate':'NR',
                'mobilediff':'NA','ctb2csplashedprice':'0','ctappsplashedprice':'0','ctb2ctaxes':'N/A','ctapptaxes':'N/A','child':child,
                'ctcouponcode':'N/A','ctcoupondescription':'N/A', 'ctcoupondiscount':'N/A','rmtc':'N/A', 'check_out':check_out,})
                yield ct_items

        else:
            ct_items=CTRIPItem()
            ct_items.update({'city':normalize(city_name),'cthotelname':normalize(h_name),'cthotelid':h_id,'check_in':check_in,
                'dx':dx,'los':los,'ctpax':adult,'ctroomtype':'N/A','ctrate':'NR','ctb2cdiff':'NA','ctinclusions':'NA','ctapprate':'NR',
                'mobilediff':'NA','ctb2csplashedprice':'0','ctappsplashedprice':'0','ctb2ctaxes':'N/A','ctapptaxes':'N/A','child':child,
                'ctcouponcode':'N/A','ctcoupondescription':'N/A', 'ctcoupondiscount':'N/A','rmtc':'N/A', 'check_out':check_out,})
            yield ct_items

           
        


        
