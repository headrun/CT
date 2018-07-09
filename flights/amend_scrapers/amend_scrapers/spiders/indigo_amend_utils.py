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


class IndigoAmendUtils(object):

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
	data_ = data_.get('details', [])
	if len(data_) > 1:
	    self.multiple_pnr = True
	    return pcc_name, amend_dict, "multiple PNRs not suported"
	if len(data_) == 0:
	    return amend_dict, amend_dict, "No segments found"
	data_ = data_[0]
	pnr = data_.get('pnr', '')
	all_segment_details = data_.get('all_segment_details', [])
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
		'trip_type':trip_type,
		'proceed_to_book': proceed_to_book,
		'cabin_class':cabin_class,
		'tolerance_amount':tolerance_amount,
		'pax_paid_amount': pax_paid_amount,
	})
        pcc = data_.get('pcc', '')
        if pcc:
            pcc_name = 'indigo_%s' % pcc
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
	if amend_ow_sort_list:
	    amd_ow_origin, amd_ow_dest, amd_ow_dep, amd_ow_depature_date = amend_ow_sort_list[0]
	if amend_rt_sort_list:
	    amend_origin, amend_dest, amend_dep, amd_rt_depature_date = amend_rt_sort_list[0]
	if not amd_ow_depature_date:
	    amd_ow_depature_date = depature_date
	search_keys_dict.update({
		'origin':origin,
		'destination': dest,
		'depature_date':depature_date,
		'rt_depature_date':rt_depature_date,
                'amd_ow_depature_date':amd_ow_depature_date,
		'amd_rt_depature_date':amd_rt_depature_date,
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
	sellkey, fares_, flight_id  = self.get_flight_sell_key(flight_keys, avail_flights)
	ticket_class_dict = {'Economy' : 'SAVER', 'Business' : 'FLEXI'}
	fare_class_dict = {'FLEXI':'J', 'SAVER': 'R', 'LITE': 'B'}
	fare_key, price = fares_.get(fare_class_dict.get(ticket_class_dict.get(cabin_class, ''), ''), ['']*2)
	if fare_key and sellkey:
            flight_fin_key = '%s|%s'%(fare_key, sellkey)
	else: flight_fin_key = ''
	return (flight_fin_key, flight_id)

    def trip_pricing_details(self, sellkey, cookies):
	import requests
	url = 'https://book.goindigo.in/Flight/PriceItineraryAEM?SellKeys%5B%5D='+ sellkey
	journey_list = []
        body = requests.get(url, cookies=cookies).text
	try:
	    json_body = json.loads(body)
	except:
	    json_body = {}
	    error = 'pricing details not found'
	price_ite_lst = json_body.get('indiGoPriceItinerary', {}).get('indigoJourneyPrice', {}).get('indigoJourneyPriceItineraryList', [])
	tot_fare = json_body.get('indiGoPriceItinerary', {}).get('indigoJourneyPrice', {}).get('totalPrice', '')
	for item in price_ite_lst:
	    journey_dict = {}
	    journey = item.get('journeyPriceItinerary', {})
	    journey_dict['cuteCharges'] = journey.get('cuteCharges', '')
	    journey_dict['fuelCharges'] = journey.get('fuelCharges', '')
	    journey_dict['infantAmount'] = journey.get('infantAmount', '')
	    journey_dict['feesAndTaxesTotal'] = journey.get('feesAndTaxesTotal', '')
	    journey_dict['airfareCharges'] = journey.get('airfareCharges', '')
	    taxAmountList = journey.get('taxAmountList', [])
	    for i in taxAmountList:
		key = i.get('key', '')
		val = i.get('value', '')
		journey_dict[key]=val
	    journey_dict['totalPrice'] = tot_fare
	    journey_list.append(journey_dict)
	return journey_list	

    def check_tolerance_level(self, amend_dict, indigo_pay):
	try:
	    indigo_pay = float(indigo_pay.split(' ')[0].replace(',', '').strip())
	except:
	    indigo_pay = 0
	pax_paid = float(amend_dict.get('pax_paid_amount', 0))
	tolerance_amount = amend_dict.get('tolerance_amount', 0)
	#indigo_pay = float(indigo_pay.replace(',', '').strip())
	price_diff = indigo_pay - pax_paid
	if price_diff > tolerance_amount:
	    tolerance_level = True
	else:
	    tolerance_level = False
	return (tolerance_level, price_diff)
		
    def get_flight_sell_key(self, flight_keys, avail_flights):
	sellkey, fares_ = '', {}
	'''
	for flight_id in flight_keys:
	    flight_id = flight_id.replace(' ', '').strip()
            sellkey, fares_ = avail_flights.get(flight_id, ['', {}])
            if sellkey:
                break
	'''
	temp_rank, fin_key = 0, ''
        for f_key in avail_flights.keys():
            for j in flight_keys:
                j = j.replace(' ', '').strip()
                if j in f_key:
                    temp_rank +=1
            if len(flight_keys) == temp_rank:
                fin_key = f_key
                break
	sellkey, fares_ = avail_flights.get(fin_key, ['', {}])
	return (sellkey, fares_, fin_key)

	
    def get_avail_flights(self, body, trip_type):
        if trip_type == 'OW':
            flights = body.get('indiGoAvailability', {}).get('trips', [])[0].get('flightDates',[{}])[0].get('flights', [])
        elif trip_type == 'RT':
            flights = body.get('indiGoAvailability', {}).get('trips', [])[1].get('flightDates',[{}])[0].get('flights', [])
        else:
            return {}
        flight_avail_dict = {}
        for flight in flights:
            carriercode = str(flight.get('carrierCode', '')).strip()
            flight_no = str(flight.get('flightNumber', '')).strip()
            flight_key = '%s%s'%(carriercode, flight_no)
            sell_key = flight.get('sellKey', '')
            fares_dict = {}
            fares = flight.get('fares', [])
	    flt_key_list = flight.get('legs', [])
	    flight_ids = []
	    for key in flt_key_list:
	        carrier = key.get('flightDesignator', {}).get('carrierCode', '').strip()
		flt_no = key.get('flightDesignator', {}).get('flightNumber', '').strip()
		if carrier and flt_no:
		    flight_ids.append('%s%s'%(carrier, flt_no))
            for fare in fares:
                product_class = fare.get('productClass', '')
                pro_sellkey = fare.get('sellKey', '')
                pax_fare = fare.get('passengerFares', [{}])[0]
                fare_amount = pax_fare.get('fareAmount', '0')
                fares_dict.update({product_class:[pro_sellkey, fare_amount]})
            flight_avail_dict.update({'<>'.join(flight_ids):[sell_key, fares_dict]})
        return flight_avail_dict

    def send_mail(self, sub, error_msg=''):
        recievers_list = []
        if 'Login' in sub:
            recievers_list = ast.literal_eval(_cfg.get('indigo_common', 'login_recievers_list'))
            import way2sms
            obj = way2sms.sms('9442843049', 'bhava')
            phones = ast.literal_eval(_cfg.get('indigo_common', 'phones'))
            for i in phones:
                sent = obj.send(i, 'Unable to login to Indigo,Please check')
                if sent:
                    print 'Sent sms successfully'
        recievers_list = ast.literal_eval(_cfg.get('indigo_common', 'recievers_list'))
        sender, receivers = 'prasadk@notemonk.com', ','.join(recievers_list)
        ccing = []
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'INDIGO QA TEST : %s On %s'%(sub, str(datetime.datetime.now().date()))
        mas = '<p>%s</p>' % error_msg
        msg['From'] = sender
        msg['To'] = receivers
        msg['Cc'] = ','.join(ccing)
        tem = MIMEText(''.join(mas), 'html')
        msg.attach(tem)
        s = smtplib.SMTP('smtp.gmail.com:587')
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(sender, 'amma@nanna')
        s.sendmail(sender, (recievers_list + ccing), msg.as_string())
        s.quit()

    def insert_error_msg(self, book_dict, err):
        tripid = book_dict.get('trip_ref', '') or book_dict.get('tripid', '')
        vals = (tripid, 'IndiGo', '', '', book_dict.get('origin', ''),\
                book_dict.get('destination', ''), book_dict.get('triptype', ''), book_dict.get('ctprice', ''),\
                '', 'Booking Failed', '', err, '', '',\
                err, '', tripid, ''\
                )
        try:
            self.cur.execute(self.insert_query, vals)
        except:
            print 'some insert error'
        self.conn.commit()

    def get_travel_date(self, date):
        try:
            date_ = datetime.datetime.strptime(date.strip(), '%d-%b-%y')
            date_format = date_.strftime('%Y-%m-%d')
        except:
            date_format, day, month, year = ['']*4
        return date_format
