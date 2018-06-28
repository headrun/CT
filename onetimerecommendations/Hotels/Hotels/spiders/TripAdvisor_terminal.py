from configobj import ConfigObj
from scrapy.xlib.pydispatch import dispatcher
import scrapy
from scrapy.selector import Selector
from scrapy.http import Request
from scrapy.http import FormRequest
from Hotels.items import *
import os
import json
import datetime
import time
import urllib
from Hotels.utils import *
import re
import MySQLdb
import collections
import csv
import logging
from scrapy import log
from scrapy import signals
from operator import itemgetter


def Strp_times(dx, los):
    date_ = datetime.datetime.now() + datetime.timedelta(days=int(dx))
    dx = date_.strftime('%Y_%m_%d')
    los_date = date_ + datetime.timedelta(days=int(los))
    los = los_date.strftime('%Y_%m_%d')
    return (dx, los)


class TripAdvisor(scrapy.Spider):
    name = 'tripadvisoro_terminal'
    handle_httpstatus_list = [400, 404, 500, 503, 403]
    custom_settings = {"REDIRECT_ENABLED": True}

    def __init__(self, *args, **kwargs):
        super(TripAdvisor, self).__init__(*args, **kwargs)
        self.name = 'Tripadvisor'
        if kwargs.get('set_up', ''):
            self.name = 'TripadvisorAPC'
        self.name_invent = '%sInventory' % self.name
        self.update_query_ta = "update %s_crawl set crawl_status=%s where sk = '%s'"
        self.headers = {
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive',
        }
        self.cursor = create_crawl_table_cusor()
        self.log = create_logger_obj(self.name)
        self.crawl_type = kwargs.get('crawl_type', 'keepup')
        self.content_type = kwargs.get('content_type', 'hotels')
        self.limit = kwargs.get('limit', 1000)
        self.dx_val = kwargs.get('dx', '')
        self.out_put_file = get_gobtrip_file(self.name)
        self.out_put_file1 = get_gobtrip_file(self.name_invent)
        self.rate_avg_dict = {}
        with open('csv_file/rate_level_average_difference.csv') as csvfile:
            self.all_lines = csv.reader(csvfile, delimiter=',')
            self.all_lines = [icsv for icsv in self.all_lines]
            for alll in self.all_lines:
                if 'AVERAGE_PRICE_DIFFERENCE' not in alll[1]:
                    self.rate_avg_dict.update({alll[0]: alll[1]})
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.cursor.close()
        gob_crawlout_processing(self.out_put_file)
        gob_crawlout_processing(self.out_put_file1)

    def start_requests(self):
        rows = terminal_tripadvisor_requests(
            self.cursor, self.name, self.crawl_type, self.content_type, self.dx_val, self.limit)
        if rows:
            for row_inner in rows:
                sk, ta_url, dx, los, pax, start_date, end_date,\
                    ctid, hotel_id, hotel_name, aux_info = row_inner
                no_of_rooms = str(sk.split('_')[-1])
                DX_num = str(dx)
                LOS_num = str(los)
                PAX_val = str(pax)
                ctid = str(ctid)
                hotel_id = str(hotel_id)
                dxs, loss = str(start_date), str(end_date)
                city_name = json.loads(aux_info).get('city_name', '')
                date_time_ = time.time()
                full_ti = str(time.strftime(
                    '%Y-%m-%d %H:%M:%S', time.localtime(date_time_)))
                date_time = str(date_time_).split('.')[0]
                index_count = True
                counter_number = 0
                while index_count:
                    trip_advisor_url = "https://www.tripadvisor.in/MiniMetaCRAjax?detail=%s&staydates=%s_%s&rooms=%s&adults=%s&child_rm_ages=&area=QC_Meta_Mini&returnAllOffers=true&imp=true&metaReferer=Hotel_Review&baseLocId=%s&metaRequestTiming=%s&finalRequest=true" % (
                        hotel_id, dxs, loss, no_of_rooms, PAX_val, hotel_id, date_time)
                    yield Request(trip_advisor_url, callback=self.parse_next, headers=self.headers, meta={"req": counter_number, "ta_url": ta_url, "city_name": city_name, "hotel_name": hotel_name, "hotel_id": hotel_id, "dxs": dxs.replace('_', '-'), "DX_num": DX_num, "PAX_val": PAX_val, "full_time": full_ti, 'ta_url': ta_url, 'sk': sk, 'loss': loss, 'ctid': ctid}, dont_filter=True)
                    counter_number += 1
                    if counter_number == 3:
                        index_count = False

    def parse_vendor(self, response):
        vendor_key, to_go_check, go_here = ['']*3
        redirect_url = ''.join(re.findall(
            'window\.location\.href = \"(.*?)\"; ', response.body)).replace('\\', '')
        if not redirect_url:
            redirect_url = ''.join(re.findall(
                'window\.location\.replace\(\"(.*?)\"\)', response.body)).replace('\\', '')
        if 'makemytrip.com' in redirect_url:
            vendor_key = 'mmt'
            redirect_url = redirect_url.replace(
                'www.', 'dtr-hoteldom.').replace('site/hotels/detail', 'site/searchPriceNew')
        elif 'goibibo.com' in redirect_url:
            vendor_key = 'goibibo'
        elif 'cleartrip.com' in redirect_url:
            vendor_key = 'cleartrip'
        elif 'booking.com' in redirect_url:
            vendor_key = 'booking'
        else:
            transfer_meta = response.meta
            ct_url_c = transfer_meta.get('ct_url', '')
            status = 'cheapest ota is other than ct, goibibo, mmt and booking'
            status_inner, room_name = ['']*2
            if "goibibo.com" in response.url:
                vendor_key = 'goibibo'
                cit_vcid = ''.join(re.findall('\"vcid\":\"(.*?)\"', response.body))
                cit_ci = ''.join(re.findall('\"ci\":\"(.*?)\"', response.body))
                cit_co = ''.join(re.findall('\"co\":\"(.*?)\"', response.body))
                cit_r = ''.join(re.findall('\"r\":\"(.*?)\"', response.body))
                cit_hotel_id = ''.join(re.findall('\"hotelId\":\"(.*?)\"', response.body))
                cit_co = response.meta.get('checkout', '').replace('-', '').replace('_', '') 
                cit_ci = response.meta.get('checkin', '').replace('-', '').replace('_', '') 
                redirect_url = 'https://hermes.goibibo.com/hotels/v7/detail/price/v3/%s/%s/%s/%s/%s?ibp=&im=true&slot=true' % (cit_vcid, cit_ci, cit_co, cit_r, cit_hotel_id)
                go_here = 'yes'
            elif 'makemytrip.com' in response.url:
                to_go_check = 'yes'
                status_inner, room_name = self.get_mmt_room_name(response.body)
            elif "booking.com" in response.url:
                to_go_check = 'yes'
                status_inner, room_name = self.get_booking_room_name(response)
            if ct_url_c:
                transfer_meta['ct_url'] = ''
                if to_go_check:
                    transfer_meta.update({"cheapest_room_name": room_name, "status_inner_message": status_inner,"is_going_to_ct": "yes", "cheaperst_url": response.url, "vendor_key": "cleartrip"})
                else:
		    if not go_here:
			transfer_meta['cheapest_ota_data'] = ('NA', 'NA')
        	    	transfer_meta.update({"cheapest_room_name": "NA", "cheapest_ota_price": "NA", "status": status,
                	                      "is_going_to_ct": "yes", "vendor_key": "cleartrip", "cheaperst_url": response.url})
	        	yield Request(ct_url_c, callback=self.parse_vendordetails, meta=transfer_meta, dont_filter=True)
            else:
                if to_go_check:
                    transfer_meta.update({"cheapest_room_name":room_name, "status_inner_message":status_inner, "vendor_key":vendor_key, "cheaperst_url":response.url})
                    vendor_iyield = self.yield_vendor(transfer_meta)
                    if vendor_iyield:
                        yield vendor_iyield
                else:
		    if not go_here:
			    transfer_meta['cheapest_ota_data'] = ('NA', 'NA')
        	            transfer_meta.update({"cheapest_room_name": "NA", "cheapest_ota_price": "NA", "status": status})
                	    vendor_iyield = self.yield_vendor(transfer_meta)
	                    if vendor_iyield:
        	                yield vendor_iyield

        if vendor_key and not to_go_check:
            yield Request(redirect_url, callback=self.parse_vendordetails, meta={"vendor_key": vendor_key, "transfer_meta": response.meta}, dont_filter=True)


    def get_goibibo_room_name(self, res):
        status_inner, room_name = ['']*2
        try:
            room_name = json.loads(res).get('data', {}).get('reg', [])[0].get('rp_list', [])[0].get('rtn', '')
            if room_name:
                status_inner = "success"
        except:
            status_inner = 'room name not found'
        return status_inner, room_name

    def get_mmt_room_name(self, res):
        status_inner, room_name = ['']*2
        data = json.loads(res)
        main_node = data.get('room_details_section', {})
        if not main_node:
            main_node = data.get('recommended_section', {})
        if main_node:
            room_details1 = main_node.get("room_details", [])
            if room_details1:
                room_details = room_details1[0]
                room_opens = room_details.get(
                    "room_details_open_section", {})
                room_codes = room_opens.get("room_static_info", {})
                room_name = room_codes.get('room_name', '')
                status_inner = "success"
            else:
                status_inner = 'room name not found'
        else:
            status_inner = 'room name not found'
        return  status_inner, room_name

    def get_booking_room_name(self, res):
        status_inner, room_name = ['']*2
        sel = Selector(res)
        room_fin = sel.xpath(
            '//span[contains(@class, "roomtype-icon-")]//text()').extract()
        if room_fin:
            room_name = room_fin[0]
            if room_name:
                status_inner = "success"
            else:
                status_inner = 'room name not found'
        else:
            status_inner = 'room name not found'
        return  status_inner, room_name

    def get_cleartrip_room_name(self, res):
        status_inner, room_name = ['']*2
        data = json.loads(res)
        rms = data.get('rc', {}).get('d0', {}).get('rms', [])
        if rms:
            room_name = rms[0].get('rmn', '')
            if room_name:
                status_inner = "success"
            else:
                status_inner = 'room name not found'
        else:
            status_inner = 'room name not found'
        return status_inner, room_name


    def parse_vendordetails(self, response):
	not_to_ct = ''
        vendor_key = response.meta.get('vendor_key', '')
        transfer_meta = response.meta.get('transfer_meta', {})
        if vendor_key == "cleartrip":
            transfer_meta = response.meta
        status_inner, room_name = ['']*2
        if vendor_key == "goibibo":
            if not transfer_meta.get('next_yield') and 'hermes.goibibo.com/hotels/v7/detail/price/' not in response.url:
                not_to_ct = 'yes'
                cit_vcid = ''.join(re.findall('\"vcid\":\"(.*?)\"', response.body))
                cit_ci = ''.join(re.findall('\"ci\":\"(.*?)\"', response.body))
                cit_co = ''.join(re.findall('\"co\":\"(.*?)\"', response.body))
                cit_r = ''.join(re.findall('\"r\":\"(.*?)\"', response.body))
                cit_hotel_id = ''.join(re.findall('\"hotelId\":\"(.*?)\"', response.body))
                cit_co = response.meta.get('transfer_meta', {}).get('checkout', '').replace('-', '').replace('_', '')
                cit_ci = response.meta.get('transfer_meta', {}).get('checkin', '').replace('-', '').replace('_', '')
		if not cit_co:
			cit_co = response.meta.get('checkout', '').replace('-', '').replace('_', '')
		if not cit_ci:
			cit_ci = response.meta.get('checkin', '').replace('-', '').replace('_', '')
                url = 'https://hermes.goibibo.com/hotels/v7/detail/price/v3/%s/%s/%s/%s/%s?ibp=&im=true&slot=true' % (cit_vcid, cit_ci, cit_co, cit_r, cit_hotel_id)
                transfer_meta.update({'next_yield':'yes'})
                yield Request(url, callback=self.parse_vendordetails, meta={"vendor_key": vendor_key, "transfer_meta": transfer_meta}, dont_filter=True)
            else:
                status_inner, room_name = self.get_goibibo_room_name(response.body)
        if vendor_key == "mmt":
            status_inner, room_name = self.get_mmt_room_name(response.body)
        if vendor_key == "cleartrip":
            status_inner, room_name = self.get_cleartrip_room_name(response.body)
        if vendor_key == "booking":
            status_inner, room_name = self.get_booking_room_name(response)
        if transfer_meta.get('ct_url', '') and not not_to_ct:
            ct_url_c = transfer_meta['ct_url']
            transfer_meta['ct_url'] = ''
            transfer_meta.update({"cheapest_room_name": room_name, "status_inner_message": status_inner,
                                  "is_going_to_ct": "yes", "cheaperst_url": response.url, "vendor_key": "cleartrip"})
            yield Request(ct_url_c, callback=self.parse_vendordetails, meta=transfer_meta, dont_filter=True, )
        else:
            if transfer_meta.get('is_going_to_ct', '') and not not_to_ct:
                transfer_meta.update({'cleartrip_room_name': room_name, "cleartrip_inner_message": status_inner,
                                      "vendor_key": vendor_key, "ct_ta_url": response.url})
                vendor_iyield = self.yield_vendor(transfer_meta)
                if vendor_iyield:
                    yield vendor_iyield
            else:
		if not not_to_ct:
	                transfer_meta.update({"cheapest_room_name": room_name, "status_inner_message": status_inner,
        	                              "vendor_key": vendor_key, "cheaperst_url": response.url})
                	vendor_iyield = self.yield_vendor(transfer_meta)
	                if vendor_iyield:
        	            yield vendor_iyield

    def cheapest_re(self, update_cheapest_three, cheapest_to_return):
        cheapest_to_returninner = ''
	if cheapest_to_return[-1].lower() not in ['goibibo', 'booking',  'makemytrip', 'goibibointl', 'bookingintl', 'makemytripintl', 'bookingcom', 'bookingcomintl']:
            cheapest_to_returninner = [(int(val[0]), val[1]) for val in update_cheapest_three if val[0] != '0' and (
                val[1].lower() == 'makemytrip' or val[1].lower() == "makemytripintl") and val[0] != 0]
            if not cheapest_to_returninner:
                cheapest_to_returninner = [(int(val[0]), val[1]) for val in update_cheapest_three if val[0] != '0' and (
                    val[1].lower() == 'goibibo' or val[1].lower() == "goibibointl") and val[0] != 0]
            if not cheapest_to_returninner:
                cheapest_to_returninner = [(int(val[0]), val[1]) for val in update_cheapest_three if val[0] != '0' and (
                    val[1].lower() == 'bookingcom' or val[1].lower() == "bookingcomintl") and val[0] != 0]
            if not cheapest_to_returninner:
                cheapest_to_returninner = cheapest_to_return
            else:
                cheapest_to_returninner = cheapest_to_returninner[0]
        else:
            cheapest_to_returninner = cheapest_to_return
        return cheapest_to_returninner, cheapest_to_return

    def yield_vendor(self, transfer_meta):
        to_yield = TripadvisorInventoryItem()
        ct_pric_her, cheapest_ota_data, cheapest_pric_her, cheapest_ota_name = [
            '']*4
        vendor_prices, vendor_names = ['']*2
        if transfer_meta.get('ct_data', ''):
            ct_pric_her = transfer_meta['ct_data'][0]
        if transfer_meta.get('cheapest_ota_data', ''):
            cheapest_pric_her, cheapest_ota_name = transfer_meta['cheapest_ota_data']
        if transfer_meta.get('cheapest_proper_ota', ''):
            vendor_prices, vendor_names = transfer_meta['cheapest_proper_ota']
        status = transfer_meta.get('status', '')
        if transfer_meta.get('status_inner_message') == "room name not found":
            status = "room name not found for ct or cheapest ota"
        to_yield.update({"sk": transfer_meta.get('sk', ''), "city_name": transfer_meta.get('city_name', ), "property_name": transfer_meta.get('propert_name', ''), "TA_hotel_id": transfer_meta.get('TA_hotel_id', ''), "CT_hotel_id": transfer_meta.get('ctid', ''), "checkin": transfer_meta.get('checkin', ''), "DX": transfer_meta.get('dx', ''), "Pax": transfer_meta.get('pax', ''), "ct_price": ct_pric_her, "cheapest_ota_price": cheapest_pric_her, "cheapest_ota_name": normalize_clean(
            cheapest_ota_name), "ct_room_name": normalize_clean(transfer_meta.get('cleartrip_room_name', '')), "cheapest_ota_room_name": normalize_clean(transfer_meta.get('cheapest_room_name', '')), "status": normalize_clean(status), "which_case": vendor_prices,  "Ranking_ClearTrip": transfer_meta.get('Ranking_ClearTrip', ''), "Time": transfer_meta.get('average_3_cheapest_ots', ''), "reference_url": transfer_meta.get('cheaperst_url', ''), "main_url": transfer_meta.get('which_case', ''), "from_ta_url": vendor_names})
        return to_yield

    def parse_next(self, response):
        in_out_dates = tuple(response.meta.get('loss').split(
            '_')+response.meta.get('dxs').split('-'))
        if response.meta.get('req') == 2:
            ctid = response.meta.get('ctid', '')
            sel = Selector(response)
            check_loading = sel.xpath(
                '//span[@class="providerLogo"]/following-sibling::div[1][@class="loading"]/img/@src').extract()
            tracking_check = ''.join(
                sel.xpath('//div[@class="impressionTrackingTree"]/comment()').extract())
            if (check_loading and '\PP:' in tracking_check) or (check_loading):
                self.cursor.execute(self.update_query_ta %
                                    (self.name, '8', response.meta.get('sk')))
            else:
                final_dict, final_dict_navigations = {}, {}
                if tracking_check and not check_loading:
                    location_tracking = ''.join(
                        re.findall('\/L:(.*?)\/', tracking_check))
                    tracking_check_ = tracking_check.split('\\\\N')
                    for tch in tracking_check_:
                        rank = ''.join(re.findall(':(\d+)/PT', tch))
                        vendor = ''.join(re.findall('\\PN:(.*?)\\\\', tch))
                        price = ''.join(re.findall('\\PP:(.*?)\\\\', tch))
                        tax = ''.join(re.findall('\\PF:(.*?)\\\\', tch))
                        status = ''.join(re.findall('\\PA:(.*?)\\\\', tch))
                        bucket_ = ''.join(re.findall('\\PB:(.*?)\\\\', tch))
                        src_ = ''.join(re.findall('\\OI:(.*?)\\\\', tch))
                        url = ''
                        if location_tracking and src_ and in_out_dates:
                            url = "https://www.tripadvisor.in/Commerce?src=%s&geo=%s&from=HotelDateSearch_Hotel_Review&bucket=%s&clt=D&adults=2&child_rm_ages=&outYear=%s&outMonth=%s&outDay=%s&inYear=%s&inMonth=%s&inDay=%s&rooms=1&def_d=false&def_d=false&tp=HR_MainCommerce" % (
                                src_, location_tracking, bucket_, in_out_dates[0], in_out_dates[1], in_out_dates[2], in_out_dates[3], in_out_dates[4], in_out_dates[5])
                            final_dict_navigations.update({vendor: url})
                        if not rank:
                            rank = '-'
                        if not vendor:
                            vendor = '-'
                        if not price:
                            price = '0'
                        if not tax:
                            tax = '0'
                        if not status:
                            status = '-'
                        total = int(price)+int(tax)
                        final_dict.update(
                            {vendor: [rank, vendor, price, tax, status, total]})
                if not tracking_check:
                    self.log.info(
                        "Not getting data for the response url : %s" % response.url)
                    self.cursor.execute(self.update_query_ta %
                                        (self.name, '10', response.meta.get('sk')))
                if check_loading:
                    self.log.info(
                        "More time taking to get response : %s" % response.url)
                    self.cursor.execute(self.update_query_ta %
                                        (self.name, '7', response.meta.get('sk')))
                if final_dict:
                    filter_0and_ = filter(
                        lambda k: k[-1] != '-' and k[-1] != '0' and k[-1] != '' and k[-1] != 0, final_dict.values())
                    to_find_cheapest_three = [
                        (int(val[5]), val[1]) for val in filter_0and_ if val[5] != '0' and val[1] != 'ClearTrip' and val[5] != 0]
                    ct_pric = [chct for chct in filter_0and_ if chct[1] ==
                               'ClearTrip' and chct[0] != '0' and chct[0] != '-' and chct[0] != 0]
                    if not ct_pric:
                        ct_pric = [chct for chct in filter_0and_ if chct[1] ==
                                   'ClearTripIntl' and chct[0] != '0' and chct[0] != '-' and chct[0] != 0]
                    if ct_pric:
                        ct_data_re = (ct_pric[0][-1], ct_pric[0][1])
                    else:
                        ct_data_re = ''
                    cleartrip_ranking_inventory = final_dict.get(
                        'ClearTrip', '')
                    if not cleartrip_ranking_inventory:
                        final_dict.get('ClearTripIntl', '')
                    if cleartrip_ranking_inventory:
                        cleartrip_ranking_inventory = cleartrip_ranking_inventory[0]
                    meta_dict = {"ct_data": ct_data_re, "sk": response.meta.get('sk', ''), "city_name": response.meta.get('city_name', ''), "propert_name": response.meta.get('hotel_name', ''), "TA_hotel_id": response.meta.get('hotel_id', ''), "ctid": response.meta.get(
                        'ctid', ''), "checkin": response.meta.get('dxs'), "dx": response.meta.get('DX_num'), "pax": response.meta.get('PAX_val'),  "Ranking_ClearTrip": cleartrip_ranking_inventory, "time_in": response.meta.get('full_time', ''), "checkout":response.meta.get('loss', '')}
                    if len(filter_0and_) > 2 and len(to_find_cheapest_three) >= 3 and ct_pric:
                        update_cheapest_three = sorted(
                            to_find_cheapest_three, key=itemgetter(0))[0:3]
                        uctt = sum([asa[0] for asa in update_cheapest_three])/3
                        dif_pr = float(
                            (ct_pric[0][-1]) - (uctt))
                        dif_lo = self.rate_avg_dict.get(ctid, '')
                        if dif_lo:
                            if dif_pr > float(dif_lo):
                                cheapest_to_return = min(
                                    update_cheapest_three, key=lambda t: t[0])
                                cheapest_to_return, cheapest_proper_ota = self.cheapest_re(
                                    update_cheapest_three, cheapest_to_return)
                                cheapest_to_return_ct = ct_pric[0][-1], ct_pric[0][1]
                                if final_dict_navigations[cheapest_to_return[-1]] and final_dict_navigations[cheapest_to_return_ct[-1]]:
                                    cturl_checkin_ = datetime.datetime.strftime((datetime.datetime.strptime(
                                        meta_dict.get('checkin', ''), '%Y-%m-%d')), '%d/%m/%Y')
                                    cturl_checkout = datetime.datetime.strftime((datetime.datetime.strptime(
                                        response.meta.get('loss', ''), '%Y_%m_%d')), '%d/%m/%Y')
                                    ct_url_ = "https://www.cleartrip.com/hotels/service/rate-calendar?chk_in=%s&chk_out=%s&num_rooms=1&adults1=2&children1=0&shwb=true&adults=2&childs=0&ct_hotelid=%s&pahCCRequired=true&bestprice=true" % (
                                        cturl_checkin_, cturl_checkout, ctid)
                                    meta_dict.update({"ct_url": ct_url_, "status": "success", "which_case": "case_one",
                                                      "cheapest_ota_data": cheapest_to_return, "cheapest_proper_ota": cheapest_proper_ota, "average_3_cheapest_ots": uctt})
                                    yield Request(final_dict_navigations[cheapest_to_return[-1]], callback=self.parse_vendor, dont_filter=True, meta=meta_dict)
                                else:
                                    statuss_ = 'Vendor url is not preset as static keys are changed, failed'
                                    meta_dict.update(
                                        {"status": statuss_, "which_case": "case_one"})
                                    vendor_iyield = self.yield_vendor(
                                        meta_dict)
                                    if vendor_iyield:
                                        yield vendor_iyield
                            else:
                                statuss_ = 'greater than condition not satisfied, it is lower, failed'
                                meta_dict.update(
                                    {"status": statuss_, "which_case": "case_one"})
                                vendor_iyield = self.yield_vendor(meta_dict)
                                if vendor_iyield:
                                    yield vendor_iyield
                        else:
                            statuss_ = 'average price is not present for this hotel, failed'
                            meta_dict.update(
                                {"status": statuss_, "which_case": "case_one"})
                            vendor_iyield = self.yield_vendor(meta_dict)
                            if vendor_iyield:
                                yield vendor_iyield
                    elif len(to_find_cheapest_three) >= 4 and not ct_pric:
                        cheapest_to_return_one = min(
                            to_find_cheapest_three, key=lambda t: t[0])
                        update_cheapest_three = sorted(
                            to_find_cheapest_three, key=itemgetter(0))[0:3]
                        cheapest_to_return, cheapest_proper_ota = self.cheapest_re(
                            update_cheapest_three, cheapest_to_return_one)
                        if final_dict_navigations[cheapest_to_return[-1]]:
                            meta_dict.update({"ct_url": '', "status": "success", "which_case": "case_two",
                                              "cheapest_ota_data": cheapest_to_return, "cheapest_proper_ota": cheapest_proper_ota})
                            yield Request(final_dict_navigations[cheapest_to_return[-1]], callback=self.parse_vendor, dont_filter=True, meta=meta_dict)
                        else:
                            statuss_ = 'Vendor url is not preset as static keys are changed, failed'
                            meta_dict.update(
                                {"status": statuss_, "which_case": "case_two"})
                            vendor_iyield = self.yield_vendor(meta_dict)
                            if vendor_iyield:
                                yield vendor_iyield
                    else:
                        statuss_ = 'we dont have atleast 3 or 4 cheapest OTA prices, failed'
                        meta_dict.update(
                            {"status": statuss_, "which_case": "case_one_two"})
                        vendor_iyield = self.yield_vendor(meta_dict)
                        if vendor_iyield:
                            yield vendor_iyield
                    to_find_cheaper = [(int(val[2]), val[1])
                                       for val in final_dict.values() if val[2] != '0']
                    min_fin = {}
                    if to_find_cheaper:
                        min_fin = min(to_find_cheaper, key=lambda t: t[0])
                    if min_fin:
                        min_fin = {min_fin[1]: min_fin[0]}
                    for keyf, valuf in final_dict.iteritems():
                        if keyf in min_fin.keys():
                            cheaper = 'Y'
                        else:
                            cheaper = 'N'
                        final_dict[keyf].extend(cheaper)
                    default_val_list = ['-', '-', '-', '-', '-', '-', '-']
                    agoda = final_dict.get('Agoda', default_val_list)
                    if agoda == default_val_list:
                        agoda = final_dict.get('AgodaIntl', default_val_list)
                    booking_com = final_dict.get(
                        'BookingCom', default_val_list)
                    if booking_com == default_val_list:
                        booking_com = final_dict.get(
                            'BookingComIntl', default_val_list)
                    cleartrip = final_dict.get('ClearTrip', default_val_list)
                    if cleartrip == default_val_list:
                        cleartrip = final_dict.get(
                            'ClearTripIntl', default_val_list)
                    expedia = final_dict.get('Expedia', default_val_list)
                    if expedia == default_val_list:
                        expedia = final_dict.get(
                            'ExpediaIntl', default_val_list)
                    goibibo = final_dict.get('Goibibo', default_val_list)
                    if goibibo == default_val_list:
                        goibibo = final_dict.get(
                            'GoibiboIntl', default_val_list)
                    hotelscom = final_dict.get('HotelsCom2', default_val_list)
                    if hotelscom == default_val_list:
                        hotelscom = final_dict.get(
                            'HotelsCom2Intl', default_val_list)
                    makemytrip = final_dict.get('MakeMyTrip', default_val_list)
                    if makemytrip == default_val_list:
                        makemytrip = final_dict.get(
                            'MakeMyTripIntl', default_val_list)
                    yatra = final_dict.get('Yatra', default_val_list)
                    if yatra == default_val_list:
                        yatra = final_dict.get('YatraIntl', default_val_list)
                    tg = final_dict.get('TG', default_val_list)
                    if tg == default_val_list:
                        tg = final_dict.get('TGIntl', default_val_list)
                    stayzilla = final_dict.get('Stayzilla', default_val_list)
                    if stayzilla == default_val_list:
                        stayzilla = final_dict.get(
                            'StayzillaIntl', default_val_list)

                    total_dict = TRIPADVISORItem()
                    total_dict.update({"sk": response.meta.get('sk', ''), "city_name": response.meta.get('city_name', ''),
                                       "property_name": response.meta.get('hotel_name', ''),
                                       "TA_hotel_id": response.meta.get('hotel_id', ''),
                                       "checkin": response.meta.get('dxs'), "DX": response.meta.get('DX_num'),
                                       "Pax": response.meta.get('PAX_val'), "Ranking_Agoda": agoda[0],
                                       "Ranking_BookingCom": booking_com[0], "Ranking_ClearTrip": cleartrip[0],
                                       "Ranking_Expedia": expedia[0], "Ranking_Goibibo": goibibo[0],
                                       "Ranking_HotelsCom2": hotelscom[0], "Ranking_MakeMyTrip": makemytrip[0],
                                       "Ranking_Yatra": yatra[0], "Ranking_TG": tg[0], "Price_Agoda": agoda[2],
                                       "Price_BookingCom": booking_com[2], "Price_ClearTrip": cleartrip[2],
                                       "Price_Expedia": expedia[2], "Price_Goibibo": goibibo[2],
                                       "Price_HotelsCom2": hotelscom[2], "Price_MakeMyTrip": makemytrip[2],
                                       "Price_Yatra": yatra[2], "Price_TG": tg[2], "Tax_Agoda": agoda[3],
                                       "Tax_BookingCom": booking_com[3], "Tax_ClearTrip": cleartrip[3],
                                       "Tax_Expedia": expedia[3], "Tax_Goibibo": goibibo[3], "Tax_HotelsCom2": hotelscom[3],
                                       "Tax_MakeMyTrip": makemytrip[3], "Tax_Yatra": yatra[3],
                                       "Tax_TG": tg[3], "Total_Agoda": agoda[5], "Total_BookingCom": booking_com[5],
                                       "Total_ClearTrip": cleartrip[5], "Total_Expedia": expedia[5],
                                       "Total_Goibibo": goibibo[5], "Total_HotelsCom2": hotelscom[5],
                                       "Total_MakeMyTrip": makemytrip[5], "Total_Yatra": yatra[5], "Total_TG": tg[5],
                                       "Cheaper_Agoda": agoda[6], "Cheaper_BookingCom": booking_com[6],
                                       "Cheaper_ClearTrip": cleartrip[6], "Cheaper_Expedia": expedia[6],
                                       "Cheaper_Goibibo": goibibo[6], "Cheaper_HotelsCom2": hotelscom[6],
                                       "Cheaper_MakeMyTrip": makemytrip[6], "Cheaper_Yatra": yatra[6],
                                       "Cheaper_TG": tg[6], "Status_Agoda": agoda[4],
                                       "Status_BookingCom": booking_com[4], "Status_ClearTrip": cleartrip[4],
                                       "Status_Expedia": expedia[4], "Status_Goibibo": goibibo[4],
                                       "Status_HotelsCom2": hotelscom[4], "Status_MakeMyTrip": makemytrip[4],
                                       "Status_Yatra": yatra[4], "Status_TG": tg[4],
                                       "Ranking_Stayzilla": stayzilla[0], "Price_Stayzilla": stayzilla[2],
                                       "Tax_Stayzilla": stayzilla[3], "Total_Stayzilla": stayzilla[5],
                                       "Cheaper_Stayzilla": stayzilla[6], "Status_Stayzilla": stayzilla[4],
                                       "Time": response.meta.get('full_time', ''), "reference_url": response.url})
                    yield total_dict
                    self.cursor.execute(self.update_query_ta %
                                        (self.name, '1', response.meta.get('sk')))
