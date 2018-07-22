import os
import re
import json
import csv
import sys
import md5
import MySQLdb
import hashlib
import datetime
import operator
import logging
import requests
from CTPCC.utils import *
from scrapy import log
from scrapy import signals
from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher


class CleartripRoundTripBrowse(Spider):
    name = "cleartripkwd_browse"
    start_urls = []

    def __init__(self, *args, **kwargs):
        super(CleartripRoundTripBrowse, self).__init__(*args, **kwargs)
        self.crawl_type = kwargs.get('crawl_type', '')
        self.trip_type = kwargs.get('trip_type', '')
        self.limit = kwargs.get('limit', '')
        #self.source_name = kwargs.get('source', '')
        self.source_name = 'cleartripkwd'
        '''
        if not self.source_name:
            self.source_name = 'cleartripkwd'
            if self.trip_type == 'roundtrip':
                file_name = 'cleartrippbsrt'
            else:
                file_name = 'cleartrippbs'
        else:
            file_name = self.source_name
        '''
        self.log = create_logger_obj(self.source_name)
        self.out_put, self.out_put_file = get_output_file(self.source_name)
        self.cr_tabe = create_crawl_table_cursor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.out_put.close()
        self.cr_tabe.close()
        move_crawlout_processing(self.out_put_file)

    def start_requests(self):
        '''
        requests = terminal_requests(
            self.cr_tabe, self.source_name, self.crawl_type, self.trip_type, self.limit)
        '''
        requests = [("nkjsadfklaf", "BAH", "KWI", "2018-07-26", "1", '2018-08-26')]
        for input_ in requests:
            got_sk, from_, to_, date, dx, re_date = input_
            from_ = from_.strip()
            to_ = to_.strip()
            self.no_of_pax = '1'
            self.route = '%s-%s'%(from_, to_)
            #date = str(date.date())
            if self.trip_type == 'roundtrip':
                re_date = '2018-08-26'#str(re_date.date())
                url = 'https://meta.cleartrip.com/air/1.0/search?from=%s&to=%s&depart-date=%s&return-date=%s&adults=1&currency=KWD&jsonVersion=1.0' % (
                    from_, to_, date, re_date)
            elif self.trip_type == 'oneway':
                url = 'https://meta.cleartrip.com/air/1.0/search?from=%s&to=%s&depart-date=%s&adults=1&jsonVersion=1.0&currency=KWD' % (
                    from_, to_, date)
            headers = {
                'X-CT-API-KEY': 'bce875d513bab5fa2cba6371f7b1ea58',
                'X-CT-SOURCETYPE': 'B2C'
            }
            yield Request(url, callback=self.parse, headers=headers, meta={'d_date': date, 'from_': from_, 'to_': to_, 're_date': re_date, 'dx': dx, 'got_sk': got_sk})

    def parse(self, response):
        sel = Selector(response)
        date = response.meta.get('d_date', '')
        re_date = response.meta.get('re_date', '')
        from_ = response.meta['from_']
        to_ = response.meta['to_']
        seg = '%s-%s' % (from_, to_)
        re_seg = '%s-%s' % (to_, from_)
        got_sk = response.meta.get('got_sk', '')
        dx = response.meta.get('dx', '')
        body = json.loads(response.body)
        content = body.get('content', {})
        mapping = body.get('mapping', {})
        air_names = body.get('jsons', {}).get('airline_names', {})
        fares = body.get('fare', {})
        oneway_mapping = mapping.get('onward', [])
        return_mapping = mapping.get('return', [])
        if self.crawl_type == 'international':
            seg_price_order = self.get_international_price_order(
                oneway_mapping, content, fares, date, seg, air_names, re_date, dx)
            ow_sorted = self.get_sorted_values(seg_price_order)
            ow_fin_dict = self.get_finalranking(ow_sorted)
            for key, vals in ow_fin_dict.iteritems():
                self.out_put.write('%s\n' % '#<>#'.join(vals))
            got_page(self.cr_tabe, self.source_name, got_sk,
                     '1', self.crawl_type, self.trip_type)
        else:
            seg_price_order = self.get_price_order_dict(
                oneway_mapping, content, fares, date, seg, air_names, dx)
            return_price_order = self.get_price_order_dict(
                return_mapping, content, fares, date, re_seg, air_names, dx)
            ow_sorted = self.get_sorted_values(seg_price_order)
            rt_sorted = self.get_sorted_values(return_price_order)
            ow_fin_dict = self.get_finalranking(ow_sorted)
            rt_fin_dict = self.get_finalranking(rt_sorted)
            temp_val = ''
            for key, vals in ow_fin_dict.iteritems():
                if temp_val != vals[12]:
                    self.out_put.write('%s\n' % '#<>#'.join(vals))
                temp_val = vals[12]
            rt_temp_val = ''
            for key, vals in rt_fin_dict.iteritems():
                if rt_temp_val != vals[12]:
                    self.out_put.write('%s\n' % '#<>#'.join(vals))
                rt_temp_val = vals[12]
            got_page(self.cr_tabe, self.source_name, got_sk,
                     '1', self.crawl_type, self.trip_type)

    def get_finalranking(self, sorted_x):
        fin_rank, dict_ = 1, {}
        for i in sorted_x:
            lsttt = sorted(i[1], key=lambda x: (x[4]))
            for k in lsttt:
                sk, fare, air_name, de_dat, ar_dat, rank, seg, flts_lst, sk, \
                    aux_info, ct_base_fare, ct_tax_fare, dx, ct_discount, price_slashed, no_of_stops = k
                '''
                vals = (
                    str(sk), str(seg), str(de_dat), str(
                        ar_dat), 'Cleartrip', str(no_of_stops), str(flts_lst),
                    str(ct_base_fare), str(ct_tax_fare), str(ct_discount), str(
                        price_slashed), str(fare),  str(fin_rank),
                    str(dx), str(self.crawl_type.capitalize()), str(
                        self.trip_type.capitalize()), aux_info

                )'''
                aux_ = json.loads(aux_info)
                aux = aux_.get('return_details', {})
                aux_.update({'FareBreakupdetails': {'infantprice': u'', 'taxesprice': ct_tax_fare, 'adultprice': u'', 'childprice': u'', 'basefare':ct_base_fare}})
                vals = (str(sk), str(fare), str(air_name), str(de_dat), str(ar_dat), str(fin_rank), self.crawl_type, str(seg), self.trip_type.capitalize(),
                        str(flts_lst), self.no_of_pax, str(no_of_stops),str(aux.get('airline', '')), str(aux.get('depature', '')),
                        str(aux.get('arrival', '')), str(aux.get('segments', '')), str(aux.get('flight_no', '')),
                        str(aux.get('no_of_stops', '')), str(dx), self.route, str(json.dumps(aux_))
                )
                dict_.update({fin_rank: vals})
                fin_rank = fin_rank + 1
        return dict_

    def get_sorted_values(self, seg_price_order):
        rank, price_, lst_, lst, fin_dict = 0, 0, {}, {}, {}
        lsss = []
        for idx, i in enumerate(seg_price_order):
            price = i[1]
            try:
                nex_price = seg_price_order[idx+1][1]
            except:
                nex_price = 0
            lsss.append(i)
            lst.update({rank: lsss})
            if price != nex_price:
                rank = rank + 1
                lsss = []
        fin_dict = {}
        for key, val in lst.iteritems():
            price = val[0][1]
            fin_dict.update({price: val})
        sorted_x = sorted(fin_dict.items(), key=operator.itemgetter(0))
        return sorted_x

    def get_price_order_dict(self, oneway_mapping, content, fares, date, seg, air_names, dx):
        segments_lst, seg_price_order = [], []
        temp_dict = {}
        for rank, ow in enumerate(oneway_mapping, 1):
            seg_details, status, aux_info = {}, False, {}
            ct_discount, price_slashed = ['']*2
            cont_code_lst = ow.get('c', [])
            fare_code = ow.get('f', '')
            fare_dict = fares.get(fare_code, {})
            fr_ = fare_dict.get('dfd', '')
            fare_ = fare_dict.get('HBAG', {}).get('dfd', {})
            if fare_:
                fare_ = fare_dict.get('HBAG', {}).get(fare_, {}).get('pr', '')
            if not fare_:
                fare_ = fare_dict.get(fr_, {}).get('pr', '')
            full_tax_dict = fare_dict.get(fr_, {})
            ct_base_fare = full_tax_dict.get('bp', '0')
            ct_tax_fare = full_tax_dict.get('t', '')
            flts_lst, air_name = [], []
            sk_date = str(datetime.datetime.now())
            sk = str(hashlib.md5('%s%s' %
                                 (str(cont_code_lst), sk_date)).hexdigest())
            ar_seg_time, de_seg_time = '', ''
            aux_info['flights'] = full_tax_dict
            no_of_stops = len(cont_code_lst) - 1
            if len(cont_code_lst) == 0:
                no_of_stops = 0
            for seg_idx, i in enumerate(cont_code_lst):
                i = content.get(i, {})
                flt_dict = {}
                ar_date = i.get('ad', '')
                ar_time = i.get('a', '')
                ar_seg_time = ar_time
                ar_ori = i.get('fr', '')
                ar_dest = i.get('to', '')
                flt_key = i.get('fk', '')
                flight_no = ''.join(re.findall('_(\w{2}-\d+)_', flt_key))
                de_seg_t = ''.join(re.findall('_(\d+:\d+)_', flt_key))
                if seg_idx == 0:
                    de_seg_time = de_seg_t
                air_code = flight_no.split('-')[0].strip()
                airline = air_names.get(air_code, '').title()
                if airline:
                    air_name.append(airline)
                flts_lst.append(flight_no)
            ar_dat = '%s %s' % (date, ar_seg_time)
            de_dat = '%s %s' % (date, de_seg_time)
            aux_info['dx'] = dx
            seg_price_order.append([sk, fare_, '<>'.join(air_name), de_dat, ar_dat, '0', seg, '<>'.join(
                flts_lst), sk, json.dumps(aux_info), ct_base_fare, ct_tax_fare, dx, ct_discount, price_slashed, no_of_stops])
        return seg_price_order

    def get_international_price_order(self, oneway_mapping, content, fares, date, seg, air_names, re_date, dx):
        segments_lst, seg_price_order = [], []
        temp_dict = {}
        for rank, ow in enumerate(oneway_mapping, 1):
            ct_discount, price_slashed = ['']*2
            seg_details, status = {}, False
            aux_info, return_details = {}, {}
            cont_code_lst = ow.get('c', [])
            fare_code = ow.get('f', '')
            fare_dict = fares.get(fare_code, {})
            fr_ = fare_dict.get('dfd', '')
            fare_ = fare_dict.get('HBAG', {}).get('dfd', {})
            if fare_:
                fare_ = fare_dict.get('HBAG', {}).get(fare_, {}).get('pr', '')
            if not fare_:
                fare_ = fare_dict.get(fr_, {}).get('pr', '')
            full_tax_dict = fare_dict.get(fr_, {})
            ct_base_fare = full_tax_dict.get('bp', '0')
            ct_tax_fare = full_tax_dict.get('t', '')
            flts_lst, air_name = [], []
            sk_date = str(datetime.datetime.now())
            sk = str(hashlib.md5('%s%s' %
                                 (str(cont_code_lst), sk_date)).hexdigest())
            ar_seg_time, de_seg_time = '', ''
            try: ow_map_lst, rt_map_lst = cont_code_lst
            except:
                ow_map_lst = cont_code_lst[0]
                rt_map_lst = []
            flts_lst, air_name, ar_seg_time, de_seg_time, no_of_stops = self.get_flight_details(
                ow_map_lst, air_names, content)
            re_flt_lst, re_air_name, re_ar_seg_time, re_de_seg_time, rt_no_of_stops = self.get_flight_details(
                rt_map_lst, air_names, content)
            ar_dat = '%s %s' % (date, ar_seg_time)
            de_dat = '%s %s' % (date, de_seg_time)
            re_ar_dat = '%s %s' % (re_date, re_ar_seg_time)
            re_de_dat = '%s %s' % (re_date, re_de_seg_time)
            return_details.update({'flight_no': '<>'.join(re_flt_lst),
                                   'airline': '<>'.join(re_air_name),
                                   'arrival': re_ar_dat,
                                   'depature': re_de_dat,
                                   'no_of_stops': rt_no_of_stops,
                                   })
            aux_info.update({'return_details': return_details})
            aux_info['flights'] = full_tax_dict
            aux_info['dx'] = dx
            seg_price_order.append([sk, fare_, '<>'.join(air_name), de_dat, ar_dat, '0', seg, '<>'.join(
                flts_lst), sk, json.dumps(aux_info), ct_base_fare, ct_tax_fare, dx, ct_discount, price_slashed, no_of_stops])
        return seg_price_order

    def get_flight_details(self, map_lst, air_names, content):
        ar_seg_time, de_seg_time = '', ''
        flts_lst, air_name = [], []
        no_of_stops = len(map_lst) - 1
        if len(map_lst) == 0:
            no_of_stops = 0
        for seg_idx, i in enumerate(map_lst):
            i = content.get(i, {})
            flt_dict = {}
            ar_date = i.get('ad', '')
            ar_time = i.get('a', '')
            ar_seg_time = ar_time
            ar_ori = i.get('fr', '')
            ar_dest = i.get('to', '')
            flt_key = i.get('fk', '')
            flight_no = ''.join(re.findall('_(\w{2}-\d+)_', flt_key))
            de_seg_t = ''.join(re.findall('_(\d+:\d+)_', flt_key))
            if seg_idx == 0:
                de_seg_time = de_seg_t
            air_code = flight_no.split('-')[0].strip()
            airline = air_names.get(air_code, '').title()
            if airline:
                air_name.append(airline)
            flts_lst.append(flight_no)
        return (flts_lst, air_name, ar_seg_time, de_seg_time, no_of_stops)
