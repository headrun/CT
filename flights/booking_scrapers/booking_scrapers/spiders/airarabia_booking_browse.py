from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
import ast
import tornado.httpclient as HT
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from booking_scrapers.utils import *
from scrapy.conf import settings
from airarabia_utils import *
from indigo_utils import *
import sys
sys.path.append('../../../')
from root_utils import Helpers
from common_utils import *
import requests
_cfg = SafeConfigParser()
_cfg.read(settings['BOOK_PCC_PATH'])

from scrapy.utils.response import open_in_browser


class AirArabiaBookBrowse(Spider, AirArabiaUtils):
    name = "airarabia_booking_browse"
    start_urls = [
        "https://reservations.airarabia.com/agents/public/showLogin.action"]
    handle_httpstatus_list = [404, 500, 400]

    def __init__(self, *args, **kwargs):
        super(AirArabiaBookBrowse, self).__init__(*args, **kwargs)
        self.log = create_logger_obj('airarabia_booking')
        self.insert_query = 'insert into airarabia_booking_report (sk, airline, pnr, flight_number, from_location, to_location, triptype, cleartrip_price, airline_price, status_message, tolerance_amount, oneway_date, return_date, error_message, paxdetails, price_details, created_at, modified_at) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now()) on duplicate key update modified_at=now(), pnr=%s, flight_number=%s, airline_price=%s, status_message=%s, error_message=%s, paxdetails=%s, price_details=%s, triptype=%s, cleartrip_price=%s, tolerance_amount=%s, from_location=%s, to_location=%s'
        self.booking_dict = ast.literal_eval(kwargs.get('jsons', '{}'))
        self.all_data_counter = 0
        self.ct_price = 0
        self.onewaymealcode, self.returnmealcode = '', ''
        self.onewaybaggagecode, self.returnbaggagecode = '', ''
        self.meals_sector_length, self.baggages_sector_length = 0, 0

        self.currency = self.booking_dict.get('currency_code', '')
        self.auto_phone_check = False
        self.ow_flight_nos, self.rt_flight_nos = '', ''
        self.ow_fullinput_dict, self.rt_fullinput_dict = [], []
        self.ow_input_flight, self.rt_input_flight = [], []

        self.adult_fail, self.child_fail, self.infant_fail = False, False, False
        self.datas_checked = []
        self.fin_flt_ids = []
        self.default_dob = '1988-02-01'
        self.auto_pnr = ''
        self.tt = ''
        self.queue = self.booking_dict['queue']
        self.book_using = ''
        self.multi_pcc = False
        self.connection_check = False
        self.ow_class, self.rt_class = '', ''
        self.ow_fare, self.rt_fare, self.base_fare = '0', '0', '0'
        self.ow_segcodes, self.rt_segcodes = '', ''
        self.agent_name = ''
        self.adlt_price, self.child_price, self.airline_amount, self.tolerance_amount = 0,0,0,0
        self.session_cookie = {}
        self.process_input()
        if self.booking_dict['no_of_infants'] > self.booking_dict['no_of_adults']:
            self.insert_error_msg(err='Infants more than adults')
            return
        self.amount, self.new_p_details, self.tolerance_value = 0, {}, 0
        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('booking', 'IP')
        passwd = db_cfg.get('booking', 'PASSWD')
        user = db_cfg.get('booking', 'USER')
        db_name = db_cfg.get('booking', 'DBNAME')
        self.conn = MySQLdb.connect(
            host=host, user=user, passwd=passwd, db=db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()

        self.headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Origin': 'https://reservations.airarabia.com',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.headers['Referer'] = 'http://reservations.airarabia.com/agents/private/showTop'
        url = 'http://reservations.airarabia.com/agents/public/logout.action'
        logout = requests.post(url, headers=self.headers,
                               cookies=self.session_cookie)
        self.cur.close()
        self.conn.close()

    def parse(self, response):
        sel = Selector(response)
        self.pcc_name = self.get_pcc_name()
        self.agent_name = self.pcc_name.replace('AIRARABIA_', '').strip()
        self.tt = '%s_%s_%s' % (
            self.booking_dict['trip_type'], self.queue, self.pcc_name)
        persons = int(self.booking_dict['no_of_adults']) + \
            int(self.booking_dict['no_of_children'])
        if len(self.onewaymealcode) > persons:
            self.insert_error_msg(err='one person one meal site level issue')
            return
        elif len(self.onewaybaggagecode) > persons:
            self.insert_error_msg(
                err='one person one baggage site level issue')
            return
        elif len(self.returnmealcode) > persons:
            self.insert_error_msg(err='one person one meal site level issue')
            return
        elif len(self.returnbaggagecode) > persons:
            self.insert_error_msg(
                err='one person one baggage site level issue')
            return
        self.pax_details()
        if self.adult_fail or self.child_fail or self.infant_fail:
            self.insert_error_msg(err="Duplicate passengers")
            self.log.debug('Duplicate passengers')
            return
        all_segments = self.booking_dict['all_segments']
        segment_len = len([i.keys() for i in all_segments])
        if self.booking_dict['trip_type'] == 'RT' and segment_len == 1:
            segments_list = []
            segment1 = filter(None, [
                              i if i['seq_no'] == '1' else '' for i in all_segments[0][all_segments[0].keys()[0]]['segments']])
            segment2 = filter(None, [
                              i if i['seq_no'] == '2' else '' for i in all_segments[0][all_segments[0].keys()[0]]['segments']])
            for index, seg in enumerate([segment1, segment2]):
                new_all_segments = {}
                amount = float('0')
                if index == 0:
                    amount = all_segments[0][all_segments[0].keys()[
                        0]]['amount']
                new_all_segments.update(
                    {all_segments[0].keys()[0]: {'amount': amount, 'segments': seg}})
                segments_list.append(new_all_segments)
            self.booking_dict['all_segments'] = segments_list

        self.log.debug('PCC : %s, Trip: %s' %
                       (self.pcc_name, self.booking_dict.get('trip_ref')))
        if self.multi_pcc:
            self.insert_error_msg(err='Multiple PCC found')
            return
        res_headers = json.dumps(str(response.headers))
        res_headers = json.loads(res_headers)
        my_dict = ast.literal_eval(res_headers)
        cookies = {}
        for i in my_dict.get('Set-Cookie', []):
            data = i.split(';')[0]
            if data:
                try:
                    key, val = data.split('=', 1)
                except:
                    continue
                cookies.update({key.strip(): val.strip()})
        self.session_cookie = cookies
        self.headers['Referer'] = 'https://reservations.airarabia.com/agents/public/showLogin.action'
        try:
            username = _cfg.get(self.pcc_name, 'username')
            password = _cfg.get(self.pcc_name, 'password')
            self.book_using = username
        except:
            self.insert_error_msg(err="PCC not found")
            return
        data = [
            ('j_token', '1'),
            ('j_username', 'ABY%s@G9$XBETYPE$|741' %
             username.upper().strip()),  # ABYWSCLEARTRIP_NEW@G9$XBETYPE$|741
            ('username_txt', username),
            ('j_password', password),
            ('captcha_txt', ''),
            ('carrierCode', 'G9'),
            ('prefLangunage', 'en'),
            ('hdnUserStatus', ''),
        ]
        yield FormRequest('https://reservations.airarabia.com/agents/public/j_security_check',
                          callback=self.login_autopnr, headers=self.headers,
                          cookies=cookies, formdata=data, dont_filter=True,
                          meta={'username': username, 'password': password}
        )

    def login_autopnr(self, response):
        if 'User/Agent ID is INACTIVE' in response.body:
            print "Login failed"
            self.insert_error_msg(err="Login failed")
            return
        if response.status == 400:
            self.headers['Referer'] = 'https://reservations.airarabia.com/agents/public/j_security_check'
            yield Request('https://reservations.airarabia.com/agents/private/showXBEMain.action',
                          headers=self.headers, callback=self.parse_retry,
                          meta=response.meta, dont_filter=True
            )

    def parse_retry(self, response):
        self.headers['Referer'] = 'https://reservations.airarabia.com/agents/private/showXBEMain.action'
        data = [
            ('j_token', '1'),
            ('j_username', 'ABY%s@G9$XBETYPE$|741' %
             response.meta['username'].upper().strip()),
            ('username_txt', response.meta['username']),
            ('j_password', response.meta['password']),
            ('captcha_txt', ''),
            ('carrierCode', 'G9'),
            ('prefLangunage', 'en'),
            ('hdnUserStatus', 'false  '),
        ]
        yield FormRequest('https://reservations.airarabia.com/agents/public/j_security_check',
                          headers=self.headers, callback=self.parseRetryLogin,
                          formdata=data, dont_filter=True
        )

    def parseRetryLogin(self, response):
        if 'User/Agent ID is INACTIVE' in response.body:
            print "Login failed"
            self.insert_error_msg(err="Login failed")
            return
        return Request('http://reservations.airarabia.com/agents/private/showNewFile!searchRes.action',
                       callback=self.parseAutoPNR
        )
        # return Request('https://reservations.airarabia.com/agents/private/makeReservation.action?mc=false', callback=self.parseMakebook)

    def parseAutoPNR(self, response):
        pax_name = self.booking_dict.get(
            'pax_details', {}).get('adult1', ['']*6)
        firstname, lastname = pax_name[1], pax_name[2]
        data = [
            ('searchParams.exactMatch', 'on'),
            ('rSearch', 'pnr'),
            ('searchParams.pnr', ''),
            ('searchParams.firstName', firstname),
            ('searchParams.lastName', lastname),
            ('searchParams.searchSystem', 'AA'),
            ('searchParams.fromAirport', ''),
            ('searchParams.depatureDate', ''),
            ('searchParams.phoneCntry', ''),
            ('searchParams.phoneArea', ''),
            ('searchParams.phoneNo', ''),
            ('searchParams.toAirport', ''),
            ('searchParams.returnDate', ''),
            ('searchParams.flightNo', ''),
            ('searchParams.creditCardNo', ''),
            ('searchParams.cardExpiry', ''),
            ('searchParams.authCode', ''),
            ('searchParams.bookingType', ''),
            ('searchParams.passport', ''),
            ('pageNo', '1'),
        ]
        return FormRequest('http://reservations.airarabia.com/agents/private/reservationList.action',
                           formdata=data, callback=self.parseCheckAutoPnr
        )

    def parseCheckAutoPnr(self, response):
        auto_pnr_flag = False
        try:
            data = json.loads(response.body)
            cookies = {}
            res_headers = response.request.headers['Cookie'].split(';')
            for i in res_headers:
                try:
                    key, val = i.split('=', 1)
                except:
                    continue
                cookies.update({key.strip(): val.strip()})

        except:
            data, cookies = {}, {}
        reservations = data.get('reservations', [])
        rslt_dict = {}
        if reservations:
            for res_dict in reservations:
                pnr_no = res_dict.get('pnrNo', '')
                pax_name = res_dict.get('paxName', '')
                pax_mobile = res_dict.get('paxMobile', '')
                pax_phone_no = res_dict.get('paxPhone', '')
                pax_email = res_dict.get('paxEmail', '')
                site_flightIds = res_dict.get('flightInfo', [])
                auto_flt_ids = [i.get('flightNo', '') for i in site_flightIds]
                segments = '-'.join([i.get('orignNDest', '').replace('/', '-')
                                     for i in site_flightIds])
                rslt_dict[pnr_no] = [pax_name, pax_mobile, pax_email,
                                     site_flightIds, pax_phone_no, segments, auto_flt_ids]
        else:
            print "No search results, go ahead for booking %s" % self.booking_dict.get(
                'trip_ref', '')
            return Request('https://reservations.airarabia.com/agents/private/makeReservation.action?mc=false',
                           callback=self.parseMakebook
            )
        fin_pnr_dict = {}
        for key, val_lst in rslt_dict.iteritems():
            dep_date_time_status = self.checkDepartureDateTime(val_lst)
            email_status = self.checkPaxEmail(val_lst)
            mobile_no_status = self.checkMobileNo(val_lst)
            flight_id_status = self.checkFlightIds(val_lst)
            if dep_date_time_status:
                print "Date time missmatched %s, %s" % (self.booking_dict.get(
                    'trip_ref', ''), key)
                continue
            if email_status:
                print "Email missmatched %s" % self.booking_dict.get(
                    'trip_ref', '')
                continue
            if flight_id_status:
                print "Flight Ids missmatched %s" % self.booking_dict.get(
                    'trip_ref', '')
                continue
            if mobile_no_status:
                print "Mobile Number missmatched %s" % self.booking_dict.get(
                    'trip_ref', '')
                continue
            else:
                fin_pnr_dict[key] = val_lst
        if fin_pnr_dict:
            for key, val_lst in fin_pnr_dict.iteritems():
                pax_names_lst, paxPayment = self.getAirlinePaxNames(
                    key, cookies)
                if pax_names_lst:
                    pax_status = self.checkHqPaxNames(pax_names_lst)
                    if not pax_status:
                        msg = "Auto PNR Exists: %s" % key
                        auto_pnr_flag = True
                        paxPayment['AUTO_PNR_EXISTS'] = True
                        paxPayment['seg'] = val_lst[5]
                        paxPayment['total'] = str(paxPayment.get('paid', 0))
                        price_dict = {key: paxPayment for key in val_lst[6]}
                        self.insert_error_msg(
                            pnr=key, mesg=msg, p_details=str(price_dict))
                        print msg, self.booking_dict.get('trip_ref', '')
                        return
                    else:
                        continue
            else:
                return Request('https://reservations.airarabia.com/agents/private/makeReservation.action?mc=false',
                               callback=self.parseMakebook
                )
        else:
            return Request('https://reservations.airarabia.com/agents/private/makeReservation.action?mc=false',
                           callback=self.parseMakebook
            )

    def parseMakebook(self, response):
        origin_code = self.booking_dict.get('origin_code', '')
        dest_code = self.booking_dict.get('destination_code', '')
        ow_date = self.DateFormat(self.booking_dict.get('departure_date', ''))
        if self.booking_dict.get('trip_type', '') == 'RT':
            rt_date = self.DateFormat(self.booking_dict.get('return_date', ''))
        else:
            rt_date = ''
        no_of_children = self.booking_dict.get('no_of_children', '0')
        no_of_infants = self.booking_dict.get('no_of_infants', '0')
        no_of_adults = self.booking_dict.get('no_of_adults', '0')
        search_keys = {
            'origin_code': origin_code,
            'dest_code': dest_code,
            'ow_date': ow_date,
            'no_of_children': no_of_children,
            'no_of_infants': no_of_infants,
            'no_of_adults': no_of_adults,
            'rt_date': rt_date,
        }
        data = [
            ('searchParams.fromAirport', origin_code),
            ('searchParams.departureDate', ow_date),
            ('searchParams.departureVariance', '0'),
            ('searchParams.adultCount', no_of_adults),
            ('classOfService', 'Y'),
            ('searchParams.toAirport', dest_code),
            ('searchParams.returnDate', rt_date),
            ('searchParams.returnVariance', ''),
            ('searchParams.childCount', no_of_children),
            ('searchParams.selectedCurrency', self.currency),
            ('searchParams.searchSystem', 'AA'),
            ('searchParams.infantCount', no_of_infants),
            ('searchParams.bookingType', 'NORMAL'),
            ('searchParams.promoCode', ''),
            ('searchParams.bankIdentificationNo', ''),
            ('searchParams.fareType', 'A'),
            ('searchParams.paxType', 'A'),
            ('searchParams.bookingClassCode', ''),
            ('searchParams.firstDeparture', ''),
            ('searchParams.lastArrival', ''),
            ('searchParams.fromAirportSubStation', ''),
            ('searchParams.toAirportSubStation', ''),
            ('ticketExpiryDate', ''),
            ('ticketValidFrom', ''),
            ('ticketExpiryEnabled', ''),
            ('oldPerPaxFare', ''),
            ('oldPerPaxFareId', ''),
            ('hdnBookingClassCode', ''),
            ('hdnCabinClassCode', ''),
            ('modifyBooking', 'false'),
            ('searchParams.ondQuoteFlexiStr', '{"0":true,"1":true}'),
            ('searchParams.classOfService', 'Y'),
            ('searchParams.logicalCabinClass', ''),
            ('fareDiscountPercentage', ''),
            ('fareDiscountNotes', ''),
            ('fareDiscountCode', ''),
            ('searchParams.ticketValidityMax', ''),
            ('searchParams.ticketValidityMin', ''),
            ('searchParams.ticketValidityExist', ''),
            ('searchParams.hubTimeDetailJSON', '[]'),
            ('searchParams.ondWiseCitySearchStr',
                '{"0":{"DEP":false,"ARR":false},"1":{"DEP":false,"ARR":false}}'),
        ]

        yield FormRequest('https://reservations.airarabia.com/agents/private/availabilitySearch.action',
                          formdata=data, callback=self.parseSearch,
                          meta={'search_keys': search_keys}
        )

    def parseSearch(self, response):
        body = json.loads(response.body)
        search_keys = response.meta.get('search_keys', {})
        trip_type, hq_ow_flight, hq_rt_flight = self.HqFlights()
        ow_flt_avail_lst = body.get('outboundFlights', [])
        if not ow_flt_avail_lst:
            self.insert_error_msg(err="Flights not found")
            return
        rt_flt_avail_lst = body.get('returnFlights', [])
        if trip_type == 'RT' and not rt_flt_avail_lst:
            self.insert_error_msg(err="Flights not found")
            return
        ow_avail_flt = self.FomatAvailFlights(ow_flt_avail_lst)
        rt_avail_flt = self.FomatAvailFlights(rt_flt_avail_lst)
        classSelection = self.FareRuleKey(body)
        logicalCCSelection = self.LogicalCCSelection(body)
        ow_fin_key, ow_fin_flight = self.SeletectFlightsKeys(
            hq_ow_flight, ow_avail_flt)
        flightRphList = self.flightRPHList(ow_avail_flt, 0, 'false')
        self.ow_segcodes = '-'.join([i.get('segmentCode',
                                           '').replace('/', '-') for i in flightRphList])
        carrier_list = self.carrierCode(ow_avail_flt)
        search_form_dict = {}
        if not ow_fin_flight:
            print "Flights not found"
            self.insert_error_msg(err="Flights not found")
            return
        if trip_type == 'RT':
            rt_fin_key, rt_fin_flight = self.SeletectFlightsKeys(
                hq_rt_flight, rt_avail_flt)
            if not rt_fin_flight:
                print "Flights not found"
                self.insert_error_msg(err="Flights not found")
                return
            rt_flightRphList = self.flightRPHList(rt_avail_flt, 1, 'true')
            self.rt_segcodes = '-'.join([i.get('segmentCode',
                                               '').replace('/', '-') for i in rt_flightRphList])
            flightRphList.extend(rt_flightRphList)
        else:
            rt_fin_flight, rt_fin_key = {}, ''
        self.fin_flt_ids = [ow_fin_key, rt_fin_key]
        ow_sell_keys = self.SellKeys(ow_fin_flight, 'OW')
        rt_sell_keys = self.SellKeys(rt_fin_flight, 'RT')
        search_form_dict['flightRphList'] = flightRphList
        search_form_dict['classSelection'] = classSelection
        search_form_dict['logicalCCSelection'] = logicalCCSelection
        search_form_dict['carrierCode'] = carrier_list
        if not flightRphList:
            self.insert_error_msg(err="Flights not found")
            return
        data = [
            ('fareQuoteParams.fromAirport', str(
                search_keys.get('origin_code', ''))),
            ('fareQuoteParams.toAirport', str(search_keys.get('dest_code', ''))),
            ('fareQuoteParams.departureDate', str(search_keys.get('ow_date', ''))),
            ('fareQuoteParams.returnDate', str(search_keys.get('rt_date', ''))),
            ('fareQuoteParams.validity', ''),
            ('fareQuoteParams.adultCount',
             self.booking_dict.get('no_of_adults', '0')),
            ('fareQuoteParams.childCount',
             self.booking_dict.get('no_of_children', '0')),
            ('fareQuoteParams.infantCount',
                self.booking_dict.get('no_of_infants', '0')),
            ('fareQuoteParams.classOfService', 'Y'),
            ('fareQuoteParams.logicalCabinClass', ''),
            ('fareQuoteParams.selectedCurrency', str(self.currency)),
            ('fareQuoteParams.bookingType', 'NORMAL'),
            ('fareQuoteParams.paxType', 'A'),
            ('fareQuoteParams.fareType', 'A'),
            ('fareQuoteParams.openReturn', 'false'),
            ('fareQuoteParams.searchSystem', 'AA'),
            ('fareQuoteParams.fromAirportSubStation', ''),
            ('fareQuoteParams.toAirportSubStation', ''),
            ('fareQuoteParams.openReturnConfirm', 'false'),
            ('fareQuoteParams.travelAgentCode', ''),
            ('fareQuoteParams.bookingClassCode', ''),
            ('fareQuoteParams.fareQuoteOndSegLogicalCCSelection', 'null'),
            ('fareQuoteParams.fareQuoteSegWiseLogicalCCSelection', 'null'),
            ('fareQuoteParams.fareQuoteOndSegBookingClassSelection', '%s' %
             classSelection),
            ('fareQuoteParams.ondQuoteFlexiStr', '{"0":true,"1":true}'),
            ('fareQuoteParams.promoCode', ''),
            ('fareQuoteParams.bankIdentificationNo', ''),
            ('fareQuoteParams.ondSegBookingClassStr', '{}'),
            ('fareQuoteParams.allowOverrideSameOrHigherFare', 'false'),
            ('fareQuoteParams.ondWiseCitySearchStr',
                '{"0":{"DEP":false,"ARR":false},"1":{"DEP":false,"ARR":false}}'),
        ]
        rt_data = [
            ('searchParams.fareQuoteLogicalCCSelection', '{"0":"Y","1":"Y"}'),
            ('searchParams.ondAvailbleFlexiStr', '{"0":true,"1":true}'),
            ('searchParams.ondSelectedFlexiStr', '{"0":false,"1":false}'),
            ('searchParams.preferredBundledFares', '{"0":null,"1":null}'),
            ('searchParams.ondSegBookingClassStr', '{"0":null,"1":null}'),
        ]
        ow_data = [
            ('searchParams.fareQuoteLogicalCCSelection', '{"0":"Y"}'),
            ('searchParams.ondAvailbleFlexiStr', '{"0":true}'),
            ('searchParams.ondSelectedFlexiStr', '{"0":false,"1":false}'),
            ('searchParams.preferredBundledFares', '{"0":null}'),
            ('searchParams.ondSegBookingClassStr', '{"0":null}'),
        ]
        if trip_type == 'OW':
            data.extend(ow_data)
            data.extend(ow_sell_keys)
        else:
            data.extend(rt_data)
            data.extend(ow_sell_keys)
            data.extend(rt_sell_keys)
        self.booking_dict.update({'ow_sell_keys':ow_sell_keys, 'rt_sell_keys':rt_sell_keys})
        return FormRequest('https://reservations.airarabia.com/agents/private/loadFareQuote.action',
                           callback=self.parseSelectedFlights, formdata=data,
                           meta={'search_form_dict': search_form_dict,
                                 'search_keys': search_keys, 'form_data': data}
        )

    def parseSelectedFlights(self, response):
        carrierCode = ','.join(response.meta.get(
            'search_form_dict', {}).get('carrierCode', []))
        print "stop"
        data = [
            ('system', 'AA'),
            ('carriers', carrierCode),
            ('paxType', 'A'),
        ]
        return FormRequest('https://reservations.airarabia.com/agents/private/loadPaxContactConfig.action',
                           callback=self.parsePaxNames,
                           formdata=data, meta=response.meta
        )

    def parsePaxNames(self, response):
        search_form_dict = response.meta.get('search_form_dict', {})
        search_keys = response.meta.get('search_keys', {})
        form_data = response.meta.get('form_data', [])
        data = [
            ('searchParams.fromAirport', str(search_keys.get('origin_code', ''))),
            ('searchParams.toAirport', str(search_keys.get('dest_code', ''))),
            ('searchParams.departureDate', str(search_keys.get('ow_date', ''))),
            ('searchParams.returnDate', str(search_keys.get('rt_date', ''))),
            ('searchParams.validity', ''),
            ('searchParams.adultCount', self.booking_dict.get('no_of_adults', '0')),
            ('searchParams.childCount', self.booking_dict.get('no_of_children', '0')),
            ('searchParams.infantCount', self.booking_dict.get('no_of_infants', '0')),
            ('searchParams.classOfService', 'Y'),
            ('searchParams.logicalCabinClass', ''),
            ('searchParams.selectedCurrency', str(self.currency)),
            ('searchParams.bookingType', 'NORMAL'),
            ('searchParams.paxType', 'A'),
            ('searchParams.fareType', 'A'),
            ('searchParams.openReturn', 'false'),
            ('searchParams.searchSystem', 'AA'),
            ('searchParams.fromAirportSubStation', ''),
            ('searchParams.toAirportSubStation', ''),
            ('searchParams.openReturnConfirm', 'false'),
            ('searchParams.travelAgentCode', ''),
            ('searchParams.bookingClassCode', ''),
            ('searchParams.fareQuoteOndSegLogicalCCSelection', json.dumps(
                search_form_dict.get('logicalCCSelection', {}))),
            ('searchParams.fareQuoteSegWiseLogicalCCSelection', 'null'),
            ('searchParams.fareQuoteOndSegBookingClassSelection',
                json.dumps(search_form_dict.get('classSelection', {}))),
            ('searchParams.ondQuoteFlexiStr', '{"0":true,"1":true}'),
            ('searchParams.promoCode', ''),
            ('searchParams.bankIdentificationNo', ''),
            ('searchParams.preferredBookingCodes', '{}'),
            ('searchParams.allowOverrideSameOrHigherFare', 'false'),
            ('searchParams.ondWiseCitySearchStr',
                '{"0":{"DEP":false,"ARR":false},"1":{"DEP":false,"ARR":false}}'),
            ('flightRPHList', json.dumps(search_form_dict.get('flightRphList', []))), ]
        rt_data = [
            ('searchParams.fareQuoteLogicalCCSelection', '{"0":"Y","1":"Y"}'),
            ('searchParams.ondAvailbleFlexiStr', '{"0":true,"1":true}'),
            ('searchParams.ondSelectedFlexiStr', '{"0":false,"1":false}'),
            ('searchParams.preferredBundledFares', '{"0":null,"1":null}'),
            ('searchParams.ondSegBookingClassStr', '{"0":null,"1":null}'),
        ]
        ow_data = [
            ('searchParams.fareQuoteLogicalCCSelection', '{"0":"Y"}'),
            ('searchParams.ondAvailbleFlexiStr', '{"0":true}'),
            ('searchParams.ondSelectedFlexiStr', '{"0":false,"1":false}'),
            ('searchParams.preferredBundledFares', '{"0":null}'),
            ('searchParams.ondSegBookingClassStr', '{"0":null}'),
        ]
        data_ = [
            ('onHoldBooking', 'false'),
            ('waitListingBooking', 'false'),
            ('foidIds', ''),
            ('foidCode', ''),
            ('segmentList', ''),
            ('selectedSystem', 'AA'),
            ('mulipleMealsSelectionEnabled', 'true'),
            ('isOpenReturnReservation', 'false'),
        ]
        meta = response.meta
        if self.booking_dict.get('trip_type', '') == 'OW':
            data.extend(ow_data)
        else:
            data.extend(rt_data)
        meta['form_data'] = data
        data.extend(data_)
        return FormRequest('https://reservations.airarabia.com/agents/private/ancillaryAvailability.action',
                           callback=self.parsePaxPage, formdata=data, meta=meta
        )

    def parsePaxPage(self, response):
        search_form_dict = response.meta.get('search_form_dict', {})
        search_keys = response.meta.get('search_keys', {})
        form_data = response.meta.get('form_data', [])
        res_headers = response.request.headers['Cookie'].split(';')
        cookies = {}
        for i in res_headers:
            try:
                key, val = i.split('=', 1)
            except:
                continue
            cookies.update({key.strip(): val.strip()})
        email_status, pay_cont_data = self.checkEMailDomain(cookies)
        print email_status
        bag_dict, bag_seg_dict = self.paxBagResponse(
            form_data, cookies, search_form_dict, search_keys)
        if not bag_dict:
            self.insert_error_msg(err="Baggage response not loaded")
            return
        #paxWiseAnci = self.paxFormFilling(bag_dict, bag_seg_dict)
        bag_key = self.getBaggageWait(0)
        if bag_key == 0.0:
            bag_key = self.getBaggageWait(1)
        baggageName = bag_dict.get(str(bag_key), {}).get('baggageName', '')
        if not baggageName:
            self.insert_error_msg(err="Baggage not found")
            return
        paxWiseAnci = self.paxFormFilling(bag_dict, bag_seg_dict, str(bag_key))
        data_ = [
            ('paxWiseAnci', json.dumps(paxWiseAnci)),
            ('insurances', '[{"total":0,"selected":false,"insuranceRefNumber":null,"operatingAirline":null,"insuredJourney":null,"quotedTotalPremiumAmount":0}]'),
            ('insurableFltRefNumbers', 'null'),
            ('blockSeats', 'false'),
            ('selectedSeats', '[]'),
            ('selectedFareType', ''),
            ('ondwiseFlexiSelected', '{"0":false,"1":false}'),
            ('paxCountryCode', self.booking_dict.get('country_code', '')),
            ('paxState', ''),  # 37
            ('paxTaxRegistered', 'false'),
            ('isOnd', 'N'),
        ]
        form_data.extend(data_)
        meta = response.meta
        meta['pay_cont_data'] = pay_cont_data
        return FormRequest('https://reservations.airarabia.com/agents/private/anciBlocking.action',
                           formdata=form_data, callback=self.parseBaggage,
                           meta=meta
        )

    def parseBaggage(self, response):
        search_form_dict = response.meta.get('search_form_dict', {})
        search_keys = response.meta.get('search_keys', {})
        form_data = response.meta.get('form_data', [])
        form_data.extend([('selCurrency', str(self.currency)), ('selectedFareType', ''),])
        try:
            body = json.loads(response.body)
            if body.get('messageTxt', ''):
                print body.get('messageTxt', '') ,self.booking_dict.get('trip_ref', '')
                self.insert_error_msg(err="Failed to submit pax details")
                return
        except:
            self.insert_error_msg(err="Failed to submit pax details")
        return FormRequest('https://reservations.airarabia.com/agents/private/paymentTab.action', callback=self.parsePaymentInfo, formdata=form_data, meta=response.meta)

    def parsePaymentInfo(self, response):
        try:
            data = json.loads(response.body)
        except:
            data = {}
        pricing_details = {}
        search_form_dict = response.meta['search_form_dict']
        payment_dict = data.get('paymentSummaryTO', {})
        adlt_price_lst, child_price_lst = [], []
        pax_pricing_lst = data.get('passengerPayment', [])
        for d in pax_pricing_lst:
            pax_type = d.get('paxType', '')
            try:
                pax_price = float(d.get('displayTotal', '0'))
            except:
                pax_price = '0'
            if pax_type == 'AD':
                adlt_price_lst.append(pax_price)
            elif pax_type == 'CH':
                child_price_lst.append(pax_price)
        if adlt_price_lst:
            adlt_price = sorted(adlt_price_lst)[0]
            self.adlt_price = adlt_price
            payment_dict['Adult'] = str(adlt_price)
        if child_price_lst:
            child_price = sorted(child_price_lst)[0]
            self.child_price = child_price
            payment_dict['Child'] = str(child_price)
        payment_dict['total'] = payment_dict.get('ticketPrice', '')
        payment_dict['seg'] = self.ow_segcodes
        payment_dict['pcc'] = self.book_using
        pricing_details[self.fin_flt_ids[0]] = payment_dict
        if len(self.fin_flt_ids) == 2:
            if self.fin_flt_ids[1]:
                payment_dict['seg'] = self.rt_segcodes
                pricing_details[self.fin_flt_ids[1]] = payment_dict
        airline_amount = payment_dict.get('ticketPrice', '')
        self.airline_amount = airline_amount
        pax_wise_price = data.get("passengerPayment", [])
        try:
            tolerance_value, is_proceed = self.checkTolerance(airline_amount)
            self.tolerance_amount = tolerance_value
        except:
            tolerance_value, is_proceed = 0, 0
            self.tolerance_amount = 0
            self.insert_error_msg(mesg="Airline price not found")
            return
        if int(self.booking_dict.get('proceed_to_book', '0')) == 1:
            if is_proceed == 1:
                print "Proceed to commit payment"
                payment_form_data = {}
                pax_payment = data.get('passengerPayment', [])
                pax_payment_list = []
                for i in pax_payment:
                    i['hasPayment']='true'
                    pax_payment_list.append(i)
                from_data = response.meta['form_data']
                pay_cont_data = response.meta['pay_cont_data']
                selectedFlightList = json.dumps(search_form_dict.get('flightRphList', []))
                ow_sell_keys = self.booking_dict.get('ow_sell_keys', [])
                rt_sell_keys = self.booking_dict.get('rt_sell_keys', [])
                data = {
                  'payment.amount': str(payment_dict.get('ticketPrice', '')),
                  'payment.type': 'ACCO',
                  'payment.agentOneAmount': '',
                  'payment.actualPaymentMethod': '',
                  'payment.paymentReference': '',
                  'payment.agentTwo': '',
                  'payment.agentTwoAmount': '',
                  'payment.amountWithCharge': '0',
                  'payment.mode': '',
                  'groupBookingReference': '',
                  'totalAmount': '0',
                  'chkEmail': 'on',
                  'selLang': 'en',
                  'reasonForAllowBlPax': '',
                  'customerProfileUpdate': 'false',
                  'hdnOrigin': self.booking_dict.get('origin_code', ''),
                  'hdnDestination': self.booking_dict.get('destination_code', ''),
                  'hdnSelCurrency': 'INR',
                  'paxInfants': '',
                  'selectedFareType': '',
                  'selectedFlightList': selectedFlightList,
                  'flexiSelected': '{"0":false,"1":false}',
                  'selectedBookingCategory': 'STD',
                  'paxState': '',
                  'paxCountryCode': '',
                  'paxTaxRegistered': 'false',
                  'itineraryFareMaskOption': 'N',
                  'fareQuoteParams.searchSystem': 'AA',
                  'selectedOriginCountry': '',
                  'payment.agent': str(self.agent_name.upper()),#'ABYBOM692',
                  'forceConfirm': 'false',
                  'actualPayment': 'true',
                  'paxPayments': json.dumps(pax_payment_list),
                }
                form_dict = {i[0]:i[1] for i in from_data}
                pay_cont_dict = {i[0]:i[1] for i in pay_cont_data}
                ow_sell_dict = {i[0]:i[1] for i in ow_sell_keys if i}
                rt_sell_dict = {i[0]:i[1] for i in rt_sell_keys if i}
                data.update(form_dict)
                data.update(pay_cont_dict)
                data.update(ow_sell_dict)
                data.update(rt_sell_dict)
                return FormRequest('https://reservations.airarabia.com/agents/private/confirmationTab.action',
                        callback = self.parsePostPayment, formdata=data, meta=response.meta)

            else:
                self.insert_error_msg(pnr="TEST100", mesg="Fare increased by airline", tolerance=str(
                    tolerance_value), a_price=str(airline_amount), p_details=str(pricing_details))
                print "Fare increased by airline"
        else:
            self.insert_error_msg(pnr="TEST100", mesg="Mock Success", tolerance=str(
                tolerance_value), a_price=str(airline_amount), p_details=str(pricing_details))
            print "Mock Success"

    def parsePostPayment(self, response):
        try:
            open('payment_%s'%self.booking_dict.get('trip_ref', ''), 'w+').write('%s'%response.body)
            body = json.loads(response.body)
        except:
            body = {}
        pnr = body.get('bookingTO', {}).get('PNR', '')
        status = body.get('bookingTO', {}).get('status', '')
        if status != "CONFIRMED":
            status = "Payment failed where as payment success"
        pricing_details = {}
        paymentSummary = body.get('itineraryPaymentSummaryTO', {})
        paymentSummary['seg'] = self.ow_segcodes
        paymentSummary['pcc'] = self.book_using
        paymentSummary['Adult'] = str(self.adlt_price)
        paymentSummary['Child'] = str(self.child_price)
        pricing_details[self.fin_flt_ids[0]] = paymentSummary
        if len(self.fin_flt_ids) == 2:
            if self.fin_flt_ids[1]:
                paymentSummary['seg'] = self.rt_segcodes
                pricing_details[self.fin_flt_ids[1]] = paymentSummary
        self.insert_error_msg(pnr=pnr, mesg=status, tolerance=str(self.tolerance_amount), a_price=str(self.airline_amount), p_details=str(pricing_details))
