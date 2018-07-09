'''Flights Indigo Amend Support functions'''
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
_cfg.read('/root/scrapers/flights/amend_airline_names.cfg')


class SpicejetAmendUtils(object):

    def get_pcc_name(self):
        pcc_name, amend_dict = '', {}
	data = self.amend_dict
        try: data_ = ast.literal_eval(data)
	except Exception as e:
	    return (pcc_name, amend_dict, e.message)
	trip_ref = data_.get('trip_ref', '')
	origin = data_.get('origin_code', '')
	destination = data_.get('destination_code', '')
	trip_type = data_.get('trip_type', '')
	proceed_to_book = data_.get('proceed_to_book', 0)
	cabin_class = data_.get('cabin_class', 'Economy')
	tolerance_amount = data_.get('tolerance_amount', 0)
	pax_paid_amount = data_.get('cleartrip_price', 0)
	data_ = data_.get('details', [])
	if len(data_) > 1:
	    self.multiple_pnr = True
	    return pcc_name, amend_dict, "multiple PNRs not suported"
	if len(data_) == 0:
	    return amend_dict, amend_dict, "No segments found"
	data_ = data_[0]
	pnr = data_.get('pnr', '')
	all_segment_details = data_.get('all_segment_details', [])
	flight_ids, return_flights_ids, flt_list, _flt_list = self.get_segments(all_segment_details)
	amend_type = data_.get('amend_type', {}).get('type', '')
	amend_segment_details = data_.get('amend_segment_details', [])
	amend_ow_flt_list, amend_rt_flt_list, ow_flt_list, rt_flt_list = self.get_segments(amend_segment_details)
	ori_ow_flt_list, ori_rt_flt_list, _ow_flt_list, _rt_flt_list = self.get_segments(all_segment_details)
	amend_dict.update({
		'all_ow_flt':flight_ids,
		'all_rt_flt':return_flights_ids,
		'amend_ow_flt':amend_ow_flt_list,
		'amend_rt_flt':amend_rt_flt_list,
		'amend_ow_flt_time':ow_flt_list,
		'amend_rt_flt_time':rt_flt_list,
		'amend_type': amend_type,
		'trip_ref': trip_ref,
		'pnr': pnr,
		'trip_type':trip_type,
		'proceed_to_book': proceed_to_book,
		'cabin_class':cabin_class,
		'tolerance_amount':tolerance_amount,
		'pax_paid_amount': pax_paid_amount,
		'ori_ow_flt_list': ori_ow_flt_list,
		'ori_rt_flt_list':ori_rt_flt_list,
		'origin': origin,
		'destination': destination,
		'trip_ref': trip_ref,
	})
        pcc = data_.get('pcc', '')
        if pcc:
            pcc_name = 'spicejet_%s' % pcc
            return pcc_name, amend_dict, ""
	else:
	    return pcc_name, amend_dict, "pcc not found"

    def get_date_format(self, date):
	try:
		year = str(date.year)
        	month = str(date.month)
        	day = str(date.day)
	except:
	    _format = datetime.datetime.strptime(return_dapart_date, '%d-%b-%y')
            year = str(_format.year)
	    month = str(_format.month)
            day = str(_format.day)
	if len(day) == 1:
	    dat = '0%s'%day
	if len(month) == 1:
	    month = '0%s'%month
	year_month = '%s-%s'%(year, month)
	return (year_month, day)

    def get_segments(self, lists):
	list_, re_list, list_ow, re_list_ = {}, {}, {}, {}
	for i in lists:
            flight_no = i.get('flight_no', '')
	    departure_time = i.get('departure_time', '')
	    departure_date = i.get('departure_date', '')
	    date_time = '%s %s'%(departure_date, departure_time)
	    date_time = str(datetime.datetime.strptime(date_time, '%d-%b-%y %M:%S')) 
            seq_no = i.get('seq_no', '')
            if (seq_no == '1' or seq_no == 1) and flight_no:
                list_.update({flight_no:i})
		list_ow.update({date_time:i})
            elif (seq_no == '2' or seq_no == 2) and flight_no:
                re_list.update({flight_no:i})
		re_list_.update({date_time:i})
	return (list_, re_list, list_ow, re_list_)

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
	amend_ow_flt_time = amend_dict.get('amend_ow_flt_time', {})
        amend_rt_flt_time = amend_dict.get('amend_rt_flt_time', {})
	all_ow_sort_list = self.get_seg_list(all_ow_flt)
	all_rt_sort_list = self.get_seg_list(all_rt_flt)
	amend_ow_sort_list = self.get_seg_list(amend_ow_flt)
	amend_rt_sort_list = self.get_seg_list(amend_rt_flt)
	amend_ow_sort_time_list = sorted(amend_ow_flt_time.items())
	amend_rt_sort_time_list =  sorted(amend_rt_flt_time.items())
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
	else:
	    amd_ow_origin, amd_ow_dest, amd_ow_dep, amd_ow_depature_date = ['']*4
	if amend_rt_sort_list:
	    amend_origin, amend_dest, amend_dep, amd_rt_depature_date = amend_rt_sort_list[0]
	else:
	    amend_origin, amend_dest, amend_dep, amd_rt_depature_date = ['']*4
	if not amd_ow_depature_date:
	    amd_ow_depature_date = depature_date
	amend_ow_flt_time = amend_dict.get('amend_ow_flt_time', {})
	amend_rt_flt_time = amend_dict.get('amend_rt_flt_time', {})
	try:
	    rt_origin_ = amend_rt_sort_time_list[0][1].get('segment_src', '')
	    rt_amend_date = amend_rt_sort_time_list[0][1].get('departure_date', '')
	    rt_dest_ = amend_rt_sort_time_list[-1][1].get('segment_dest', '')
	except: rt_origin_, rt_dest_, rt_amend_date = ['']*3
	try:
	    origin_ = amend_ow_sort_time_list[0][1].get('segment_src', '')
	    dest_ = amend_ow_sort_time_list[-1][1].get('segment_dest', '')
	    ow_amend_date = amend_ow_sort_time_list[0][1].get('departure_date', '')
	except: origin_, dest_, ow_amend_date = ['']*3
	search_keys_dict.update({
		'origin': origin,
		'destination': dest,
		'rt_origin':rt_origin,
		'rt_dest': rt_dest,
		#'ow_amend_origin': amd_ow_origin,
		#'ow_amend_dest': amd_ow_dest,
		#'rt_amend_origin': amend_origin,
		#'rt_amend_dest': amend_dest,
		'ow_amend_origin':origin_,
		'ow_amend_dest': dest_,
		'rt_amend_origin':rt_origin_,
		'rt_amend_dest': rt_dest_,
		'depature_date':depature_date,
		'rt_depature_date':rt_depature_date,
                #'amd_ow_depature_date':amd_ow_dep,
		#'amd_rt_depature_date':amend_dep,
		'amd_ow_depature_date': ow_amend_date,
		'amd_rt_depature_date': rt_amend_date,
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
	fares_, flight_id  = self.get_flight_sell_key(flight_keys, avail_flights)
	ticket_class_dict = {'Economy' : 'cabin_baggage', 'Regular': 'free_checkin_baggage', 'Business' : 'free_meal_baggage'}
	form_key, fare_key, price = fares_.get(ticket_class_dict.get(cabin_class, ''), ['']*3)
	if cabin_class == 'Economy' and not fare_key:
	    cabin_class = 'Regular'
	    form_key, fare_key, price = fares_.get(ticket_class_dict.get(cabin_class, ''), ['']*3)
	return (fare_key, flight_id)

    def get_ori_amend_sell_keys(self, amend_dict, avail_flights, cabin_class, trip_type, return_flt=False):
        rt_flight_keys, flight_keys = [], []
        flight_keys = amend_dict.get('ori_ow_flt_list', {}).keys()
        if trip_type == 'OW':
            flight_keys = amend_dict.get('ori_ow_flt_list', {}).keys()
	elif trip_type == 'RT':
	    flight_keys = amend_dict.get('ori_rt_flt_list', {}).keys()
        fares_, flight_id  = self.get_flight_sell_key(flight_keys, avail_flights)
        ticket_class_dict = {'Economy' : 'cabin_baggage', 'Regular': 'free_checkin_baggage', 'Business' : 'free_meal_baggage'}
        form_key, fare_key, price = fares_.get(ticket_class_dict.get(cabin_class, ''), ['']*3)
        if cabin_class == 'Economy' and not fare_key:
            cabin_class = 'Regular'
            form_key, fare_key, price = fares_.get(ticket_class_dict.get(cabin_class, ''), ['']*3)
        return (fare_key, flight_id)

    def get_flight_sell_key(self, flight_keys, avail_flights):
	sellkey, fares_ = '', {}
	temp_rank, fin_key = 0, ''
	flight_keys = list(set(flight_keys))
	flight_keys = [x.replace(' ', '').strip() for x in flight_keys]
	avail_flights_keys = [x.replace(' ', '').strip() for x in avail_flights.keys()]
        for f_key in avail_flights_keys:
            for j in flight_keys:
                #j = j.replace(' ', '').strip()
                if j in f_key:
                    temp_rank +=1
            if len(flight_keys) == temp_rank:
                fin_key = f_key
                break
	fares_ = avail_flights.get(fin_key, {})
	return (fares_, fin_key)
	
    def get_travel_date(self, date):
        try:
            date_ = datetime.datetime.strptime(date.strip(), '%d-%b-%y')
            date_format = date_.strftime('%Y-%m-%d')
        except:
            date_format, day, month, year = ['']*4
        return date_format
