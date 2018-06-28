from configobj import ConfigObj
import scrapy
from scrapy.selector import Selector
from scrapy.http import Request
from scrapy.http import FormRequest
import os
import json
import datetime
import time
import urllib
from Hotels.utils import *
from Hotels.blacklist_properties import total_blacklist_properties


def Strp_times(dx, los):
    date_ = datetime.datetime.now() + datetime.timedelta(days=int(dx))
    dx = date_.strftime('%Y%m%d')
    los_date = date_ + datetime.timedelta(days=int(los))
    los = los_date.strftime('%Y%m%d')
    return (dx, los)

def create_crawl_table_cursor():
    conn = MySQLdb.connect(host='localhost', user='root', db=PROD_DB_NAME, charset='utf8', use_unicode=True, passwd=DB_PASSWORD)
    cur = conn.cursor()
    return cur


class goibibospider(scrapy.Spider):
    name = 'Goibibotrip_browse'
    handle_httpstatus_list = [400,404,500,503]
    allowed_domains = ['www.goibibo.com', 'hermes.goibibo.com']
    start_urls = ['https://www.goibibo.com/hotels/']

    def __init__(self, *args, **kwargs):
        super(goibibospider, self).__init__(*args, **kwargs)
        self.name='Goibibotrip'
        self.cursor =create_mmt_table_cusor()
        ensure_gob_table(self.cursor,self.name)
	drop_gob_table(self.cursor,self.name)
	with open('GoiboCity_codes.json') as json_data:
		self.d = json.load(json_data)
        self.mmt_ct_ids_list_check = []
        with open('SampleCITY.json') as json_data11:
            self.dsample = json.load(json_data11)
            for d_city_name, d_hotel_id in self.dsample.iteritems():
                for d_hotel_ids, d_hotel_details in d_hotel_id.iteritems():
                    ct_mmt_id = d_hotel_details[2]
                    self.mmt_ct_ids_list_check.append(ct_mmt_id)



    def parse(self, response):
        sel = Selector(response)
	dict_={}
        cur = create_crawl_table_cursor()
        ensure_crawlgb_table(cur, self.name)
	drop_crawlgb_table(cur, self.name)
	#combinations_dict_Pax = {'1':'1-1_0','2':'1-2_0'}
	
	combinations_dict_Pax = {'2 Adult0 Child':'1-2_0'}
	config = ConfigObj('GoiConfig.cfg')
        sectionall = config.sections
        for sectionbyone in sectionall:
                sections_ = config[sectionbyone]
                DX_num = sections_['Dx']
                LOS_num = sections_['LoS']
                PAX_val = ''.join(sections_['Pax'])
		pax,hotel_name,city_code,city_name,hotel_id = '','','','',''
		dxs, loss = Strp_times(DX_num, LOS_num)
		if PAX_val in combinations_dict_Pax.keys():
			pax = combinations_dict_Pax[PAX_val]
			for city_name,hotel_details in self.d.iteritems():
				city_name=city_name
				for hotel_id,hotel_data in hotel_details.iteritems():
					hotel_id=hotel_id
					hotel_name=hotel_data[0]
					city_code=hotel_data[1]
					ct_goi_id = hotel_data[2]
					if city_code is not None and city_code!='' and city_name!='' and (ct_goi_id not in total_blacklist_properties) and (ct_goi_id not in self.mmt_ct_ids_list_check):
						sk = "_".join([city_name,str(DX_num),str(LOS_num),str(pax),hotel_id])
						city_code=city_code.strip(" ")
						hotel_id=hotel_id.strip(" ")
						hotel_name=hotel_name.strip(" ")
						city_name=city_name.strip(" ")
						urls ='https://hermes.goibibo.com/hotels/v6/detail/price/v3/%s/%s/%s/%s/%s?ibp=v3'%(city_code,dxs,loss,pax,hotel_id)
						dict_.update({'sk': sk,'start_date': dxs,'dx': str(DX_num),'los': str(LOS_num),'pax': str(pax),
						'url': urls, 'crawl_type': 'keepup', 'crawl_status': '0','content_type': 'hotels',
						'end_date': loss, 'ccode': city_code, 'hotel_ids': hotel_id,'hotel_name': hotel_name,
						'meta_data': json.dumps({'sk': city_name,'start_date': dxs,'dx': str(DX_num),
						'los': str(LOS_num),'pax': pax,'url': urls,'end_date': loss,'ccode': city_code,
						'hotel_ids': hotel_id,'hotel_name': hotel_name, "ct_id":str(ct_goi_id)}),'aux_info':json.dumps({'city_code':city_code,
						'dxs':dxs,'loss':loss,'pax':pax,'hotel_id':hotel_id}),'reference_url':urls,})
						insert_crawlgb_tables_data(cur, self.name, dict_) 
	
	cur.close()
	self.cursor.close()


	



	   

