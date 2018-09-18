'''Flights Air Arabia Support functions'''
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.mime.multipart import MIMEMultipart
import datetime
import MySQLdb
import ast
import requests
from collections import Counter


class AirArabiaUtils(object):

    def get_pcc_name(self):
        pcc_name = ''
        data = self.booking_dict['all_segments']
        if len(data) == 1:
            pcc_name = 'AIRARABIA_%s' % data[0].keys()[0]
        elif len(data) == 2:
            if data[0].keys() != data[1].keys():
                self.multiple_pcc = True
            else:
                pcc_name = 'AIRARABIA_%s' % data[0].keys()[
                    0].replace('AIRARABIA_', '')
        else:
            self.multi_pcc = True
        return pcc_name.upper()

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
        vals = (str(trip_id), 'AirArabia', str(pnr), str(f_no), origin, destination, trip_type, str(self.ct_price), str(a_price), mesg, str(tolerance), str(ow_date), str(rt_date), err, str(
            self.booking_dict), str(p_details), str(pnr), str(f_no), str(a_price), mesg,  err, str(self.booking_dict), str(p_details), str(trip_type), str(self.ct_price), str(tolerance), origin, destination)
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

    def pax_details(self):
        pax_details = self.booking_dict['pax_details']
        fin_pax, fin_infant, fin_child = [], [], []
        gender_format_dict = {'Mr': 'Male', 'Mrs': 'Female',
                              'Ms': 'Female', 'Miss': 'Female',
                              'Mstr': 'Male'}
        dob = ''
        email = self.booking_dict.get('emailid', '')
        for key, lst in pax_details.iteritems():
            pax_ = {}
            title, firstname, lastname, day, month, year = lst
            gender = gender_format_dict.get(title.strip(), '')
            if day and month and year:
                dob = '%s-%s-%s' % (year, month, day)
            else:
                dob = ''  # "1988-02-01"
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
        ticket_class = self.booking_dict.get('ticket_booking_class', '')
        self.booking_dict['adults'] = fin_pax
        self.booking_dict['children'] = fin_child
        self.booking_dict['infants'] = fin_infant

    def process_input(self):
        book_dict, paxdls = {}, {}
        # sectors length calc
        rt_sectors = 0
        ow_sectors = len(
            self.booking_dict['all_segments'][0].values()[0]['segments'])
        if self.booking_dict['trip_type'] == 'RT':
            rt_sectors = len(
                self.booking_dict['all_segments'][1].values()[0]['segments'])
        self.meals_sector_length = ow_sectors + rt_sectors
        self.baggages_sector_length = 1 if self.booking_dict['trip_type'] == 'OW' else 2

        # ct price calculation
        prices_segs = [i for i in self.booking_dict['all_segments']]

        for i in prices_segs:
            self.ct_price += int(i.values()[0]['amount'])

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
        pnr = self.booking_dict.get('auto_pnr', '')
        #self.onewaymealcode, self.returnmealcode = self.mealcode_inputs()
        #self.onewaybaggagecode, self.returnbaggagecode = self.baggagecode_inputs()
        ticket_class = self.booking_dict.get('ticket_booking_class', '')
        ticket_class_dict = {'Economy': 'GoSmart', 'Business': 'GoBusiness'}
        ticket_class = ticket_class_dict.get(ticket_class, '')
        onewayclass, returnclass = ticket_class, ticket_class
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

    def checkTolerance(self, airlineprice):
        ctprice = sum([i.values()[0].get('amount')
                       for i in self.booking_dict.get('all_segments', [])])
        tolerance_value, is_proceed = 0, 0
        total_fare = float(airlineprice)
        if total_fare != 0:
            tolerance_value = total_fare - \
                float(ctprice)
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

    def getBaggageWait(self, ttype):
        try:
            wait = self.booking_dict.get('all_segments', {})[ttype].values()[0].get(
                'segments', [])[0].get('baggage_info', {}).get('weight', '')
            wait = ''.join(re.findall('\d+', wait))
            if '15' in wait:
                wait = '20'
            elif '25' in wait:
                wait = '30'
            elif '35' in wait:
                wait = '40'
            elif '45' in wait:
                wait = '50'
            wait = float(wait, 1)
        except:
            wait = 0.0
        return wait

    def paxFormFilling(self, bag_dict, bag_seg_dict, bag_key):
        hqpax_dict = self.booking_dict.get('pax_details', {})
        infantpax_dict = len([val for key, val in self.booking_dict.get(
            'pax_details', {}).iteritems() if 'infant' in key])
        sec_no, infant_count = 1, 1
        pax_form_list = []
        pax_sorted_lst = sorted(hqpax_dict)
        # for key, val_lst in hqpax_dict.iteritems():
        for key in pax_sorted_lst:
            val_lst = hqpax_dict.get(key)
            pax_dict = {u'displaypnrPaxArrivalFlightNumber': None, u'displayInfantWith': u'', u'displayAdultDOB': u'', u'displayETicket': None, u'displayAdultLastName': None, u'displaypnrPaxDepartureTime': None, u'displayFFID': u'', u'displayAdultFirstName': None, u'displayAdultTitleOl': None, u'seqNumber': 1, u'displayNameTranslationLanguage': None, u'displayPnrPaxCatFOIDPlace': None, u'displayPaxCategory': u'A', u'displayPnrPaxCatFOIDNumber': u'', u'displayPnrPaxGroupId': None, u'displayVisaDocPlaceOfIssue': None, u'displaypnrPaxDepartureFlightNumber': None, u'displayAdultLastNameOl': None, u'displaypnrPaxFltDepartureDate': None, u'displayVisaApplicableCountry': None, u'displayAdultType': u'AD', u'displayAdultFirstNameOl': None, u'displayTravelDocType': None,
                        u'displayAdultNationality': None, u'displaypnrPaxFltArrivalDate': None, u'displayVisaDocIssueDate': None, u'displayPnrPaxPlaceOfBirth': None, u'displayVisaDocNumber': None, u'anci': [{}, {u'baggage': {u'baggages': [{u'old': False, u'baggageName': None, u'baggageIndex': 0, u'ondBaggageChargeId': None, u'baggageQty': 1, u'baggageCharge': None, u'subTotal': None}], u'baggageQtyTotal': 1, u'baggageChargeTotal': None}, u'segInfo': {u'baggageONDGroupId': None, u'returnFlag': False, u'flightNumber': None, u'logicalCabinClass': u'Y', u'pnrSegId': None, u'segCode': None, u'cabinClassCode': u'Y', u'flightRefNumber': None}}], u'displayPnrPaxCatFOIDExpiry': None, u'removeAnci': [{}, {}], u'displayAdultTitle': None, u'displaypnrPaxArrivalTime': None, u'paxId': 0, u'displayNationalIDNo': None}
            # pax details
            title, name, lastname, b_day, b_month, b_year = val_lst
            if 'adult' in key:
                pax_dict['displayAdultType'] = 'AD'
                if infantpax_dict != 0 and infant_count <= infantpax_dict:
                    #inf_val = ''.join(re.findall('\d+', key))
                    pax_dict['displayInfantWith'] = str(infant_count)
                    infant_count += 1
            elif 'child' in key:
                pax_dict['displayAdultType'] = 'CH'
            else:
                continue
            pax_dict['displayAdultTitle'] = title.upper()
            pax_dict['displayAdultFirstName'] = name
            pax_dict['displayAdultLastName'] = lastname
            pax_dict['displayAdultNationality'] = ''
            pax_dict['seqNumber'] = sec_no
            pax_dict['paxId'] = sec_no - 1
            if b_day and b_month and b_year:
                pax_dict['displayAdultDOB'] = '%s/%s/%s' % (
                    b_day, b_month, b_year)
            else:
                pax_dict['displayAdultDOB'] = ''
            pax_dict['displayPaxCategory'] = 'A'
            anci = pax_dict['anci'][1]
            # baggage details
            pax_dict['anci'][1]['baggage']['baggages'] = []
            bagg = {}
            bagg['baggageName'] = bag_dict.get(
                bag_key, {}).get('baggageName', '')
            bagg['baggageIndex'] = bag_dict.get(
                bag_key, {}).get('baggageIndex', 0)
            bagg['ondBaggageChargeId'] = bag_dict.get(
                bag_key, {}).get('ondBaggageChargeId', '')
            bagg['baggageQty'] = bag_dict.get(bag_key, {}).get('baggageQty', 1)
            bagg['baggageCharge'] = bag_dict.get(
                bag_key, {}).get('baggageCharge', '')
            bagg['subTotal'] = bag_dict.get(
                bag_key, {}).get('baggageCharge', '')
            bagg['old'] = False
            pax_dict['anci'][1]['baggage']['baggages'].append(bagg)
            pax_dict['anci'][1]['baggage'][u'baggageChargeTotal'] = bag_dict.get(
                bag_key, {}).get('baggageCharge', '')
            # seg_details
            seg_dict = pax_dict['anci'][1]['segInfo']
            seg_dict[u'logicalCabinClass'] = bag_seg_dict.get(
                'logicalCabinClassCode', '')
            seg_dict[u'baggageONDGroupId'] = bag_seg_dict.get(
                'baggageONDGroupId', '')
            seg_dict[u'pnrSegId'] = bag_seg_dict.get('pnrSegId', '')
            seg_dict[u'segCode'] = bag_seg_dict.get('segmentCode', '')
            seg_dict[u'cabinClassCode'] = bag_seg_dict.get(
                'cabinClassCode', '')
            seg_dict[u'returnFlag'] = bag_seg_dict.get('returnFlag', '')
            seg_dict[u'flightRefNumber'] = bag_seg_dict.get(
                'flightRefNumber', '')
            seg_dict[u'flightNumber'] = bag_seg_dict.get('flightNumber', '')
            pax_dict['anci'][1]['segInfo'] = seg_dict
            pax_form_list.append(pax_dict)
            sec_no += 1
        return pax_form_list

    def carrierCode(self, flights_dict):
        carriers_lst = flights_dict.values()[0]['carrierList']
        return carriers_lst

    def flightRPHList(self, flights_dict, Sequence, returnflag):
        keys = [u'departureTime', u'depatureTime', u'departureTimeZulu', u'flightRPH', u'segmentCode', u'domesticFlight',
                u'arrivalTime', u'arrivalTimeZulu', u'carrierCode',  u'waitListed', u'flightNo', 'ondSequence', 'returnFlag']
        form_keys = []
        for idx in range(len(flights_dict.values()[0]['flightRPHList'])):
            keys_dict = {}
            for key, value in flights_dict.values()[0].iteritems():
                if isinstance(value, list):
                    try:
                        ke = key.replace('List', '')
                        if 'carrier' in key:
                            ke = u'carrierCode'
                        if u'depatureTime' == ke:
                            ke = u'departureTime'
                        keys_dict[ke] = value[idx]
                    except:
                        if 'return' in key:
                            keys_dict[key] = value
            keys_dict1 = {key: val for key,
                          val in keys_dict.iteritems() if key in keys}
            keys_dict1[u'ondSequence'] = Sequence
            keys_dict1[u'returnFlag'] = returnflag
            keys_dict1[u'waitListed'] = 'false'
            if Sequence == 1:
                keys_dict1.pop('waitListed', None)
            keys_dict1[u'domesticFlight'] = 'flase'
            form_keys.append(keys_dict1)
        return form_keys

    def SellKeys(self, fin_flight, trip):
        params = []
        for i, key in enumerate(fin_flight.get('flightRPHList', [])):
            if trip == 'OW':
                params.extend([('outFlightRPHList[%s]' % i, key)])
            elif trip == 'RT':
                params.extend([('retFlightRPHList[%s]' % i, key)])
        return params

    def SeletectFlightsKeys(self, hq_flight, avail_flt):
        avail_flts_list = avail_flt.keys()
        fin_key, flag = '', False
        flight_key_list = [x.replace(' ', '').strip() for x in hq_flight]
        for f_key in avail_flts_list:
            temp_rank = 0
            f_key_ = f_key.split('<>')
            for j in flight_key_list:
                j = j.replace(' ', '').strip()
                if j in f_key_:
                    temp_rank += 1
                if len(hq_flight) == temp_rank:
                    fin_key = f_key
                    flag = True
                    break
                else:
                    fin_key = ''
            if flag: break
        fin_dict = avail_flt.get(fin_key, {})
        return (fin_key, fin_dict)

    def HqFlights(self):
        trip_type = self.booking_dict.get('trip_type', '')
        ow_flight_ids, rt_flight_ids = [], []
        if trip_type == 'OW':
            all_segments = self.booking_dict.get('all_segments', [])[0].values()[
                0].get('segments', [])
            ow_flight_ids = [x.get('flight_no', '') for x in all_segments]
        elif trip_type == 'RT':
            all_segments = self.booking_dict.get('all_segments', [])[0].values()[
                0].get('segments', [])
            ow_flight_ids = [x.get('flight_no', '') for x in all_segments]
            rt_segments = self.booking_dict.get('all_segments', [])[1].values()[
                0].get('segments', [])
            rt_flight_ids = [x.get('flight_no', '') for x in rt_segments]
        return (trip_type, ow_flight_ids, rt_flight_ids)

    def DateFormat(self, date_text):
        if date_text:
            date = datetime.datetime.strptime(
                date_text, '%d-%b-%y').strftime('%d/%m/%Y')
            return date
        else:
            return ''

    def LogicalCCSelection(self, body):
        try:
            available = body.get('availableFare', {}).get('fareQuoteTO', [])
        except:
            available = []
        sec_dict = {}
        for idx, i in enumerate(available):
            code = i.get('ondCode', '')
            sec_dict[str(idx)] = {code: "Y"}
            sec_dict[code] = {"undefined": "Y"}
        return sec_dict

    def FareRuleKey(self, body):
        try:
            availableFare = body.get('availableFare', {}).get(
                'fareRulesInfo', {}).get('fareRules', [])
        except:
            availableFare = []
        classSelection = {}
        for idx, k in enumerate(availableFare):
            inn_dict = {}
            class_code = k.get('bookingClassCode', '')
            cbc_code = k.get('cabinClassCode', '')
            ond_code = k.get('orignNDest', '')
            inn_dict[ond_code] = class_code
            classSelection[str(idx)] = inn_dict
        return classSelection

    def FomatAvailFlights(self, flt_list):
        avail_dict = {}
        for i in flt_list:
            key = i.get('flightNoList', [])
            avail_dict['<>'.join(key)] = i
        return avail_dict

    def paxBagResponse(self, form_data, cookies, search_form_dict, search_keys):
        self.headers['Referer'] = 'https://reservations.airarabia.com/agents/private/makeReservation.action?mc=false'
        form_data.extend([('selectedFlightList', json.dumps(
            search_form_dict.get('flightRphList', []))), ])
        data = requests.post('https://reservations.airarabia.com/agents/private/anciBaggage.action',
                             headers=self.headers, cookies=cookies, data=form_data).text
        if data:
            try:
                data = json.loads(data)
                bag_dict = {str(i.get(
                    'weight', '')): i for i in data['baggageResponseDTO']['flightSegmentBaggages'][0]['baggages']}
                bag_seg_dict = data['baggageResponseDTO']['flightSegmentBaggages'][0]['flightSegmentTO']
                return (bag_dict, bag_seg_dict)
            except:
                pass
        return ({}, {})

    def getInfantDetails(self):
        infant_list = [val for key, val in self.booking_dict.get(
            'pax_details', {}).iteritems() if 'infant' in key]
        return (len(infant_list), infant_list)

    def checkEMailDomain(self, cookies):
        pax_list = self.booking_dict.get(
            'pax_details', {}).get('adult1', ['']*6)
        phone_code = self.booking_dict.get('country_phonecode', '')
        if not phone_code:
            phone_code = ''
        email_id = self.booking_dict.get('emailid', '')
        email_domain = email_id.split('@')[-1]
        title, name, last_name, b_day, b_month, b_year = pax_list
        country_code = self.booking_dict.get('country_code', '')
        if not country_code:
            country_code = ''
        contact_mobile = self.booking_dict.get('contact_mobile', '')
        if contact_mobile and len(contact_mobile) == 10:
            mobileArea = contact_mobile[:4]
            mobileNo = contact_mobile[4:]
        elif contact_mobile and len(contact_mobile) == 12:
            mobileArea = contact_mobile[2:6]
            mobileNo = contact_mobile[6:]
        else:
            mobileArea, mobileNo = ['']*2
        data = [
            ('displayAdultTitle', title.upper()),
            ('displayAdultFirstName', name),
            ('displayAdultLastName', last_name),
            ('displayAdultNationality', ''),  # 585
            ('displayAdultDOB', ''),
            ('displayFFID', ''),
            ('loadProfileSearch.profileID', ''),
        ]
        pay_cont_data = [
            ('contactInfo.title', title.upper()),
            ('contactInfo.firstName', name),
            ('contactInfo.lastName', last_name),
            ('contactInfo.street', ''),
            ('contactInfo.mobileCountry', phone_code),
            ('contactInfo.mobileArea', mobileArea),
            ('contactInfo.mobileNo', mobileNo),
            ('contactInfo.address', ''),
            ('contactInfo.phoneCountry', ''),
            ('contactInfo.phoneArea', ''),
            ('contactInfo.phoneNo', ''),
            ('contactInfo.city', ''),
            ('contactInfo.faxCountry', phone_code),
            ('contactInfo.faxArea', ''),
            ('contactInfo.faxNo', ''),
            ('contactInfo.nationality', ''),
            ('contactInfo.email', email_id),
            ('contactInfo.zipCode', ''),
            ('contactInfo.preferredLang', 'en'),
            ('contactInfo.userNoteType', 'PUB'),
            ('contactInfo.userNotes', ''),
            ('contactInfo.country', country_code),
            ('contactInfo.state', ''),  # 37
            ('contactInfo.taxRegNo', ''),
            ('contactInfo.emgnTitle', ''),
            ('contactInfo.emgnFirstName', ''),
            ('contactInfo.emgnLastName', ''),
            ('contactInfo.emgnPhoneCountry', ''),
            ('contactInfo.emgnPhoneArea', ''),
            ('contactInfo.emgnPhoneNo', ''),
            ('contactInfo.emgnEmail', ''),
            ('selBookingCategory', 'STD'),
            ('selSSRCode', ''),
            ('resAvailableBundleFareLCClassStr', ''),
            ('resFlexiAvailableStr', '{"0":true}'),
            ('domain', email_domain),
        ]
        data.extend(pay_cont_data)
        infant = []
        infant_ln, infant_lst = self.getInfantDetails()
        for idx, vals_lst in enumerate(infant_lst):
            title, name, last_name, b_day, b_month, b_year = vals_lst
            if b_day:
                b_date = '%s/%s/%s' % (b_day, b_month, b_year)
            else:
                b_date = ''
            infant.extend([
                ('displayInfantFirstName', name),
                ('displayInfantLastName', last_name),
                ('displayInfantNationality', ''),
                ('displayInfantDOB', str(b_date)),
                ('displayInfantTravellingWith', str(idx+1)),
            ])
            if idx != 0:
                pax_list = self.booking_dict.get('pax_details', {}).get(
                    'adult%s' % str(idx+1), ['']*6)
                title, name, last_name, b_day, b_month, b_year = vals_lst
                if b_day:
                    b_date = '%s/%s/%s' % (b_day, b_month, b_year)
                else:
                    b_date = ''
                if title:
                    infant.extend([
                        ('displayAdultTitle', title.upper()),
                        ('displayAdultFirstName', name),
                        ('displayAdultLastName', last_name),
                        ('displayAdultNationality', ''),
                        ('displayAdultDOB', b_date),
                    ])
        if infant:
            data.extend(infant)
        self.headers['Referer'] = 'http://reservations.airarabia.com/agents/private/makeReservation.action?mc=false'
        res_data = requests.post('http://reservations.airarabia.com/agents/private/checkEMailDomain.action',
                                 data=data, headers=self.headers, cookies=cookies)
        return (res_data.text, pay_cont_data)

    def checkFlightIds(self, val_lst):
        hq_ow_flt_list = [i.replace(' ', '').strip()
                          for i in self.ow_flight_nos.split('<>')]
        site_flt_lst = [i['flightNo'].strip() for i in val_lst[3]]
        if self.booking_dict.get('trip_type', '') == 'RT':
            hq_rt_flt_list = [i.replace(' ', '').strip()
                              for i in self.rt_flight_nos.split('<>')]
            hq_ow_flt_list.extend(hq_rt_flt_list)
        ow_flt_status = self.flightIdMap(hq_ow_flt_list, site_flt_lst)
        return ow_flt_status

    def checkDepartureDateTime(self, val_lst):
        hq_dep_date = self.booking_dict.get('departure_date', '')
        site_dep_date = val_lst[3][0].get('departureDate', '')
        site_dep_time = val_lst[3][0].get('departureTime', '')
        site_arr_date = val_lst[3][0].get('arrivalDate', '')
        site_arr_time = val_lst[3][0].get('arrivalTime', '')
        hq_dep = self.ow_input_flight[0].get('date', '')
        hq_dep_time = self.ow_input_flight[0].get('dep_time', '')
        try:
            site_date = datetime.datetime.strptime('%s %s' % (
                site_dep_date, site_dep_time), '%d/%m/%Y %H:%M')
            hq_date = datetime.datetime.strptime(
                '%s %s' % (hq_dep, hq_dep_time), '%d-%b-%y %H:%M')
            if site_date == hq_date:
                flag = False
            else:
                flag = True
        except:
            print "Error in date check"
            self.insert_error_msg(err="Date check failed")
        return flag

    def flightIdMap(self, hq_flt_list, site_flt_lst):
        rank = 0
        for i in hq_flt_list:
            if i in site_flt_lst:
                rank += 1
        if len(site_flt_lst) == rank:
            return False
        else:
            return True

    def checkPaxEmail(self, val_lst):
        hq_email = self.booking_dict.get('custemailid', '')
        if hq_email.lower().strip() != val_lst[2].lower().strip():
            flag = True
        else:
            flag = False
        return flag

    def checkMobileNo(self, val_lst):
        flag = False
        mobile_no = self.booking_dict.get('contact_mobile', '')
        phone_no = val_lst[4].replace('-', '').replace('_', '').strip()
        if len(phone_no) == 12:
            phone_no = phone_no[2:]
        if mobile_no.strip() != val_lst[1].replace('-', '').replace('_', '').strip():
            flag = True
        else:
            flag = False
        if flag:
            if mobile_no.strip() == phone_no:
                flag = False
        return flag

    def checkHqPaxNames(self, site_pax_names_lst):
        hq_pax_names = [' '.join(i[:3]).lower() for i in self.booking_dict.get(
            'pax_details', {}).values()]
        rank = 0
        for k in site_pax_names_lst:
            if k.lower() in hq_pax_names:
                rank += 1
        if rank == len(hq_pax_names):
            flag = False
        else:
            flag = True
        return flag

    def getAirlinePaxNames(self, pnr, cookies):
        data = [
            ('groupPNR', ''),
            ('pnr', pnr),
            ('loadAudit', 'true'),
            ('marketingAirlineCode', ''),
            ('airlineCode', ''),
            ('interlineAgreementId', ''),
        ]
        url = 'http://reservations.airarabia.com/agents/private/loadReservationShowData.action'
        pax_res = requests.post(url, headers=self.headers,
                                cookies=cookies, data=data).text
        pax_names_lst = []
        paxPayment = {}
        try:
            json_data = json.loads(pax_res)
            paxPayment = json_data.get('paymentSummary', {})
            if json_data.get("paxAdults", []):
                for i in json_data.get("paxAdults", []):
                    pax_names = []
                    pax_names.append(i['displayAdultTitle'])
                    pax_names.append(i['displayAdultFirstName'])
                    pax_names.append(i['displayAdultLastName'])
                    pax_names_lst.append(' '.join(pax_names))
            else:
                print "Pax names not found"
        except:
            print "Pax names not found"
        return (pax_names_lst, paxPayment)
