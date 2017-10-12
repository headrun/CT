from configobj import ConfigObj
import scrapy
from scrapy.selector import Selector
from scrapy.http import Request
import os
import json
import datetime
import time
import urllib
from Hotels.utils import *


def Strp_times(dx, los):
    date_ = datetime.datetime.now() + datetime.timedelta(days=int(dx))
    dx = date_.strftime('%m%d%Y')
    los_date = date_ + datetime.timedelta(days=int(los))
    los = los_date.strftime('%m%d%Y')
    return (dx, los)


def create_crawl_table_cursor():
    conn = MySQLdb.connect(host='localhost', user='root', db='urlqueue_dev', charset='utf8', use_unicode=True)
    cur = conn.cursor()
    return cur

class mytripspider(scrapy.Spider):
    name = 'Makemytrip_browse'
    handle_httpstatus_list = [400,404,500]
    allowed_domains = ['makemytrip.com', 'dtr-hoteldom.makemytrip.com']
    start_urls = ['https://www.makemytrip.com/hotels']
    
    def __init__(self, *args, **kwargs):
        super(mytripspider, self).__init__(*args, **kwargs)
        self.name='Makemytrip'
        self.cursor =create_mmt_table_cusor()
        ensure_mmt_table(self.cursor,self.name)
	drop_mmt_table(self.cursor,self.name)
        with open('SampleCITY.json') as json_data:
            self.d = json.load(json_data) 


    def parse(self, response):
        sel = Selector(response)
        cur = create_crawl_table_cursor()
        ensure_crawlmt_table(cur, self.name)
	drop_crawlmt_table(cur, self.name)
        dict_={}
        #timestamp = str(time.time()).replace('.', '')
        #payload = {'filters': {},'filterApplied': 'false','uiFilterOrClear': 'false','seoSemFilterApplied': 'false'}
        #headers = {'Content-Type': 'application/json'}
        config = ConfigObj('MmtConfig.cfg')
        #combinations_dict_Pax = {'1 Adult0 Child': '1e0e','2 Adult0 Child': '2e0e','3 Adult0 Child': '3e0e','2 Adult1 ChildChild Age = 8': '2e1e8e','2 Adult2 ChildChild Age = 88': '2e2e8e8e'}

        combinations_dict_Pax = {'2 Adult0 Child': '2e0e'}
        sectionall = config.sections
        for sectionbyone in sectionall:
            sections_ = config[sectionbyone]
            DX_num = sections_['Dx']
            LOS_num = sections_['LoS']
            PAX_val = ''.join(sections_['Pax'])
            pax,hotel_name,city_code,city_name,hotel_ids = '','','','',''
            dxs, loss = Strp_times(DX_num, LOS_num)
            if PAX_val in combinations_dict_Pax.keys():
                pax = combinations_dict_Pax[PAX_val]
                for city_name,hotel_id in self.d.iteritems():
                    for hotel_ids, hotel_details in hotel_id.iteritems():
                        hotel_ids=hotel_ids
                        city_name= city_name
                        city_code= hotel_details[1]
                        hotel_name =hotel_details[0]
                        if city_name!='' and city_code!='' and hotel_name!='' and hotel_ids!='':
                            sk = "_".join([city_name, str(DX_num), str(LOS_num), str(pax), hotel_ids])
                            urls='https://www.makemytrip.com/mmthtl/site/searchPriceNew?country=IN&city=%s&checkin=%s&checkout=%s&roomStayQualifier=%s&hotelId=%s&newListing=true'%(city_code,dxs,loss,pax,hotel_ids)
                            dict_.update({'sk': sk,'start_date': dxs,'dx': str(DX_num),'los': str(LOS_num),'pax': pax,'url': urls,
                            'crawl_type': 'keepup',   'crawl_status': '0','content_type': 'hotels','end_date': loss,'ccode': city_code,
                            'hotel_ids': hotel_ids,'hotel_name': hotel_name,'meta_data': json.dumps({'sk': city_name,'start_date': dxs,
                            'dx': str(DX_num),'los': str(LOS_num),'pax': pax,'url': urls,'end_date': loss,'ccode': city_code,
                            'hotel_ids': hotel_ids,'hotel_name': hotel_name})})
                            insert_crawlmt_tables_data(cur, self.name, dict_)
        
        cur.close()
        self.cursor.close()






                             





