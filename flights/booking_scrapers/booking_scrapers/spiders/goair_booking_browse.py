from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
import ast
import tornado.httpclient as HT
from booking_scrapers.utils import *

from scrapy.conf import settings

from goair_xpath import *
from goair_utils import *
from indigo_utils import *

import sys
sys.path.append('../../../')

from root_utils import Helpers


_cfg = SafeConfigParser()
_cfg.read(settings['BOOK_PCC_PATH'])

class GoairBookBrowse(Spider, GoairUtils, Helpers, IndigoUtils):
    name = "goair_browse"
    start_urls = ["https://book.goair.in/Agent/Login"]
    handle_httpstatus_list = [404, 500]

    def __init__(self, *args, **kwargs):
        super(GoairBookBrowse, self).__init__(*args, **kwargs)
        self.log = create_logger_obj('goair_booking')
        self.insert_query  = 'insert into goair_booking_report (sk, airline, pnr, flight_number, from_location, to_location, triptype, cleartrip_price, airline_price, status_message, tolerance_amount, oneway_date, return_date, error_message, paxdetails, price_details, created_at, modified_at) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now()) on duplicate key update modified_at=now(), pnr=%s, flight_number=%s, airline_price=%s, status_message=%s, error_message=%s, paxdetails=%s, price_details=%s'
        self.booking_dict = ast.literal_eval(kwargs.get('jsons','{}'))
        self.all_data_counter = 0
        self.ct_price = 0
        self.onewaymealcode, self.returnmealcode = '', ''
        self.onewaybaggagecode, self.returnbaggagecode = '', ''
        self.meals_sector_length, self.baggages_sector_length = 0, 0

        self.currency = self.booking_dict.get('currency_code', 'INR')
        self.auto_phone_check = False

        self.ow_flight_nos, self.rt_flight_nos = '', ''
        self.ow_fullinput_dict, self.rt_fullinput_dict = [], []
        self.ow_input_flight, self.rt_input_flight = [], []

        self.adult_fail, self.child_fail, self.infant_fail = False, False, False

        self.datas_checked = []
        self.default_dob = '1988-02-01'
        self.auto_pnr = ''
        self.tt = ''
        self.queue = self.booking_dict['queue']
        self.book_using = ''
        self.multi_pcc = False
        self.connection_check = False
        self.ow_class, self.rt_class = '', ''
        self.ow_fare, self.rt_fare, self.base_fare = '0', '0', '0'

        self.process_input()
        if self.booking_dict['no_of_infants'] > self.booking_dict['no_of_adults']:
            self.insert_error(err='Infants more than adults')
            return

        self.amount, self.new_p_details, self.tolerance_value = 0, {}, 0

        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('booking', 'IP')
        passwd = db_cfg.get('booking', 'PASSWD')
        user = db_cfg.get('booking', 'USER')
        db_name = db_cfg.get('booking', 'DBNAME')
        self.conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()

    def parse(self, response):
        sel = Selector(response)
        self.pcc_name = self.get_pcc_name()
        self.tt = '%s_%s_%s' % (self.booking_dict['trip_type'], self.queue, self.pcc_name)
        persons = int(self.booking_dict['no_of_adults']) + int(self.booking_dict['no_of_children'])
        if len(self.onewaymealcode) > persons:
            self.insert_error(err='one person one meal check failure')
            return
        elif len(self.onewaybaggagecode) > persons:
            self.insert_error(err='one person one baggage check failure')
            return
        elif len(self.returnmealcode) > persons:
            self.insert_error(err='one person one meal check failure')
            return
        elif len(self.returnbaggagecode) > persons:
            self.insert_error(err='one person one baggage check failure')
            return
        self.pax_details()
        if self.adult_fail or self.child_fail or self.infant_fail:
            self.insert_error(err="Duplicate passengers")
            self.log.debug('Duplicate passengers')
            return
        req_token_key = ''.join(sel.xpath('//form[@action="/Agent/Login"]/input/@name').extract())
        req_token_value = ''.join(sel.xpath('//form[@action="/Agent/Login"]/input/@value').extract())
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

        self.log.debug('PCC : %s, Trip: %s' % (self.pcc_name, self.booking_dict.get('trip_ref')))
        if self.multi_pcc:
            self.insert_error(err='Multi PCC Booking')
            return
        try:
            data = [
                (req_token_key, req_token_value),
                ('starterAgentLogin.Username', _cfg.get(self.pcc_name, 'username')),
                ('starterAgentLogin.Password', _cfg.get(self.pcc_name, 'passwd'))
                ]
            self.book_using  = _cfg.get(self.pcc_name, 'username')
            try: self.tt = '%s_%s_%s' % (self.booking_dict['trip_type'], self.queue, self.book_using)
            except: pass
            self.log.debug('Booking using %s' % self.book_using)
        except:
            self.insert_error(err='PCC not %s available with scrapper' % self.pcc_name)
            self.log.debug('PCC not %s available with scrapper' % self.pcc_name)
            return
        next_url = 'https://book.goair.in/Agent/Login'
        yield FormRequest(next_url, callback=self.login_autopnr, formdata=data, method='POST')

    def login_autopnr(self, response):
        print "Login works"
        if 'Error' in response.url or 'Profile' not in response.url:
            self.insert_error(err='Unable to login on Login ID %s' % self.pcc_name)
            self.send_mail('Unable to login on Login ID %s'  % self.pcc_name, '', airline='goair', config='booking', receiver='goair_common')
        profile_url = 'https://book.goair.in/Agent/Profile'
        yield Request(profile_url, callback=self.parse_profile, meta={'auto_phone_check' : False}, dont_filter=True)

    def parse_profile(self, response):
        sel = Selector(response)
        search_email = self.booking_dict['custemailid']
        token = ''.join(sel.xpath('//form[@id="RetrieveByEmailAddress"]/input[@name="__RequestVerificationToken"]/@value').extract())
        data = {'__RequestVerificationToken' : token}
        data.update({'goAirRetrieveBookingsByEmailAddress.EmailAddress' : search_email})
        data.update({'goAirRetrieveBookingsByEmailAddress.PageSize' : '20'})
        data.update({'goAirRetrieveBookingsByEmailAddress.PerformSearch' : 'True'})
        data.update({'goAirRetrieveBookingsByEmailAddress.SearchArchive' : 'false'})
        #data.update({'goAirRetrieveBookingsByEmailAddress.FlightDate' : self.booking_dict['departure_date']})
        data.update({'goAirRetrieveBookingsByEmailAddress.FlightOrigin' : self.booking_dict['origin_code']})
        data.update({'goAirRetrieveBookingsByEmailAddress.FlightDestination' : self.booking_dict['destination_code']})

        yield FormRequest('https://book.goair.in/MyBookings', callback=self.parseall_pnrs, formdata=data, dont_filter=True)

    def parseall_pnrs(self, response):
        sel = Selector(response)
        all_data = sel.xpath('//div[@class="bookings-search-results-container"]//tbody/tr')
        datas = []
        for data in all_data:
            try:
                dep, org, dest, pnr, name, _, _, _ = data.xpath('.//td/text()').extract()
            except:
                try:
                    dep, org, dest, pnr, name, _, _ = data.xpath('.//td/text()').extract()
                except:
                    self.log.debug('Xpath issue while auto pnr check')
                    self.insert_error(err='Xpath issue while auto pnr check')
                    return
            if dest != self.booking_dict['destination_code']: continue
            if org != self.booking_dict['origin_code']: continue
            try: dep_date = datetime.datetime.strptime(dep.strip(), '%b %d, %Y').strftime('%d-%b-%y')
            except: dep_date = ''
            if dep_date != self.booking_dict['departure_date']: continue
            datas.append(pnr)
        for i in self.datas_checked:
            datas.remove(i)
        self.all_data_len = len(datas)
        for pnr in datas:
            url = 'https://book.goair.in/Booking/Retrieve/%s' % pnr
            token = ''.join(data.xpath('.//input[@name="__RequestVerificationToken"]/@value').extract())
            data = {'goairRetrieveBooking.IsBookingListRetrieve' : 'true'}
            data.update({'__RequestVerificationToken' : token})
            return FormRequest(url, callback=self.parse_pnrpage, formdata=data)
        if not datas :
                print "No PNRs, can book"

                origin_station = self.booking_dict.get('origin_code', '')
                destination_station = self.booking_dict.get('destination_code', '')
                trip_type = self.booking_dict.get('trip_type', '')
                departure_date = self.booking_dict.get('departure_date', '')
                return_date = self.booking_dict.get('return_date', '')
                adults = self.booking_dict.get('no_of_adults', '')
                children = self.booking_dict.get('no_of_children', '')
                infants = self.booking_dict.get('no_of_infants', '')
                no_of_passengers = int(adults) + int(children) + int(infants)

                if trip_type == 'OW':
                    params = (
                        ('s', 'True'),
                        ('o1', origin_station),
                        ('d1', destination_station),
                        ('ADT', adults),
                        ('CHD', children),
                        ('inl', infants),
                        ('dd1', departure_date),
                        ('mon', 'true'),
                        ('cc', self.currency)
                        )

                elif trip_type == 'RT':
                    params = (
                        ('s', 'true'),
                        ('o1', origin_station),
                        ('d1', destination_station),
                        ('dd1', departure_date),
                        ('dd2', return_date),
                        ('r', 'true'),
                        ('ADT', adults),
                        ('CHD', children),
                        ('inl', infants),
                        ('mon', 'true'),
                        ('cc', self.currency)
                        )
                next_url = 'https://book.goair.in/Flight/Select'
                return FormRequest(next_url, callback=self.parse_select, formdata=params, method="GET", meta={'no_of_passengers':no_of_passengers, 'infants':infants, 'book_dict':self.booking_dict})



    def parse_pnrpage(self, response):
        sel = Selector(response)
        flight_check, passengers_check, dep_arr_check = False, False, False
        pnr = response.url.split('/')[-1]
        open('%s' % response.url.split('/')[-1], 'w').write(response.body)
        #Flight numbers check happening here
        flight_numbers = sel.xpath('//div[@class="itin-flight-details-1 mdl-grid"]/div[contains(@class, "itin-flight-details-carrier")]/h4/text()').extract()
        #self.booking_dict[''][u'G8  283']
        print flight_numbers, response.url, sel.xpath('//h3[contains(@class, "pnr")]/text()').extract()

        if self.booking_dict['trip_type'] == 'OW':
            hq_flight_nos = [i[0]['flight_no'] for i in [i.values()[0]['segments'] for i in self.booking_dict['all_segments']]]
            #Commenting dep and arr time checks as patch needed from air team side
            #hq_dep_arr = [(x[0]['dep_time'], x[0]['arr_time']) for x in [i.values()[0]['segments']  for i in self.booking_dict['all_segments']]]
        elif self.booking_dict['trip_type'] == 'RT':
            hq_flight_nos = [i[0]['flight_no'] for i in [i.values()[0]['segments'] for i in self.booking_dict['all_segments']]]
            #hq_dep_arr = [(x[0]['dep_time'], x[0]['arr_time']) for x in [i.values()[0]['segments']  for i in self.booking_dict['all_segments']]]
        for index, i in enumerate(flight_numbers):
            if i.replace('  ', ' ') != hq_flight_nos[index]:
                print "flight numbers mismatch"
                flight_check = True
                break
        #Passenger names check here
        g8_pass_names = sel.xpath('//div[@class="itin-passengers-content group"]/div[2]/h5/text()').extract()#[u'1', u'Mr Manish Kumar', u'Adult']
        g8_infants = [i.strip('Traveling with ') for i in sel.xpath('//div[@class="itin-infant-name"]/h5/text()').extract()]
        g8_pass_names = g8_pass_names + g8_infants
        counter = 0
        hq_pass_names = [' '.join(i[1:3]) for i in self.booking_dict['pax_details'].values()]
        allhq_names = len(hq_pass_names)
        for i in hq_pass_names:
            for j in g8_pass_names:
                rpls = ['Mr ', 'Ms ', 'Mrs ', 'Miss ', 'Mis ']
                for k in rpls:
                    j = j.replace(k, '').strip()
                if i.title() == j.title():
                    counter += 1
                    break
        if counter != allhq_names:
            print 'passenger name mismatch'
            passengers_check = True
        #Departure and arrival timings check here
        '''dep_arr_times = sel.xpath('//div[contains(@class, "itin-flight-details-time")]/h4/text()').extract()#[u'05:45', u'07:10']
        dep_arr = [dep_arr_times[x:x+2] for x in range(0, len(dep_arr_times), 2)]
        if len(dep_arr) == len(hq_dep_arr):
            for i, j in zip(dep_arr, hq_dep_arr):
                if i[0] == j[0] and i[1] == j[1]:
                    print 'dep arr matches'
                else:
                    dep_arr_check = True'''
        #if not dep_arr_check and not flight_check and not passengers_check:
        if not flight_check and not passengers_check:
            #This is true
            total = ''.join(sel.xpath('//div[@class="itin-contact"]//div/h5[contains(text(), "INR")]/text()').extract())
            p_details = self.get_autopnr_pricingdetails({'total' : total, 'AUTO_PNR_EXISTS' : True})
            #so return PNR to HQ thereby stopping the crawler from going further.
            self.insert_error(pnr=pnr, mesg='Auto PNR exists: %s' % pnr, err='', p_details=p_details)
            print "This should be returned to HQ"
            return
        self.datas_checked.append(pnr)
        self.all_data_counter += 1
        print "Tried with PNR : %s, Count : %s" % (pnr, self.all_data_counter)
        profile_url = 'https://book.goair.in/Agent/Profile'
        yield Request(profile_url, callback=self.parse_profile, dont_filter=True)

    def parse_select(self, response):
        print 'Select flight works'
        data = []
        sel = Selector(response)
        no_of_passengers = response.meta['no_of_passengers']
        book_dict = response.meta['book_dict']
        infants = response.meta['infants']
        trip_type = book_dict.get('trip_type', '')

        out_flight_number = self.ow_flight_nos
        in_flight_number = self.rt_flight_nos
        out_travel_class = self.ow_class
        in_travel_class = self.rt_class
        rows = sel.xpath('//div[@class="overflow-auto"]//tbody/tr')
        classes = ['GoSmart', 'GoValue', 'GoBusiness']
        next_url = 'https://book.goair.in/Flight/Select'
        all_flights_dict = {}
        for class_ in classes:
            flights_dict = {}
            for row in rows:
                key = '<>'.join(row.xpath('.//div[contains(text(), "G8")]/text()').extract()).replace('  ', ' ')
                value = '<>'.join(row.xpath('.//td[@data-mobile-label="%s"]//input/@value' % class_).extract())
                cost = ''.join(row.xpath('.//td[@data-mobile-label="%s"]//span[@class="js-extract-text"]/text()' % class_).extract())
                flights_dict.update({key : '%s#<>#%s' % (value, cost)})
            all_flights_dict.update({class_ : flights_dict})
        #flight_numbers = sel.xpath(flight_numbers_xpath).extract()
        print all_flights_dict
        if trip_type == 'OW':
            try:
                flight_value, self.ow_fare = all_flights_dict[self.ow_class][self.ow_flight_nos].split('#<>#')
            except:
                self.insert_error(err="Flights not found")
                self.send_mail('Flight not found in selected class %s' % self.booking_dict['trip_ref'], '', airline='goair', config='booking', receiver='goair_common')
                return
            data = {'goAirAvailability.BundleCodes[0]' : ''}
            data.update({'goAirAvailability.MarketFareKeys[0]' : flight_value})
            print flight_value
            yield FormRequest(next_url, callback=self.parse_passenger, formdata=data, meta={'no_of_passengers':no_of_passengers, 'infants':infants, 'book_dict':book_dict}, dont_filter=True)
        elif trip_type == 'RT':
            try:
                ow_flight_value, self.ow_fare = all_flights_dict[self.ow_class][self.ow_flight_nos].split('#<>#')
                rt_flight_value, self.rt_fare = all_flights_dict[self.rt_class][self.rt_flight_nos].split('#<>#')
            except:
                self.insert_error(err="Flights not found")
                self.send_mail('Flight not found in selected class %s'  % self.booking_dict['trip_ref'], '', airline='goair', config='booking', receiver='goair_common')
                return
            #calculate percentage of ow & rt from amount
            data = {'goAirAvailability.BundleCodes[0]' : ''}
            data.update({'goAirAvailability.BundleCodes[1]' : ''})
            data.update({'goAirAvailability.MarketFareKeys[0]' : ow_flight_value})
            data.update({'goAirAvailability.MarketFareKeys[1]' : rt_flight_value})
            print ow_flight_value, rt_flight_value
            yield FormRequest(next_url, callback=self.parse_passenger, formdata=data, meta={'no_of_passengers':no_of_passengers, 'infants':infants, 'book_dict':book_dict}, dont_filter=True)

    def parse_passenger(self, response):
        pax_count = response.meta['no_of_passengers']
        book_dict = response.meta['book_dict']
        infants = int(response.meta['infants'])
        sel = Selector(response)
        self.base_fare = ''.join(sel.xpath('//div[@class="price-display-summary-line-item"]/div[contains(text(), "Base Fare")]/../div[contains(text(), "INR")]/text()').extract()).strip(' INR')
        pass_count = len(book_dict.get('pax_details', ''))
        contact_details = {}
        if pax_count != pass_count:
            print "Please Enter the acccurate persons count"
        else:
            passenger_details = self.booking_dict['adults']
            passenger_details.extend(self.booking_dict['children'])

            infants_details = self.booking_dict['infants']
            pax_names = []
            data = []
            if passenger_details:
                passenger_details = filter(None, passenger_details)
                for h, i in enumerate(passenger_details):
                    if i.get('gender', '') == 'Male': gender = '1'
                    else: gender = '2'
                    data.append(('goAirPassengers[%s].Name.Title' % h, i.get('title')))
                    data.append(('goAirPassengers[%s].Name.First' % h, i.get('firstname')))
                    data.append(('goAirPassengers[%s].Name.Last' % h, i.get('lastname')))
                    data.append(('goAirPassengers[%s].Info.Gender' % h, gender))
                    data.append(('goAirPassengers[%s].Info.Nationality' % h, 'IN'))
                    if i.get('dob', '') != '':
                        data.append(('goAirPassengers[%s].date_of_birth_day_%s' % (h, h), i.get('dob', '').split('-')[-1]))
                        data.append(('goAirPassengers[%s].date_of_birth_month_%s' % (h, h), i.get('dob', '').split('-')[1]))
                        data.append(('goAirPassengers[%s].date_of_birth_year_%s' % (h, h), i.get('dob', '').split('-')[0]))
                        data.append(('goAirPassengers[%s].TypeInfo.DateOfBirth' % h, i.get('dob', '')))

                    else:
                        data.append(('goAirPassengers[%s].date_of_birth_day_%s' % (h, h), ''))
                        data.append(('goAirPassengers[%s].date_of_birth_month_%s' % (h, h), ''))
                        data.append(('goAirPassengers[%s].date_of_birth_year_%s' % (h, h), ''))
                        data.append(('goAirPassengers[%s].TypeInfo.DateOfBirth' % h, ''))

                    if h == 0:
                        contact_details.update({'title':i.get('title'), 'firstname':i.get('firstname'), 'lastname':i.get('lastname')})
                    pax_names.append(i.get('firstname') + ' ' + i.get('lastname'))


            if infants_details and len(infants_details) == infants:
                for h, i in enumerate(infants_details):
                    if i.get('gender', '') == 'Male': gender = '1'
                    else: gender = '2'
                    data.append(('goAirPassengers.Infants[%s].Name.First' % h, i.get('firstname')))
                    data.append(('goAirPassengers.Infants[%s].Name.Last' % h, i.get('lastname')))
                    data.append(('goAirPassengers.Infants[%s].Gender' % h, gender))
                    data.append(('goAirPassengers.Infants[%s].Nationality' % h, 'IN'))
                    if i.get('dob', '') != '':
                        data.append(('goAirPassengers.Infants[%s].infant_date_of_birth_day_%s' % (h, h), i.get('dob').split('-')[-1]))
                        data.append(('goAirPassengers.Infants[%s].infant_date_of_birth_month_%s' % (h, h), i.get('dob').split('-')[1]))
                        data.append(('goAirPassengers.Infants[%s].infant_date_of_birth_year_%s' % (h, h), i.get('dob').split('-')[0]))
                        data.append(('goAirPassengers.Infants[%s].DateOfBirth' % h, i.get('dob')))
                    else:
                        self.insert_error(err='Infant does not have dob')
                        return

                    data.append(('goAirPassengers.Infants[%s].AttachedPassengerNumber' % h, '%s' % h))

            emerg_no, emerg_isd = self.booking_dict['trip_ref'][:2], self.booking_dict['trip_ref'][2:]
            mob_isd = '91'
            if contact_details:
                data.append(('goAirContact.TypeCode', 'P'))
                data.append(('goAirContact.CustomerNumber', ''))
                data.append(('goAirContact.ImFirstPassenger', 'on'))
                data.append(('goAirContact.Name.Title', contact_details.get('title')))
                data.append(('goAirContact.Name.First', contact_details.get('firstname')))
                data.append(('goAirContact.Name.Last', contact_details.get('lastname')))
                data.append(('goAirContact.MobileISDNumber', mob_isd))
                data.append(('goAirContact.MobileNumber', self.booking_dict.get('contact_mobile', '')))
                data.append(('goAirContact.EmailAddress', self.booking_dict.get('emailid', '')))
                data.append(('goAirContact.EmergencyContactISDNumber', emerg_isd))
                data.append(('goAirContact.EmergencyContactAreaNumber', ''))
                data.append(('goAirContact.EmergencyNumber', emerg_no))
                data.append(('goAirGstContact.HaveGst', 'false'))
                data.append(('goAirGstContact.CustomerNumber', ''))
                data.append(('goAirGstContact.CompanyName', ''))
                data.append(('goAirGstContact.EmailAddress', ''))
            next_url = 'https://book.goair.in/Passengers/Update'
            yield FormRequest(next_url, callback=self.parse_extras, formdata=data, method="POST", meta={'pax_names':pax_names, 'book_dict':book_dict})

    def parse_extras(self, response):
        sel = Selector(response)
        book_dict = response.meta['book_dict']
        apply_meals = []
        hq_meals = self.onewaymealcode + self.returnmealcode
        if hq_meals:
            meals = sel.xpath('//div[@class="extras-ssr-body meals-container"]//div[contains(@class, "nesting ssr-forms")]')
            xx = [meal.xpath('.//select[contains(@class, "ssr-input")]/option/@value').extract() for meal in meals]
	    check = set([i.split('_')[-1] for i in  hq_meals]) - set( [i.split('|')[2] for i in xx[0]])
            if check:
                self.insert_error(err="Meals not available in site %s" % '<>'.join(check))
                self.log.debug('Meals not available in site %s' % '<>'.join(check))
                return
            apply_meals, meal_counter_check = self.adding_meals(hq_meals, xx, apply_meals)
            print apply_meals
    	    if meal_counter_check:
                self.insert_error(err="Meals not available in site")
                self.log.debug('Meals not available in site')
                return
        apply_baggages = []
        hq_baggages = self.onewaybaggagecode + self.returnbaggagecode
        if hq_baggages:
            baggages = sel.xpath('//div[@class="extras-ssr-body baggage-container"]//div[contains(@class, "nesting ssr-forms")]')
            yy = [baggage.xpath('.//select[contains(@class, "ssr-input")]/option/@value').extract() for baggage in baggages]
    	    check = set([i.split('_')[-1] for i in  hq_meals]) - set( [i.split('|')[2] for i in yy[0]])
            if check:
                    self.insert_error(err="Baggages not available in site %s" % '<>'.join(check))
                    self.log.debug('Baggages not available in site %s' % '<>'.join(check))
                    return
            apply_baggages, baggage_counter_check = self.adding_baggages(hq_baggages, yy, apply_baggages)

            print apply_baggages
    	    if baggage_counter_check:
                    self.insert_error(err="Baggages not available in site")
                    self.log.debug('Baggages not available in site')
                    return
        #ins_aquation = ''.join(sel.xpath(insu_aquation_xpath).extract())
        insu_qute_keys = sel.xpath(insu_qute_keys_xpath).extract()
        insu_qute_values = sel.xpath(insu_qute_values_xpath).extract()
        insu_data = [('goAirInsuranceQuote.IsBuyInsurance', 'False'),
                     ('goAirInsuranceQuote.Address.LineOne.Data', ''),
                     ('goAirInsuranceQuote.Address.PostalCode.Data', ''),
                     ('goAirInsuranceQuote.Address.LineTwo.Data', ''),
                     ('goAirInsuranceQuote.Address.City.Data', ''),
                     ('goAirInsuranceQuote.Address.Country.Data', ''),
                     ('goAirInsuranceQuote.Address.EmailAddress.Data', ''),
                    ]

        for i, j in zip(insu_qute_keys, insu_qute_values):
            insu_data.append((i, j))
        if apply_baggages or apply_meals:
            apply_all = apply_meals + apply_baggages
            i = apply_all.pop(0)
            i = '%s|1' % i
            print i
            data = {'goAirSsr.SelectedJourneySsrs[0]' : i}
            url = 'https://book.goair.in/Ssrs/Apply'
            from pprint import pprint
            print pprint(data)
            return FormRequest(url, callback=self.parse_reload, formdata=data, meta={'insu_data' : insu_data, 'apply_all' : apply_all})
        else:
            print 'No meals or baggages'
            next_url = 'https://book.goair.in/Extras/Add'
            return FormRequest(next_url, callback=self.parse_purchase, formdata=insu_data, method="POST")

            #From here only we have to do the parse_purchase

    def parse_reload(self, response):
        insu_data = response.meta['insu_data']
        apply_all = response.meta['apply_all']
        if apply_all:
            i = apply_all.pop(0)
            i = '%s|1' % i
            print i
            data = {'goAirSsr.SelectedJourneySsrs[0]' : i}
            url = 'https://book.goair.in/Ssrs/Apply'
            return FormRequest(url, callback=self.parse_reload, formdata=data, meta={'insu_data' : insu_data, 'apply_all' : apply_all}, dont_filter=True)
        else:
            next_url = 'https://book.goair.in/Extras/Add'
            return FormRequest(next_url, callback=self.parse_purchase, formdata=insu_data, method="POST")

    def parse_purchase(self, response):
        sel = Selector(response)
        book_dict = self.booking_dict
        self.amount = int(''.join(sel.xpath(final_price_xpath).extract()).replace(' INR', '').replace(',', ''))
        infant_amount = sel.xpath('//div[@class="price-display-passenger-charges"]//div[contains(text(), "INR")]/text()').extract()
        if infant_amount:
            infant_amount = infant_amount[0].replace('INR', '')
        tax_breakdown = sel.xpath('//div[@id="tax_breakdown_content"]//tr')
        tax_flights_split = {}
        for taxes in tax_breakdown:
            _, _, f_no, _, _, tax_name, tax = [i.strip() for i in taxes.xpath('./td/text()').extract()]
            tax = int(tax.strip('INR'))
            if tax_flights_split.get(f_no):
                if tax_flights_split[f_no].get(tax_name, ''):
                    new_tax = int(tax_flights_split[f_no].get(tax_name)) + tax
                    tax_flights_split[f_no][tax_name] = str(new_tax)
                else:
                    tax_flights_split[f_no].update({tax_name : str(tax)})
            else:
                tax_flights_split.update({f_no : {tax_name : str(tax)}})
        is_proceed = 0
        token = ''.join(sel.xpath('//form[@id="agency payment"]/input[@name="__RequestVerificationToken"]/@value').extract())
        if not self.amount:
            self.send_mail("Agency Account not found %s"%book_dict.get('tripid', ''), '', airline='goair', config='booking', receiver='goair_common')
            #Fifth Error Msg To Db
            self.insert_error(err="Agency Account not found")
	    return
        else:
            self.tolerance_value, is_proceed = self.check_tolerance(self.ct_price, self.amount)
        base_fare = self.price_details()
        meals_bags = [i.strip() for i in sel.xpath('//div[@class="price-display-passenger-charges"]/div/text()').extract()]
        key1, key2 = '', ''
        if self.booking_dict['trip_type'] == 'RT':
            key1, key2 = tax_flights_split.keys()
            if key1.replace('  ', ' ') not in self.ow_flight_nos:
                key1, key2 = key2, key1
        else:
            key1 = tax_flights_split.keys()[0]
        if meals_bags:
                if self.returnmealcode or self.returnbaggagecode:
                    ow_mb = filter(None, [i.strip() for i in sel.xpath('//div[@class="price-display-section"]/div[2]/b[2]/preceding-sibling::div//text()').extract()])
                    ow_mbs = {ow_mb[i]: str(ow_mb[i+1]) for i in range(0, len(ow_mb), 2)}
                    rt_mb = filter(None, [i.strip() for i in sel.xpath('//div[@class="price-display-section"]/div[2]/b[2]/following-sibling::div//text()').extract()])
                    rt_mbs = {rt_mb[i]: str(rt_mb[i+1]) for i in range(0, len(rt_mb), 2)}
                    #check here for key 1 and key 2 changes
                    tax_flights_split[key1].update(ow_mbs)
                    tax_flights_split[key2].update(rt_mbs)
                else:
                    meals_bags = {meals_bags[i]: meals_bags[i+1] for i in range(0, len(meals_bags), 2)}
                    tax_flights_split.values()[0].update(meals_bags)
        if self.booking_dict['no_of_adults'] != '0':
            tax_flights_split[key1].update({'Adult' : base_fare})
            if self.booking_dict['trip_type'] == 'RT':
                tax_flights_split[key2].update({'Adult' : base_fare})
        if self.booking_dict['no_of_children'] != '0':
            tax_flights_split[key1].update({'Child' : base_fare})
            if self.booking_dict['trip_type'] == 'RT':
                tax_flights_split[key2].update({'Child' : base_fare})
        from_key_value = '-'.join([i['segment_name'] for i in self.booking_dict['all_segments'][0].values()[0]['segments']])
        if self.amount:
            total_by_2 = self.amount
            tax_flights_split[key1].update({'total' : total_by_2})
            tax_flights_split[key1].update({'pcc' : self.booking_dict['all_segments'][0].keys()[0]})
            tax_flights_split[key1].update({'pcc_' : self.book_using})
            tax_flights_split[key1].update({'seg' : from_key_value})
            if self.booking_dict['trip_type'] == 'RT':
            	total_by_2 = int(self.amount)/2.0
                to_key_value = '-'.join([i['segment_name'] for i in self.booking_dict['all_segments'][1].values()[0]['segments']])
                tax_flights_split[key2].update({'total' : total_by_2})
                tax_flights_split[key2].update({'pcc' : self.booking_dict['all_segments'][1].keys()[0]})
                tax_flights_split[key2].update({'pcc_' : self.book_using})
                tax_flights_split[key2].update({'seg' : to_key_value})
        else:
            print 'Xpath Issue for Total before payment'
            return
        #Key modification needs to happen
        self.new_p_details[self.ow_flight_nos] = tax_flights_split[key1]
        if self.rt_flight_nos:
            self.new_p_details.update({self.rt_flight_nos : tax_flights_split[key2]})

        if is_proceed == 0:
            commit_url = 'https://book.goair.in/Booking/Commit'
            data = {
                  '__RequestVerificationToken': token,
                  'AgencyPayment.AccountNumber': self.pcc_name.replace('GOAIR_', ''),
                  'AgencyPayment.PaymentMethodCode': 'AG',
                  'AgencyPayment.PaymentMethodType': 'AgencyAccount',
                  'AgencyPayment.QuotedCurrencyCode': self.currency,
                  'AgencyPayment.QuotedAmount': str(self.amount),
                    }
            if self.proceed_to_book == 1:
                self.log.debug('Booking will happen')
                yield FormRequest(commit_url, callback=self.parse_postcommit, formdata=data, dont_filter=True)
            else:
                self.log.debug('Send Mock response')
                self.insert_error(p_details=self.new_p_details, pnr='TEST101', mesg='Mock Success', tolerance=self.tolerance_value, a_price=self.amount)
        else:
            self.log.debug('Fare Increased by GoAir')
            self.send_mail("Fare increased by GoAir for %s by %s or response error" % ((self.booking_dict.get('trip_ref', ''), self.tolerance_value)), '', airline='goair', config='booking', receiver='goair_common')
            self.insert_error(tolerance=self.tolerance_value, err='Fare increased by Airline', a_price=self.amount)
            return

    def parse_postcommit(self, response):
        url = 'https://book.goair.in/Booking/PostCommit'
        import time
        time.sleep(10)
        yield Request(url, callback=self.parse_final_report, dont_filter=True)

    def parse_final_report(self, response):
        sel = Selector(response)
        try: pnr = ''.join(sel.xpath('//div[@class="itin-header group"]/h3[contains(@class, "itin-pnr")]/text()').extract())
        except: pnr = 'check manual'
        open('%s%s.html' % (self.booking_dict['trip_ref'], pnr), 'w').write(response.body)
        if not pnr:
            self.insert_error(err='Payment failed whereas payment is successful')
            return
        self.insert_error(p_details=self.new_p_details, pnr=pnr, mesg='Confirmed', tolerance=self.tolerance_value, a_price=self.amount)
