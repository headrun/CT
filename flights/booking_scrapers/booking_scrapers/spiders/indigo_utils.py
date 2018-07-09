'''Flights Indigo Support functions'''
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.mime.multipart import MIMEMultipart
import datetime
import ast
from collections import Counter
from ConfigParser import SafeConfigParser
_cfg = SafeConfigParser()
_cfg.read('../../../booking_airline_names.cfg')


class IndigoUtils(object):

    def get_pcc_name(self):
        pcc_name = ''
        #data = self.booking_dict
        #data_ = ast.literal_eval(data)
        data_ = self.booking_dict
        data = data_['all_segments']
        if len(data) == 1:
            pcc_name = 'indigo_%s' % data[0].keys()[0].upper()
        elif len(data) == 2:
            if data[0].keys() != data[1].keys():
                self.multiple_pcc = True
            else:
                pcc_name = 'indigo_%s' % data[0].keys()[0].upper()
        return data_, pcc_name

    def parse_flight_segments(self, seg_trips):
        seg_flights = {}
        for seg_idx, seg in enumerate(seg_trips):
            flights = seg.get('flightDates', [])
            if flights:
                flights = flights[0]
            else:
                flights = {}
            flt = flights.get('flights', [])
            flight_dict = {}
            for idx, i in enumerate(flt):
                carrier = i.get('carrierCode', '').strip()
                flt_no = i.get('flightNumber', '').strip()
                if len(i['legs']) > 1:
                    all_flights = []
                    for leg in i['legs']:
                        all_flights.append(
                            leg['flightDesignator']['flightNumber'].strip())
                    flt_no = '<>6E'.join(set(all_flights))
                m_sellkey = i.get('sellKey', '').strip()
                fares = i.get('fares', [])
                fare_dict = {}
                for fare in fares:
                    productclass = fare.get('productClass', '')
                    f_sellkey = fare.get('sellKey', '')
                    pax_fares = fare.get('passengerFares', [])
                    if pax_fares:
                        pax_fares = pax_fares[0]
                    else:
                        pax_fares = {}
                    fareamount = pax_fares.get('fareAmount', 0)
                    fare_dict.update({productclass: (fareamount, f_sellkey)})
                flight_dict.update({'%s%s' % (carrier, flt_no): {
                                   'fares': fare_dict, 'sellkey': m_sellkey}})
            seg_flights.update({seg_idx: flight_dict})
        return seg_flights

    def mealcode_inputs(self):
        onewaymealcode, returnmealcode = [], []
        for index, i in enumerate(self.ow_input_flight):
            owmeal = i.get('meal_codes', '')
            if owmeal:
                owmeal = [(str(index) + '_' + str(count) + '_' + i)
                          for count, i in enumerate(owmeal)]
                onewaymealcode.extend(owmeal)
            if index > 0 and owmeal:
                self.ow_meals_connection = True
        for index, i in enumerate(self.rt_input_flight):
            rtmeal = i.get('meal_codes', '')
            if rtmeal:
                rtmeal = [(str(index) + '_' + str(count) + '_' + i)
                          for count, i in enumerate(rtmeal)]
                returnmealcode.extend(rtmeal)
            if index > 0 and rtmeal:
                self.rt_meals_connection = True
        return onewaymealcode, returnmealcode

    def baggagecode_inputs(self):
        onewaybaggagecode, returnbaggagecode = [], []
        for index, i in enumerate(self.ow_input_flight):
            ow_baggage = i.get('baggage_codes', '')
            if ow_baggage:
                ow_baggage = [(str(index) + '_' + str(count) + '_' + i)
                              for count, i in enumerate(ow_baggage)]
                onewaybaggagecode.extend(ow_baggage)
            if index > 0 and ow_baggage:
                self.ow_baggage_connection = True
        for index, i in enumerate(self.rt_input_flight):
            rt_baggage = i.get('baggage_codes', '')
            if rt_baggage:
                rt_baggage = [(str(index) + '_' + str(count) + '_' + i)
                              for count, i in enumerate(rt_baggage)]
                returnbaggagecode.extend(rt_baggage)
            if index > 0 and rt_baggage:
                self.rt_baggage_connection = True
        return onewaybaggagecode, returnbaggagecode

    def process_input(self):
        book_dict, paxdls = {}, {}
        if self.booking_dict.get('trip_type', '') == 'OW':
            triptype = 'OneWay'
        elif self.booking_dict.get('trip_type', '') == 'RT':
            triptype = 'RoundTrip'
        else:
            triptype = 'MultiCity'
        self.proceed_to_book = self.booking_dict.get('proceed_to_book', 0)
        self.get_input_segments(self.booking_dict)
        try:
            ow_input_flight = self.ow_input_flight[0]
        except:
            ow_input_flight = {}
        try:
            rt_input_flight = self.rt_input_flight[0]
        except:
            rt_input_flight = {}
        ow_flt_id, rt_flt_id = [], []
        ow_hb, rt_hb = '', ''
        for i in self.ow_input_flight:
            flt = i.get('flight_no', '')
            if flt:
                ow_flt_id.append(flt)
            ow_hb = i.get('no_hand_baggage')
        for i in self.rt_input_flight:
            flt = i.get('flight_no', '')
            if flt:
                rt_flt_id.append(flt)
            rt_hb = i.get('no_hand_baggage')
        print ow_hb, rt_hb
        pnr = self.booking_dict.get('auto_pnr', '')
        onewaymealcode, returnmealcode, onewaybaggagecode, returnbaggagecode = [], [], [], []
        if self.mb_check:
            onewaymealcode, returnmealcode = self.mealcode_inputs()
            onewaybaggagecode, returnbaggagecode = self.baggagecode_inputs()
        # self.ow_input_flight.get('date', '')
        onewaydate = self.booking_dict.get('departure_date', '')
        onewaydate = str(self.get_travel_date(onewaydate))
        # self.rt_input_flight.get('date', '')
        returndate = self.booking_dict.get('return_date', '')
        returndate = str(self.get_travel_date(returndate))
        origin = self.booking_dict.get('origin_code', '')
        destination = self.booking_dict.get('destination_code', '')
        pax_details = self.booking_dict.get('pax_details', {})
        contact_no = self.booking_dict.get('contact_mobile', '')
        countryphcode = self.booking_dict.get('country_phonecode', '')
        countrycode = self.booking_dict.get('country_code', '')
        email = self.booking_dict.get('emailid', '')
        ticket_class = self.booking_dict.get('ticket_booking_class', '')
        ticket_class_dict = {'Economy': 'SAVER', 'Business': 'FLEXI'}
        self.ow_farebasis_class = self.ow_fullinput_dict.get(
            'segments', [{}])[0].get('fare_basis_code', '')
        self.rt_farebasis_class = self.rt_fullinput_dict.get(
            'segments', [{}])[0].get('fare_basis_code', '')

        ticket_class = ticket_class_dict.get(ticket_class, '')
        onewayclass, returnclass = ticket_class, ticket_class
        if self.booking_dict.get('ticket_booking_class', '') == 'Economy':
            if ow_hb:
                onewayclass = 'LITE'
            if rt_hb:
                returnclass = 'LITE'
        print onewayclass, returnclass
        ct_ow_price = self.ow_fullinput_dict.get('amount', 0)
        ct_rt_price = self.rt_fullinput_dict.get('amount', 0)
        currencycode = self.booking_dict.get('currency_code', 'INR')
        if triptype == 'RoundTrip':
            ct_price = ct_ow_price + ct_rt_price
        else:
            ct_price = ct_ow_price
        self.ct_price = ct_price
        fin_pax, fin_infant, fin_child = [], [], []
        gender_format_dict = {'Mr': 'Male', 'Mrs': 'Female',
                              'Ms': 'Female', 'Miss': 'Female',
                              'Mstr': 'Male'}
        dob = '0000-00-00'
        for key, lst in pax_details.iteritems():
            pax_ = {}
            title, firstname, lastname, day, month, year = lst
            gender = gender_format_dict.get(title.strip(), '')
            if day and month and year:
                dob = '%s-%s-%s' % (year, month, day)
            else:
                "1989-02-02"
            pax_.update({'title': title, 'firstname': firstname,
                         'lastname': lastname, 'dob': dob,
                         'gender': gender, 'email': email,
                         'countrycode': 'IN'})
            if 'adult' in key:
                fin_pax.append(pax_)
            elif 'child' in key:
                fin_child.append(pax_)
            elif 'infant' in key:
                fin_infant.append(pax_)
        paxdls.update({'adult': str(self.booking_dict.get('no_of_adults', 0)),
                       'child': str(self.booking_dict.get('no_of_children', 0)),
                       'infant': str(self.booking_dict.get('no_of_infants', 0))
                       })
        if fin_pax:
            adult_names = ['%s %s %s' % (i.get('title'), i.get(
                'firstname'), i.get('lastname')) for i in fin_pax]
            if len(adult_names) != len(set(adult_names)):
                self.adult_fail = True
        if fin_child:
            child_names = ['%s %s %s' % (i.get('title'), i.get(
                'firstname'), i.get('lastname')) for i in fin_child]
            if len(child_names) != len(set(child_names)):
                self.child_fail = True
        if fin_infant:
            infant_names = ['%s %s %s' % (i.get('title'), i.get(
                'firstname'), i.get('lastname')) for i in fin_infant]
            if len(infant_names) != len(set(infant_names)):
                self.infant_fail = True
        self.adult_count = self.booking_dict.get('no_of_adults', '0')
        self.child_count = self.booking_dict.get('no_of_children', '0')
        self.infant_count = str(self.booking_dict.get('no_of_infants', '0'))
        self.ow_flight_nos = '<>'.join(ow_flt_id)
        self.rt_flight_nos = '<>'.join(rt_flt_id)
        book_dict.update({"tripid": self.booking_dict.get('trip_ref', ''),
                          'onewayflightid': ['<>'.join(ow_flt_id)], "onewayclass": onewayclass,
                          'returnflightid': ['<>'.join(rt_flt_id)], 'returnclass': returnclass,
                          'pnr': pnr, 'onewaymealcode': onewaymealcode,
                          'returnmealcode': returnmealcode, 'ctprice': str(ct_price),
                          'onewaybaggagecode': onewaybaggagecode, 'returnbaggagecode': returnbaggagecode,
                          'onewaydate': onewaydate, 'returndate': returndate, 'paxdetails': paxdls,
                          'origin': origin, 'destination': destination,
                          'triptype': triptype, 'multicitytrip': {}, 'emergencycontact': {},
                          'guestdetails': fin_pax, 'infant': fin_infant, 'childdetails': fin_child,
                          "countrycode": countrycode, "countryphcode": countryphcode, "phonenumber": contact_no,
                          "email": email, "currencycode": currencycode,
                          })
        return book_dict

    def get_input_segments(self, segments):
        all_segments = segments.get('all_segments', [])
        self.ow_flights_connection, self.rt_flights_connection = False, False
        ow_flight_dict, rt_flight_dict = {}, {}
        dest = segments.get('destination_code', '').strip()
        origin = segments.get('origin_code', '').strip()
        from_to = '%s-%s' % (origin, dest)
        ow_check = False
        if len(all_segments) == 1:
            key = ''.join(all_segments[0].keys())
            ow_flight_dict = all_segments[0][key]
            self.ow_fullinput_dict = ow_flight_dict
            if ow_flight_dict:
                try:
                    self.ow_input_flight = ow_flight_dict.get('segments', [])
                except:
                    self.ow_input_flight = {}
            else:
                self.ow_input_flight = {}
        elif len(all_segments) == 2:
            key1, key2 = ''.join(all_segments[0].keys()), ''.join(
                all_segments[1].keys())
            flight_dict1, flight_dict2 = all_segments[0][key1], all_segments[1][key2]
            f_to = flight_dict1.get('segments', [])
            self.ow_input_flight = flight_dict1.get('segments', [])
            self.rt_input_flight = flight_dict2.get('segments', [])
            self.ow_fullinput_dict, self.rt_fullinput_dict = flight_dict1, flight_dict2
        else:
            vals = (segments.get('trip_ref', ''), 'Indigo', '', '',
                    segments.get('origin_code', ''), segments.get(
                        'destination_code', ''),
                    self.tt, '', '', "Booking Failed", '', "Multi-city booking",
                    json.dumps(segments), '{}', 'Multi-city booking',
                    json.dumps(segments), segments.get('trip_ref', ''), '')
            self.cur.execute(self.inserttwo_query, vals)

        rt_len = 0
        if self.ow_fullinput_dict:
            ow_len = len(self.ow_fullinput_dict['segments'])
        if self.rt_fullinput_dict:
            rt_len = len(self.rt_fullinput_dict['segments'])
        if ow_len > 1 or rt_len > 1:
            # vals = (segments.get('trip_ref', ''), 'Indigo', '', '', segments.get('origin_code', ''),\
            #		segments.get('destination_code', ''), self.tt, '', '', "Booking Failed", '',\
            #		"Connection flights booking", json.dumps(segments), '{}', 'Connection flights booking',\
            #		json.dumps(segments), segments.get('trip_ref', ''),'')
            self.connection_check = True
            #self.cur.execute(self.inserttwo_query, vals)
            if ow_len > 1:
                self.ow_flights_connection = True
            if rt_len > 1:
                self.rt_flights_connection = True

    def get_baggage_meals(self, edit_data, book_dict):
        baggages, meals = [], []
        ow_baggage_price, rt_baggage_price = [], []
        ow_meals_price, rt_meals_price = [], []
        if edit_data['indiGoAvailableSsr']['availableSsrsList'] == None:
            return baggages, meals, ow_baggage_price, rt_baggage_price, ow_meals_price, rt_meals_price
        # Baggage for OW
        for i in book_dict['onewaybaggagecode']:
            count = int(i.split('_')[1])
            i = i.split('_')[-1]
            print 'Checking for %s' % i
            try:
                bags_available = edit_data['indiGoAvailableSsr']['availableSsrsList']['ssrsBaggagesList'][0]['paxSsrsList'][count]
                for bags in bags_available['ssrsList']:
                    if i in bags['key']:
                        baggages.append(bags['key'])
                        ow_baggage_price.append((i, bags['price']))
                        bags_check = True
                        break
            except Exception as e:
                print "Need to break and move to manual queue"
                vals = (book_dict.get('tripid', ''), 'IndiGo', '', '', book_dict.get('origin', ''),
                        book_dict.get('destination', ''), self.tt,
                        book_dict.get('ctprice', ''), '',
                        'Baggages error', '', 'Check oneway baggages', '', '{}',
                        'Check oneway baggages', '', book_dict.get(
                            'tripid', ''), ''
                        )
                self.cur.execute(self.inserttwo_query, vals)
                self.conn.commit()
                print e
                self.ow_baggage_connection = True
        for i in book_dict['returnbaggagecode']:
            count = int(i.split('_')[1])
            i = i.split('_')[-1]
            print 'Checking for %s' % i
            try:
                bags_available = edit_data['indiGoAvailableSsr']['availableSsrsList']['ssrsBaggagesList'][1]['paxSsrsList'][count]
                for bags in bags_available['ssrsList']:
                    if i in bags['key']:
                        baggages.append(bags['key'])
                        rt_baggage_price.append((i, bags['price']))
                        bags_check = True
                        break
            except Exception as e:
                print "Need to break and move to manual queue"
                vals = (book_dict.get('tripid', ''), 'IndiGo', '', '', book_dict.get('origin', ''),
                        book_dict.get('destination', ''), self.tt,
                        book_dict.get('ctprice', ''),
                        '', 'Baggages error', '', 'Check return baggages', '', '{}',
                        'Check return baggages', '', book_dict.get(
                            'tripid', ''), ''
                        )
                self.cur.execute(self.inserttwo_query, vals)
                self.conn.commit()
                print e
                self.rt_baggage_connection = True
        for i in book_dict['onewaymealcode']:
            count = int(i.split('_')[1])
            i = i.split('_')[-1]
            print 'Checking for %s' % i
            try:
                bags_available = edit_data['indiGoAvailableSsr']['availableSsrsList']['ssrsMealsList'][0]['paxSsrsList'][count]
                for bags in bags_available['ssrsList']:
                    if i in bags['key']:
                        meals.append(bags['key'])
                        ow_meals_price.append((i, bags['price']))
                        bags_check = True
                        break
            except Exception as e:
                print "Need to break and move to manual queue"
                vals = (book_dict.get('tripid', ''), 'IndiGo', '', '', book_dict.get('origin', ''),
                        book_dict.get('destination', ''), self.tt,
                        book_dict.get('ctprice', ''),
                        '', 'Meals error', '', 'Check oneway meals', '', '{}',
                        'Check oneway meals', '', book_dict.get(
                            'tripid', ''), ''
                        )
                self.cur.execute(self.inserttwo_query, vals)
                self.conn.commit()
                print e
                self.ow_meals_connection = True
                break
        for i in book_dict['returnmealcode']:
            count = int(i.split('_')[1])
            i = i.split('_')[-1]
            print 'Checking for %s' % i
            try:
                bags_available = edit_data['indiGoAvailableSsr']['availableSsrsList']['ssrsMealsList'][1]['paxSsrsList'][count]
                for bags in bags_available['ssrsList']:
                    if i in bags['key']:
                        meals.append(bags['key'])
                        rt_meals_price.append((i, bags['price']))
                        bags_check = True
                        break
            except Exception as e:
                print "Need to break and move to manual queue"
                vals = (book_dict.get('tripid', ''), 'IndiGo', '', '', book_dict.get('origin', ''),
                        book_dict.get('destination', ''), self.tt,
                        book_dict.get('ctprice', ''),
                        '', 'Meals error', '', 'Check return meals', '', '{}',
                        'Check return meals', '', book_dict.get(
                            'tripid', ''), ''
                        )
                self.cur.execute(self.inserttwo_query, vals)
                self.conn.commit()
                print e
                self.rt_meals_connection = True
        if baggages == [] or meals == []:
            print 'baggage : %s' % len(baggages)
            print 'meals : %s' % len(meals)
        return baggages, meals, ow_baggage_price, rt_baggage_price, ow_meals_price, rt_meals_price

    def send_mail(self, sub, error_msg=''):
        recievers_list = []
        recievers_list = ast.literal_eval(
            _cfg.get('indigo_common', 'recievers_list'))
        if 'Login' in sub:
            recievers_list = ast.literal_eval(
                _cfg.get('indigo_common', 'login_recievers_list'))
            import way2sms
            obj = way2sms.sms('9442843049', 'bhava')
            phones = ast.literal_eval(_cfg.get('indigo_common', 'phones'))
            for i in phones:
                sent = obj.send(i, 'Unable to login to Indigo,Please check')
                if sent:
                    print 'Sent sms successfully'
        sender, receivers = 'ctmonitoring17@gmail.com', ','.join(
            recievers_list)
        ccing = []
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'INDIGO PROD : %s On %s' % (
            sub, str(datetime.datetime.now().date()))
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
        s.login(sender, 'ctmonitoring@123')
        s.sendmail(sender, (recievers_list + ccing), msg.as_string())
        s.quit()

    def get_fin_fares_dict(self, flight_fares, ct_flights):
        aa_keys = flight_fares.keys()
        fin_fare_dict, flight_no = {}, ''
        for key in aa_keys:
            flt_status_key = False
            for ct_flt in ct_flights:
                ct_flt = ct_flt.replace(' ', '').replace('-', '').strip()
                if ct_flt.lower() in key.lower():
                    flt_status_key = True
                else:
                    flt_status_key = False
            if flt_status_key:
                fin_fare_dict = flight_fares.get(key, {})
                flight_no = key
                break
            else:
                fin_fare_dict, flight_no = {}, ''
        return (fin_fare_dict, flight_no)

    def check_tolerance(self, ctprice, indiprice):
        tolerance_value, is_proceed = 0, 0
        total_fare = float(indiprice)
        if total_fare != 0:
            tolerance_value = total_fare - \
                float(ctprice.replace(',', '').strip())
            check_tolerance = float(
                self.booking_dict.get('tolerance_amount', '5000'))
            if self.queue == 'coupon':
                check_tolerance = float(10000)
            if tolerance_value >= check_tolerance:  # 2000:
                is_proceed = 0  # movie it to off line
            else:
                is_proceed = 1
        else:
            tolerance_value, is_proceed = 0, 0
        return (tolerance_value, is_proceed)

    def get_date_format(self, text):
        if text:
            try:
                date = datetime.datetime.strptime(text, '%Y-%m-%d')
                re_date = date.strftime('%d %b %Y')
                return re_date
            except:
                return ''
        else:
            return ''

    def get_flight_keys(self, seg_ft, ct_class, ct_flt_id, fb_code=[]):
        '''
        Should return customer selected flight + fare from Json comparing with the customer inputs.
        Sell keys below needs to be passed to next function, important one as it is used throughout.
        '''
        if not seg_ft:
            return ('', '')
        fare_class_dict = {'FLEXI': 'J', 'SAVER': 'R',
                           'LITE': 'B', 'SAVERS': 'S', 'SRT': 'N'}
        fin_fare_dict = {}
        #if self.srt_check: ct_class = 'SRT'
        self.log.debug(seg_ft.keys())
        # Check the loop here
        for key in seg_ft.keys():
            bool_check = False
            for ct_flt_id_ in ct_flt_id:
                ct_id = ct_flt_id_.replace(' ', '').replace('-', '')
                if ct_id == key:
                    fin_fare_dict = seg_ft.get(key, {})
                    bool_check = True
                else:
                    try:
                        ct_id = '<>'.join(ct_flt_id[0].replace(
                            ' ', '').replace('-', '').split('<>')[::-1])
                        if ct_id == key:
                            fin_fare_dict = seg_ft.get(key, {})
                            bool_check = True
                        else:
                            fin_fare_dict = {}
                    except:
                        self.log.debug('Ulta flights check fail')
                        pass
            if bool_check:
                break
        fares_dict = fin_fare_dict.get('fares', {})
        print fares_dict
        try: final_flt_tuple = filter(None, [(i,j) if fb_code[0] in j else '' for i,j in fares_dict.values()])[0]
        except: final_flt_tuple = ''
        try: print 'Find here : %s %s' % final_flt_tuple
        except: pass
        if not final_flt_tuple:
		if ct_class == 'SAVERS' or ct_class == 'LITE':
		    if ct_class == 'SAVERS':
			    try: final_flt_tuple = fares_dict.get(fare_class_dict.get(ct_class, ''), '') or sorted(fares_dict.values())[0]
			    except:final_flt_tuple = ['']*2
		    else:
			    final_flt_tuple = fares_dict.get(
			        fare_class_dict.get(ct_class, ''), ['']*2)

		elif self.srt_check or self.booking_dict.get('trip_type') == 'RT':
		    #ct_class = 'SRT'
		    print fares_dict
		    print 'came here for SRT'
		    if fb_code:
			if 'RT' in fb_code[0]:
			    try:
				final_flt_tuple = sorted(fares_dict.values())[0]
			    except:
				final_flt_tuple = ['']*2
			elif '0IP' in fb_code[0]:
			    final_flt_tuple = fares_dict.get(
				fare_class_dict.get('SAVER', ''), ['']*2)
			elif 'UIP' in fb_code[0]:
			    final_flt_tuple = fares_dict.get(
				fare_class_dict.get('FLEXI', ''), ['']*2)
			elif 'FIP' in fb_code[0]:
			    final_flt_tuple = fares_dict.get('A', ['']*2)
			elif 'MIP' in fb_code[0]:
			    final_flt_tuple = fares_dict.get('M', ['']*2)
			elif '0CRP' in fb_code[0]:
			    final_flt_tuple = fares_dict.get('F', ['']*2)
			elif 'SSPL' in fb_code[0]:
			    final_flt_tuple = fares_dict.get('S', ['']*2)
			else:
			    print ct_class
			    final_flt_tuple = fares_dict.get(
				fare_class_dict.get(ct_class, ''), ['']*2)
		    else:
			final_flt_tuple = fares_dict.get(
			    fare_class_dict.get(ct_class, ''), ['']*2)
		else:
		    if fb_code:
			if '0IP' in fb_code[0]:
			    final_flt_tuple = fares_dict.get(
				fare_class_dict.get('SAVER', ''), ['']*2)
			elif 'UIP' in fb_code[0]:
			    final_flt_tuple = fares_dict.get(
				fare_class_dict.get('FLEXI', ''), ['']*2)
			elif 'FIP' in fb_code[0]:
			    final_flt_tuple = fares_dict.get('A', ['']*2)
			elif 'MIP' in fb_code[0]:
			    final_flt_tuple = fares_dict.get('M', ['']*2)
			elif '0CRP' in fb_code[0]:
			    final_flt_tuple = fares_dict.get('F', ['']*2)
			elif 'SSPL' in fb_code[0]:
			    final_flt_tuple = fares_dict.get('S', ['']*2)
			else:
			    final_flt_tuple = fares_dict.get(
				fare_class_dict.get(ct_class, ''), '')
		    else:
			final_flt_tuple = fares_dict.get(
			    fare_class_dict.get(ct_class, ''), '')
        flt_sell = fin_fare_dict.get('sellkey', '')
        finfare, fare_sell = final_flt_tuple
        if flt_sell and fare_sell:
            fin_sell = '%s|%s' % (fare_sell, flt_sell)
        else:
            fin_sell = ''
        return (finfare, fin_sell)

    def insert_error_msg(self, pnr='', mesg='', err='', tolerance='', f_no='', a_price='', p_details='{}'):
        trip_id = self.booking_dict['trip_ref']
        origin = self.booking_dict['origin_code']
        destination = self.booking_dict['destination_code']
        trip_type = self.booking_dict['trip_type']
        trip_type = '%s_%s_%s' % (trip_type, self.queue, self.book_using)
        ow_date = self.booking_dict['departure_date']
        ow_date = datetime.datetime.strptime(ow_date, '%d-%b-%y')
        rt_date = self.booking_dict.get('return_date', '')
        if rt_date:
            rt_date = datetime.datetime.strptime(rt_date, '%d-%b-%y')
        if not f_no:
            f_no = [self.ow_flight_nos, self.rt_flight_nos]
            f_no = '<>'.join(f_no).strip('<>')
        vals = (trip_id, 'IndiGo', pnr, f_no, origin, destination, trip_type, self.ct_price, a_price, mesg, tolerance, ow_date, rt_date, err, str(
            self.booking_dict), str(p_details), pnr, f_no, a_price, mesg,  err, str(self.booking_dict), str(p_details), str(trip_type), self.ct_price, tolerance)
        try:
            self.cur.execute(self.insert_query, vals)
        except Exception as e:
            print "some insert error %s" % e
            self.log.debug(e)
            try:
                self.cur.execute(self.insert_query, vals)
            except:
                self.log.debug(e)
        self.conn.commit()

    def get_travel_date(self, date):
        try:
            date_ = datetime.datetime.strptime(date.strip(), '%d-%b-%y')
            date_format = date_.strftime('%Y-%m-%d')
        except:
            date_format, day, month, year = ['']*4
        return date_format

    def process_price_details(self, all_edit, price_details_major, book_dict):
        edits = all_edit['indiGoPriceBreakdown']['indigoJourneyPrice']['indigoJourneyPriceItineraryList']
        key_flights = all_edit['journeys']
        to_key_value, to_flight_key = '', ''
        from_key_value = '%s-%s' % (key_flights['items'][0]['segments']['items'][0]['departureStation'],
                                    key_flights['items'][0]['segments']['items'][0]['arrivalStation'])
        from_flight_key = '%s %s' % (key_flights['items'][0]['segments']['items'][0]['flightDesignator']
                                     ['carrierCode'], key_flights['items'][0]['segments']['items'][0]['flightDesignator']['flightNumber'])
        if self.ow_flights_connection:
            all_from_flights = []
            for i in key_flights['items'][0]['segments']['items']:
                all_from_flights.append(i['flightDesignator']['flightNumber'])
            from_flight_key = '%s %s' % (
                key_flights['items'][0]['segments']['items'][0]['flightDesignator']['carrierCode'], '<>6E'.join(all_from_flights))
            from_key_value = from_key_value + '-' + \
                '%s-%s' % (key_flights['items'][0]['segments']['items'][1]['departureStation'],
                           key_flights['items'][0]['segments']['items'][1]['arrivalStation'])
        if self.trip_type == 'RoundTrip':
            to_key_value = '%s-%s' % (key_flights['items'][1]['segments']['items'][0]['departureStation'],
                                      key_flights['items'][1]['segments']['items'][0]['arrivalStation'])
            to_flight_key = '%s %s' % (key_flights['items'][1]['segments']['items'][0]['flightDesignator']
                                       ['carrierCode'], key_flights['items'][1]['segments']['items'][0]['flightDesignator']['flightNumber'])
            if self.rt_flights_connection:
                all_to_flights = []
                for i in key_flights['items'][1]['segments']['items']:
                    all_to_flights.append(
                        i['flightDesignator']['flightNumber'])
                    to_flight_key = '%s %s' % (
                        key_flights['items'][1]['segments']['items'][0]['flightDesignator']['carrierCode'], '<>6E'.join(all_to_flights))
                    to_key_value = to_key_value + '-' + \
                        '%s-%s' % (key_flights['items'][1]['segments']['items'][1]['departureStation'],
                                   key_flights['items'][1]['segments']['items'][1]['arrivalStation'])
        all_keys = []
        if len(key_flights) > 2:
            return price_details_major
        #totalFare = all_edit['indiGoPriceBreakdown']['indigoJourneyPrice']['totalPrice']
        baggage_keys, meal_keys, ow_baggage_price, rt_baggage_price, ow_meals_price, rt_meals_price = self.get_baggage_meals(
            all_edit, book_dict)
        print baggage_keys, meal_keys
        for index, edit in enumerate(edits):
            edit_pi = edit['journeyPriceItinerary']
            price_details = {}
            try:
                adult_child_base = float(
                    float(edit_pi['baseFare'])/(int(self.adult_count) + int(self.child_count)))
            except:
                print 'Error'
                vals = (book_dict.get('tripid', ''), 'IndiGo', '', '', book_dict.get('origin', ''),
                        book_dict.get('destination', ''), self.tt,
                        book_dict.get('ctprice', ''),
                        '', 'Booking failed', '', 'Error with adult child calc', '', json.dumps(
                            price_details_major),
                        'Error with adult child calc', '', book_dict.get(
                            'tripid', ''), json.dumps(price_details_major)
                        )
                # Manual Error Insert To Db
                self.cur.execute(self.inserttwo_query, vals)
                self.conn.commit()
                return price_details_major
            amount_list = {}
            for i in edit_pi['taxAmountList']:
                if i['value']:
                    amount_list.update({i['key']: i['value']})
            if edit_pi['cuteCharges']:
                price_details.update({'Cute Charges': edit_pi['cuteCharges']})
            if edit_pi['fuelCharges']:
                price_details.update({'Fuel Charges': edit_pi['fuelCharges']})
            price_details.update(amount_list)
            price_details.update({'Adult': str(adult_child_base)})
            if self.child_count != '0':
                price_details.update({'Child': str(adult_child_base)})
            if self.infant_count != '0':
                try:
                    price_details.update(
                        {'Infant': edit_pi['ssrAmountList'][0]['value']})
                except:
                    pass
            if index == 0:
                if ow_baggage_price:
                    for i in ow_baggage_price:
                        price_details.update({i[0] + ' baggage':  i[1]})

                if ow_meals_price:
                    for i in ow_meals_price:
                        price_details.update({i[0] + ' meals':  i[1]})
            else:
                if rt_meals_price:
                    for i in rt_meals_price:
                        price_details.update({i[0] + ' meals':  i[1]})
                if rt_baggage_price:
                    for i in rt_baggage_price:
                        price_details.update({i[0] + ' baggage':  i[1]})
            total = 0
            for key, val in price_details.iteritems():
                if 'Adult' in key:
                    adults = int(self.adult_count) * float(val)
                    val = float(adults)
                elif 'Child' in key:
                    children = int(self.child_count) * float(val)
                    val = float(children)
                if val:
                    total += float(val)
            price_details.update({'total': total})
            if index == 0:
                price_details.update({'seg': from_key_value})
                price_details.update(
                    {'pcc': self.booking_dict['all_segments'][0].keys()[0]})
                # self.booking_dict['all_segments'][0].keys()[0]})
                price_details.update({'pcc_': self.book_using})
                price_details_major.update({from_flight_key: price_details})
            elif index == 1:
                price_details.update({'seg': to_key_value})
                price_details.update(
                    {'pcc': self.booking_dict['all_segments'][1].keys()[0]})
                # self.booking_dict['all_segments'][1].keys()[0]})
                price_details.update({'pcc_': self.book_using})
                price_details_major.update({to_flight_key: price_details})
        if baggage_keys:
            all_keys.extend(baggage_keys)
        if meal_keys:
            all_keys.extend(meal_keys)
        return price_details_major, all_keys

    def get_autopnr_pricingdetails(self, data):
        pcc = self.book_using
        pcc_ = self.pcc_name
        p_details = {}
        for input_flight in [self.ow_input_flight, self.rt_input_flight]:
            if input_flight == {} or not input_flight:
                continue
            segments = [(i['flight_no'], i['segment_name'])
                        for i in input_flight]
            flights, segs = [], []
            for i in segments:
                flights.append(i[0]), segs.append(i[1])
            f_no, segs = '<>'.join(flights), '-'.join(segs)
            p_details.update({f_no: {'seg': segs, 'pcc': pcc, 'pcc_': pcc_}})
            p_details[f_no].update(data)
        print p_details
        return p_details
