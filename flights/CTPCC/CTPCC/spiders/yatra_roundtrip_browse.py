import csv
import datetime
import hashlib
import json
import logging
import md5
import operator
import os
import re
import requests
import sys

from scrapy.xlib.pydispatch import dispatcher
from operator import itemgetter
from scrapy.http import FormRequest
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy import signals
from scrapy.spider import Spider
from scrapy import log

import MySQLdb

from pbm_scrapers.utils import *


class YatraRoundTripBrowse(Spider):
    name = "yatrapbs_browse"
    start_urls = []
    def __init__(self, *args, **kwargs):
        super(YatraRoundTripBrowse, self).__init__(*args, **kwargs)

        self.crawl_type = kwargs.get('crawl_type', '')
        self.trip_type = kwargs.get('trip_type', '')
        self.source_name = kwargs.get('source', '')
        self.iter_count = 0
        if not self.source_name:
            self.source_name = 'yatrapbs'
            if self.trip_type == 'roundtrip':
                file_name = 'yatrapbsrt'
            else:
                file_name = 'yatrapbs'
        else:
            file_name = self.source_name
        self.log = create_logger_obj(self.source_name)
        self.out_put, self.out_put_file = get_output_file(file_name)
        self.cr_tabe = create_crawl_table_cursor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        stats = self.crawler.stats.get_stats()
        self.out_put.close()
        self.cr_tabe.close()
        move_crawlout_processing(self.out_put_file)

    def start_requests(self):
        requests = terminal_requests(self.cr_tabe, self.source_name, self.crawl_type, self.trip_type, self.limit)
        for input_ in requests:
            got_sk, from_, to_, date, dx, re_date = input_
            from_ = from_.strip()
            to_ = to_.strip()
            date_ = datetime.datetime.strftime(date, '%d/%m/%Y')
            date = datetime.datetime.strftime(date, '%Y-%m-%d')
            redate = ''
            if self.trip_type == 'roundtrip':
                redate = datetime.datetime.strftime(re_date, '%Y-%m-%d')
                re_date = datetime.datetime.strftime(re_date, '%d/%m/%Y')
            if self.crawl_type == 'international' and self.trip_type == 'oneway':
	            url = 'https://flight.yatra.com/air-search-ui/int2/trigger?ADT=1&CHD=0&INF=0&class=Economy&destination=%s&flexi=0&flight_depart_date=%s&noOfSegments=1&origin=%s&source=fresco-home&type=O'%(to_, date_, from_)
            elif self.crawl_type == 'international' and self.trip_type == 'roundtrip':
                url = 'https://flight.yatra.com/air-search-ui/int2/trigger?ADT=1&CHD=0&INF=0&arrivalDate=%s&class=Economy&destination=%s&flexi=0&flight_depart_date=%s&noOfSegments=2&origin=%s&source=fresco-home&type=R&viewName=normal'%(re_date, to_, date_, from_)
            elif self.crawl_type == 'domestic' and self.trip_type == 'roundtrip':
                url = 'https://flight.yatra.com/air-search-ui/dom2/trigger?ADT=1&CHD=0&INF=0&arrivalDate='+re_date+'&class=Economy&destination='+to_+'&flexi=0&flight_depart_date='+date_+'&noOfSegments=2&origin='+from_+'&source=fresco-home&type=R&viewName=normal&version=1.1&destinationCountry=IN&&originCountry=IN'
            elif self.crawl_type == 'domestic' and self.trip_type == 'oneway':
                url = "https://flight.yatra.com/air-search-ui/dom2/trigger?type=O&viewName=normal&flexi=0&noOfSegments=1&origin="+ from_+"&originCountry=IN&destination="+to_+"&destinationCountry=IN&flight_depart_date="+date_+"&ADT=1&CHD=0&INF=0&class=Economy&source=fresco-home&version=1.1"
            yield Request(url, callback=self.parse, meta={'d_date':date, 'from_':from_, 'to_':to_, 're_date':redate, 'dx':dx})
    def parse(self, response):
        sel = Selector(response)
        date = response.meta.get('d_date', '')
        re_date = response.meta.get('re_date', '')
        from_ = response.meta.get('from_', '')
        to_ = response.meta.get('to_', '')
        seg = '%s-%s' % (from_, to_)
        re_seg = '%s-%s' % (to_, from_)
        dx = response.meta.get('dx', '')
        data = sel.xpath(
            '//script[@type="text/javascript"]//text()[contains(., "resultData")]').extract()
        body = json.loads(
            ''.join(re.findall('=(.*resultData.*)=?', ''.join(data))).strip('\r;'))
        resultdata = body.get('resultData', [])
        if len(resultdata[0].keys()) < 2 and self.iter_count <=5:
            self.iter_count += 1
            return Request(response.url, callback=self.parse, dont_filter=True, meta={'d_date':date, 'from_':from_, 'to_':to_, 're_date':re_date, 'dx':dx})
        elif self.iter_count > 5 and self.crawl_type !='international':
            return
        flt_lst_key = '%s%s%s' % (from_, to_, date.replace('-', ''))
        re_flt_lst_key = '%s%s%s' % (to_, from_, re_date.replace('-', ''))
        unorder_lst = self.get_flight_details(flt_lst_key, resultdata, seg, dx)
        if self.crawl_type == 'domestic':
            re_unorder_lst = self.get_flight_details(
                re_flt_lst_key, resultdata, re_seg, dx)
        else:
            re_unorder_lst = []
        self.write_datainto_file(unorder_lst)
        self.write_datainto_file(re_unorder_lst)

    def get_flight_details(self, flt_lst_key, resultdata, seg, dx):
        unorder_lst = []
        for res in resultdata:
            schedule_lst = res.get('fltSchedule', {}).get(flt_lst_key, {})
            airlinenames = res.get('fltSchedule', {}).get('airlineNames', {})
            fare_dict = {}
            fare_details = res.get('fareDetails', {}).get(flt_lst_key, {})
            fr_keys = fare_details.keys()
            sk = str(hashlib.md5('%s' % (str())).hexdigest())
            for fr in fr_keys:
                fr_ = fare_details.get(fr, {}).get(
                    'O', {}).get('ADT', {}).get('tf', '')
                fare_dict.update(
                    {fr: [fr_, fare_details.get(fr, {}).get('O', {})]})
            if isinstance(schedule_lst, dict):
                for key, ele in schedule_lst.iteritems():
                    return_details = {}
                    sk_date = str(datetime.datetime.now())
                    sk = str(hashlib.md5('%s%s' %
                                         (str(ele), sk_date)).hexdigest())
                    id_ = ele.get('ID', '')
                    no_of_stops = str(ele.get('OD', [{}])[0].get('ts', ''))
                    if no_of_stops:
                        no_of_stops = int(no_of_stops)
                    flt_od_ = ele.get('OD', [{}])[0].get('FS', [{}])
                    try:
                        re_flt_od_ = ele.get('OD', [{}, {}])[1].get('FS', [{}])
                    except:
                        re_flt_od_ = []
                    result = self.get_flt_details(
                        flt_od_, fare_details, airlinenames, id_)
                    airline_names, depart_date, arrival_date, flight_ids, base_price, total_price, taxes_price, discount_price, total_price_slashed, aux_info = result
                    #fare_val, airline_names, depart_date, arrival_date, \
                    #flight_ids, aux_info = self.get_flt_details(flt_od_, fare_details, airlinenames, id_)
                    if re_flt_od_:
                        result = self.get_flt_details(
                            flt_od_, fare_details, airlinenames, id_)
                        re_airline_names, re_depart_date, re_arrival_date, re_flight_ids, re_base_price, re_total_price, re_taxes_price, re_discount_price, re_total_price_slashed, re_aux_info = result
                        #re_fare_val, re_airline_names, re_depart_date, re_arrival_date, \
                        #re_flight_ids, re_aux_info = self.get_flt_details(re_flt_od_, fare_dict, airlinenames, id_)
                        return_details.update({'arrival': re_arrival_date, 'flight_no': re_flight_ids,
                                               'airline': re_airline_names, 'depature': re_depart_date})
                    aux_info.update({'return_details': return_details})
                    aux_info['dx'] = dx
                    val = [sk, seg, depart_date, arrival_date, airline_names, no_of_stops, flight_ids, base_price, taxes_price, discount_price,
                           total_price_slashed, total_price, dx, self.crawl_type.capitalize(), self.trip_type.capitalize(), json.dumps(aux_info)]
                    # val = [sk, fare_val, airline_names, depart_date, arrival_date,
                    #self.crawl_type.capitalize(), seg, self.trip_type.capitalize(),
                    # flight_ids, json.dumps(aux_info)]
                    unorder_lst.append(val)
            else:
                for ele in schedule_lst:
                    return_details = {}
                    no_of_stops = str(ele.get('OD', [{}])[0].get('ts', ''))
                    if no_of_stops:
                        no_of_stops = int(no_of_stops)
                    sk_date = str(datetime.datetime.now())
                    sk = str(hashlib.md5('%s%s' %
                                         (str(ele), sk_date)).hexdigest())
                    id_ = ele.get('ID', '')
                    flt_od_ = ele.get('OD', [{}])[0].get('FS', [{}])
                    # try: re_flt_od_ = ele.get('OD', [{}, {}])[1].get('FS', [{}])
                    try:
                        re_flt_od_ = ele.get('OD', [{}, {}])[1].get('FS', [{}])
                    except:
                        re_flt_od_ = []
                    #airline_names, depart_date, arrival_date, \
                      #[flight_ids], base_price,total_price,taxes_price,discount_price,total_price_slashed,aux_info = self.get_flt_details(flt_od_, fare_details, airlinenames, id_)
                    result = self.get_flt_details(
                        flt_od_, fare_details, airlinenames, id_)
                    airline_names, depart_date, arrival_date, flight_ids, base_price, total_price, taxes_price, discount_price, total_price_slashed, aux_info = result
                    if re_flt_od_:
                        result = self.get_flt_details(
                            flt_od_, fare_details, airlinenames, id_)
                        re_airline_names, re_depart_date, re_arrival_date, re_flight_ids, re_base_price, re_total_price, re_taxes_price, re_discount_price, re_total_price_slashed, re_aux_info = result

                        #re_fare_val, re_airline_names, re_depart_date, re_arrival_date, \
                        #re_flight_ids, re_aux_info = self.get_flt_details(re_flt_od_, fare_details, airlinenames, id_)
                        return_details.update({'arrival': re_arrival_date, 'flight_no': re_flight_ids,
                                               'airline': re_airline_names, 'depature': re_depart_date})
                    aux_info.update({'return_details': return_details})
                    aux_info['dx'] = dx
                    # val = [sk, fare_val, airline_names, depart_date, arrival_date,
                    #self.crawl_type.capitalize(), seg, self.trip_type.capitalize(),
                    # flight_ids, json.dumps(aux_info)]
                    val = [sk, seg, depart_date, arrival_date, airline_names, no_of_stops, flight_ids, base_price, taxes_price, discount_price,
                           total_price_slashed, total_price, dx, self.crawl_type.capitalize(), self.trip_type.capitalize(), json.dumps(aux_info)]
                    unorder_lst.append(val)
        return unorder_lst

    def get_flt_details(self, flt_od_, fare_details, airlinenames, id_):
        de_dat, ar_dat = ['']*2
        fr_ = {}
        flt_ids, airline_lst = [], []
        if bool(fare_details):
            fr_ = fare_details.get(id_, {}).get('O', {}).get('ADT', {})
            for key in fr_:
                fr_[key] == str(fr_[key])

        base_price, taxes_price, total_price = ['0.0']*3
        if bool(fr_):
            frnew_ = {}
            for key in fr_.keys():
                if type(fr_[key]) == float:
                    fr_[key] = str(int(round(fr_[key])))
                elif type(fr_[key]) == int:
                    fr_[key] = str(int(fr_[key]))
                else:
                    fr_[key] = fr_[key]

                if str(fr_[key]).isdigit():
                    frnew_[key] = int(str(fr_[key]))
            base_price = frnew_.pop('bf')
            total_price = frnew_.pop('tf')
            allvalues = frnew_.values()
            taxes_price = sum(allvalues)
        discount_price = 0.0
        total_price_slashed = 0.0
        for idx, flt_od in enumerate(flt_od_):
            air_code = flt_od.get('ac', '')
            flt_id = flt_od.get('fl', '')
            ddt = flt_od.get('ddt', '')
            adt = flt_od.get('adt', '')
            dd = flt_od.get('dd', '')
            ad = flt_od.get('ad', '')
            airline = airlinenames.get(air_code, '')
            airline_lst.append(airline)
            if idx == 0:
                de_dat = '%s %s' % (ddt, dd)
            ar_dat = '%s %s' % (adt, ad)
            flt_id = '%s-%s' % (air_code, flt_id)
            flt_ids.append(flt_id)
        aux_info = {}
        try:
            fare_val, fare_dict_ = fare_details.get(id_, '')
        except:
            fare_val, fare_dict_ = 0, {}
        base_fare = str(fr_.get('bf', ''))
        pax_service_fare = str(fr_.get('PSF', ''))
        udf = str(fr_.get('UDF', ''))
        yt_cute = str(fr_.get('YQ', ''))
        aux_info.update({'base_fare': base_fare, 'tax': 'PSF:%s, UDF:%s, YQ:%s' % (
            pax_service_fare, udf, yt_cute)})
        return ('<>'.join(airline_lst), de_dat, ar_dat, '<>'.join(flt_ids), base_price, total_price, taxes_price, discount_price, total_price_slashed, aux_info)

    def write_datainto_file(self, unorder_lst):
        price_order_lst = sorted(unorder_lst, key=itemgetter(1))
        f_list = self.get_sorted_values(price_order_lst)
        fin_dict = self.get_finalranking(f_list)
        for key, vals in fin_dict.iteritems():
            self.out_put.write('%s\n' % '#<>#'.join(vals))

    def get_finalranking(self, sorted_x):
        fin_rank, dict_ = 1, {}
        for i in sorted_x:
            lsttt = sorted(i[1], key=lambda x: (x[3]))
            for k in lsttt:
                #sk, fare, air_name, de_dat, ar_dat, seg_type, seg, trip_type, flts_ids, aux_ = k
                # vals = (str(sk), str(fare), str(air_name), str(de_dat), \
                # str(ar_dat), str(fin_rank), seg_type, str(seg), trip_type, str(flts_ids), aux_)
                sk, seg, de_dat, ar_dat, air_name, no_of_stops, flts_ids, base_price, taxes_price, discount_price, total_price_slashed, total_price, idx, seg_type, trip_type, aux_info = k
                vals = (str(sk), str(seg), str(de_dat),
                        str(ar_dat), str(air_name), str(no_of_stops), str(flts_ids), str(base_price), str(taxes_price), str(discount_price), str(total_price_slashed), str(total_price), str(fin_rank), str(idx), seg_type, trip_type, aux_info)
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
