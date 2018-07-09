'''Spicejet cancellation helper functions'''
import smtplib
import json
import re
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.mime.multipart import MIMEMultipart
import datetime
import ast
from collections import Counter
from ConfigParser import SafeConfigParser

from scrapy.conf import settings

BOOK_PCC_PATH=settings['BOOK_PCC_PATH']

_cfg = SafeConfigParser()
_cfg.read(BOOK_PCC_PATH)


class SGBooking(object):

    def get_pcc_name(self):
        pcc_name = ''
        data_ = self.booking_dict
        data = data_['all_segments']
        if len(data)==1:
            pcc_name = 'spicejet_%s' % data[0].keys()[0].upper()
        elif len(data)==2:
            if data[0].keys() != data[1].keys():
                self.multiple_pcc = True
            else:
                pcc_name = 'spicejet_%s' % data[0].keys()[0].upper()
        return pcc_name

    def insert_error_msg(self, pnr='', mesg='', err='', tolerance='', f_no='', a_price='', p_details='{}'):
        trip_id = self.booking_dict['trip_ref']
        origin = self.booking_dict['origin_code']
        destination = self.booking_dict['destination_code']
        trip_type = self.booking_dict['trip_type']
        trip_type = '%s_%s_%s'%(trip_type, self.queue, self.book_using)
        ow_date = self.booking_dict['departure_date']
        ow_date = datetime.datetime.strptime(ow_date, '%d-%b-%y')
        rt_date = self.booking_dict.get('return_date', '')
        if rt_date:
            rt_date = datetime.datetime.strptime(rt_date, '%d-%b-%y')
        if not f_no:
            f_no = [self.ow_flight_nos, self.rt_flight_nos]
            f_no = '<>'.join(f_no).strip('<>')
        vals = (trip_id, 'Spicejet', pnr, f_no, origin, destination, trip_type, self.ct_price, a_price, mesg, tolerance, ow_date, rt_date, err, str(self.booking_dict), str(p_details), pnr, f_no, a_price, mesg,  err, str(self.booking_dict), str(p_details), str(trip_type), self.ct_price, tolerance)
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

    def special_rt_change(self):
        try:
            all_segments = self.booking_dict['all_segments']
            segment_len = len([i.keys() for i in all_segments])
            if self.booking_dict['trip_type'] == 'RT' and segment_len == 1:
                segments_list = []
                segment1 = filter(None, [i if i['seq_no'] == '1' else '' for i in all_segments[0][all_segments[0].keys()[0]]['segments']])
                segment2 = filter(None, [i if i['seq_no'] == '2' else '' for i in all_segments[0][all_segments[0].keys()[0]]['segments']])
                for index, seg in enumerate([segment1, segment2]):
                    new_all_segments = {}
                    amount = float('0')
                    if index == 0:
                        amount = all_segments[0][all_segments[0].keys()[0]]['amount']
                    new_all_segments.update({all_segments[0].keys()[0] : {'amount' : amount, 'segments' : seg}})
                    segments_list.append(new_all_segments)
                self.booking_dict['all_segments'] = segments_list
            self.log.debug(self.booking_dict.get('trip_ref'))
        except Exception as e:
            self.log.debug(e.message)
            self.send_mail('Input Error', e.message)
            self.insert_error_msg(err="Wrong input dict format")
            book_dict, pnr = {}, ''
            return

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

    def get_first_details(self, sel, check, find=True):
        AGMBKey = ''.join(sel.xpath('//input[@id="AGMBKey"]/@value').extract())
        keys = ['AGMBKey', 'AGPKey', 'AGPRETURNURL', 'QPKey', 'ReportsKey', '__VIEWSTATE']
        first_dict = {}
        for key in keys:
            actual_key = key
            if key == '__VIEWSTATE':
                key = 'viewState'
            value = ''.join(sel.xpath('//input[@id="%s"]/@value' % key).extract())
            first_dict.update({actual_key : value})
        firstname, lastname = self.booking_dict['adults'][0]['firstname'], self.booking_dict['adults'][0]['lastname']
        if find:
            if check:
                search_name = self.booking_dict['contact_mobile']
                type_of_search = '2'
            else:
        	search_name = '%s, %s' % (lastname, firstname)
                type_of_search = '5'
            self.log.debug('Checking for %s' % search_name)
            first_dict.update({
                            'ControlGroupBookingListView$BookingListBookingListView$DropDownListTypeOfSearch' : '5',
                            'ControlGroupBookingListView$BookingListBookingListView$Search' : 'ForAgency',
                            'ControlGroupBookingListView$BookingListBookingListView$TextBoxKeyword' : search_name,
                            'ISAGENTLOGGEDIN' : 'True',
                            '__EVENTARGUMENT' : '',
                            '__EVENTTARGET' : 'ControlGroupBookingListView$BookingListBookingListView$LinkButtonFindBooking',
                            'pageToken' : ''
                            })
        return first_dict

    def journey_check(self, journey_details):
        journ_details = [journey_details[x:x+6] for x in range(0, len(journey_details), 6)]
        all_segments = self.booking_dict['all_segments']
        if self.booking_dict['trip_type'] == 'OW':
            hq_flight_nos = [i['flight_no'] for i in [i.values()[0]['segments'] for i in self.booking_dict['all_segments']][0]]
            hq_dep_dates = [i['date'] for i in [i.values()[0]['segments'] for i in self.booking_dict['all_segments']][0]]
        elif self.booking_dict['trip_type'] == 'RT':
            hq_flight_nos_ = [i.values()[0]['segments'] for i in self.booking_dict['all_segments']]
            if len(hq_flight_nos_) == 2:
                hq_flight_nos = [i['flight_no'] for i in hq_flight_nos_[0]]
                hq_dep_dates = [i['date'] for i in hq_flight_nos_[0]]
                hq_flight_nos.extend([i['flight_no'] for i in hq_flight_nos_[1]])
                hq_dep_dates.extend([i['date'] for i in hq_flight_nos_[1]])
            else:
                flight_check = True
                self.log.debug('HQ Flight number issue')
                hq_flight_nos = []
                hq_dep_dates = []
                self.log.debug('HQ Departure date issue')
        journey_check = True
        for index, i in enumerate(journ_details):
            travel_date = datetime.datetime.strptime(i[0], '%a %d %b, %Y').strftime('%d-%b-%y')
            flight_no = i[1].replace(u'\xa0\r\n', '')
            flight_no = ' '.join(re.findall('(SG).*\s(\d+)', flight_no)[0])
            departure_time = i[-2]
            arrival_time = i[-1]
            #Compare with self.booking_dict of original all_segment_details.
            #Cancelled_segment_details and all_segment_details will  be equal always.
            if not hq_dep_dates[index] == travel_date:
                self.log.debug('travel date mismatch %s %s' % (all_segments[index]['departure_date'], travel_date))
                self.journey_mismatch = 'travel date mismatch'
                journey_check = True
                break
            if not hq_flight_nos[index] == flight_no:
                self.log.debug('flight no mismatch  %s %s' % (all_segments[index]['flight_no'], flight_no))
                self.journey_mismatch = 'flight no mismatch'
                journey_check = True
                break

            self.log.debug('%sth index of all segments matched' % index)
            journey_check = False
        return journey_check

    def get_autopnr_pricingdetails(self, data):
        pcc = self.book_using
        pcc_ = self.pcc_name
        p_details = {}
        for input_flight in [self.ow_input_flight, self.rt_input_flight]:
            if input_flight == {}: continue
            segments = [(i['flight_no'], i['segment_name']) for i in input_flight]
            flights, segs = [], []
            for i in segments:
                flights.append(i[0]), segs.append(i[1])
            f_no, segs = '<>'.join(flights), '-'.join(segs)
            p_details.update({f_no : {'seg' : segs, 'pcc' : pcc, 'pcc_' : pcc_}})
            p_details[f_no].update(data)
        print p_details
        return p_details

    def get_flight_fares(self, sel):
        flight_fares = sel.xpath('//tr[contains(@class, "fare-row")]')
        ticketclass_dict = {}
        for flights in flight_fares:
            flight_no = ''.join(flights.xpath('./td[1]//span[@class="white-space-nowrap"]/text()').extract())
            if ',' in flight_no:
                flight_nos = []
                for i in flight_no.split(','):
                    flight_nos.append(i.strip())
                flight_no = '<>'.join(flight_nos)
            print flight_no
            flights_classes = flights.xpath('./td/p[@productclass]')
            for classes in flights_classes:
                ticket_class = ''.join(classes.xpath('./@productclass').extract())
                value = ''.join(classes.xpath('./input/@value').extract())
                key = ''.join(classes.xpath('./input/@name').extract())
                if ticketclass_dict.get(ticket_class, ''):
                    ticketclass_dict[ticket_class].update({flight_no : '%s#<>#%s' % (key, value)})
                else:
                    ticketclass_dict.update({ticket_class : {flight_no : '%s#<>#%s' % (key, value)}})
        return ticketclass_dict

    def find_flight_keyval(self, ticket_class, ticketclass_dict, flight_nos, oneway=True, farebasis_code=''):
        #Here check for no hand baggage thing
        print ticketclass_dict
        if True in [i.get('no_hand_baggage') for i in self.ow_input_flight] and oneway:
            ticket_class = ['Hand Baggage Only']
        elif True in [i.get('no_hand_baggage') for i in self.rt_input_flight] and oneway:
            ticket_class = ['Hand Baggage Only']
        print ticket_class
        try: 
		all_flights = [i[flight_nos] for i in ticketclass_dict.values()]
		flight_actual = filter(None, [i if farebasis_code in i else '' for i in all_flights])[0]
		print flight_actual
		print 'found here itself'
		if flight_actual: return flight_actual
        except: 
		self.log.debug('Fare basis code not found')
        for i in ticket_class:
            class_flights = ticketclass_dict.get(i, '')
            if class_flights:
                flight = class_flights.get(flight_nos, '')
                if flight:
                    print flight
                    return flight
            else:
                self.log.debug('%s not found in %s' % (flight_nos, i))
        return ''

    def update_meals(self, hq_meals, sel):
        update_dict = {}
        meals = sel.xpath('//div[@class="mealPanel-item-selection"]/input/@name').extract()
        meals_xpath = sel.xpath('//div[@class="mealDropdown"]//input[contains(@id, "MealLegInputViewPassengerView") and @type="text"]/@name').extract()
        meals_xpath_select = sel.xpath('//div[@class="mealDropdown"]//select[contains(@id, "Select_CONTROLGROUPPASSENGER")]/@name').extract()
        all_meals_xpath = meals_xpath + meals_xpath_select
        for i in hq_meals:
            if not i: break
            passenger, flight_no, count, bag_code = i[0].split('_')
            passenger_name = 'passengerNumber_%s' % passenger
            flight_no = flight_no.replace(' ', '-')
            keys = []
            for meal_xpath in all_meals_xpath:
                counter = 0
                for data in [passenger_name, flight_no]:
                    if data in meal_xpath:
                        counter += 1
                if counter == 2:
                    keys.append(meal_xpath)
            print keys
            for meal in meals:
                counter = 0
                for data in [passenger_name, flight_no, bag_code]:
                    if data in meal:
                        counter += 1
                if counter == 3:
                    value = meal
                    break
            if not value:
                self.meals_issue = True
                break
            for key in keys:
                update_dict.update({key : value})
            return update_dict



    def update_baggages(self, hq_baggages, sel):
        baggages = sel.xpath('//select[contains(@class, "baggage")]/option/@value').extract()
        baggage_xpath = sel.xpath('//div[@class="mealdropdown"]//select[contains(@id, "BaggageInputViewPassengerView")]/@name').extract()
        update_dict = {}
        value = ''
        for i in hq_baggages:
            if not i: break
            passenger, flight_no, count, bag_code = i[0].split('_')
            passenger_name = 'passengerNumber_%s' % passenger
            flight_no = flight_no.replace(' ', '-')

            for bag_xpath in baggage_xpath:
                counter = 0
                for data in [passenger_name, flight_no]:
                    if data in bag_xpath:
                        counter += 1
                if counter == 2:
                    key = bag_xpath
                    break
            for bag in baggages:
                counter = 0
                for data in [passenger_name, flight_no, bag_code]:
                    if data in bag:
                        counter += 1
                if counter == 3:
                    value = bag
                    break
            if not value:
                self.baggage_issue = True
                break
            update_dict.update({key : value})
        return update_dict

    def price_details(self, sel):
        p_details = {}
        ow_price_details = sel.xpath('//div[@class="priceSummaryContainer"][1]//table[@class="priceSummary"]//tr')
        ow_total = ''.join(filter(None, ow_price_details[2].xpath('.//text()').extract())).strip()
        p_details.update({self.ow_flight_nos : {'total' : str(ow_total)}})
        p_details = self.get_price_dict(ow_price_details, p_details, self.ow_flight_nos)
        if self.booking_dict['trip_type'] == 'RT':
            rt_price_details = sel.xpath('//div[@class="priceSummaryContainer"][2]//table[@class="priceSummary"]//tr')
            rt_total = ''.join(filter(None, rt_price_details[2].xpath('.//text()').extract())).strip()
            p_details.update({self.rt_flight_nos : {'total' : str(rt_total)}})
            p_details = self.get_price_dict(rt_price_details, p_details, self.rt_flight_nos)
        return p_details


    def get_price_dict(self, ow_price_details, p_details, flight_no):
        for data in ow_price_details[3:9]:
            data = filter(None, [i.strip() for i in data.xpath('.//text()').extract()])
            if len(data) in [2, 3, 4]:
                try: data.remove(u'Fare + Fuel Charge')
                except: pass
                key, value = ' '.join(data[0:2]).replace(u'\xa0\r\n', ' ').replace('  ', '').strip(), data[-1]
                p_details[flight_no].update({key : value})
            elif len(data) >= 16:
                try: data.remove(u'Special Services')
                except: pass
                tax_dict = dict(data[i:i+2] for i in range(0, len(data), 2))
                p_details[flight_no].update(tax_dict)

        return p_details

    def check_tolerance(self, ctprice, indiprice):
        tolerance_value, is_proceed = 0, 0
        total_fare = float(indiprice)
        if total_fare != 0:
            tolerance_value = total_fare - float(ctprice)
            check_tolerance = float(self.booking_dict.get('tolerance_amount', '5000'))
            if self.queue == 'coupon':
                check_tolerance = float(10000)
            if tolerance_value >= check_tolerance:#2000:
                    is_proceed = 0  #movie it to off line
            else: is_proceed = 1
        else:
            tolerance_value, is_proceed = 0, 0
        return (tolerance_value, is_proceed)
