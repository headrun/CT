import json
import scrapy
import MySQLdb
#from scrapy.spiders import Spider
from scrapy.selector import Selector
from scrapy.http import Request
import datetime
import os
from configobj import ConfigObj
from Hotels.utils import *



def Strp_times(dx,los):
    date_=datetime.datetime.now() + datetime.timedelta(days=int(dx))
    dx = date_.strftime("%d/%m/%Y")
    los_date =date_ + datetime.timedelta(days=int(los))
    los=los_date.strftime("%d/%m/%Y")
    return dx,los,


def create_crawl_table_cursor():
    conn = MySQLdb.connect(host='localhost', user='root', db='urlqueue_dev', charset='utf8', use_unicode=True)
    cur = conn.cursor()
    return cur
    


class ClearTrip(scrapy.Spider):
    name = 'Cleartrip_browse'
    allowed_domains=['www.cleartrip.com']
    start_urls = ['https://www.cleartrip.com/hotels']
    
    
    def __init__(self, Configfile='', *args,**kwargs):
        super(ClearTrip,self).__init__(*args,**kwargs)
        self.name ='Cleartrip'
	self.Configfile=Configfile
        self.cursor=create_ct_table_cusor()
        ensure_ct_table(self.cursor,self.name)
	drop_ct_table(self.cursor,self.name)
        with open('City_H_IDNS.json') as json_data:
            self.d = json.load(json_data)
            
            
    def parse(self,response):
        sel = Selector(response)
        cur = create_crawl_table_cursor()
        ensure_crawlct_table(cur, self.name)
	drop_crawlct_table(cur, self.name)
        dict_={}
        headers = {"Content-Type":"application/json"}
        #config = ConfigObj('MCGConfig.cfg')
	
        config = ConfigObj(self.Configfile)
#        combinations_dict_Pax={"1 Adult0 Child":{"Adult":"1","Child":"0","Age1":"0","Age2":"0"},"2 Adult0 Child":{"Adult":"2","Child":"0","Age1":"0","Age2":"0"},"3 Adult0 Child":{"Adult":"3","Child":"0","Age1":"0","Age2":"0"},"2 Adult1 ChildChild Age = 8":{"Adult":"2","Child":"1","Age1":"8","Age2":"0"},"2 Adult2 ChildChild Age = 88":{"Adult":"2","Child":"2","Age1":"8","Age2":"8"}}

        combinations_dict_Pax={"2 Adult0 Child":{"Adult":"2","Child":"0","Age1":"0","Age2":"0"}}
	#,"1 Adult0 Child":{"Adult":"1","Child":"0","Age1":"0","Age2":"0"}}
        sectionall=config.sections
        for sectionbyone in sectionall:
            sections_= config[sectionbyone]
            dx=sections_["Dx"]
            los=sections_["LoS"]
            paxses="".join(sections_["Pax"])
            st,dt = Strp_times(dx,los)
            paxs=''
            if paxses in combinations_dict_Pax.keys():
                pax= combinations_dict_Pax[paxses]
                adult = pax['Adult']
                child = pax['Child']
                age1 = pax['Age1']
                age2 = pax['Age2']
                paxs=adult+"e"+child+"e"+age1+"e"+age2+"e"
                
                for city_name,h_ids in self.d.iteritems():
                    for h_id,hotel_name in h_ids.iteritems():
                        if h_id and hotel_name:
                            sk = "_".join([city_name,str(dx), str(los), paxs, str(h_id)])
                            urls ='https://www.cleartrip.com/hotels/service/rate-calendar?chk_in=%s&chk_out=%s&num_rooms=1&adults1=%s&children1=%s&ca1=%s&cal1=%s&uiRank=1&fr=1&uiRankType=featured&stp=chmm&adults=%s&childs=%s&city=%s&cnm=%s&country=IN&ct_hotelid=%s&pahCCRequired=true'%(st,dt,adult,child,age1,age2,adult,child,city_name,city_name,h_id)
                            dict_.update({'sk': sk,'start_date': st,'dx': str(dx),'los': str(los),'pax': paxs,'url': urls,'crawl_type': 'keepup','crawl_status': '0','content_type': 'hotels','end_date': dt,'h_name':hotel_name,'h_id':h_id,'meta_data': json.dumps({'sk': city_name,'start_date': st,'dx': str(dx),'los': str(los),'pax': paxs,'url': urls,'end_date': dt,'h_name':hotel_name,'h_id':h_id})})
                        insert_crawlct_tables_data(cur, self.name, dict_)
        
        cur.close()
        self.cursor.close()






    
