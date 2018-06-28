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
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class MMTCrawltreterive(scrapy.Spider):
    name = "MMTRIP_terminal"
    handle_httpstatus_list = [400, 404, 500]

    def __init__(self, *args, **kwargs):
        super(MMTCrawltreterive, self).__init__(*args, **kwargs)
        self.check = kwargs.get('check', '')
        self.name = 'Makemytrip'
        if self.check == 'dynamic':
            self.name = 'Makemytriponetime'
        self.log = create_logger_obj(self.name)
        self.crawl_type = kwargs.get('crawl_type', 'keepup')
        self.content_type = kwargs.get('content_type', 'hotels')
        self.limit = kwargs.get('limit', 1000)
        self.out_put_file = get_mmtrip_file(self.name)
        self.cursor = create_crawl_table_cusor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.cursor.close()
        mmt_crawlout_processing(self.out_put_file)

    def start_requests(self):
        headers = {'Content-Type': 'application/json'}
        rows = terminal_requests(
            self.cursor, self.name, self.crawl_type, self.content_type, self.limit)
        if rows:
            for city_name, main_url, dx, los, pax, start_date, end_date, city_code, hotel_ids, hotel_name, meta_data in rows:
                if main_url:
                    ct_id = ''
                    try:
                        ct_id = json.loads(meta_data).get('ct_id', '')
                    except:
                        pass
                    yield Request(main_url, callback=self.parse_innerpage1, headers=headers, meta={'city_name': city_name.split('_')[0].strip(), 'dx': dx, 'los': los,
                                                                                                   'pax': pax, 'start_date': start_date, 'end_date': end_date, 'city_code': city_code, 'hotel_ids': hotel_ids, 'hotel_name': hotel_name, 'crawl_sk': city_name, "ct_id": ct_id})

    def parse_innerpage1(self, response):
        ct_id = response.meta.get('ct_id', '')
        crawl_sk = response.meta.get('crawl_sk', '')
        city_name = response.meta.get('city_name', '')
        city_code = response.meta.get('city_code', '')
        dx = response.meta.get('dx', '')
        los = response.meta.get('los', '')
        start_date = response.meta.get('start_date', '')
        check_in = datetime.datetime.strptime(
            start_date, '%m%d%Y').strftime('%Y-%m-%d')
        end_date = response.meta.get('end_date', '')
        check_out = datetime.datetime.strptime(
            end_date, '%m%d%Y').strftime('%Y-%m-%d')
        pax_ac = response.meta.get('pax', '')
        adult = pax_ac.split("e")[0]
        child = pax_ac.split("e")[1]
        h_id = response.meta.get('hotel_ids', '')
        hot_name = response.meta.get('hotel_name', '')

        actual_price, splashed_price, coupon_code, coupon_description = '', '', '', ''
        coupon_value, inclusions, tariffIdentifierFork, reviewUrl, urls, rmtc = '', '', '', '', '', ''

        if response.status == 200:
            data = json.loads(response.body)
            soldout = "".join(data.keys())

            if data and data != '':
                if "sold_out" in soldout:
                    mmt_items = MMTRIPItem()
                    mmt_items.update({'city': normalize(city_name), 'mmthotelname': normalize(hot_name), 'mmthotelid': h_id, 'check_in': check_in,
                                      'dx': dx, 'los': los, 'mmtpax': adult, 'mmtroomtype': 'CLOSED', 'mmtrate': 'Sold Out', 'mmtb2cdiff': 'NA', 'mmtinclusions': 'NA',
                                      'mmtapprate': 'N/A', 'mobilediff': 'NA', 'mmtb2csplashedprice': '0', 'mmtappsplashedprice': 'N/A',
                                      'mmtb2ctaxes': 'CLOSED', 'mmtapptaxes': 'N/A', 'child': child, 'mmtcouponcode': 'N/A', 'mmtcoupondescription': 'N/A',
                                      'mmtcoupondiscount': 'N/A', 'rmtc': 'CLOSED', 'check_out': check_out, 'gstincluded': 'N/A', 'totalamtaftergst': 'N/A', "ct_id": str(ct_id)})
                    yield mmt_items

                else:
                    no_of_recomnd_rooms = str(data.get('recommended_section', {}).get('total_display_fare', {}).get('numOfRooms', ''))
                    main_node = data.get('room_details_section', {})
                    if not main_node:
                        main_node = data.get('recommended_section', {})
                    if main_node:
                        room_details = main_node.get("room_details", {})
                        room_opens = room_details[0].get(
                            "room_details_open_section", {})
                        room_codes = room_opens.get("room_static_info", {})
                        room_vailables = room_opens.get(
                            "room_details_visible", {})

                        rmtc = room_codes.get('room_code', '')
                        room_vailable = room_vailables[0]
                        actual_room_infos = room_vailable.get(
                            'tarrif_details', {})

                        actual_price = actual_room_infos.get(
                            'actual_price', '')
                        splashed_price = actual_room_infos.get(
                            'splashed_price', '')
                        coupon_code = actual_room_infos.get('coupon_code', '')
                        coupon_description = actual_room_infos.get(
                            'coupon_description', '')
                        coupon_value = actual_room_infos.get(
                            'coupon_value', '')
                        inclusions = ', '.join(
                            room_vailable.get('inclusion_section', []))
                        cancellation_policy = actual_room_infos.get(
                            'cancellation_text', '')
                        hotel_availability_url = actual_room_infos.get(
                            'hotelAvailAbilityUrl', '')
                        if hotel_availability_url:
                            if not hotel_availability_url.startswith('http') and 'makemytrip.com' in hotel_availability_url:
                                hotel_availability_url = 'https:%s' % hotel_availability_url
                            if 'makemytrip.com' not in hotel_availability_url:
                                hotel_availability_url = 'https://www.makemytrip.com%s' % hotel_availability_url.replace('/dtr-hoteldom.makemytrip.com/', '')
                        cp_list = []
                        if not 'Non Refundable' in cancellation_policy:
                            can1 = cp_list.append(cancellation_policy)
                            cp_inner_list = room_vailable.get(
                                'fair_policy_section', [])
                            for cpil in cp_inner_list:
                                cp_list.append(cpil)
                            cancellation_policy = '<>'.join(cp_list)
                        tariffIdentifierFork = actual_room_infos.get(
                            'tariffIdentifierFork', '')
                        traffic_split = tariffIdentifierFork.split("_")
                        traffic_code1 = traffic_split[0].strip()
                        traffic_code2 = traffic_split[1].strip()
                        up_checkIn = datetime.datetime.strptime(
                            start_date, '%m%d%Y').strftime('%m/%d/%Y')
                        up_checkout = datetime.datetime.strptime(
                            end_date, '%m%d%Y').strftime('%m/%d/%Y')
                        if hotel_availability_url:
                            urls = "%s%s" % (
                                hotel_availability_url, '&roomCriteria=%s-~%s-~-~%s' % (pax_ac, traffic_code1, traffic_code2))
                            yield Request(urls, callback=self.parse_innerpage4, meta={'city_name': city_name, 'city_code': city_code, 'dx': dx,
                                                                                      'los': los, 'start_date': check_in, 'end_date': check_out, 'pax_ac': pax_ac, 'h_id': h_id, 'actual_price': actual_price,
                                                                                      'splashed_price': splashed_price, 'coupon_code': coupon_code, 'coupon_description': coupon_description,
                                                                                      'room_code': rmtc, 'coupon_value': coupon_value, 'inclusions': inclusions, 'hot_name': hot_name, "cancellation_policy": normalize_clean(cancellation_policy), "ct_id": ct_id, "no_of_recomnd_rooms":no_of_recomnd_rooms})

        else:
            mmt_items = MMTRIPItem()
            mmt_items.update({'city': normalize(city_name), 'mmthotelname': normalize(hot_name), 'mmthotelid': h_id, 'check_in': check_in,
                              'dx': dx, 'los': los, 'mmtpax': adult, 'mmtroomtype': 'N/A', 'mmtrate': 'N/A', 'mmtb2cdiff': 'NA', 'mmtinclusions': 'NA',
                              'mmtapprate': 'N/A', 'mobilediff': 'NA', 'mmtb2csplashedprice': 'N/A', 'mmtappsplashedprice': 'N/A', 'mmtb2ctaxes': 'N/A',
                              'mmtapptaxes': 'N/A', 'child': child, 'mmtcouponcode': 'N/A', 'mmtcoupondescription': 'N/A', 'mmtcoupondiscount': 'N/A',
                              'rmtc': 'N/A', 'check_out': check_out, 'gstincluded': 'N/A', 'totalamtaftergst': 'N/A', "cancellation_policy": 'NA', "ct_id": ct_id})
            yield mmt_items
        self.cursor.execute(
            "update %s_crawl set crawl_status=1 where sk = '%s'" % (self.name, crawl_sk))

    def parse_innerpage4(self, response):
        data = json.loads(response.body)
        ct_id = response.meta.get('ct_id', '')
        no_of_recomnd_rooms = response.meta.get('no_of_recomnd_rooms', '')
        city_name = response.meta.get('city_name', '')
        city_code = response.meta.get('city_code', '')
        dx = response.meta.get('dx', '')
        los = response.meta.get('los', '')
        check_in = response.meta.get('start_date', '')
        check_out = response.meta.get('end_date', '')
        pax_ac = response.meta.get('pax_ac', '')
        adult = pax_ac.split("e")[0]
        child = pax_ac.split("e")[1]
        h_id = response.meta.get('h_id', '')
        room_code = response.meta.get('room_code', '')
        coupon_code = response.meta.get('coupon_code', '')
        coupon_description = response.meta.get('coupon_description', '')
        coupon_value = response.meta.get('coupon_value', '')
        inclusions = response.meta.get('inclusions', '')
        hot_name = response.meta.get('hot_name', '')
        cancellation_policy = response.meta.get('cancellation_policy', '')
        sold_outs = ''

        if data and data != '':
            error_node = data.get('error_dto', {})
            sold_outs = error_node.get('displayMsg', '')
            if "sold out" in sold_outs:
                mmt_items = MMTRIPItem()
                mmt_items.update({'city': normalize(city_name), 'mmthotelname': normalize(hot_name), 'mmthotelid': h_id, 'check_in': check_in,
                                  'dx': dx, 'los': los, 'mmtpax': adult, 'mmtroomtype': 'CLOSED', 'mmtrate': 'Sold Out', 'mmtb2cdiff': 'NA',
                                  'mmtinclusions': 'NA', 'mmtapprate': 'N/A', 'mobilediff': 'NA', 'mmtb2csplashedprice': '0', 'mmtappsplashedprice': 'N/A',
                                  'mmtb2ctaxes': 'CLOSED', 'mmtapptaxes': 'N/A', 'child': child, 'mmtcouponcode': 'N/A', 'mmtcoupondescription': 'N/A',
                                  'mmtcoupondiscount': 'N/A', 'rmtc': 'CLOSED', 'check_out': check_out, 'gstincluded': 'N/A', 'totalamtaftergst': 'N/A', "cancellation_policy": 'NA', "ct_id": str(ct_id), 'aux_info':no_of_recomnd_rooms})
                yield mmt_items

            main_node = data.get('aggr_view_price', {})
            if main_node:
                parent_node = main_node
                supplier_datas = parent_node.get('supplierDetails', {})
                total, discount_amt, final_amt, gst_data, gst_included, total_after_gst, gst_amt = '', '0', '', '', '', '', '0'

                suppliercode = supplier_datas.get('supplierCode', '')
                costprice = supplier_datas.get('costPrice', '')
                dynamic_price = parent_node.get('dynamic_price_view', {})
                data_infos = dynamic_price
                subprice = data_infos.get('subPrice', '')
                discount = data_infos.get('discount', '').replace(",", "")
                totaltax = data_infos.get('totalTax', '').replace(",", "")
                total_tod = data_infos.get('total', '').replace(",", "")
                total = data_infos.get('subPrice', '').replace(",", "")
                gst_data = data_infos.get('taxExcludedInstruction', '')
                if not gst_data or (gst_data == None):
                    gst_data = ''
                #hotel_service_charge = ''.join(re.findall(r'service charge\s?\(.*? (\w+.\w+)', gst_data))
                hotel_service_charge = data_infos.get('serviceCharge', 0)
                if hotel_service_charge or (hotel_service_charge != None) or (hotel_service_charge != 0):
                    hotel_service_charge = float(hotel_service_charge)
                else:
                    hotel_service_charge = 0
                f_gst_amt = data_infos.get('hotelTax', 0)
                if f_gst_amt or (f_gst_amt != 'None'):
                    f_gst_amt = float(f_gst_amt)
                else:
                    f_gst_amt = 0
                if "excluded" in gst_data:
                    gst_included = 'No'
                    #gst_amt = ''.join(re.findall(r'GST\s?\(.*? (\w+.\w+)', gst_data))
                    total_after_gst = int(total)+float(f_gst_amt)
                elif ("added" in gst_data) or (f_gst_amt != 0):
                    gst_included = 'Yes'
                    total_after_gst = 'N/A'
                elif gst_data == '':
                    gst_included = 'N/A'
                    total_after_gst = 'N/A'
                #mmtrate = (int(total)+float(gst_amt)) - (int(discount) + hotel_service_charge)
                mmtrate = float(total) - \
                    (float(hotel_service_charge) + float(discount))
                room_cd = data_infos.get('multiRoomWiseView', {})
                room_data_infos = room_cd
                room_data_info = room_data_infos[0]
                room_type_name = room_data_info.get('roomTypeName', '')
                child_type_no = room_data_info.get('numberOfChildren', '')

                discount_price = parent_node.get('aggr_coupons_view', {})
                data_dis_infos = discount_price
                agv_infos = data_dis_infos.get('twoPasCpns', {}) or data_dis_infos.get('threePasCpns', {}) or \
                    data_dis_infos.get('onePasCpn', {}) or data_dis_infos.get(
                        'fourPasCpns', {}) or data_dis_infos.get('fivePasCpns', {})
                cpns_info = agv_infos
                if isinstance(cpns_info, list):
                    premire_discounts = cpns_info[0]
                    discount_amt = str(premire_discounts.get(
                        'discountAmount', '0')).replace(",", "")
                elif isinstance(cpns_info, dict):
                    discount_amt = str(cpns_info.get(
                        'discountAmount', '0')).replace(",", "")
                mmtsplashed_amt = int(total_tod)-int(discount_amt)
                mmt_items = MMTRIPItem()
                mmt_items.update({'city': normalize(city_name), 'mmthotelname': normalize(hot_name), 'mmthotelid': h_id, 'check_in': check_in,
                                  'dx': dx, 'los': los, 'mmtpax': adult, 'mmtroomtype': room_type_name, 'mmtrate': mmtrate, 'mmtb2cdiff': mmtrate,
                                  'mmtinclusions': normalize_clean(inclusions), 'mmtapprate': 'N/A', 'mobilediff': 'N/A', 'mmtb2csplashedprice': mmtsplashed_amt,
                                  'mmtappsplashedprice': 'N/A', 'mmtb2ctaxes': f_gst_amt, 'mmtapptaxes': 'N/A', 'child': child, 'mmtcouponcode': coupon_code,
                                  'mmtcoupondescription': normalize(coupon_description), 'mmtcoupondiscount': discount_amt, 'rmtc': room_code,
                                  'check_out': check_out, 'gstincluded': gst_included, 'totalamtaftergst': total_after_gst, "cancellation_policy": cancellation_policy, "ct_id": str(ct_id), 'aux_info':no_of_recomnd_rooms})

                yield mmt_items
