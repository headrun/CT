'''Flights GoAir Amend Support functions'''
import ast
from collections import Counter
from ConfigParser import SafeConfigParser
import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import smtplib
from operator import itemgetter


_cfg = SafeConfigParser()
_cfg.read('airline_names.cfg')


class GoairAmendUtils(object):

    def get_pcc_name(self):
        pcc_name, amend_dict = '', {}
        data = self.amend_dict
        try: data_ = ast.literal_eval(data)
        except Exception as e:
            return (pcc_name, amend_dict, e.message)
        trip_ref = data_.get('trip_ref', '')
        trip_type = data_.get('trip_type', '')
        proceed_to_book = data_.get('proceed_to_book', 0)
        cabin_class = data_.get('cabin_class', 'Economy')
        tolerance_amount = data_.get('tolerance_amount', 0)
        pax_paid_amount = data_.get('cleartrip_price', 0)
        origin = data_.get('origin', '')
        destination = data_.get('destination', '')
        data_ = data_.get('details', [])
        if len(data_) > 1:
            self.multiple_pnr = True
            return pcc_name, amend_dict, "multiple PNRs not suported"
        if len(data_) == 0:
            return amend_dict, amend_dict, "No segments found"
        data_ = data_[0]
        pnr = data_.get('pnr', '')
        all_segment_details = data_.get('all_segment_details', [])
        all_pax_details = data_.get('all_pax_details', [])
        if all_pax_details:
            try: pax_last_name = all_pax_details[0][2]
            except: pax_last_name = ''
        flight_ids, return_flights_ids = self.get_segments(all_segment_details)
        amend_type = data_.get('amend_type', {}).get('type', '')
        amend_segment_details = data_.get('amend_segment_details', [])
        amend_ow_flt_list, amend_rt_flt_list = self.get_segments(amend_segment_details)
        amend_dict.update({
            'all_ow_flt':flight_ids,
            'all_rt_flt':return_flights_ids,
            'amend_ow_flt':amend_ow_flt_list,
            'amend_rt_flt':amend_rt_flt_list,
            'amend_type': amend_type,
            'trip_ref': trip_ref,
            'pnr': pnr,
            'origin': origin,
            'destination': destination,
            'trip_type':trip_type,
            'proceed_to_book': proceed_to_book,
            'cabin_class':cabin_class,
            'tolerance_amount':tolerance_amount,
            'pax_paid_amount': pax_paid_amount,
            'pax_last_name':pax_last_name,
        })
        pcc = data_.get('pcc', '')
        if pcc:
            pcc_name = 'goair_%s' % pcc
            return pcc_name, amend_dict, ""
        else:
            return pcc_name, amend_dict, "pcc not found"

    def get_segments(self, lists):
        list_, re_list = {}, {}
        for i in lists:
            flight_no = i.get('flight_no', '')
            seq_no = i.get('seq_no', '')
            if (seq_no == '1' or seq_no == 1) and flight_no:
                list_.update({flight_no:i})
            elif (seq_no == '2' or seq_no == 2) and flight_no:
                re_list.update({flight_no:i})
        return (list_, re_list)

    def get_trip_type(self, segments):
        all_ow_flt = segments.get('all_ow_flt', {})
        all_rt_flt = segments.get('all_rt_flt', {})
        if all_rt_flt:
            trip_type = 'RT'
        else:
            trip_type = 'OW'
        return trip_type

    def get_amend_type(self, amend_dict):
        rt_full_amend, ow_amend, rt_amend = False, False, False
        amend_ow_flt = amend_dict.get('amend_ow_flt', {})
        amend_rt_flt = amend_dict.get('amend_rt_flt', {})
        if amend_ow_flt and amend_rt_flt:
            rt_full_amend = True
        elif amend_ow_flt and not amend_rt_flt:
            ow_amend = True
        elif not amend_ow_flt and amend_rt_flt:
            rt_amend = True
        return (rt_full_amend, ow_amend, rt_amend)

    def get_segment_details(self, amend_dict):
        all_ow_flt = amend_dict.get('all_ow_flt', {})
        all_rt_flt = amend_dict.get('all_rt_flt', {})
        amend_ow_flt = amend_dict.get('amend_ow_flt', {})
        amend_rt_flt = amend_dict.get('amend_rt_flt', {})
        all_ow_sort_list = self.get_seg_list(all_ow_flt)
        all_rt_sort_list = self.get_seg_list(all_rt_flt)
        amend_ow_sort_list = self.get_seg_list(amend_ow_flt)
        amend_rt_sort_list = self.get_seg_list(amend_rt_flt)
        search_keys_dict, amd_search_keys_dict = {}, {}
        origin, dest, depature_date, rt_depature_date = ['']*4
        amd_ow_depature_date, amd_rt_depature_date = ['']*2
        if len(all_ow_sort_list) > 1:
            origin, dest_temp, dep, depature_date = all_ow_sort_list[0]
            origin_temp, dest, dep, depature_temp = all_ow_sort_list[-1]
        elif all_ow_sort_list:
            origin, dest, dep, depature_date = all_ow_sort_list[0]
        if len(all_rt_sort_list) > 1:
            rt_origin, rt_dest_temp, dep, rt_depature_date = all_rt_sort_list[0]
            rt_origin_temp, rt_dest, dep, rt_depature_temp = all_rt_sort_list[-1]
        elif all_rt_sort_list:
            rt_origin, rt_dest, dep, rt_depature_date = all_rt_sort_list[0]
        else:
            rt_origin, rt_dest, dep, rt_depature_date = ['']*4
        if amend_ow_sort_list:
            amd_ow_origin, amd_ow_dest, amd_ow_dep, amd_ow_depature_date = amend_ow_sort_list[0]
            amd_ow_origin_temp, amd_ow_dest, amd_ow_dep_temp, amd_ow_depature_date_temp = amend_ow_sort_list[-1]
        else:
            amd_ow_origin, amd_ow_dest, amd_ow_dep, amd_ow_depature_date = ['']*4
        if amend_rt_sort_list:
            amend_origin, amend_dest, amend_dep, amd_rt_depature_date = amend_rt_sort_list[0]
            amend_origin_temp, amend_dest, amend_dep_temp, amd_rt_depature_date_temp = amend_rt_sort_list[-1]
        else:
            amend_origin, amend_dest, amend_dep, amd_rt_depature_date = ['']*4

        if not amd_ow_depature_date:
            amd_ow_depature_date = depature_date
        search_keys_dict.update({
                'origin': origin,
                'destination': dest,
                'rt_origin':rt_origin,
                'rt_dest': rt_dest,
                'ow_amend_origin': amd_ow_origin,
                'ow_amend_dest': amd_ow_dest,
                'rt_amend_origin': amend_origin,
                'rt_amend_dest': amend_dest,
                'depature_date':depature_date,
                'rt_depature_date':rt_depature_date,
                'amd_ow_depature_date':amd_ow_dep,
                'amd_rt_depature_date':amend_dep,
        })
        return search_keys_dict

    def get_seg_list(self, all_ow_flt):
        list_ = []
        for flight_no, dict_ in all_ow_flt.iteritems():
            departure_date = dict_.get('departure_date', '').replace(' ', '')
            departure_time = dict_.get('departure_time', '').replace(' ', '')
            segment_dest = dict_.get('segment_dest', '')
            segment_src = dict_.get('segment_src', '')
            dep_date_time = datetime.datetime.strptime('%s %s'%(departure_date, departure_time), '%d-%b-%y %M:%S')
            date_format = datetime.datetime.strftime(dep_date_time, '%d %b %Y')
            if departure_date:
                list_.append([segment_src, segment_dest, dep_date_time, date_format])
        sort_list = sorted(list_, key=itemgetter(2))
        return sort_list

    def get_amend_sell_keys(self, amend_dict, avail_flights, cabin_class, return_flt=False):
        rt_flight_keys, flight_keys = [], []
        flight_keys = amend_dict.get('amend_ow_flt', {}).keys()
        if self.trip_type == 'OW':
            flight_keys = amend_dict.get('amend_ow_flt', {}).keys()
        elif self.ow_amendment:
            flight_keys = amend_dict.get('amend_ow_flt', {}).keys()
        elif self.rt_amendment:
            flight_keys = amend_dict.get('amend_rt_flt', {}).keys()
        else:
            flight_keys = amend_dict.get('amend_ow_flt', {}).keys()
        if return_flt:
            flight_keys = amend_dict.get('amend_rt_flt', {}).keys()
        fares_dict, flight_id  = self.get_flight_sell_key(flight_keys, avail_flights)
        ticket_class_dict = {'Economy' : 'economy', 'Business' : 'business'}
        fare_key, sell_key, price = fares_dict.get(ticket_class_dict.get(cabin_class, ''), ['']*3)
        return (fare_key, sell_key, flight_id)

    def get_flight_sell_key(self, flight_keys, avail_flights):
        sellkey, fares_ = '', {}
        fin_key =''
        avail_flts_list = avail_flights.keys()
        flight_key_list = list(set(flight_keys))
        flight_key_list = [x.replace(' ', '').strip() for x in flight_key_list]
        for f_key in avail_flts_list:
            temp_rank = 0
            f_key = f_key.split('<>')
            for j in flight_key_list:
                j = j.replace(' ', '').strip()
                if j in f_key:
                    temp_rank +=1
                if len(flight_keys) == temp_rank:
                    fin_key = f_key
                    break
        fares_dict = avail_flights.get('<>'.join(fin_key), {})
        return (fares_dict, fin_key)

    def get_travel_date(self, date):
        try:
            date_ = datetime.datetime.strptime(date.strip(), '%d-%b-%y')
            date_format = date_.strftime('%Y-%m-%d')
        except:
            date_format, day, month, year = ['']*4
        return date_format
