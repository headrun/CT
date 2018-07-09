import smtplib
import json
import ast
import re
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.mime.multipart import MIMEMultipart
import datetime
from collections import Counter
from ConfigParser import SafeConfigParser
_cfg = SafeConfigParser()
_cfg.read('/root/scrapers/flights/booking_airline_names.cfg')

class AirAsiaUtils(object):

    def get_travel_date(self, date):
        try:
            date_ = datetime.datetime.strptime(date.strip(), '%d-%b-%y')
            date_format = date_.strftime('%Y-%m-%d')
        except:
            date_format, day, month, year = ['']*4
        return date_format

    def get_pcc_name(self):
        pcc_name = ''
        data = self.booking_dict
        if isinstance(data, dict):
            data_ = data
        else:
            data_ = ast.literal_eval(data)
        data = data_['all_segments']
	self.multiple_pcc = False
	key_list = []
	for j in data:
	    for i in j.keys():
	        key_list.append(i)
	if len(set(key_list)) == 1:
	    pcc_name = 'airasia_%s' % key_list[0].upper()
	else:
	    self.multiple_pcc = True
        return (pcc_name, data_)

    def process_input(self):
        '''Reruest processing to required dict format'''
        if isinstance(self.booking_dict, dict):
            pass
        else:
            self.booking_dict = ast.literal_eval(self.booking_dict)
        book_dict, paxdls = {}, {}
        if self.booking_dict.get('trip_type', '') == 'OW': triptype = 'OneWay'
        elif self.booking_dict.get('trip_type', '') == 'RT': triptype = 'RoundTrip'
        else: triptype = 'MultiCity'
	self.proceed_to_book = self.booking_dict.get('proceed_to_book', 0)
	self.tolerance_amount = self.booking_dict.get('tolerance_amount', 5000)
	self.queue = self.booking_dict.get('queue', '')
        self.get_input_segments(self.booking_dict)
        try: ow_input_flight = self.ow_input_flight[0]
        except: ow_input_flight = {}
        try:rt_input_flight = self.rt_input_flight[0]
        except: rt_input_flight = {}
        ow_flt_id, rt_flt_id = [], []
        for i in self.ow_input_flight:
            flt = i.get('flight_no', '')
            if flt: ow_flt_id.append(flt)
        for i in self.rt_input_flight:
            flt = i.get('flight_no', '')
            if flt: rt_flt_id.append(flt)
        pnr = self.booking_dict.get('auto_pnr', '')
        onewaymealcode = ow_input_flight.get('meal_codes', [])
        returnmealcode = rt_input_flight.get('meal_codes', [])
        onewaybaggagecode = ow_input_flight.get('baggage_codes', [])
        returnbaggagecode = rt_input_flight.get('baggage_codes', [])
        onewaydate = self.booking_dict.get('departure_date', '')
        onewaydate = str(self.get_travel_date(onewaydate))
        returndate = self.booking_dict.get('return_date', '')
        returndate = str(self.get_travel_date(returndate))
        origin = self.booking_dict.get('origin_code', '')
        destination = self.booking_dict.get('destination_code', '')
        pax_details = self.booking_dict.get('pax_details', {})
	pax_last_name = pax_details.get('adult1', []*6)
	pax_last_name = '%s,%s'%(pax_last_name[2], pax_last_name[1])
        contact_no = self.booking_dict.get('contact_mobile', '')
        countryphcode = self.booking_dict.get('country_phonecode', '')
        countrycode = self.booking_dict.get('country_code', '')
        email = self.booking_dict.get('emailid', '')
        ticket_class = self.booking_dict.get('ticket_booking_class', '')
        ct_ow_price = self.ow_fullinput_dict.get('amount', 0)
	ct_rt_price = self.rt_fullinput_dict.get('amount', 0)
        if triptype == 'RoundTrip': ct_price = ct_ow_price + ct_rt_price
        else: ct_price = ct_ow_price
        fin_pax, fin_infant, fin_child = [], [], []
        gender_format_dict = {'Mr': 'Male', 'Mrs': 'Female', 'Ms': 'Female' , 'Miss': 'Female', 'Mstr': 'Male'}
        tc_booking_cls_dict = {'Economy':'Economy', 'First':'Regular', 'PremiumEconomy':'PremiumFlex',
                                         'Business':'PremiumFlatbed', 'N/A':' '}
        if ticket_class:
            ticket_class = tc_booking_cls_dict.get(ticket_class.replace(' ', '').strip(), 'Economy')
        else: ticket_class = 'Economy'
	auto_pax_names = []
        for key, lst in pax_details.iteritems():
            pax_ = {}
            title, firstname, lastname, day, month, year  = lst
	    full_name_format = '%s %s'%(firstname, lastname)
	    auto_pax_names.append(full_name_format)
            gender = gender_format_dict.get(title.strip(), '')
            if not gender:
                gender = ''
            if day and month and year: dob = '%s-%s-%s'%(year, month, day)
            elif 'adult' in key:
                dob_ = datetime.datetime.now() + datetime.timedelta(days=-9125)
                dob = str(dob_.date())
            elif 'child' in key:
                dob_ = datetime.datetime.now() + datetime.timedelta(days=-2190)
                dob = str(dob_.date())
            elif 'infant' in key:
                dob_ = datetime.datetime.now() + datetime.timedelta(days=-365)
                dob =  str(dob_.date())
            pax_.update({'title':title, 'firstname':firstname, 'lastname':lastname,
                        'dob':dob, 'gender': gender, 'email':email, 'countrycode':'IN'})
            if 'adult' in key:fin_pax.append(pax_)
            elif 'child'in key:fin_child.append(pax_)
            elif 'infant' in key:fin_infant.append(pax_)
	paxdls.update({
                        'adult':str(self.booking_dict.get('no_of_adults', 0)),
                        'child':str(self.booking_dict.get('no_of_children', 0)),
                        'infant':str(self.booking_dict.get('no_of_infants', 0))
                        })

        book_dict.update({
                        "tripid":self.booking_dict.get('trip_ref', ''),
                        'onewayflightid': ow_flt_id, "onewayclass": ticket_class,
                        'returnflightid': rt_flt_id, 'returnclass': ticket_class,
                        'pnr': pnr, 'onewaymealcode': onewaymealcode,
                        'returnmealcode': returnmealcode, 'ctprice': str(ct_price),
                        'onewaybaggagecode': onewaybaggagecode, 'returnbaggagecode':returnbaggagecode,
                        'onewaydate': onewaydate, 'returndate': returndate, 'paxdetails':paxdls,
                        'origin': origin, 'destination': destination,
                        'triptype': triptype, 'multicitytrip':{}, 'emergencycontact':{},
                        'guestdetails':fin_pax, 'infant': fin_infant, 'childdetails':fin_child,
                        "countrycode": countrycode, "countryphcode": countryphcode, "phonenumber": contact_no,
                        "email": email, 'proceed_to_book':self.proceed_to_book, 'queue':self.queue,
			"pax_last_name":pax_last_name, 'hq_pax_names':auto_pax_names,
                        })
        return book_dict

    def check_arrival_departure_date(self, site_depart_date, site_arrival_date, hq_depart_date, hq_arrival_date):
	site_dapart_tuple = self.get_date_perticulars(site_depart_date)
	site_arrival_tuple = self.get_date_perticulars(site_arrival_date)
	#check and convert same as for hq_depart_date and hq_arrival_date
	#do checks for timings and return the boolean value True or False

    def get_date_perticulars(self, site_date):
	site_date = ''.join(re.findall('\).*\)(.*,.*)\(', site_date)).strip()
        try:
            site_date = datetime.datetime.strptime(site_date, '%d %b %Y, %I%M %p')
            site_day, site_month, site_year, site_hour, site_minute = site_date.day, site_date.month,\
                site_date.year, site_date.hour, site_date.minute
        except:
            site_day, site_month, site_year, site_hour, site_minute = ['']*5

	return (site_day, site_month, site_year, site_hour, site_minute)

    def check_depature_date(self, book_dict, cur_booking_dict):
        request_depart_date = book_dict.get('onewaydate', '').replace('-', '')
        request_return_date = book_dict.get('returndate', '').replace('-', '')
        auto_book_dict = {}
        for auto_pnr, details_lst in cur_booking_dict.iteritems():
            if details_lst[0] == request_depart_date:
                auto_book_dict[auto_pnr] = details_lst
        return auto_book_dict

    def check_hq_flights(self, hd_flight_list, flights_list):
        hd_flight_list = list(set(hd_flight_list))
        flights_list = list(set(flights_list))
        rank = 0
        for flight in hd_flight_list:
            if flight in flights_list:
                rank += 1
        if rank == len(flights_list):
            status = True
        else:
            status = False
        return status

    def check_hq_pax_name(self, book_dict, cur_booking_dict):
        hq_pax_names_lst = book_dict.get('hq_pax_names', [])
        hq_pax_names_lst = [x.lower().replace(' ', '').strip() for x in hq_pax_names_lst]
        auto_pnr_dict = {}
        for auto_pnr, details_lst in cur_booking_dict.iteritems():
            site_pax_name_lst = details_lst[2].lower().replace(' ', '').strip()
            if site_pax_name_lst in hq_pax_names_lst:
                auto_pnr_dict[auto_pnr] = details_lst
        return auto_pnr_dict

    def check_guest_names(self, book_dict, guest_names_list):
        hq_pax_names_lst = book_dict.get('hq_pax_names', [])
        hq_pax_names_lst = [x.lower().replace(' ', '').strip() for x in hq_pax_names_lst]
        guest_names_list = [x.lower().replace(' ', '').strip() for x in guest_names_list]
        pax_count, status = 0, False
        for name in hq_pax_names_lst:
            if name in guest_names_list:
                pax_count +=1
            if pax_count == len(guest_names_list):
                status = True
                return status
            else: status = False
        return status

    def get_fin_fares_dict(self, flight_fares, ct_flights):
        '''
        returing the requested flight details
        '''
        aa_keys = flight_fares.keys()
	ct_flights = set(ct_flights)
        fin_fare_dict, flight_no = {}, ''
        for key in aa_keys:
            flt_status_key, rank = False, 0
            for ct_flt in ct_flights:
                ct_flt = ct_flt.replace(' ', '').replace('-', '').strip()
                if str(ct_flt.lower()) == str(key.lower()):
                    flt_status_key = True
                    rank = rank + 1
                else: flt_status_key = False
            #if flt_status_key:
            if len(ct_flights) == rank:
                fin_fare_dict = flight_fares.get(key, {})
                flight_no = key
                break
            else:
                fin_fare_dict, flight_no = {}, ''
        return (fin_fare_dict, flight_no)

    def send_mail(self, sub, error_msg):
        ''' sending mails '''
	recievers_list = []
	if '403' in sub:
            import way2sms
            obj = way2sms.sms('9442843049', 'bhava')
            phones = [u'9553552623', u'8217866491']
            for i in phones:
                sent = obj.send(i, 'AirAsia-Booking: Login page got 403 status')
                if sent:
                    print 'Sent sms successfully'
	    return

	if 'login' in sub:
            recievers_list = ast.literal_eval(_cfg.get(self.pcc_name, 'login_recievers_list'))
            import way2sms
            obj = way2sms.sms('9442843049', 'bhava')
            phones = ast.literal_eval(_cfg.get(self.pcc_name, 'phones'))
            for i in phones:
                sent = obj.send(i, 'Unable to login to AirAsia,Please check')
                if sent:
                    print 'Sent sms successfully'
        recievers_list = ast.literal_eval(_cfg.get(self.pcc_name, 'recievers_list'))
        sender, receivers = 'ctmonitoring17@gmail.com', ','.join(recievers_list)
        ccing = []
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '%s On %s'%(sub, str(datetime.datetime.now().date()))
        mas = '<p>%s</p>'%error_msg
        msg['From'] = sender
        msg['To'] = receivers
        msg['Cc'] = ','.join(ccing)
        tem = MIMEText(''.join(mas), 'html')
        msg.attach(tem)
        s = smtplib.SMTP('smtp.gmail.com:587')
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(sender, 'ctmonitoring@123')
        s.sendmail(sender, (recievers_list + ccing), msg.as_string())
        s.quit()

    def get_date_values(self, date):
        '''
        parsing date format
        '''
        try:
            date_ = datetime.datetime.strptime(date, '%Y-%m-%d')
            bo_day, bo_month, bo_year = date_.day, date_.month, date_.year
            boarding_date = date_.strftime('%m/%d/%Y')
        except:
            boarding_date, bo_day, bo_month, bo_year = ['']*4
        return (boarding_date, bo_day, bo_month, bo_year)
    def get_flight_fares(self, dict_):
        '''
        flight fare selection for multi-city
        '''
        schedules = dict_.get('Schedules', [])
        segments_len = len(schedules)
        seg1_flt, seg2_flt, seg3_flt, seg4_flt, seg5_flt, seg6_flt = {},\
                {}, {}, {}, {}, {}
        seg1, seg2, seg3, seg4, seg5, seg6 = {}, {}, \
                {}, {}, {}, {}
        if segments_len == 2: seg1, seg2 = schedules
        elif segments_len == 3: seg1, seg2, seg3 = schedules
        elif segments_len == 4: seg1, seg2, seg3, seg4 = schedules
        elif segments_len == 5: seg1, seg2, seg3, seg4, seg5 = schedules
        elif segments_len == 6: seg1, seg2, seg3, seg4, seg5, seg6 = schedules
        if seg1: seg1_flt = self.get_flight_prices(seg1)
        if seg2: seg2_flt = self.get_flight_prices(seg2)
        if seg3: seg3_flt = self.get_flight_prices(seg3)
        if seg4: seg1_flt = self.get_flight_prices(seg4)
        if seg5: seg2_flt = self.get_flight_prices(seg5)
        if seg6: seg3_flt = self.get_flight_prices(seg6)
        return (seg1_flt, seg2_flt, seg3_flt, seg4_flt, seg5_flt, seg6_flt)


    def get_flight_prices(self, flt):
        '''
        returnig multi-city flights
        '''
        market = flt.get('JourneyDateMarketList', [])
        flights = {}
        if market:
            market = market[3]
            journeys = market.get('Journeys', [])
            for i in journeys:
                flight_id = i.get('FlightDesignator', '').replace(' ', '').strip()
                sell_key = i.get('SellKey', '')
                journeyfares = i.get('JourneyFares', [])
                ec, hf, pm = {}, {}, {}
                ec_rank, hf_rank, pm_rank = 0, 0, 0
                for jf in journeyfares:
                    farebasiscode = jf.get('FareBasisCode', '')
                    amount = jf.get('Amount', '')
                    productclass = jf.get('ProductClass', '')
                    sellkey = jf.get('SellKey', '')
                    if productclass == 'EC':
                        ec_rank += 1
                        ec.update({ec_rank:(farebasiscode, amount, sellkey)})
                    elif productclass == 'HF':
                        hf_rank += 1
                        hf.update({hf_rank:(farebasiscode, amount, sellkey)})
                    elif productclass == 'PM':
                        pm_rank += 1
                        pm.update({pm_rank:(farebasiscode, amount, sellkey)})
                flights.update({flight_id:{'ec':ec[1], 'hf':hf[1], 'pm':pm[1],'sellkey':sell_key}})
        return flights
