import scrapy
from scrapy.selector import Selector
from scrapy.http import Request
from scrapy.http import FormRequest
import datetime
import json
import os
import time
import re
import sys
import MySQLdb
import logging
from scrapy import log
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from Hotels.utils import *
from Hotels.items import *
import md5
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class Bookingretrival(scrapy.Spider):
    name = "Bookingretrival_terminal"
    handle_httpstatus_list = [400, 404, 500, 503]
    start_urls = []

    def __init__(self, *args, **kwargs):
        super(Bookingretrival, self).__init__(*args, **kwargs)
        self.name = 'Booking'
        self.log = create_logger_obj(self.name)
        self.crawl_type = kwargs.get('crawl_type', 'keepup')
        self.content_type = kwargs.get('content_type', 'hotels')
        self.limit = kwargs.get('limit', 1000)
        self.out_put_file = get_gobtrip_file(self.name)
        self.cursor = create_crawl_table_cusor()
        self.aux_info = {}
        reload(sys)
        sys.setdefaultencoding("utf-8")
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.cursor.close()
        gob_crawlout_processing(self.out_put_file)

    def start_requests(self):
        headers = {'Content-Type': 'application/json'}
        rows = terminal_staticrequests(
            self.cursor, self.name, self.crawl_type, self.content_type, self.limit)
        if rows:
            for city_name, main_url, dx, los, pax, start_date, end_date, city_code, hotel_ids, hotel_name, meta_data in rows:
                if main_url:
                    ct_id = ''
                    try:
                        ct_id = json.loads(meta_data).get('ct_id', '')
                        child = json.loads(meta_data).get('child', '')
                        to_terminal = json.loads(
                            meta_data).get('to_terminal', '')
                    except:
                        pass
                    yield Request(main_url, callback=self.parse, headers=headers, meta={'city_name': city_name.split("_")[0].strip(), 'dx': dx, 'los': los, 'pax': pax, 'start_date': start_date, 'end_date': end_date, 'city_code': city_code, 'hotel_ids': hotel_ids, 'hotel_name': hotel_name, 'crawl_sk': city_name, "ct_id": ct_id, "child": child, "to_terminal": to_terminal})

    def parse(self, response):
        crawl_sk = response.meta.get('crawl_sk', '')
        data = Selector(response)
        reference_url = response.url
        error_secure_url = ''.join(re.findall('\/in\/(.*?)\?', reference_url))
        error_secure_checkin = ''.join(
            re.findall('checkin=(.*?);', reference_url))
        try:
            ct_id = response.meta.get('ct_id', '')
            to_terminal = response.meta.get('to_terminal', '')
            city_name = response.meta.get('city_name', '').title()
            dx = response.meta.get('dx', '')
            los = response.meta.get('los', '')
            pax = response.meta.get('pax', '')
            check_in = response.meta.get('start_date', '')
            check_out = response.meta.get('end_date', '')
            city_code = response.meta.get('city_code', '')
            h_id = response.meta.get('hotel_ids', '')
            hot_name = response.meta.get('hotel_name', '')
            adult = pax
            sk_hash_id, room_type_, rate_plan, final_rate_plan, inclusions, cancellation_policy, splashed_price, actual_price = [
                'N/A']*8
            rmtc = ''
            child = response.meta.get('child', '')
            aux_info = {}
            if response.status == 200:
                meta_data_ = len(data.xpath('//div[@id="group_recommendation"]//table[contains(@class, "recommendation")]/tbody/tr'))
                if meta_data_ < 2:
                    meta_data_ = ''
                room_nodes = data.xpath(
                    '//div[@id="available_rooms"]/div[@class="roomArea"]/form/table/tbody/tr[@data-block-id][td[contains(@class, "table-cell")]]')
                room_type_dict = {}
                if room_nodes:
                    rn = room_nodes[0]
                    data_block_id = ''.join(
                        rn.xpath('./self::tr/@data-block-id').extract())
                    room_type_main_nd = ''.join(
                        rn.xpath('.//span[contains(@class, "roomtype-icon-")]//text()').extract())
                    room_type_id = ''.join(
                        rn.xpath('./self::tr/@data-block-id').extract())
                    if room_type_id and '_' in room_type_id:
                        room_type_id = room_type_id.split('_')[0]
                    else:
                        room_type_id = ''
                    actual_price = ''.join(rn.xpath('.//div[contains(@class, "hprt-price-price")]/span/text()').extract(
                    )).replace(u'\xa0', '').replace('Rs.', '').replace(',', '').replace('\xe2\x82\xb9', '').replace(u'\u20b9', '')
                    soldout_check = ''.join(
                        rn.xpath('.//span[contains(@class, "important_text")]//text()').extract())
                    splashed_price = ''.join(rn.xpath('.//span[i[contains(@class, "crossedout-price-icon")]]/text()').extract(
                    )).replace(u'\xa0', '').replace('Rs.', '').replace(',', '').replace('\xe2\x82\xb9', '').replace(u'\u20b9', '')
                    meal_plan = ''.join(rn.xpath(
                        './/li[contains(@data-et-mouseenter, "mealplan")]//text()').extract()).replace(u'\xa0', '')
                    if 'sold' in soldout_check.lower() and not actual_price:
                        actual_price = 'SOLDOUT'
                    inclusions = rn.xpath(
                        './/div[contains(@class, "hprt-facilities")]//span[not(contains(@class, "hprt-facilities"))]/text()').extract()
                    inclusions_ = [rns.replace(u'\u2022', '') for rns in rn.xpath(
                        './/ul[contains(@class, "hprt-facilities")]//li/span[contains(@class, "hprt-facilities")]/text()').extract()]
                    inclusions.extend(inclusions_)
                    inclusions = normalize_clean('<>'.join(inclusions).replace(
                        ' <> ', '<>').replace('<> ', '<>').replace(' <>', '<>'))
                    if room_type_id and (room_type_id not in room_type_dict.keys()):
                        room_type_dict.update(
                            {room_type_id: [room_type_main_nd, inclusions]})
                    if room_type_id in room_type_dict.keys():
                        room_type_main_nd, inclusions = room_type_dict[room_type_id]
                    final_rate_plan = room_type_main_nd
                    non_refundable = ''.join(rn.xpath(
                        './/li[contains(@data-et-mouseenter, "non_refundable")]//text()').extract())
                    if non_refundable:
                        cancellation_policy = 'Non Refundable'
                    else:
                        cancellation_policy = ''.join(rn.xpath(
                            './/li[contains(@data-et-mouseenter, "free_cancellation")]//text()').extract())
                    if 'sold' not in soldout_check.lower() and not actual_price:
                        actual_price = 'N/A'
                        rmtc = 'N/A'
                    if actual_price == 'SOLDOUT':
                        rmtc = 'CLOSED'
                    if not rmtc:
                        rmtc = room_type_id
                    h_id_bs = data.xpath(
                        '//input[@name="hotel_id"]/@value').extract()
                    if h_id_bs:
                        h_id_bs = h_id_bs[0]
                    else:
                        h_id_bs = ''
                    item_booking = self.get_yield(ct_id,  final_rate_plan, adult, child, dx, los, check_in, check_out, city_name, hot_name,
                                                  h_id, reference_url, room_type_, rate_plan, inclusions, cancellation_policy, splashed_price, actual_price, '', meta_data_, rmtc)
                    if item_booking:
                        if rmtc and rmtc != 'N/A' and rmtc != 'CLOSED' and data_block_id and h_id_bs:
                            if '17' in to_terminal:
                                refsecure_url = 'https://secure.booking.com/book.html?hotel_id=%s&error_url=%s&hostname=www.booking.com&stage=1&checkin=%s&interval=1&children_extrabeds=&hp_visits_num=1&rt_pos_selected=1&from_source=hotel&nr_rooms_%s=1&room1=%s&is_family_friendly=1' % (
                                    h_id_bs, error_secure_url, error_secure_checkin, data_block_id, to_terminal)
                            else:
                                refsecure_url = 'https://secure.booking.com/book.html?hotel_id=%s&error_url=%s&hostname=www.booking.com&stage=1&checkin=%s&interval=1&children_extrabeds=&hp_visits_num=1&rt_pos_selected=1&from_source=hotel&nr_rooms_%s=1&room1=%s' % (
                                    h_id_bs, error_secure_url, error_secure_checkin, data_block_id, to_terminal)
                            yield Request(refsecure_url, callback=self.parse_nexts, meta={"item_booking": item_booking})
                        else:
                            yield item_booking
                if not room_nodes:
                    actual_price = 'N/A'
                    rmtc = 'N/A'
                    item_booking = self.get_yield(ct_id,  final_rate_plan, adult, child, dx, los, check_in, check_out, city_name, hot_name,
                                                  h_id, reference_url, room_type_, rate_plan, inclusions, cancellation_policy, splashed_price, actual_price, '', '', rmtc)
                    if item_booking:
                        yield item_booking
            else:
                actual_price = 'N/A'
                rmtc = 'N/A'
                item_booking = self.get_yield(ct_id,  final_rate_plan, adult, child, dx, los, check_in, check_out, city_name, hot_name,
                                              h_id, reference_url, room_type, rate_plan, inclusions, cancellation_policy, splashed_price, actual_price, '', meta_data_, rmtc)
                if item_booking:
                    yield item_booking
            self.cursor.execute(
                "update %s_crawl set crawl_status=1 where sk = '%s'" % (self.name, crawl_sk))
        except Exception, e:
            print str(e)
            self.cursor.execute(
                "update %s_crawl set crawl_status=8 where sk = '%s'" % (self.name, crawl_sk))

    def get_yield(self, ct_id, final_rate_plan, adult, child, dx, los, check_in, check_out, city_name, hot_name, h_id, reference_url, room_type_, rate_plan, inclusions, cancellation_policy, splashed_price, actual_price, unique_sk, meta_data_, rmtc):
        mmtstatic_items = BookingItem()
        mmtstatic_items.update({"ct_id": normalize_clean(ct_id), "final_rate_plan": normalize_clean(final_rate_plan), "pax": adult, "child": child, "dx": dx, "los": los, 'check_in': check_in, 'check_out': check_out, 'city': normalize(city_name), 'hotelname': normalize(hot_name), 'hotelid': h_id, "reference_url": reference_url, "room_type": normalize_clean(
            final_rate_plan), "rate_plan": normalize_clean(rate_plan), "inclusions": normalize_clean(inclusions), "cancellation_policy": normalize_clean(cancellation_policy), "splashed_price": normalize_clean(splashed_price), "actual_price": normalize_clean(actual_price), "unique_sk": unique_sk, "aux_info": meta_data_, "rmtc": normalize_clean(rmtc)})
        return mmtstatic_items

    def parse_nexts(self, response):
        sel = Selector(response)
        goods_service_tax = sel.xpath(
            '//div[@class="bp_pricedetails_excluded_fees_legibility"]//ul/li[span[contains(text(), "Goods & services tax")]]/span[@class]/text()').extract()
        if not goods_service_tax:
            goods_service_tax = sel.xpath('//div[@class="bp_pricedetails_excluded_fees_legibility"]//ul/li[span[contains(text(), "Tax")]]/span[@class]/text()').extract()
        if goods_service_tax:
            goods_service_tax = normalize_clean(goods_service_tax[0].encode(
                'ascii', errors='ignore').replace('Rs.', '').replace(',', '').replace(u'\u20b9', '').replace('\xe2\x82\xb9', ''))
        else:
            goods_service_tax = 0
        property_service_charge = sel.xpath(
            '//div[@class="bp_pricedetails_excluded_fees_legibility"]//ul/li[span[contains(text(), "Property service charge")]]/span[@class]/text()').extract()
        if property_service_charge:
            property_service_charge = normalize_clean(property_service_charge[0].encode(
                'ascii', errors='ignore').replace('Rs.', '').replace(',', '').replace(u'\u20b9', '').replace('\xe2\x82\xb9', ''))
        else:
            property_service_charge = 0
        city_tax = sel.xpath('//div[@class="bp_pricedetails_excluded_fees_legibility"]//ul/li[span[contains(text(), "City tax")]]/span[@class]/text()').extract()
        if city_tax:
            city_tax = normalize_clean(city_tax[0].encode('ascii', errors='ignore').replace('Rs.', '').replace(',', '').replace(u'\u20b9', '').replace('\xe2\x82\xb9', ''))
        else:
            city_tax = 0
        cleaning_fee = sel.xpath('//div[@class="bp_pricedetails_excluded_fees_legibility"]//ul/li[span[contains(text(), "cleaning fee")]]/span[@class]/text() | //div[@class="bp_pricedetails_excluded_fees_legibility"]//ul/li[span[contains(text(), "Cleaning fee")]]/span[@class]/text()').extract()
        if cleaning_fee:
            cleaning_fee = normalize_clean(cleaning_fee[0].encode('ascii', errors='ignore').replace('Rs.', '').replace(',', '').replace(u'\u20b9', '').replace('NOK', '').replace('\xe2\x82\xb9', '').strip())
        else:
            cleaning_fee = 0
        damage_deposit = sel.xpath('//li[@class="charge excluded deposit"][span[div[contains(text(), "Damage deposit")]]]/span[@class="excluded_fees_price"]/text()').extract()
        refundable_check = ''.join(sel.xpath('//li[@class="charge excluded deposit"]/span/div[contains(text(), "Damage deposit")]/following-sibling::div[1]//text()').extract())
        if damage_deposit and 'refundable' not in refundable_check:
            damage_deposit = normalize_clean(damage_deposit[0].encode('ascii', errors='ignore').replace('Rs.', '').replace(',', '').replace(u'\u20b9', '').replace('\xe2\x82\xb9', ''))
        else:
            damage_deposit = 0
        item_Bookin = response.meta['item_booking']
        final_actual_price = float(item_Bookin.get(
            'actual_price', 0)) + float(goods_service_tax)+float(property_service_charge)+float(city_tax)+float(cleaning_fee)+float(damage_deposit)
        if goods_service_tax == 0:
            goods_service_tax = sel.xpath('//div[@class="bp_pricedetails_fauxtable"]//ul/li[span[contains(text(), "Goods & services tax")]]/span[contains(@class, "breakdown_price")]/text()').extract()
            if goods_service_tax:
                goods_service_tax =  normalize_clean(goods_service_tax[0].encode('ascii', errors='ignore').replace('Rs.', '').replace(',', '').replace(u'\u20b9', '').replace('\xe2\x82\xb9', ''))
            else:
                goods_service_tax = 0
        item_Bookin['actual_price'] = str(final_actual_price)
        item_Bookin['gst_amt'] = str(float(goods_service_tax))
        yield item_Bookin
