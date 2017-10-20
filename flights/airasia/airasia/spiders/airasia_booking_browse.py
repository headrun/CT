import re
import json
import md5
import smtplib
import MySQLdb
import datetime
from random import randint
import smtplib, ssl
from email import encoders
from airasia_xpaths import *
from ast import literal_eval
from scrapy import signals
from airasia.items import *
from scrapy.spider import Spider
from collections import OrderedDict
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from scrapy.http import FormRequest, Request
from email.mime.multipart import MIMEMultipart
from scrapy.selector import Selector
from ConfigParser import SafeConfigParser
from scrapy.xlib.pydispatch import dispatcher
#from scrapy_splash import SplashRequest, SplashFormRequest
_cfg = SafeConfigParser()
_cfg.read('airline_names.cfg')

class AirAsiaBookingBrowse(Spider):
    name = "airasiabooking_browse"
    start_urls = ["https://booking2.airasia.com/AgentHome.aspx"]
    handle_httpstatus_list = [404, 500, 400]

    def __init__(self, *args, **kwargs):
        super(AirAsiaBookingBrowse, self).__init__(*args, **kwargs)
        self.price_patt = re.compile(r'\d+')
        self.log = create_logger_obj('airasia_booking')
        self.booking_dict = kwargs.get('jsons', {})
        self.ow_input_flight = self.rt_input_flight = {}
        self.ow_fullinput_dict = self.rt_fullinput_dict = {}
        self.insert_query = 'insert into airasia_booking_report(sk, airline, flight_number, auto_pnr, pnr, triptype, cleartrip_price, airasia_price, status_message, tolerance_amount, error_message, paxdetails, price_details, created_at, modified_at) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now()) on duplicate key update modified_at=now(), sk=%s, status_message=%s'
        self.existing_pnr_query = 'insert into airasia_booking_report (sk, airline, auto_pnr, flight_number, from_location, to_location, status_message, oneway_date, error_message, paxdetails, created_at, modified_at) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), error_message=%s, paxdetails=%s, sk=%s'
        self.conn = MySQLdb.connect(host="localhost", user = "root", db = "TICKETBOOKINGDB", charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()
    
    def get_travel_date(self, date):
        try:
            date_ = datetime.datetime.strptime(date.strip(), '%d-%b-%y')
            date_format = date_.strftime('%Y-%m-%d')
        except:
            date_format, day, month, year = ['']*4
        return date_format

    def process_input(self):
        '''
        Reruest processing to required dict format
        '''
        book_dict, paxdls = {}, {}
        if self.booking_dict.get('trip_type', '') == 'OW': triptype = 'OneWay'
        elif self.booking_dict.get('trip_type', '') == 'RT': triptype = 'RoundTrip'
        else: triptype = 'MultiCity'
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
        onewaydate = self.booking_dict.get('departure_date', '')#self.ow_input_flight.get('date', '')
        onewaydate = str(self.get_travel_date(onewaydate))
        returndate = self.booking_dict.get('return_date', '')#self.rt_input_flight.get('date', '')
        returndate = str(self.get_travel_date(returndate))
        origin = self.booking_dict.get('origin_code', '')
        destination = self.booking_dict.get('destination_code', '')
        pax_details = self.booking_dict.get('pax_details', {})
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
        for key, lst in pax_details.iteritems():
            pax_ = {}
            title, firstname, lastname, day, month, year, gender = lst
            if day and month and year: dob = '%s-%s-%s'%(year, month, day)
            else: "1989-02-02"
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
                        "email": email, 
                        })
        return book_dict

    def parse(self, response):
        '''
        Login to AirAsia
        '''
        sel = Selector(response)
        view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
        login_data_list.append(('__VIEWSTATE', view_state))
        login_data_list.append(('__VIEWSTATEGENERATOR', gen))
        user_name = _cfg.get('airasia', 'username')
        user_psswd = _cfg.get('airasia', 'password')
        login_data_list.append(('ControlGroupLoginAgentView$AgentLoginView$TextBoxUserID', str(user_name)))
        login_data_list.append(('ControlGroupLoginAgentView$AgentLoginView$PasswordFieldPassword', str(user_psswd)))
        yield FormRequest('https://booking2.airasia.com/LoginAgent.aspx', \
                formdata=login_data_list, callback=self.parse_next)

    def parse_next(self, response):
        '''
        Parse the request to my bookings or manage my booking
        '''
        sel = Selector(response)
        temp_status = True 
        manage_booking = sel.xpath('//a[@id="MyBookings"]/@href').extract()
        if response.status !=200 and not manage_booking:
            temp_status = False
            self.send_mail('Booking Scraper unable to login AirAsia', '')
        if self.booking_dict and temp_status:
            try:
                book_dict = OrderedDict(eval(self.booking_dict))
                print book_dict
                self.booking_dict = book_dict
                pnr = book_dict.get('pnr', '')
                book_dict = self.process_input()
                print book_dict
            except Exception as e:
                logging.debug(e.message)
                self.send_mail('AirAsia Booking Faild', e.message)
                book_dict, pnr = {}, ''
                print e.message
            headers = {
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                        'cache-control': 'no-cache',
                        'authority': 'booking2.airasia.com',
                        'referer': 'https://booking2.airasia.com/AgentHome.aspx',
                }
            if not pnr:
                search_flights = 'https://booking2.airasia.com/Search.aspx'
                if book_dict.get('triptype', '') == 'OneWay' or book_dict.get('triptype', '') == 'RoundTrip':
                    yield Request(search_flights, callback=self.parse_search_flights, headers=headers,\
                                         dont_filter=True, meta={'book_dict':book_dict})
                elif book_dict.get('triptype', '') == 'MultiCity':
                    self.send_mail('AirAsia Booking Faild', 'AirAsia Booking Faild As its MultiCity trip')
                    logging.debug('AirAsia Booking Faild As its MultiCity trip')
                    vals = (
                        book_dict.get('tripid', ''), 'AirAsia', '', '', book_dict.get('origin', ''),
                        book_dict.get('destination', ''), "Booking Failed", '',
                        "Booking Faild As its MultiCity trip", json.dumps(book_dict),
                        'Booking Faild As its MultiCity trip', json.dumps(book_dict), book_dict.get('tripid', ''),
                           )
                    self.cur.execute(self.existing_pnr_query, vals)
                else:
                    self.send_mail('AirAsia Booking Faild', 'Request not found')
                    logging.debug('Request not found')
                    vals = (
                        book_dict.get('tripid', ''), 'AirAsia', '', '', book_dict.get('origin', ''),
                        book_dict.get('destination', ''), "Booking Failed", '',
                        "Request not found", json.dumps(book_dict),
                        'Request not found', json.dumps(book_dict), book_dict.get('tripid', ''),
                        )
                    self.cur.execute(self.existing_pnr_query, vals)
            elif book_dict:
                url = 'https://booking2.airasia.com/BookingList.aspx'
                yield Request(url, callback=self.parse_search, dont_filter=True, meta={'book_dict':book_dict})
        else:
            try:
               vals = (
                        book_dict.get('tripid', ''), 'AirAsia', '', '', book_dict.get('origin', ''),
                        book_dict.get('destination', ''), "Booking Failed", '',
                        "Booking Scraper unable to login AirAsia", json.dumps(book_dict),
                        'Booking Scraper unable to login AirAsia', json.dumps(book_dict), book_dict.get('tripid', ''),
                        )
               self.cur.execute(self.existing_pnr_query, vals)
            except Exception as e:
                logging.debug(e.message)

    def parse_search(self, response):
        '''
        Fetching the details for Existing PNR
        '''
        sel = Selector(response)
        book_dict = response.meta.get('book_dict', {})
        if response.status != 200:
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
        view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
        search_data_list.update({'__VIEWSTATE': str(view_state)})
        search_data_list.update({'__VIEWSTATEGENERATOR':str(gen)})
        pnr_no = book_dict.get('pnr', '')
        if pnr_no:
            search_data_list.update({'ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword':pnr_no})
            url = "http://booking2.airasia.com/BookingList.aspx"
            yield FormRequest(url, formdata=search_data_list, callback=self.parse_pnr_deatails, meta={'book_dict':book_dict})

    def parse_pnr_deatails(self, response):
        '''
        Checking the auto PNR presented in AirAsia or not.
        '''
        sel = Selector(response)
        book_dict = response.meta.get('book_dict', {})
        if response.status != 200:
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
        view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
        nodes = sel.xpath(table_nodes_path)
        headers = {
                            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                            'cache-control': 'no-cache',
                            'authority': 'booking2.airasia.com',
                        'referer': 'https://booking2.airasia.com/AgentHome.aspx',
                }
        if not nodes:
            search_flights = 'https://booking2.airasia.com/Search.aspx'
            if book_dict.get('triptype', '') == 'OneWay' or book_dict.get('triptype', '') == 'RoundTrip':
                yield Request(search_flights, callback=self.parse_search_flights, \
                        headers=headers, dont_filter=True, meta={'book_dict':book_dict})
            elif book_dict.get('triptype', '') == 'MultiCity': 
                self.send_mail('AirAsia Booking Faild', 'AirAsia Booking Faild As its MultiCity trip')
                logging.debug('AirAsia Booking Faild As its MultiCity trip')
                vals = (
                        book_dict.get('tripid', ''), 'AirAsia', '', '', book_dict.get('origin', ''),
                        book_dict.get('destination', ''), "Booking Failed", '',
                        "Booking Faild As its MultiCity trip", json.dumps(book_dict),
                        'Booking Faild As its MultiCity trip', json.dumps(book_dict), book_dict.get('tripid', ''),
                   )
                self.cur.execute(self.existing_pnr_query, vals)
        else:
            logging.debug('Auto PNR exists in AirAsia')
            for node in nodes:
                data_dict = {}
                ids = ''.join(node.xpath(table_row_id_path).extract())
                href = ''.join(node.xpath(table_row_href_path).extract())
                date_lst = node.xpath(flight_date_path).extract()
                origin = ''.join(node.xpath(flight_origin_path).extract())
                desti = ''.join(node.xpath(flight_dest_path).extract())
                book_id = ''.join(node.xpath(flight_booking_id_path).extract())
                guest_name = ''.join(node.xpath(pax_name_path).extract())
                data_dict.update({'origin':origin, 'destination':desti,
                                'booking_id':book_id, 'guest_name': guest_name})
                if not ids:
                    error_msg = 'It does not have modify option PNR-%s'%book_dict.get('pnr', '')
                    logging.debug(error_msg)
                    vals = (book_dict.get('tripid', ''), 'AirAsia', book_dict.get('pnr', ''), '', origin, desti, "Booking Failed",
                                '', error_msg, '', error_msg, '', '')
                    try:
                        self.cur.execute(self.existing_pnr_query, vals)
                        self.conn.commt()
                    except Exception as e:
                        print e.message
                    continue
                edit_key = 'Edit:' + ''.join(re.findall('Edit:(.*)', href)).strip(")'")
                booking_headers.update({'Cookie': '_gali=%s'%normalize(ids)})
                if ids:
                    booking_data_list.update({'__EVENTARGUMENT':normalize(edit_key)})
                    booking_data_list.update({'__VIEWSTATE':normalize(view_state)})
                    booking_data_list.update({'ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword':normalize(book_id)})
                    url = 'https://booking2.airasia.com/BookingList.aspx'
                    yield FormRequest(url, callback=self.parse_details, headers=booking_headers,\
                        formdata=booking_data_list, meta={'data_dict':data_dict, 'book_dict':book_dict})
                else:
                    err_vals = (
                                book_dict.get('tripid', ''), "AirAsia", book_dict.get('pnr', ''),
                                '', book_dict.get('origin', ''), book_dict.get('destination', ''),
                                'Booking Faild', '', 'Itinerary exixts', json.dumps(book_dict.get('guestdetails', [])),
                                'Itinerary exixts', json.dumps(book_dict.get('guestdetails', [])), book_dict.get('tripid', '')
                                )
                    try:
                        self.cur.execute(self.existing_pnr_query, err_vals)
                        self.conn.commit()
                    except Exception as e:
                        print e.message

    def parse_details(self, response):
        sel = Selector(response)
        url = 'http://booking2.airasia.com/ChangeItinerary.aspx'
        yield FormRequest.from_response(response, callback=self.parse_existing_pax, \
                meta={'url':url, 'data_dict':response.meta['data_dict'],
                        'book_dict':response.meta['book_dict']})

    def parse_existing_pax(self, response):
        '''
        PNR data parsing
        '''
        sel = Selector(response)
        book_dict = response.meta.get('book_dict', {})
        if response.status != 200:
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
        data_dict = response.meta['data_dict']
        booking_id = normalize(''.join(sel.xpath(pax_page_booking_id_path).extract()))
        total_paid = normalize(''.join(sel.xpath(pax_page_amount_path).extract()))
        depart = normalize(''.join(sel.xpath(pax_page_depart_loc_path).extract()))
        flight_id = normalize(''.join(sel.xpath(pax_page_flight_id_path).extract()))
        from_airport_details = normalize(' '.join(sel.xpath(pax_page_fr_air_path).extract()))
        to_airport_details = normalize(' '.join(sel.xpath(pax_page_to_air_path).extract()))
        guest_name = normalize('<>'.join(sel.xpath(pax_page_guest_name_path).extract()))
        mobile_no = normalize(''.join(sel.xpath(pax_page_mo_no_path).extract()))
        email = normalize(''.join(sel.xpath(pax_page_email_path).extract()))
        data_dict.update({'flightid':flight_id, 'guest':guest_name, 'mobile_no':mobile_no, 'email':email})
        values = (book_dict.get('tripid', ''), 'AirAsia', booking_id, flight_id, data_dict.get('origin', ''), 
                data_dict.get('destination', ''), "Booking Failed", '', 'Itinerary exixts', json.dumps(data_dict),
                'Itinerary exixts', json.dumps(data_dict), book_dict.get('tripid', ''))
        self.cur.execute(self.existing_pnr_query, values)
        self.conn.commit()
    
    def parse_search_flights(self, response):
        '''
        Fetching flights
        '''
        sel = Selector(response)
        book_dict = response.meta.get('book_dict', {})
        if response.status != 200:#
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
        view_state = normalize(''.join(sel.xpath(view_state_path).extract()))
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
        origin = book_dict.get('origin', '')
        dest = book_dict.get('destination', '')
        trip_type = book_dict.get('triptype', '')
        oneway_date = book_dict.get('onewaydate', '')
        return_date = book_dict.get('returndate', '')
        oneway_date_ = datetime.datetime.strptime(oneway_date, '%Y-%m-%d')
        bo_day, bo_month, bo_year = oneway_date_.day, oneway_date_.month, oneway_date_.year
        boarding_date = oneway_date_.strftime('%m/%d/%Y')
        if return_date:
            return_date_ = datetime.datetime.strptime(return_date, '%Y-%m-%d')
            re_day, re_month, re_year = return_date_.day, return_date_.month, return_date_.year,
            return_date = return_date_.strftime('%m/%d/%Y')
        else : return_date, re_day, re_month, re_year = '', '', '', '', 
        no_of_adt = book_dict.get('paxdetails', {}).get('adult', '0')
        no_of_chd = book_dict.get('paxdetails', {}).get('child', '0')
        no_of_infant = book_dict.get('paxdetails', {}).get('infant', '0')
        #OneWay,RoundTrip 
        form_data = {
                  '__EVENTTARGET': '',
                  '__EVENTARGUMENT': '',
                  '__VIEWSTATE': view_state,
                  'pageToken': '',
                  'ControlGroupSearchView$MultiCurrencyConversionViewSearchView$DropDownListCurrency':'default',
                  'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListSearchBy': 'columnView',
                  '__VIEWSTATEGENERATOR': gen,
                  'ControlGroupSearchView$ButtonSubmit': 'Search',
               }
        form_data.update({'ControlGroupSearchView$AvailabilitySearchInputSearchView$RadioButtonMarketStructure': trip_type,

                        'ControlGroupSearchView_AvailabilitySearchInputSearchVieworiginStation1': origin,
                        'ControlGroupSearchView$AvailabilitySearchInputSearchView$TextBoxMarketOrigin1':origin,
                        'ControlGroupSearchView_AvailabilitySearchInputSearchViewdestinationStation1': dest,
                        'ControlGroupSearchView$AvailabilitySearchInputSearchView$TextBoxMarketDestination1':dest,
                        'date_picker': str(boarding_date),
                        'date_picker': '',
                        'date_picker': str(return_date),
                        'date_picker': '',
                        'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListMarketDay1': str(bo_day),
                        'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListMarketMonth1': '%s-%s'%(bo_year, bo_month),
                        'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListMarketDay2': str(re_day),
                        'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListMarketMonth2': '%s-%s'%(re_year,re_month),
                        'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListPassengerType_ADT': no_of_adt,
                        'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListPassengerType_CHD': no_of_chd,
                        'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListPassengerType_INFANT': no_of_infant,

                        })
        if book_dict.get('triptype', '') == 'OneWay' or book_dict.get('triptype', '') == 'RoundTrip':
            if book_dict.get('triptype', '') == 'OneWay':
                form_data.update({'oneWayOnly':'1',})
            select_url = 'https://booking2.airasia.com/Search.aspx'
            yield FormRequest(select_url, callback=self.parse_select_fare, \
                        formdata=form_data, meta={'form_data':form_data, 'book_dict':book_dict})

    def parse_select_fare(self, response):
        '''
        Selecting flight as per request
        '''
        sel = Selector(response)
        book_dict = response.meta.get('book_dict', {})
        form_data = response.meta['form_data']
        if response.status != 200:
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
        fare_class_dict = {'Regular': 'Regular', 'PremiumFlex': 'PremiumFlex',
                                'PremiumFlatbed':'PremiumFlatbed', "Econamy":"Lowfare", "Economy": "Lowfare"}
        view_state = normalize(''.join(sel.xpath(view_state_path).extract()))
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
        fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price, rt_flt_no = [''] * 5
        refin_fare_id, refin_fare_name, refin_fare_vlue, refin_price = [''] * 4
        table_nodes = sel.xpath('//table[@id="fareTable1_4"]//tr')
        retable_nodes = sel.xpath('//table[@id="fareTable2_4"]//tr')
        field_tab_index = sel.xpath('//div[@class="tabsHeader"][1]//input//@id').extract()
        field_tab_value = sel.xpath('//div[@class="tabsHeader"][1]//input//@value').extract()
        if book_dict.get('triptype', '') ==  'RoundTrip':
            if len(field_tab_index) == 2 and len(field_tab_value) == 2:
                field_tab_index, refield_tab_index = field_tab_index
                field_tab_value, refield_tab_value = field_tab_value
            else:
                refield_tab_index, refield_tab_value = ['']*2
        else:
            field_tab_index = ''.join(field_tab_index)
            field_tab_value = ''.join(field_tab_value)
            refield_tab_index, refield_tab_value = ['']*2
        if not table_nodes:
             err = 'No Flithts found'
             logging.debug('Flithts  not found')
        if not retable_nodes and book_dict.get('triptype', '') ==  'RoundTrip':
            err = 'No Flights found'
            logging.debug('Flithts  not found')
        member_time_zone = ''.join(sel.xpath('//input[@id="MemberLoginSelectView_HFTimeZone"]/@value').extract())
        flight_oneway_fares = {}
        for node in table_nodes:
            fares_ = {}
            flight_text = ''.join(node.xpath('.//div[@class="scheduleFlightNumber"]//span[@class="hotspot"]/@onmouseover').extract())
            if not flight_text:
                flight_text = ''.join(node.xpath('.//div[@class="scheduleFlightNumber"]//div[@class="hotspot"]/@onmouseover').extract())
            if flight_text:
                flt_ids = re.findall('<b>(.*?)</b>', flight_text)
                if flt_ids: flt_id = '<>'.join(flt_ids).replace(' ', '').strip()
                else: flt_id = ''
            else: flt_id = ''
            for i in range(2, 6):
                fare_cls = ''.join(node.xpath('./..//th[%s]//div[contains(@class, "fontNormal")]//text()'%i).extract()).replace(' ', '').strip()
                fare_id = ''.join(node.xpath('.//td[%s]//div[@id="fareRadio"]//input/@id'%i).extract())
                fare_name = ''.join(node.xpath('.//td[%s]//div[@id="fareRadio"]//input/@name'%i).extract())
                fare_vlue = ''.join(node.xpath('.//td[%s]//div[@id="fareRadio"]//input/@value'%i).extract())
                price = '<>'.join(node.xpath('.//td[%s]//div[@class="price"]//div[@id="originalLowestFare"]//text()'%i).extract())
                if fare_id:
                    fares_.update({fare_cls:(fare_id, fare_name, fare_vlue, price)})
            if flt_id:
                flight_oneway_fares.update({flt_id:fares_})
        flight_return_fares = {}            
        if retable_nodes:
            for renode in retable_nodes:
                refares_ = {}
                flight_text = ''.join(renode.xpath('.//div[@class="scheduleFlightNumber"]//span[@class="hotspot"]/@onmouseover').extract())
                if not flight_text:
                    flight_text = ''.join(node.xpath('.//div[@class="scheduleFlightNumber"]//div[@class="hotspot"]/@onmouseover').extract())
                if flight_text:
                    reflt_ids = re.findall('<b>(.*?)</b>', flight_text)
                    if reflt_ids: reflt_id = '<>'.join(reflt_ids).replace(' ', '').strip()
                    else: reflt_id = ''
                else: reflt_id = ''
                for i in range(2, 6):
                    fare_cls = ''.join(renode.xpath('./..//th[%s]//div[contains(@class, "fontNormal")]//text()'%i).extract()).replace(' ', '').strip()
                    flight_text = ''.join(renode.xpath('.//div[@class="scheduleFlightNumber"]//span[@class="hotspot"]/@onmouseover').extract())
                    fare_id = ''.join(renode.xpath('.//td[%s]//div[@id="fareRadio"]//input/@id'%i).extract())
                    fare_name = ''.join(node.xpath('.//td[%s]//div[@id="fareRadio"]//input/@name'%i).extract())
                    fare_vlue = ''.join(renode.xpath('.//td[%s]//div[@id="fareRadio"]//input/@value'%i).extract())
                    price = '<>'.join(renode.xpath('.//td[%s]//div[@class="price"]//div[@id="originalLowestFare"]//text()'%i).extract())
                    if fare_id:
                            refares_.update({fare_cls:(fare_id, fare_name, fare_vlue, price)})
            if reflt_id:
                flight_return_fares.update({reflt_id:refares_})
        ct_flight_id = book_dict.get('onewayflightid', [])
        ct_ticket_class = book_dict.get('onewayclass', []).replace(' ', '').strip()
        aa_keys = flight_oneway_fares.keys()
        fin_fare_dict, ow_flt_no = self.get_fin_fares_dict(flight_oneway_fares, ct_flight_id)
        final_flt_tuple = fin_fare_dict.get(fare_class_dict.get(ct_ticket_class, ''), ['']*4)
        fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price = final_flt_tuple
        refin_fare_dict = {}
        rect_ticket_class = book_dict.get('returnclass', '').replace(' ', '').strip()
        if book_dict.get('triptype', '') ==  'RoundTrip':
            rect_flight_id = book_dict.get('returnflightid', [])
            refin_fare_dict, rt_flt_no = self.get_fin_fares_dict(flight_return_fares, rect_flight_id)
        refinal_flt_tuple = refin_fare_dict.get(fare_class_dict.get(rect_ticket_class, ''), ['']*4)
        refin_fare_id, refin_fare_name, refin_fare_vlue, refin_price = refinal_flt_tuple
        book_dict.update({'ow_flt':ow_flt_no, 'rt_flt':rt_flt_no})
        if fin_fare_vlue:
            form_data.update({
                             field_tab_index:field_tab_value,
                             fin_fare_name:fin_fare_vlue,
                             'ControlGroupSelectView$SpecialNeedsInputSelectView$RadioButtonWCHYESNO':'RadioButtonWCHNO',
                             '__VIEWSTATEGENERATOR':gen,
                             '__VIEWSTATE':view_state,
                             'ControlGroupSelectView$ButtonSubmit': 'Continue',
                        })
            url = 'https://booking2.airasia.com/Select.aspx'
            if book_dict.get('triptype', '') == 'RoundTrip' and refin_fare_vlue:
                form_data.update({      refield_tab_index:refield_tab_value,
                                    'ControlGroupSelectView$AvailabilityInputSelectView$market2':refin_fare_vlue,
                                })
                yield FormRequest(url, callback=self.parse_travel, formdata=form_data, \
                        meta={'form_data':form_data, 'book_dict':book_dict}, method="POST")

            elif fin_fare_vlue and book_dict.get('triptype', '') == 'OneWay':
                yield FormRequest(url, callback=self.parse_travel, formdata=form_data, \
                        meta={'form_data':form_data, 'book_dict':book_dict}, method="POST")
            else:
                vals = (
                        book_dict.get('tripid', ''), 'AirAsia', '', '', book_dict.get('origin', ''),
                        book_dict.get('destination', ''), "Booking Failed", '', "Could not find flights", json.dumps(book_dict),
                        'Could not find flights', json.dumps(book_dict), book_dict.get('tripid', ''),
                   )
                self.cur.execute(self.existing_pnr_query, vals)
                logging.debug("Couldn't find flights for %s"%book_dict.get('tripid', ''))
                self.send_mail("Couldn't find flights for %s"%book_dict.get('tripid', ''), json.dumps(book_dict))
        else:
            vals = (
                        book_dict.get('tripid', ''), 'AirAsia', '', '', book_dict.get('origin', ''),
                        book_dict.get('destination', ''), "Booking Failed", '', "No flights find in selected class", json.dumps(book_dict),
                        'No flights find in selected class', json.dumps(book_dict), book_dict.get('tripid', ''),
                   )
            self.cur.execute(self.existing_pnr_query, vals)
            logging.debug("Couldn't find flights for given class  %s"%book_dict.get('tripid', ''))
            self.send_mail("Couldn't find flights for %s"%book_dict.get('tripid', ''), json.dumps(book_dict))
            

    def parse_travel(self, response):
        '''
        Booking form filling
        '''
        sel = Selector(response)
        book_dict = response.meta.get('book_dict', {})
        if response.status != 200:
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
        umeal_key_lst = book_dict.get('onewaymealcode', [])
        dmeal_key_lst = book_dict.get('returnmealcode', [])
        guest_count = book_dict.get('paxdetails', {})
        emergency_contact = book_dict.get('emergencycontact', {})
        guest_ph_number = book_dict.get('phonenumber', '')
        view_state = normalize(''.join(sel.xpath(view_state_path).extract()))
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
        flyerfare = ''.join(sel.xpath('//input[@name="HiFlyerFare"]/@value').extract())
        booking_data = ''.join(sel.xpath('//input[@name="HiddenFieldPageBookingData"]/@value').extract())
        token_field = ''.join(sel.xpath('//input[@name="CONTROLGROUP_OUTERTRAVELER$CONTROLGROUPTRAVELER$ContactInputTravelerView$CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ContactInputTravelerViewHtmlInputHiddenAntiForgeryTokenField"]/@value').extract())
        add_key = 'CONTROLGROUP_OUTERTRAVELER$CONTROLGROUPTRAVELER$%s'
        baggage_up_name = ''.join(sel.xpath('//ul[@class="add-on-forms "][1]//li[@class="baggageContainer"]//select/@name').extract())
        baggage_up_codes = ''.join(sel.xpath('//ul[@class="add-on-forms "]//li[@class="baggageContainer"]//select/@ssr-data').extract())
        if baggage_up_codes:
             try:
                default_bg_code = baggage_up_codes.split('|')[0].split(' ')[0].strip()
             except: default_bg_code = ''
        else: default_bg_code = ''
        oneway_hg_baggage = book_dict.get('onewaybaggagecode', '')
        if oneway_hg_baggage and baggage_up_name:
            oneway_baggage_value = baggage_up_name.split('TravelerView$')[-1]\
                        .replace('journey', 'ssrCode_%s_ssrNum'%oneway_hg_baggage)
        elif default_bg_code: oneway_baggage_value = baggage_up_name.split('TravelerView$')[-1]\
                        .replace('journey', 'ssrCode_%s_ssrNum'%default_bg_code)
        else: oneway_baggage_value = ''
        
        up_meal_lst, dw_meal_lst = [], []
        if umeal_key_lst:
            for m_code in umeal_key_lst:
                up_meal_keys = sel.xpath('//ul[@class="add-on-forms "][1]//li[@data-ssr-id="%s"]\
                        //div[@class="ucmealpanel-item-selection"]//input/@name'%m_code).extract()
                for i in up_meal_keys:
                    if i: up_meal_lst.append((i, 1))

        baggage_down_name = ''.join(sel.xpath('//ul[@class="add-on-forms "][2]//li[@class="baggageContainer"]//select/@name').extract())
        baggage_down_codes = ''.join(sel.xpath('//ul[@class="add-on-forms "]//li[@class="baggageContainer"]//select/@ssr-data').extract())
        if baggage_down_codes:
            try:
                def_bg_code = baggage_down_codes.split('|')[0].split(' ')[0].strip()
            except: def_bg_code = ''
        else: def_bg_code = ''
        return_hg_baggage = book_dict.get('returnbaggagecode', '')
        if return_hg_baggage and baggage_down_name:
            return_baggage_value = baggage_down_name.split('TravelerView$')[-1]\
                                .replace('journey', 'ssrCode_%s_ssrNum'%return_hg_baggage)
        elif def_bg_code: return_baggage_value = baggage_down_name.split('TravelerView$')[-1]\
                                .replace('journey', 'ssrCode_%s_ssrNum'%def_bg_code)
        else: return_baggage_value = ''
        if dmeal_key_lst:
            for d_code in dmeal_key_lst:
                down_meal_keys = sel.xpath('//ul[@class="add-on-forms "][1]//li[@data-ssr-id="%s"]//div[@class="ucmealpanel-item-selection"]//input/@name'%d_code).extract()
                for j in down_meal_keys:
                    if j : dw_meal_lst.append((j, 1))
        data = { 
                  '__EVENTTARGET': '',
                  '__EVENTARGUMENT': '',
                  '__VIEWSTATE': view_state,
                  'pageToken': '',
                  'MemberLoginTravelerView2$TextBoxUserID': '',
                  'hdRememberMeEmail': '',
                  'MemberLoginTravelerView2$PasswordFieldPassword': '',
                  'memberLogin_chk_RememberMe': 'on',
                  'HiFlyerFare': flyerfare,
                  'isAutoSeats': 'false',
                  'CONTROLGROUP_OUTERTRAVELER$CONTROLGROUPTRAVELER$ContactInputTravelerView$CONTROLGROUP_OUTERTRAVELER_CONTROLGROUPTRAVELER_ContactInputTravelerViewHtmlInputHiddenAntiForgeryTokenField': token_field,
                  add_key%'ContactInputTravelerView$HiddenSelectedCurrencyCode': 'INR',
                  add_key%'ContactInputTravelerView$DropDownListTitle': 'MS',
                  add_key%'ContactInputTravelerView$TextBoxFirstName': 'Preeti',
                  add_key%'ContactInputTravelerView$TextBoxLastName': 'Yadav',
                  add_key%'ContactInputTravelerView$TextBoxWorkPhone': '022 4055 4000',
                  add_key%'ContactInputTravelerView$TextBoxFax': '',
                  add_key%'ContactInputTravelerView$TextBoxEmailAddress': book_dict.get('email', ''),
                  add_key%'ContactInputTravelerView$DropDownListHomePhoneIDC': '91',
                  add_key%'ContactInputTravelerView$TextBoxHomePhone': guest_ph_number,#book_dict.get('', ''),
                  add_key%'ContactInputTravelerView$DropDownListOtherPhoneIDC': '91',
                  add_key%'ContactInputTravelerView$TextBoxOtherPhone': guest_ph_number,
                  add_key%'ContactInputTravelerView$EmergencyTextBoxGivenName': emergency_contact.get('firstname', ''),
                  add_key%'ContactInputTravelerView$EmergencyTextBoxSurname': emergency_contact.get('lastname', ''),
                  add_key%'ContactInputTravelerView$DropDownListMobileNo': emergency_contact.get('mobilephcode', ''),
                  add_key%'ContactInputTravelerView$EmergencyTextBoxMobileNo': emergency_contact.get('mobilenumber', ''),
                  add_key%'ContactInputTravelerView$DropDownListRelationship': 'other',
                  add_key%'ContactInputTravelerView$DropDownListSelectedGSTState': '',
                  add_key%'ContactInputTravelerView$GSTTextBoxCompanyName': '',
                  add_key%'ContactInputTravelerView$GSTTextBoxCompanyStreet': '',
                  add_key%'ContactInputTravelerView$GSTTextBoxCompanyPostalCode': '',
                  add_key%'ContactInputTravelerView$DropDownListGSTCountry': 'IN',
                  add_key%'ContactInputTravelerView$DropDownListGSTState': 'AN',
                  add_key%'ContactInputTravelerView$GSTTextboxRegistrationNumber': '',
                  add_key%'ContactInputTravelerView$GSTTextboxCompanyEmail': '',

                  'drinkcountname': '0',
                  'drinkcountname': '0',
                  'checkBoxInsuranceName': 'InsuranceInputControlAddOnsViewAjax$CheckBoxInsuranceAccept',
                  'checkBoxInsuranceId': 'CONTROLGROUP_InsuranceInputControlAddOnsViewAjax_CheckBoxInsuranceAccept',
                  'checkBoxAUSNoInsuranceId': 'InsuranceInputControlAddOnsViewAjax_CheckBoxAUSNo',
                  'declineInsuranceLinkButtonId': 'InsuranceInputControlAddOnsViewAjax_LinkButtonInsuranceDecline',
                  'iniiiisuranceLinkCancelId': 'InsuranceInputControlAddOnsViewAjax_LinkButtonInsuranceDecline',
                  'radioButtonNoInsuranceId': 'InsuranceInputControlAddOnsViewAjax_RadioButtonNoInsurance',
                  'radioButtonYesInsuranceId': 'InsuranceInputControlAddOnsViewAjax_RadioButtonYesInsurance',
                  'radioButton': 'on',
                  'HiddenFieldPageBookingData': booking_data,
                  '__VIEWSTATEGENERATOR': gen,
                  'CONTROLGROUP_OUTERTRAVELER$CONTROLGROUPTRAVELER$ButtonSubmit': 'Continue',
                }
        guestdetails = book_dict.get('guestdetails', [])
        guestdetails.extend(book_dict.get('childdetails', []))
        for idx, details in enumerate(guestdetails):
            birth_date = details.get('dob', '')
            bo_day, bo_month, bo_year = ['']*3
            if birth_date:
                birth_date = datetime.datetime.strptime(birth_date, '%Y-%m-%d')
                bo_day, bo_month, bo_year = birth_date.day, birth_date.month, birth_date.year
            gender = details.get('gender', '')
            if gender == 'Male': gender_val = 1
            else: gender_val = 2
            if details:        
                data.update({
                add_key%'PassengerInputTravelerView$DropDownListTitle_%s'%idx: details.get('title', ''),
                add_key%'PassengerInputTravelerView$DropDownListGender_%s'%idx:str(gender_val),
                add_key%'PassengerInputTravelerView$TextBoxFirstName_%s'%idx: details.get('firstname', ''),
                add_key%'PassengerInputTravelerView$TextBoxLastName_%s'%idx: details.get('lastname', ''),
                add_key%'PassengerInputTravelerView$DropDownListNationality_%s'%idx: book_dict.get('countrycode', ''),
                add_key%'PassengerInputTravelerView$DropDownListBirthDateDay_%s'%idx: str(bo_day),
                add_key%'PassengerInputTravelerView$DropDownListBirthDateMonth_%s'%idx: str(bo_month),
                add_key%'PassengerInputTravelerView$DropDownListBirthDateYear_%s'%idx: str(bo_year),
                add_key%'PassengerInputTravelerView$TextBoxCustomerNumber_%s'%idx: '',
                    })

        infants = book_dict.get('infant', [])
        for idf, inf in enumerate(infants):
            birth_date = inf.get('dob', '')
            bo_day, bo_month, bo_year = ['']*3
            if birth_date:
                birth_date = datetime.datetime.strptime(birth_date, '%Y-%m-%d')
                bo_day, bo_month, bo_year = birth_date.day, birth_date.month, birth_date.year
            gender = inf.get('gender', '')
            if gender == 'Male': gender_val = 1
            else: gender_val = 2
            data.update({
                add_key%'PassengerInputTravelerView$DropDownListAssign_0_0': '0',
                add_key%'PassengerInputTravelerView$DropDownListGender_0_%s'%idf: str(gender),
                add_key%'PassengerInputTravelerView$TextBoxFirstName_0_%s'%idf: inf.get('firstname', ''),
                add_key%'PassengerInputTravelerView$TextBoxLastName_0_%s'%idf: inf.get('lastname', ''),
                add_key%'PassengerInputTravelerView$DropDownListNationality_0_%s'%idf: inf.get('countrycode', ''),
                add_key%'PassengerInputTravelerView$DropDownListBirthDateDay_0_%s'%idf: str(bo_day),
                add_key%'PassengerInputTravelerView$DropDownListBirthDateMonth_0_%s'%idf: str(bo_month),
                add_key%'PassengerInputTravelerView$DropDownListBirthDateYear_0_%s'%idf: str(bo_year),
                })
        if oneway_baggage_value:
            data.update({baggage_up_name:oneway_baggage_value})
        if return_baggage_value:
            data.update({baggage_down_name:return_baggage_value})
        if up_meal_lst:
            for i in up_meal_lst:
                key, val = i
                data.update({key:str(val)})
        if dw_meal_lst:
            for i in dw_meal_lst:
                key, val = i
                data.update({key:str(val)})
        len_meal = len(umeal_key_lst)
        data.update({"drinkcountname":str(len_meal)})
        for idx, m_code in enumerate(umeal_key_lst):
            data.update({'ctl00$BodyContent$ucTravelerForm1_form$addOnsPanel1$mealPanel2$SelectedMeal_%s'%idx:m_code})
        for idx, m_code in enumerate(dmeal_key_lst):
            data.update({'ctl00$BodyContent$ucTravelerForm1_form$addOnsPanel1$mealPanel2$SelectedMeal_%s'%idx:m_code})
        travel_url = 'https://booking2.airasia.com/Traveler.aspx'
        yield FormRequest(travel_url, callback=self.parse_form, formdata=data, meta={'book_dict':book_dict})

    def parse_form(self, response):
        '''
        parsing Addons page
        '''
        book_dict = response.meta.get('book_dict', {})
        if response.status != 200:
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
        sel = Selector(response)
        tolerance_value = 0
        ct_price = book_dict.get('ctprice', '0')
        total_fare = ''.join(sel.xpath('//div[@class="total-amount-bg-last"]//span[@id="overallTotal"]//text()').extract())
        try:
            total_fare = float(total_fare.replace(',', '').strip())
        except: total_fare = 0
        if total_fare != 0:
            tolerance_value = total_fare - float(ct_price)
            if tolerance_value >= 2000:
                    is_proceed = 0  #movie it to off line
            else: is_proceed = 1
        else:
            tolerance_value, is_proceed = 0, 0
        view_state = normalize(''.join(sel.xpath(view_state_path).extract()))
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
        booking_data = ''.join(sel.xpath('//input[@name="HiddenFieldPageBookingData"]/@value').extract())
        data = [
                  ('__EVENTTARGET', ''),
                  ('__EVENTARGUMENT', ''),
                  ('__VIEWSTATE', view_state),
                  ('pageToken', ''),
                  ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$DriverAgeTextBox', 'Please enter your age'),
                  ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedCarPosition', ''),
                  ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedCarModel', ''),
                  ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedCarPrice', ''),
                  ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedCarTotalPrice', ''),
                  ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedCarDateTime', ''),
                  ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedReferenceType', ''),
                  ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedReferenceID', ''),
                  ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedReferenceIDContext', ''),
                  ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedReferenceDateTime', ''),
                  ('CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedReferenceUrl', ''),
                  ('HiddenFieldPageBookingData', booking_data),
                  ('__VIEWSTATEGENERATOR', gen),
                  ('CONTROLGROUPADDONSFLIGHTVIEW$ButtonSubmit', 'Continue'),
                ]        
        travel_url = 'https://booking2.airasia.com/AddOns.aspx'
        if is_proceed == 1:
            book_dict.update({'tolerance_value':tolerance_value})
            yield FormRequest(travel_url, callback=self.parse_seat, dont_filter=True, formdata=data, meta={'book_dict':book_dict})
        else:
            vals = (
                        book_dict.get('tripid', ''), 'AirAsia', '', '', book_dict.get('origin', ''),
                        book_dict.get('destination', ''), "Booking Failed", '',
                        "Fare increased by Airline", json.dumps(book_dict),
                        'Fare increased by Airline', json.dumps(book_dict), book_dict.get('tripid', ''),
                   )
            self.cur.execute(self.existing_pnr_query, vals)
            self.send_mail('Fare increased by AirAsia', json.dumps(book_dict))

    def parse_seat(self, response):
        '''
        parsing seat selection page
        '''
        sel = Selector(response)
        book_dict = response.meta.get('book_dict', {})
        if response.status != 200:
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
        view_state = normalize(''.join(sel.xpath(view_state_path).extract()))
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
        bookingdata = ''.join(sel.xpath('//input[@id="HiddenFieldPageBookingDataId"]/@value').extract())
        data = [
                  ('__EVENTTARGET', 'ControlGroupUnitMapView$UnitMapViewControl$LinkButtonAssignUnit'),
                  ('__EVENTARGUMENT', ''),
                  ('__VIEWSTATE', str(view_state)),
                  ('pageToken', ''),
                  ('ControlGroupUnitMapView$UnitMapViewControl$compartmentDesignatorInput', ''),
                  ('ControlGroupUnitMapView$UnitMapViewControl$deckDesignatorInput', '1'),
                  ('ControlGroupUnitMapView$UnitMapViewControl$tripInput', '0'),
                  ('ControlGroupUnitMapView$UnitMapViewControl$passengerInput', '0'),
                  ('ControlGroupUnitMapView$UnitMapViewControl$HiddenEquipmentConfiguration_0_PassengerNumber_0', ''),
                  ('ControlGroupUnitMapView$UnitMapViewControl$EquipmentConfiguration_0_PassengerNumber_0', ''),
                  ('ControlGroupUnitMapView$UnitMapViewControl$EquipmentConfiguration_0_PassengerNumber_0_HiddenFee', 'NaN'),
                  ('HiddenFieldPageBookingData', str(bookingdata)),
                  ('__VIEWSTATEGENERATOR', str(gen)),
                ]
        url = 'https://booking2.airasia.com/UnitMap.aspx'
        #Navigating to Patment Process
        yield FormRequest(url, callback=self.parse_unitmap, formdata=data, meta={'book_dict':book_dict, 'v_state':view_state, 'gen':gen}) 

    def parse_unitmap(self, response):
        '''
        Parsing to Agency Account for payment
        '''
        sel = Selector(response)
        book_dict = response.meta['book_dict']
        amount = ''.join(sel.xpath('//div[@class="totalAmtText"]//following-sibling::div[1]/text()').extract())
        amount = ''.join(re.findall('\d+,?\d+', amount))
        booking_data = ''.join(sel.xpath('//input[@name="HiddenFieldPageBookingData"]/@value').extract())
        view_state = normalize(''.join(sel.xpath(view_state_path).extract()))
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
        data = [
                  ('__EVENTTARGET', 'CONTROLGROUPPAYMENTBOTTOM$PaymentInputViewPaymentView'),
                  ('__EVENTARGUMENT', 'AgencyAccount'),
                  ('__VIEWSTATE', agency_viewstate),
                  ('pageToken', ''),
                  ('eventTarget', ''),
                  ('eventArgument', ''),
                  ('viewState', agency_viewstate),
                  ('pageToken', ''),
                  ('PriceDisplayPaymentView$CheckBoxTermAndConditionConfirm', 'on'),
                  ('CONTROLGROUPPAYMENTBOTTOM$MultiCurrencyConversionViewPaymentView$DropDownListCurrency', 'default'),
                  ('MCCOriginCountry', 'IN'),
                  ('CONTROLGROUPPAYMENTBOTTOM$PaymentInputViewPaymentView$HiddenFieldUpdatedMCC', ''),
                  ('HiddenFieldPageBookingData', str(booking_data)),
                  ('__VIEWSTATEGENERATOR', str(gen)),
                ]
        url = 'https://booking2.airasia.com/Payment.aspx'
        #Navigating to Agency Account
        if not 'Payment' in response.url:
            vals = (
                        book_dict.get('tripid', ''), 'AirAsia', '', '', book_dict.get('origin', ''),
                        book_dict.get('destination', ''), "Booking Failed", '', "Payment Failed", json.dumps(book_dict),
                        'Payment Failed', json.dumps(book_dict), book_dict.get('tripid', ''),
                   )
            self.cur.execute(self.existing_pnr_query, vals)
            self.send_mail('Payment Failed', json.dumps(book_dict))
        else:
            yield FormRequest(url, callback=self.parse_agency, formdata=data, dont_filter=True,  meta={'book_dict':response.meta['book_dict'],
                                            'booking_data':booking_data, 'gen':gen, 'amount':amount})

    def parse_agency(self, response):
        '''
        collecting payment details and submit payment
        '''
        sel = Selector(response)
        book_dict = response.meta['book_dict']
        tax_dict1, tax_dict2, fin_tax = {}, {}, {}
        flt1 = ''.join(sel.xpath('//div[@class="flightDisplay_1"]//div[@id="section_1"]//span[@class="right-text bold grey1"]//text()').extract()).replace(' ', '')
        flt1 = re.sub(flt1[1],flt1[1]+' ', flt1)
        seg = '-'.join(sel.xpath('//div[@class="flightDisplay_1"]//div[@id="section_1"]//div[@class="row2 mtop-row"]//div//text()').extract()).replace('\n', '').replace('\t', '').replace('\r', '').strip()
        tax_key = sel.xpath('//div[@class="flightDisplay_1"]//div[@id="section_1"]//span[@class="left-text black2"]//text()').extract()
        tax_val = sel.xpath('//div[@class="flightDisplay_1"]//div[@id="section_1"]//span[@class="right-text black2"]//text()').extract()
        tot1_price = ''.join(sel.xpath('//span[@id="totalJourneyPrice_1"]//text()').extract())
        tot1_price = ''.join(re.findall(r'(\d+.\d+)', tot1_price))
        for i , j in zip(tax_key, tax_val):
            if 'Adult' in i or 'Child' in i or 'Infant' in i:
                if '(' in i: i = ''.join(re.findall(r'\d+ (.*)\(', i))
                else: i = ''.join(re.findall(r'\d+ (.*)', i))
            j = ''.join(re.findall(r'(\d+.\d+)', j))
            tax_dict1.update({i.replace(' ', ''):j, 'seg':seg, 'total':tot1_price})
        if flt1: fin_tax.update({flt1:tax_dict1})
        flt2 = ''.join(sel.xpath('//div[@class="flightDisplay_2"]//div[@id="section_2"]//span[@class="right-text bold grey1"]//text()').extract()).replace(' ', '')
        try: flt2 = re.sub(flt2[1],flt2[1]+' ', flt2)
        except: flt2 = ''
        seg2 = '-'.join(sel.xpath('//div[@class="flightDisplay_2"]//div[@id="section_2"]//div[@class="row2 mtop-row"]//div//text()').extract()).replace('\n', '').replace('\t', '').replace('\r', '').strip()
        tax2_key = sel.xpath('//div[@class="flightDisplay_2"]//div[@id="section_2"]//span[@class="left-text black2"]//text()').extract()
        tax2_val = sel.xpath('//div[@class="flightDisplay_2"]//div[@id="section_2"]//span[@class="right-text black2"]//text()').extract()
        tot2_price = ''.join(sel.xpath('//span[@id="totalJourneyPrice_2"]//text()').extract())
        tot2_price = ''.join(re.findall(r'(\d+.\d+)', tot2_price))
        for i, j in zip(tax2_key, tax2_val):
            if 'Adult' in i or 'Child' in i or 'Infant' in i:
                if '(' in i: i = ''.join(re.findall(r'\d+ (.*)\(', i))
                else: i = ''.join(re.findall(r'\d+ (.*)', i))
            j = ''.join(re.findall(r'(\d+.\d+)', j))
            tax_dict2.update({i.replace(' ', ''):j, 'seg':seg2, 'total':tot2_price})
        if flt2: fin_tax.update({flt2:tax_dict2})
        booking_data = ''.join(sel.xpath('//input[@name="HiddenFieldPageBookingData"]/@value').extract())
        if not booking_data:
            booking_data = response.meta['booking_data']
        amount = ''.join(sel.xpath('//input[@id="CONTROLGROUPPAYMENTBOTTOM_PaymentInputViewPaymentView_AgencyAccount_AG_AMOUNT"]/@value').extract())
        view_state = sel.xpath('//input[@id="viewState"]/@value').extract()
        if view_state: view_state = view_state[0]
        else: view_state = ''
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
        data = { 
                  '__EVENTTARGET': '',
                  '__EVENTARGUMENT': '',
                  '__VIEWSTATE': view_state,
                  'pageToken': '',
                  'pageToken': '',
                  'eventTarget': '',
                  'eventArgument': '',
                  'viewState': view_state,
                  'PriceDisplayPaymentView$CheckBoxTermAndConditionConfirm': 'on',
                  'MCCOriginCountry': 'IN',
                  'CONTROLGROUPPAYMENTBOTTOM$PaymentInputViewPaymentView$AgencyAccount_AG_AMOUNT': amount,
                  'HiddenFieldPageBookingData': booking_data,
                  '__VIEWSTATEGENERATOR': gen,
                  'CONTROLGROUPPAYMENTBOTTOM$ButtonSubmit': 'Submit payment',
                }
        url = 'https://booking2.airasia.com/Payment.aspx'
        #Submit Payment
        if amount:
            yield FormRequest(url, callback=self.parse_itinerary, formdata=data,\
                 meta={'book_dict':response.meta['book_dict'], 'tax_dict':fin_tax})
        else:
            vals = (
                        book_dict.get('tripid', ''), 'AirAsia', '', '', book_dict.get('origin', ''),
                        book_dict.get('destination', ''), "Booking Failed", '', "Payment Failed", json.dumps(book_dict),
                        'Payment Failed', json.dumps(book_dict), book_dict.get('tripid', ''),
                   )
            self.cur.execute(self.existing_pnr_query, vals)
            self.send_mail('Payment Failed', json.dumps(book_dict))

    def parse_itinerary(self, response):
        '''
        parsing itinerary form response
        '''
        sel = Selector(response)
        yield FormRequest.from_response(response, callback=self.parse_fin_details, \
                meta={'book_dict':response.meta['book_dict'], 'tax_dict': response.meta['tax_dict']})

    def parse_fin_details(self, response):
        '''
        collecting the final booking detais
        '''
        sel = Selector(response)
        book_dict = response.meta['book_dict']
        tax_dict = response.meta['tax_dict']
        conform = ''.join(sel.xpath('//span[@class="confirm status"]//text()').extract())
        pnr_no = ''.join(sel.xpath('//span[@id="OptionalHeaderContent_lblBookingNumber"]//text()').extract())
        paid_amount = ''.join(sel.xpath('//span[@id="OptionalHeaderContent_lblTotalPaid"]//text()').extract())
        pax_details = ','.join(sel.xpath('//span[@class="guest-detail-name"]//text()').extract())
        flt_no = book_dict.get('ow_flt', '').replace('<>', ' ').strip()
        rt_flt_no = book_dict.get('rt_flt', '').replace('<>', ' ').strip()
        flt = [flt_no, rt_flt_no]
        vals = (
                        book_dict.get('tripid'), 'AirAsia', str(flt), '',
                        pnr_no, book_dict.get('triptype', ''), book_dict.get('ctprice', ''),
                        paid_amount, conform, book_dict.get('tolerance_value', ''), '', pax_details, json.dumps(tax_dict),
                        book_dict.get('tripid', ''), conform
                )
        self.cur.execute(self.insert_query, vals)
        self.conn.commit()
    '''
    def get_lower_fares(self, lst_):
        #returing the low fare flight details
        lower_dict = {}
        if lst_:
            for lst in lst_:
                fare_id, fare_name, fare_vlue, price = lst
                price = price.split('<>')
                price_int = 0
                for i in price:
                    i = i.replace(',', '').strip()
                    i = ''.join(self.price_patt.findall(i))
                    if i:
                        price_int += int(i)
                lower_dict.update({price_int:(fare_id, fare_name, fare_vlue, price_int)})
        min_price = min(lower_dict.keys())
        lower_details = lower_dict.get(min_price, ['']*4)
        return lower_details
    '''

    def get_fin_fares_dict(self, flight_fares, ct_flights):
        '''
        returing the requested flight details
        '''
        aa_keys = flight_fares.keys()
        fin_fare_dict, flight_no = {}, ''
        for key in aa_keys:
            flt_status_key = False
            for ct_flt in ct_flights:
                ct_flt = ct_flt.replace(' ', '').replace('-', '').strip()
                if ct_flt.lower() in key.lower(): flt_status_key = True
                else: flt_status_key = False
            if flt_status_key:
                fin_fare_dict = flight_fares.get(key, {})
                flight_no = key
                break
            else:
                fin_fare_dict, flight_no = {}, ''
        return (fin_fare_dict, flight_no)

    def get_input_segments(self, segments):
        '''
        returing segments
        '''
        all_segments = segments.get('all_segments', [])
        ow_flight_dict, rt_flight_dict = {}, {}
        dest = segments.get('destination_code', '').strip()
        origin = segments.get('origin_code', '').strip()
        from_to = '%s-%s'%(origin, dest)
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
            vals = (
                        segments.get('trip_ref', ''), 'AirAsia', '', '', segments.get('origin_code', ''),
                        segments.get('destination_code', ''), "Booking Failed", '', "Multi-city booking", json.dumps(segments),
                        'Multi-city booking', json.dumps(segments), segments.get('trip_ref', ''),
                   )
            self.cur.execute(self.existing_pnr_query, vals)

    def send_mail(self, sub, error_msg):
        '''
        sending mails
        '''
        ccing = ['rfan.madha@cleartrip.com',
                                'rohit.kulkarni@cleartrip.com',
                                'samir.nayak@cleartrip.com',
                                'pallavi.khandekar@cleartrip.com',
                             ]
        recievers_list = ["rohit.kulkarni@cleartrip.com"]
        sender, receivers = 'ctmonitoring17@gmail.com', ','.join(recievers_list)
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

