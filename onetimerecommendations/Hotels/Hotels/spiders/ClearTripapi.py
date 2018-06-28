import json
import scrapy
import MySQLdb
from scrapy.selector import Selector
from scrapy.http import Request
import datetime
import os
from configobj import ConfigObj
from Hotels.utils import *
from Hotels.blacklist_properties import total_blacklist_properties


def Strp_times(dx, los):
    date_ = datetime.datetime.now() + datetime.timedelta(days=int(dx))
    dx = date_.strftime("%Y-%m-%d")
    los_date = date_ + datetime.timedelta(days=int(los))
    los = los_date.strftime("%Y-%m-%d")
    return dx, los,


def create_crawl_table_cursor():
    conn = MySQLdb.connect(host='localhost', user='root', db=PROD_DB_NAME,
                           charset='utf8', use_unicode=True, passwd=DB_PASSWORD)
    cur = conn.cursor()
    return cur


class ClearTripAPI(scrapy.Spider):
    name = 'Cleartripapi_browse'
    # allowed_domains=['www.cleartrip.com']
    start_urls = ['https://www.cleartrip.com/hotels']

    def __init__(self, Configfile='', *args, **kwargs):
        super(ClearTripAPI, self).__init__(*args, **kwargs)
        #settings.set('USER_AGENT_LIST', "['CTReportsFH (+http://www.cleartrip.com)']")
        #settings.set('BOT_NAME', 'CTReportsFH')
        self.check = kwargs.get('check', '')
        self.name = 'Cleartrip'
        json_file_name = 'City_H_IDNS.json'
        if self.check == 'dynamic':
            self.name = 'Cleartriponetime'
            json_file_name = 'City_H_IDNSdynamic.json'
        self.Configfile = Configfile
        self.cursor = create_ct_table_cusor()
        ensure_ct_table(self.cursor, self.name)
        drop_ct_table(self.cursor, self.name)
        with open(json_file_name) as json_data:
            self.d = json.load(json_data)

    def parse(self, response):
        sel = Selector(response)
        cur = create_crawl_table_cursor()
        ensure_crawlct_table(cur, self.name)
        drop_crawlct_table(cur, self.name)
        dict_ = {}
        headers = {"Content-Type": "application/json"}
        config = ConfigObj(self.Configfile)
        """combinations_dict_Pax = {"2 Adult0 Child": {
            "Adult": "2", "Child": "0", "Age1": "0", "Age2": "0"}}"""
        combinations_dict_Pax={"2 Adult2 Child":{"Adult":"2","Child":"2","Age1":"0","Age2":"0"}, "3 Adult0 Child":{"Adult":"3","Child":"0","Age1":"0","Age2":"0"}, "3 Adult1 Child":{"Adult":"3","Child":"1","Age1":"0","Age2":"0"}, "4 Adult0 Child":{"Adult":"4","Child":"0","Age1":"0","Age2":"0"}}
        sectionall = config.sections
        for sectionbyone in sectionall:
            sections_ = config[sectionbyone]
            dx = sections_["Dx"]
            los = sections_["LoS"]
            paxses = "".join(sections_["Pax"])
            st, dt = Strp_times(dx, los)
            paxs = ''
            if paxses in combinations_dict_Pax.keys():
                pax = combinations_dict_Pax[paxses]
                adult = pax['Adult']
                child = pax['Child']
                age1 = pax['Age1']
                age2 = pax['Age2']
                paxs = adult+"e"+child+"e"+age1+"e"+age2+"e"

                for city_name, h_ids in self.d.iteritems():
                    for h_id, hotel_name in h_ids.iteritems():
                        if h_id and hotel_name and h_id not in total_blacklist_properties:
                            sk = "_".join(
                                [city_name, str(dx), str(los), paxs, str(h_id)])
                            #urls = "http://api.cleartrip.com/hotels/1.0/search?check-in=%s&check-out=%s&no-of-rooms=1&adults-per-room=%s&children-per-room=%s&city=%s&country=IN&scr=INR&sct=IN&ct_hotelid=%s" % (st, dt, adult, child, city_name, h_id)
                            if int(child) ==0:
                                    urls = "http://meta.cleartrip.com/hotels/1.0/search?check-in=%s&check-out=%s&no-of-rooms=1&adults-per-room=%s&children-per-room=%s&city=%s&country=IN&scr=INR&sct=IN&ct_hotelid=%s" % (st, dt, adult, child, city_name, h_id)
                            elif int(child) ==1:
                                    urls = "http://meta.cleartrip.com/hotels/1.0/search?check-in=%s&check-out=%s&no-of-rooms=1&adults-per-room=%s&children-per-room=%s&ca1=11&city=%s&country=IN&scr=INR&sct=IN&ct_hotelid=%s" % (st, dt, adult, child, city_name, h_id)
                            elif int(child) ==2:
                                    urls = "http://meta.cleartrip.com/hotels/1.0/search?check-in=%s&check-out=%s&no-of-rooms=1&adults-per-room=%s&children-per-room=%s&ca1=11&ca1=11&city=%s&country=IN&scr=INR&sct=IN&ct_hotelid=%s" % (st, dt, adult, child, city_name, h_id)
                            dict_.update({'sk': sk, 'start_date': st, 'dx': str(dx), 'los': str(los), 'pax': paxs, 'url': urls, 'crawl_type': 'keepup', 'crawl_status': '0', 'content_type': 'hotels', 'end_date': dt, 'h_name': hotel_name,
                                          'h_id': h_id, 'meta_data': json.dumps({'sk': city_name, 'start_date': st, 'dx': str(dx), 'los': str(los), 'pax': paxs, 'url': urls, 'end_date': dt, 'h_name': hotel_name, 'h_id': h_id})})
                        insert_crawlct_tables_data(cur, self.name, dict_)

        cur.close()
        self.cursor.close()
