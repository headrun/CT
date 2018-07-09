'''Flights GoAir Support functions'''
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.mime.multipart import MIMEMultipart
import datetime
import MySQLdb
import ast
from collections import Counter
from ConfigParser import SafeConfigParser
_cfg = SafeConfigParser()
_cfg.read('../../../booking_airline_names.cfg')

class GoairUtils(object):

    def get_pcc_name(self):
        pcc_name = ''
        data = self.booking_dict['all_segments']
        if len(data)==1:
            pcc_name = 'goair_%s' % data[0].keys()[0]
        elif len(data)==2:
            if data[0].keys() != data[1].keys():
                self.multiple_pcc = True
            else:
                pcc_name = 'goair_%s' % data[0].keys()[0].replace('goair_', '')
        else:
            self.multi_pcc = True
        return pcc_name.upper()

    def pax_details(self):
        pax_details = self.booking_dict['pax_details']
        fin_pax, fin_infant, fin_child = [], [], []
        gender_format_dict = {'Mr': 'Male', 'Mrs': 'Female', \
                              'Ms': 'Female', 'Miss': 'Female',\
                              'Mstr': 'Male'}
        dob = ''
        email = self.booking_dict.get('emailid', '')
        for key, lst in pax_details.iteritems():
            pax_ = {}
            title, firstname, lastname, day, month, year = lst
            gender = gender_format_dict.get(title.strip(), '')
            if day and month and year: dob = '%s-%s-%s'%(year, month, day)
            else: dob = ''#"1988-02-01"
            pax_.update({'title' : title, 'firstname' : firstname,\
                     'lastname':lastname, 'dob' : dob, \
                     'gender': gender, 'email':email,\
                     'countrycode':'IN'})
            if 'adult' in key: fin_pax.append(pax_)
            elif 'child' in key: fin_child.append(pax_)
            elif 'infant' in key: fin_infant.append(pax_)
            if fin_pax:
                adult_names = ['%s %s %s' % (i.get('title'), i.get('firstname'), i.get('lastname')) for i in fin_pax]
                if len(adult_names) != len(set(adult_names)):
                    self.adult_fail = True
            if fin_child:
                child_names = ['%s %s %s' % (i.get('title'), i.get('firstname'), i.get('lastname')) for i in fin_child]
                if len(child_names) != len(set(child_names)):
                    self.child_fail = True
            if fin_infant:
                infant_names = ['%s %s %s' % (i.get('title'), i.get('firstname'), i.get('lastname')) for i in fin_infant]
                if len(infant_names) != len(set(infant_names)):
                    self.infant_fail = True
        ticket_class = self.booking_dict.get('ticket_booking_class', '')
        self.booking_dict['adults'] = fin_pax
        self.booking_dict['children'] = fin_child
        self.booking_dict['infants'] = fin_infant

    def adding_meals(self, hq_meals, xx, apply_meals):
	counter = 0
	meal_counter_check = False

        for i in hq_meals:
            sec, f_no, person, meal = i.split('_')
            check_person = '|%s|' % person
            for j_all in xx:
                for j in j_all:
                    if not f_no in j: break
                    if not check_person in j: break
                    if meal in j:
                        apply_meals.append(j)
			counter += 1
                        break

	if counter != len(hq_meals):
	    meal_counter_check = True
        return apply_meals, meal_counter_check

    def adding_baggages(self, hq_baggages, xx, apply_baggages):
	counter = 0
	baggage_counter_check = False

        for i in hq_baggages:
            sec, f_no, person, baggage = i.split('_')
            f_no = '~ '.join(f_no.split(' '))
            check_person = '%s|' % person
            for j_all in xx:
                for j in j_all:
                    if not f_no in j: break
                    if not check_person in j: break
                    if baggage in j:
                        apply_baggages.append(j)
			counter += 1
                        break
	if counter != len(hq_baggages):
	    baggage_counter_check = True
        return apply_baggages, baggage_counter_check


    def insert_error(self, pnr=None, mesg=None, err=None, tolerance=None, f_no=None, a_price=None, p_details={}):
        trip_id = self.booking_dict['trip_ref']
        origin = self.booking_dict['origin_code']
        destination = self.booking_dict['destination_code']
        trip_type = self.tt
        ow_date = self.booking_dict['departure_date']
        rt_date = self.booking_dict.get('return_date', '')
        if not f_no:
            f_no = [self.ow_flight_nos, self.rt_flight_nos]
            f_no = '<>'.join(f_no)
	f_no = f_no.strip('<>')
        vals = (trip_id, 'GoAir', pnr, f_no, origin, destination, trip_type, self.ct_price, a_price, mesg, tolerance, ow_date, rt_date, err, str(self.booking_dict), str(p_details), pnr, f_no, a_price, mesg,  err, str(self.booking_dict), str(p_details))
        try:
            self.cur.execute(self.insert_query, vals)
        except Exception as e:
            print "some insert error"
            self.log.debug('some insert error: %s' % e)
        self.conn.commit()

    def get_travel_date(self, date):
        try:
            date_ = datetime.datetime.strptime(date.strip(), '%d-%b-%y')
            date_format = date_.strftime('%Y-%m-%d')
        except:
            date_format, day, month, year = ['']*4
        return date_format

    def mealcode_inputs(self):
        onewaymealcode, returnmealcode = [], []
        for index, i in enumerate(self.ow_input_flight):
            owmeal = i.get('meal_codes', '')
            if owmeal:
                owmeal = [(str(index) + '_' + str(i.get('flight_no', '')) + '_' + str(count) + '_' + x) for count, x in enumerate(owmeal)]
                onewaymealcode.extend(owmeal)
            if index > 0 and owmeal:
                self.ow_meals_connection = True
        for index, i in enumerate(self.rt_input_flight):
            rtmeal = i.get('meal_codes', '')
            if rtmeal:
                rtmeal = [(str(index) + '_' + str(i.get('flight_no', '')) + '_' + str(count) + '_' + x) for count, x in enumerate(rtmeal)]
                returnmealcode.extend(rtmeal)
            if index > 0 and rtmeal:
                self.rt_meals_connection = True
        return onewaymealcode, returnmealcode

    def baggagecode_inputs(self):
        onewaybaggagecode, returnbaggagecode = [], []
        for index, i in enumerate(self.ow_input_flight):
            ow_baggage = i.get('baggage_codes', '')
            if ow_baggage:
                ow_baggage = [(str(index) + '_' + str(i.get('flight_no', '')) + '_' + str(count) + '_' + x) for count, x in enumerate(ow_baggage)]
                onewaybaggagecode.extend(ow_baggage)
            if index > 0 and ow_baggage:
                self.ow_baggage_connection = True
        for index, i in enumerate(self.rt_input_flight):
            rt_baggage = i.get('baggage_codes', '')
            if rt_baggage:
                rt_baggage = [(str(index) + '_' + str(i.get('flight_no', '')) + '_' + str(count) + '_' + x) for count, x in enumerate(rt_baggage)]
                returnbaggagecode.extend(rt_baggage)
            if index > 0 and rt_baggage:
                self.rt_baggage_connection = True
        return onewaybaggagecode, returnbaggagecode

    def process_input(self):
        book_dict, paxdls = {}, {}
        #sectors length calc
        rt_sectors = 0
        ow_sectors  = len(self.booking_dict['all_segments'][0].values()[0]['segments'])
        if self.booking_dict['trip_type'] == 'RT':
                rt_sectors = len(self.booking_dict['all_segments'][1].values()[0]['segments'])
        self.meals_sector_length = ow_sectors + rt_sectors
        self.baggages_sector_length = 1 if self.booking_dict['trip_type'] == 'OW' else 2

        #ct price calculation
        prices_segs = [i for i in self.booking_dict['all_segments']]

        for i in prices_segs:
            self.ct_price += int(i.values()[0]['amount'])

        self.proceed_to_book = self.booking_dict.get('proceed_to_book', 0)
        self.get_input_segments(self.booking_dict)
        try: ow_input_flight = self.ow_input_flight[0]
        except: ow_input_flight = {}
        try: rt_input_flight = self.rt_input_flight[0]
        except: rt_input_flight = {}
        ow_flt_id, rt_flt_id = [], []
        ow_hb, rt_hb = '', ''
        for i in self.ow_input_flight:
            flt = i.get('flight_no', '')
            if flt: ow_flt_id.append(flt)
            ow_hb = i.get('no_hand_baggage')
        for i in self.rt_input_flight:
            flt = i.get('flight_no', '')
            if flt: rt_flt_id.append(flt)
            rt_hb = i.get('no_hand_baggage')
        pnr = self.booking_dict.get('auto_pnr', '')
        self.onewaymealcode, self.returnmealcode = self.mealcode_inputs()
        self.onewaybaggagecode, self.returnbaggagecode = self.baggagecode_inputs()
        onewaydate = self.booking_dict.get('departure_date', '')#self.ow_input_flight.get('date', '')
        onewaydate = str(self.get_travel_date(onewaydate))
        returndate = self.booking_dict.get('return_date', '')#self.rt_input_flight.get('date', '')
        returndate = str(self.get_travel_date(returndate))
        ticket_class = self.booking_dict.get('ticket_booking_class', '')
        ticket_class_dict = {'Economy' : 'GoSmart', 'Business' : 'GoBusiness'}
        ticket_class = ticket_class_dict.get(ticket_class, '')
        onewayclass, returnclass = ticket_class, ticket_class
        print onewayclass, returnclass
        if self.booking_dict.get('ticket_booking_class', '') == 'Economy':
            if ow_hb:
                onewayclass = 'GoValue'
            if rt_hb:
                returnclass = 'GoValue'
        self.ow_flight_nos = '<>'.join(ow_flt_id)
        self.rt_flight_nos = '<>'.join(rt_flt_id)
        self.ow_class, self.rt_class = onewayclass, returnclass

    def get_input_segments(self, segments):
        all_segments = segments.get('all_segments', [])
        ow_flight_dict, rt_flight_dict = {}, {}
        if len(all_segments) == 1:
            key = ''.join(all_segments[0].keys())
            ow_flight_dict = all_segments[0][key]
            self.ow_fullinput_dict = ow_flight_dict
            if ow_flight_dict:
                try: self.ow_input_flight = ow_flight_dict.get('segments', [])
                except: self.ow_input_flight = {}
            else:
                self.ow_input_flight = {}
        elif len(all_segments) == 2:
            key1, key2 = ''.join(all_segments[0].keys()), ''.join(all_segments[1].keys())
            flight_dict1, flight_dict2 = all_segments[0][key1], all_segments[1][key2]
            f_to = flight_dict1.get('segments', [])
            self.ow_input_flight = flight_dict1.get('segments', [])
            self.rt_input_flight = flight_dict2.get('segments', [])
            self.ow_fullinput_dict, self.rt_fullinput_dict = flight_dict2, flight_dict1
        else:
            self.insert_error(mesg="Booking Failed", err="Multi-city booking")
        rt_len = 0
        if self.ow_fullinput_dict:
            ow_len = len(self.ow_fullinput_dict['segments'])
        if self.rt_fullinput_dict:
            rt_len = len(self.rt_fullinput_dict['segments'])
        if ow_len > 1 or rt_len > 1:
            self.connection_check = True

    def get_baggage_meals(self, edit_data, book_dict):
        baggages, meals = [], []
        ow_baggage_price, rt_baggage_price = [], []
        ow_meals_price, rt_meals_price = [], []
        if edit_data['indiGoAvailableSsr']['availableSsrsList'] == None:
            return baggages, meals, ow_baggage_price, rt_baggage_price, ow_meals_price, rt_meals_price
        #Baggage for OW
        for i in book_dict['onewaybaggagecode']:
            count = int(i.split('_')[1])
            i = i.split('_')[-1]
            print 'Checking for %s' % i
            try:
                bags_available = edit_data['indiGoAvailableSsr']['availableSsrsList']\
                                ['ssrsBaggagesList'][0]['paxSsrsList'][count]
                for bags in bags_available['ssrsList']:
                    if i in bags['key']:
                        baggages.append(bags['key'])
                        ow_baggage_price.append((i, bags['price']))
                        bags_check = True
                        break
            except Exception as e:
                print "Need to break and move to manual queue"
                self.insert_error(mesg='Check oneway baggages', err='processing baggage error')
                print e
                self.ow_baggage_connection = True
        for i in book_dict['returnbaggagecode']:
                count = int(i.split('_')[1])
                i = i.split('_')[-1]
                print 'Checking for %s' % i
                try:
                    bags_available = edit_data['indiGoAvailableSsr']['availableSsrsList']\
                    ['ssrsBaggagesList'][1]['paxSsrsList'][count]
                    for bags in bags_available['ssrsList']:
                        if i in bags['key']:
                            baggages.append(bags['key'])
                            rt_baggage_price.append((i, bags['price']))
                            bags_check = True
                            break
                except Exception as e:
                    print "Need to break and move to manual queue"
                    self.insert_error(mesg='Check return baggages', err='processing rt baggage error')
                    print e
                    self.rt_baggage_connection = True
        for i in book_dict['onewaymealcode']:
            count =  int(i.split('_')[1])
            i = i.split('_')[-1]
            print 'Checking for %s' % i
            try:
                bags_available = edit_data['indiGoAvailableSsr']['availableSsrsList']\
                ['ssrsMealsList'][0]['paxSsrsList'][count]
                for bags in bags_available['ssrsList']:
                    if i in bags['key']:
                        meals.append(bags['key'])
                        ow_meals_price.append((i, bags['price']))
                        bags_check = True
                        break
            except Exception as e:
                print "Need to break and move to manual queue"
                self.insert_error(mesg='Check oneway meals', err='processing meals error')
                print e
                self.ow_meals_connection = True
                break
        for i in book_dict['returnmealcode']:
            count = int(i.split('_')[1])
            i = i.split('_')[-1]
            print 'Checking for %s' % i
            try:
                bags_available = edit_data['indiGoAvailableSsr']['availableSsrsList']\
                ['ssrsMealsList'][1]['paxSsrsList'][count]
                for bags in bags_available['ssrsList']:
                    if i in bags['key']:
                        meals.append(bags['key'])
                        rt_meals_price.append((i, bags['price']))
                        bags_check = True
                        break
            except Exception as e:
                print "Need to break and move to manual queue"
                self.insert_error(mesg='Check return meals', err='processing rt meals error')
                print e
                self.rt_meals_connection = True
        if baggages == [] or meals == []:
            print 'baggage : %s' % len(baggages)
            print 'meals : %s' % len(meals)
        return baggages, meals, ow_baggage_price, rt_baggage_price, ow_meals_price, rt_meals_price

    def check_tolerance(self, ctprice, goairprice):
        tolerance_value, is_proceed = 0, 0
        total_fare = float(goairprice)
        if total_fare != 0:
            tolerance_value = total_fare - float(ctprice)
            if tolerance_value >= float(self.booking_dict.get('tolerance_amount', '5000')):#2000:
                is_proceed = 1  #movie it to off line
            else: is_proceed = 0
        else:
            tolerance_value, is_proceed = 0, 0
        return (tolerance_value, is_proceed)

    def price_details(self):
        total_fare = int(self.ow_fare.replace(',', '')) + int(self.rt_fare.replace(',', ''))
        total_persons = int(self.booking_dict['no_of_adults']) + int(self.booking_dict['no_of_children'])
        print self.base_fare
        if self.booking_dict['trip_type'] == 'OW':
            base_fare = int(self.base_fare.replace(',', ''))/total_persons
        elif self.booking_dict['trip_type'] == 'RT':
            base_fare = int(self.base_fare.replace(',', ''))/(total_persons*2)

        return str(base_fare)

