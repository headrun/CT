import csv
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
from Hotels.blacklist_properties import total_blacklist_properties, duplicates_mmt_ct_list


def Strp_times(dx, los):
    date_ = datetime.datetime.now() + datetime.timedelta(days=int(dx))
    dx = date_.strftime('%m%d%Y')
    los_date = date_ + datetime.timedelta(days=int(los))
    los = los_date.strftime('%m%d%Y')
    return (dx, los)


def create_crawl_table_cursor():
    conn = MySQLdb.connect(host='localhost', user='root', db=PROD_DB_NAME,
                           charset='utf8', use_unicode=True, passwd=DB_PASSWORD)
    cur = conn.cursor()
    return cur


class mytripspider(scrapy.Spider):
    name = 'Makemytrip_browse'
    handle_httpstatus_list = [400, 404, 500, 304, 403]
    allowed_domains = ['makemytrip.com',
                       'dtr-hoteldom.makemytrip.com', 'dtr-seo.makemytrip.com']
    start_urls = ['https://www.makemytrip.com/hotels']

    def __init__(self, *args, **kwargs):
        super(mytripspider, self).__init__(*args, **kwargs)
        self.check = kwargs.get('check', '')
        self.name = 'Makemytrip'
        json_file_name = 'SampleCITY.json'
        if self.check == 'dynamic':
            self.name = 'Makemytriponetime'
            json_file_name = 'SampleCITYdynamic.json'
        self.cursor = create_mmt_table_cusor()
        ensure_mmt_table(self.cursor, self.name)
        drop_mmt_table(self.cursor, self.name)
        with open(json_file_name) as json_data:
            self.d = json.load(json_data)
        self.check_mmt_listb = []
        with open('csv_file/Bookingdotcom_mapping_file.csv') as bcsvfile:
            all_linesb = csv.reader(bcsvfile, delimiter=',')
            all_linesb = [icsv for icsv in all_linesb]
            for hotel_id_, b_h_url_, ct_h_id_, ta_h_id_, hotel_name_, ta_url_, b_h_name_, city_name_ in all_linesb[1:]:
                self.check_mmt_listb.append(ct_h_id_)

    def parse(self, response):
        sel = Selector(response)
        cur = create_crawl_table_cursor()
        ensure_crawlmt_table(cur, self.name)
        drop_crawlmt_table(cur, self.name)
        dict_ = {}
        #timestamp = str(time.time()).replace('.', '')
        #payload = {'filters': {},'filterApplied': 'false','uiFilterOrClear': 'false','seoSemFilterApplied': 'false'}
        #headers = {'Content-Type': 'application/json'}
        config_file_name = 'MmtConfig.cfg'
        if self.check == 'dynamic':
            config_file_name = 'MmtConfigdynamic.cfg'
        config = ConfigObj(config_file_name)
        #combinations_dict_Pax = {'1 Adult0 Child': '1e0e','2 Adult0 Child': '2e0e','3 Adult0 Child': '3e0e','2 Adult1 ChildChild Age = 8': '2e1e8e','2 Adult2 ChildChild Age = 88': '2e2e8e8e'}

        #combinations_dict_Pax = {'2 Adult0 Child': '2e0e'}
        combinations_dict_Pax = {'2 Adult0 Child': '2e0e', '2 Adult2 Child':'2e2e12e12e', '3 Adult0 Child':'3e0e', '3 Adult1 Child':'3e1e12e', '4 Adult0 Child':'4e0e'}
        sectionall = config.sections
        for sectionbyone in sectionall:
            sections_ = config[sectionbyone]
            DX_num = sections_['Dx']
            LOS_num = sections_['LoS']
            PAX_val = ''.join(sections_['Pax'])
            pax, hotel_name, city_code, city_name, hotel_ids = '', '', '', '', ''
            dxs, loss = Strp_times(DX_num, LOS_num)
            if PAX_val in combinations_dict_Pax.keys():
                pax = combinations_dict_Pax[PAX_val]
                for city_name, hotel_id in self.d.iteritems():
                    for hotel_ids, hotel_details in hotel_id.iteritems():
                        hotel_ids = hotel_ids
                        city_name = city_name
                        city_code = hotel_details[1]
                        hotel_name = hotel_details[0]
                        ct_mmt_id = hotel_details[2]
                        if city_name != '' and city_code != '' and hotel_name != '' and hotel_ids != '' and (ct_mmt_id not in total_blacklist_properties) and (ct_mmt_id not in duplicates_mmt_ct_list) and (ct_mmt_id not in self.check_mmt_listb):
                            sk = "_".join([city_name, str(DX_num), str(
                                LOS_num), str(pax), hotel_ids])
                            # urls='https://www.makemytrip.com/mmthtl/site/searchPriceNew?country=IN&city=%s&checkin=%s&checkout=%s&roomStayQualifier=%s&hotelId=%s&newListing=true'%(city_code,dxs,loss,pax,hotel_ids)
                            urls = 'https://dtr-hoteldom.makemytrip.com/mmthtl/site/searchPriceNew?country=IN&city=%s&checkin=%s&checkout=%s&roomStayQualifier=%s&hotelId=%s&mtkeys=undefined&newListing=true' % (
                                city_code, dxs, loss, pax, hotel_ids)
                            dict_.update({'sk': sk, 'start_date': dxs, 'dx': str(DX_num), 'los': str(LOS_num), 'pax': pax, 'url': urls,
                                          'crawl_type': 'keepup',   'crawl_status': '0', 'content_type': 'hotels', 'end_date': loss, 'ccode': city_code,
                                          'hotel_ids': hotel_ids, 'hotel_name': hotel_name, 'meta_data': json.dumps({'sk': city_name, 'start_date': dxs,
                                                                                                                     'dx': str(DX_num), 'los': str(LOS_num), 'pax': pax, 'url': urls, 'end_date': loss, 'ccode': city_code,
                                                                                                                     'hotel_ids': hotel_ids, 'hotel_name': hotel_name, "ct_id": str(ct_mmt_id)})})
                            insert_crawlmt_tables_data(cur, self.name, dict_)

        cur.close()
        self.cursor.close()
