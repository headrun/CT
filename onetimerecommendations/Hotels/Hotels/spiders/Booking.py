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
import csv
from Hotels.utils import *
from Hotels.blacklist_properties import total_blacklist_properties


def Strp_times(dx, los):
    date_ = datetime.datetime.now() + datetime.timedelta(days=int(dx))
    dx = date_.strftime('%Y-%m-%d')
    los_date = date_ + datetime.timedelta(days=int(los))
    los = los_date.strftime('%Y-%m-%d')
    return (dx, los)


def create_crawl_table_cursor():
    conn = MySQLdb.connect(host='localhost', user='root', db=PROD_DB_NAME,
                           charset='utf8', use_unicode=True, passwd=DB_PASSWORD)
    cur = conn.cursor()
    return cur


class Booking(scrapy.Spider):
    name = 'Booking_browse'
    handle_httpstatus_list = [400, 404, 500, 503]
    start_urls = ['https://www.cleartrip.com/']

    def __init__(self, *args, **kwargs):
        super(Booking, self).__init__(*args, **kwargs)
        self.name = 'Booking'
        self.cursor = create_mmt_table_cusor()
        ensure_booking_table(self.cursor, self.name)
        drop_gob_table(self.cursor, self.name)
        with open('csv_file/Bookingdotcom_mapping_file.csv') as csvfile:
            self.all_lines = csv.reader(csvfile, delimiter=',')
            self.all_lines = [icsv for icsv in self.all_lines]

    def parse(self, response):
        sel = Selector(response)
        dict_ = {}
        cur = create_crawl_table_cursor()
        ensure_crawlgb_table(cur, self.name)
        drop_crawlgb_table(cur, self.name)
        config = ConfigObj('BookingConfig.cfg')
        pax_combination_dict = {"2 Adult2 Child": "A,A,17,17", "3 Adult0 Child": "A,A,A",
                                "3 Adult1 Child": "A,A,A,17", "4 Adult0 Child": "A,A,A,A", "2 Adult0 Child": "A,A"}
        sectionall = config.sections
        for sectionbyone in sectionall:
            sections_ = config[sectionbyone]
            DX_num = sections_['Dx']
            LOS_num = sections_['LoS']
            PAX_val = ''.join(sections_['Pax'])
            pax, hotel_name, city_code, city_name, hotel_id = '', '', '', '', ''
            dxs, loss = Strp_times(DX_num, LOS_num)
            pax, child_ = re.findall('\d+', PAX_val)
            for hotel_id, b_h_url, ct_h_id, ta_h_id, hotel_name, ta_url, b_h_name, city_name in self.all_lines[1:]:
                sk = "_".join([city_name, str(DX_num), str(
                    LOS_num), str(pax), hotel_id, str(child_)])
                hotel_id = hotel_id.strip(" ")
                hotel_name = hotel_name.strip(" ")
                city_name = city_name.strip(" ")
                to_terminal = pax_combination_dict[PAX_val]
                if int(child_) == 0:
                    urls = '%s?checkin=%s;checkout=%s;group_adults=%s;req_adults=%s' % (
                        b_h_url, dxs, loss, pax, pax)
                elif int(child_) == 1:
                    urls = "%s?checkin=%s;checkout=%s;group_adults=%s;group_children=1;req_adults=%s;req_children=1;req_age=17" % (
                        b_h_url, dxs, loss, pax, pax)
                elif int(child_) == 2:
                    urls = '%s?checkin=%s;checkout=%s;group_adults=%s;group_children=2;req_adults=%s;req_children=2;req_age=17;req_age=17' % (
                        b_h_url, dxs, loss, pax, pax)
                dict_.update({'sk': sk, 'start_date': dxs, 'dx': str(DX_num), 'los': str(LOS_num), 'pax': str(pax),
                              'url': urls, 'crawl_type': 'keepup', 'crawl_status': '0', 'content_type': 'hotels', 'ccode': '',
                              'end_date': loss, 'hotel_ids': hotel_id, 'hotel_name': hotel_name,
                              'meta_data': json.dumps({'sk': city_name, 'start_date': dxs, 'dx': str(DX_num),
                                                       'los': str(LOS_num), 'pax': pax, 'url': urls, 'end_date': loss,
                                                       'hotel_ids': hotel_id, 'hotel_name': hotel_name,  'ct_id': ct_h_id, "child": child_, "to_terminal": to_terminal}), 'aux_info': json.dumps({
                                                           'dxs': dxs, 'loss': loss, 'pax': pax, 'hotel_id': hotel_id}), 'reference_url': urls, })
                if ct_h_id not in total_blacklist_properties:
                    insert_crawlgb_tables_data(cur, self.name, dict_)
        cur.close()
        self.cursor.close()
