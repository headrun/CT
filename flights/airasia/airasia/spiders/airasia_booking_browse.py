import re
import json
import md5
import smtplib
import MySQLdb
import datetime
import smtplib, ssl
from email import encoders
from airasia_xpaths import *
from ast import literal_eval
from scrapy import signals
from airasia.items import *
from scrapy.spider import Spider
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from scrapy.http import FormRequest, Request
from email.mime.multipart import MIMEMultipart
from scrapy.selector import Selector
from ConfigParser import SafeConfigParser
from scrapy.xlib.pydispatch import dispatcher
from scrapy_splash import SplashRequest, SplashFormRequest
from airasia_booking_data import *
_cfg = SafeConfigParser()
_cfg.read('airline_names.cfg')


class AirAsiaBookingBrowse(Spider):
    name = "airasiabooking_browse"
    start_urls = ["https://booking2.airasia.com/AgentHome.aspx"]
    handle_httpstatus_list = [404, 500, 400]
    def __init__(self, *args, **kwargs):
        super(AirAsiaBookingBrowse, self).__init__(*args, **kwargs)
	self.price_patt = re.compile('\d+')
	self.log = create_logger_obj('airasia_booking')
        self.booking_dict = kwargs.get('jsons', {})
	self.insert_query = 'insert into airasia_booking_report(sk, airline, auto_pnr, pnr, ticket, triptype, cleartrip_price, airasia_price, status_message, tolerance_amount, error_message, paxdetails, created_at, modified_at) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now()) on duplicate key update modified_at=now(), sk=%s, pnr=%s, ticket=%s, tolerance_amount=%s, error_message=%s, status_message=%s'
	self.existing_pnr_query = 'insert into airasia_booking_report (sk, airline, auto_pnr, flight_number, from_location, to_location, status_message, oneway_date, error_message, paxdetails, created_at, modified_at) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now() error_message=%s, paxdetails=%s, flight_number=%s'
	self.conn = MySQLdb.connect(host="localhost", user = "root", db = "TICKETBOOKINGDB", charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()

    def parse(self, response):
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
        sel = Selector(response)
	manage_booking = sel.xpath('//a[@id="MyBookings"]/@href').extract()
	if response.status !=200 and not manage_booking:
	    self.send_mail('Booking Scraper unable to login AirAsia', '')
	if self.booking_dict:
            try:
		book_dict = eval(self.booking_dict)
		pnr = book_dict.get('pnr', '')
            except Exception as e:
		logging.debug(e.message)
		self.send_mail('AirAsia Booking Faild', e.message)
                book_dict, pnr = {}, ''
	    headers = {
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                        'cache-control': 'no-cache',
                        'authority': 'booking2.airasia.com',
                        'referer': 'https://booking2.airasia.com/AgentHome.aspx',
                }
	    if not pnr:
	        search_flights = 'https://booking2.airasia.com/Search.aspx'
                if book_dict.get('triptype', '') == 'OneWay' or book_dict.get('triptype', '') == 'RoundTrip':
                    yield Request(search_flights, callback=self.parse_search_flights, headers=headers, dont_filter=True, meta={'book_dict':book_dict})
		elif book_dict.get('triptype', '') == 'MultiCity':
		    self.send_mail('AirAsia Booking Faild', 'AirAsia Booking Faild As its MultiCity trip')
            	    logging.debug('AirAsia Booking Faild As its MultiCity trip')
            elif book_dict:
                url = 'https://booking2.airasia.com/BookingList.aspx'
                yield Request(url, callback=self.parse_search, dont_filter=True, meta={'book_dict':book_dict})

    def parse_search(self, response):
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
		    self.cur.execute(self.existing_pnr_query, vals)
		    #update the info in notes with the actual discrepancy
                    continue
                edit_key = 'Edit:' + ''.join(re.findall('Edit:(.*)', href)).strip(")'")
                cookies.update({'_gali':ids})
                booking_headers.update({'Cookie': '_gali=%s'%normalize(ids)})
                if ids:
                    booking_data_list.update({'__EVENTARGUMENT':normalize(edit_key)})
                    booking_data_list.update({'__VIEWSTATE':normalize(view_state)})
                    booking_data_list.update({'ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword':normalize(book_id)})
                    url = 'https://booking2.airasia.com/BookingList.aspx'
                    yield FormRequest(url, callback=self.parse_details, headers=booking_headers,\
                        formdata=booking_data_list, meta={'data_dict':data_dict, 'book_dict':book_dict})

    def parse_details(self, response):
        sel = Selector(response)
        url = 'http://booking2.airasia.com/ChangeItinerary.aspx'
        yield FormRequest.from_response(response, callback=self.parse_existing_pax, \
                meta={'url':url, 'data_dict':response.meta['data_dict'],
                        'book_dict':response.meta['book_dict']})

    def parse_existing_pax(self, response):
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
		data_dict.get('destination', ''), "Booking Failed", '', 'itinerary exixts', json.dumps(data_dict),
		'itinerary exixts', json.dumps(data_dict), booking_id)
	self.cur.execute(self.existing_pnr_query, values)
	self.conn.commit()

    
    def parse_search_flights(self, response):
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
	boarding_date = oneway_date_.strftime('m/%d/%Y')
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
		'MemberLoginSearchView$HFTimeZone': '330',
		'memberLogin_chk_RememberMe': 'on',
		'MemberLoginSearchView$PasswordFieldPassword': '',
		'hdRememberMeEmail': '',
		'MemberLoginSearchView$TextBoxUserID': '',
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
	sel = Selector(response)
	book_dict = response.meta.get('book_dict', {})
        form_data = response.meta['form_data']
	if response.status != 200:
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
	fare_class_dict = {'Lowfare': 'Lowfare', 'Regular': 'Regular', 'PremiumFlex': 'PremiumFlex', 'PremiumFlatbed':'PremiumFlatbed'}
	view_state = normalize(''.join(sel.xpath(view_state_path).extract()))
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
	fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price = [''] * 4
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
	if not retable_nodes and book_dict.get('triptype', '') ==  'RoundTrip':
	    err = 'No Flights found' 
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
                    fare_name = ''.join(renode.xpath('.//td[%s]//div[@id="fareRadio"]//input/@name'%i).extract())
                    fare_vlue = ''.join(renode.xpath('.//td[%s]//div[@id="fareRadio"]//input/@value'%i).extract())
                    price = '<>'.join(renode.xpath('.//td[%s]//div[@class="price"]//div[@id="originalLowestFare"]//text()'%i).extract())
                    if fare_id:
                    	refares_.update({fare_cls:(fare_id, fare_name, fare_vlue, price)})
	    if reflt_id:
                flight_return_fares.update({reflt_id:refares_})
	ct_flight_id = book_dict.get('onewayflightid', '').replace(' ', '').strip()
	ct_ticket_class = book_dict.get('onewayclass', '').replace(' ', '').strip()	
	aa_keys = flight_oneway_fares.keys()
	fin_fare_dict = {}
	for key in aa_keys:
	    if ct_flight_id in key:
		fin_fare_dict = flight_oneway_fares.get(key, {})
		break
	    else:
		fin_fare_dict = {}
	final_flt_tuple = fin_fare_dict.get(fare_class_dict.get(ct_ticket_class, ''), ['']*4)
	fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price = final_flt_tuple
	refin_fare_dict = {}
	rect_ticket_class = book_dict.get('returnclass', '').replace(' ', '').strip()
	if book_dict.get('triptype', '') ==  'RoundTrip':
	    rect_flight_id = book_dict.get('returnflightid', '').replace(' ', '').strip()
            reaa_keys = flight_oneway_fares.keys()
            for key in reaa_keys:
                if ct_flight_id in key:
                    refin_fare_dict = flight_oneway_fares.get(key, {})
                    break
                else:
                    refin_fare_dict = {}
        refinal_flt_tuple = refin_fare_dict.get(fare_class_dict.get(rect_ticket_class, ''), ['']*4)
        refin_fare_id, refin_fare_name, refin_fare_vlue, refin_price = refinal_flt_tuple
	if fin_fare_vlue:
	    form_data.update({
			     field_tab_index:field_tab_value,
			     fin_fare_name:fin_fare_vlue,
			     'ControlGroupSelectView$SpecialNeedsInputSelectView$RadioButtonWCHYESNO':'RadioButtonWCHNO',
			     '__VIEWSTATEGENERATOR':gen,
			     '__VIEWSTATE':view_state,
			     'ControlGroupSelectView$ButtonSubmit': 'Continue',
			     #'MemberLoginSelectView$TextBoxUserID':'',
  			     #'hdRememberMeEmail': '',
  			     #'MemberLoginSelectView$PasswordFieldPassword': '',
  			     #'memberLogin_chk_RememberMe': 'on',
  			     #'MemberLoginSelectView$HFTimeZone': '330',
			})
	    url = 'https://booking2.airasia.com/Select.aspx'
	    if book_dict.get('triptype', '') == 'RoundTrip' and refin_fare_vlue:
		form_data.update({      refield_tab_index:refield_tab_value,
                                        refin_fare_name:refin_fare_vlue,
                                })
		yield FormRequest(url, callback=self.parse_travel, formdata=form_data, \
                        meta={'form_data':form_data, 'book_dict':book_dict}, method="POST")
	    elif fin_fare_vlue and book_dict.get('triptype', '') == 'OneWay':
	        yield FormRequest(url, callback=self.parse_travel, formdata=form_data, \
			meta={'form_data':form_data, 'book_dict':book_dict}, method="POST")
	    else:
		self.send_mail("Couldn't find flights for %s"%book_dict.get('tripid', ''), json.dumps(book_dict))
	else:
	    #insert the values
	    self.send_mail("Couldn't find flights for %s"%book_dict.get('tripid', ''), json.dumps(book_dict))
	    

    def parse_travel(self, response):
	sel = Selector(response)
	book_dict = response.meta.get('book_dict', {})
	if response.status != 200:
            logging.debug('Internal Server Error')
            self.send_mail('Internal Server Error', json.dumps(book_dict))
	umeal_key_lst = book_dict.get('onewaymealcode', [])
	dmeal_key_lst = book_dict.get('returnmealcode', [])
	guest_count = book_dict.get('paxdetails', {})
	emergency_contact = book_dict.get('emergencycontact', {})
	no_of_pax = guest_count.get('adult', 0) + guest_count.get('child', 0) + guest_count.get('infant', 0)
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
  		add_key%'ContactInputTravelerView$DropDownListTitle': 'MR',
  		add_key%'ContactInputTravelerView$TextBoxFirstName': 'MAXY',
  		add_key%'ContactInputTravelerView$TextBoxLastName': 'FERNANDES',
  		add_key%'ContactInputTravelerView$TextBoxWorkPhone': '022 4055 4000',
  		add_key%'ContactInputTravelerView$TextBoxFax': '',
  		add_key%'ContactInputTravelerView$TextBoxEmailAddress': 'amdtticket@cleartrip.com',
  		add_key%'ContactInputTravelerView$DropDownListHomePhoneIDC': '91',
  		add_key%'ContactInputTravelerView$TextBoxHomePhone': book_dict.get('tripid', ''),
  		add_key%'ContactInputTravelerView$DropDownListOtherPhoneIDC': '91',
  		add_key%'ContactInputTravelerView$TextBoxOtherPhone': guest_ph_number,
  		add_key%'ContactInputTravelerView$EmergencyTextBoxGivenName': emergency_contact.get('firstname', ''),
 		add_key%'ContactInputTravelerView$EmergencyTextBoxSurname': emergency_contact.get('lastname', ''),
  		add_key%'ContactInputTravelerView$DropDownListMobileNo': emergency_contact.get('mobilephcode', ''),
  		add_key%'ContactInputTravelerView$EmergencyTextBoxMobileNo': emergency_contact.get('mobilenumber', ''),
  		add_key%'ContactInputTravelerView$DropDownListRelationship': emergency_contact.get('relationship', ''),
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
  		'insuranceLinkCancelId': 'InsuranceInputControlAddOnsViewAjax_LinkButtonInsuranceDecline',
  		'radioButtonNoInsuranceId': 'InsuranceInputControlAddOnsViewAjax_RadioButtonNoInsurance',
  		'radioButtonYesInsuranceId': 'InsuranceInputControlAddOnsViewAjax_RadioButtonYesInsurance',
  		'HiddenFieldPageBookingData': booking_data,
  		'__VIEWSTATEGENERATOR': gen,
  		'CONTROLGROUP_OUTERTRAVELER$CONTROLGROUPTRAVELER$ButtonSubmit': 'Continue',
		}
	for idx, details in enumerate(book_dict.get('guestdetails', [])):
	    birth_date = details.get('dob', '')
	    bo_day, bo_month, bo_year = ['']*3
	    if birth_date:
		birth_date = datetime.datetime.strptime(birth_date, '%Y-%m-%d')
        	bo_day, bo_month, bo_year = birth_date.day, birth_date.month, birth_date.year
	    if details:	
	        data.update({
	        add_key%'PassengerInputTravelerView$DropDownListTitle_%s'%idx: details.get('title', ''),
                add_key%'PassengerInputTravelerView$DropDownListGender_%s'%idx:'1',
                add_key%'PassengerInputTravelerView$TextBoxFirstName_%s'%idx: details.get('firstname', ''),
                add_key%'PassengerInputTravelerView$TextBoxLastName_%s'%idx: details.get('lastname', ''),
                add_key%'PassengerInputTravelerView$DropDownListNationality_%s'%idx: book_dict.get('countrycode', ''),
                add_key%'PassengerInputTravelerView$DropDownListBirthDateDay_%s'%idx: str(bo_day),
                add_key%'PassengerInputTravelerView$DropDownListBirthDateMonth_%s'%idx: str(bo_month),
                add_key%'PassengerInputTravelerView$DropDownListBirthDateYear_%s'%idx: str(bo_year),
                add_key%'PassengerInputTravelerView$TextBoxCustomerNumber_%s'%idx: '',
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
	#skipping add-ons
	book_dict = response.meta.get('book_dict', {})
	if response.status != 200:
	    logging.debug('Internal Server Error')
	    self.send_mail('Internal Server Error', json.dumps(book_dict))
	sel = Selector(response)
	ct_price = book_dict.get('cleartripprice', '0')
	total_fare = ''.join(sel.xpath('//div[@class="total-amount-bg-last"]//span[@id="overallTotal"]//text()').extract())
	try:
	    total_fare = int(total_fare.replace(',', '').strip())
	except: total_fare = 0
	if total_fare != 0:
	    tolerance_value = total_fare - int(ct_price.replace(',', '').strip())
	    if total_fare >= ct_price:
	        if tolerance_value >= 2000:
		    is_proceed = 0  #movie it to off line
		else: is_proceed = 1
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
            yield FormRequest(travel_url, callback=self.parse_seat, formdata=data, meta={'book_dict':book_dict})
	else:
	    self.send_mail('Fare increased by AirAsia', json.dumps(book_dict))

    def parse_seat(self, response):
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
		  ('__VIEWSTATE', view_state),
		  ('pageToken', ''),
		  ('ControlGroupUnitMapView$UnitMapViewControl$compartmentDesignatorInput', ''),
		  ('ControlGroupUnitMapView$UnitMapViewControl$deckDesignatorInput', '1'),
		  ('ControlGroupUnitMapView$UnitMapViewControl$tripInput', '0'),
		  ('ControlGroupUnitMapView$UnitMapViewControl$passengerInput', '0'),
		  ('ControlGroupUnitMapView$UnitMapViewControl$HiddenEquipmentConfiguration_0_PassengerNumber_0', ''),
		  ('ControlGroupUnitMapView$UnitMapViewControl$EquipmentConfiguration_0_PassengerNumber_0', ''),
		  ('ControlGroupUnitMapView$UnitMapViewControl$EquipmentConfiguration_0_PassengerNumber_0_HiddenFee', 'NaN'),
		  ('HiddenFieldPageBookingData', bookingdata),
		  ('__VIEWSTATEGENERATOR', gen),
		]

	url = 'https://booking2.airasia.com/UnitMap.aspx'
	yield FormRequest(url, callback=self.parse_unitmap, formdata=data)

    def parse_unitmap(self, response):
	sel = Selector(response)
        import pdb;pdb.set_trace()
	    
	

    def get_lower_fares(self, lst_):
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

    def send_mail(self, sub, error_msg):
	recievers_list = []
	'''
	recievers_list = ['rfan.madha@cleartrip.com',
				'rohit.kulkarni@cleartrip.com',
				'samir.nayak@cleartrip.com',
				'pallavi.khandekar@cleartrip.com',
			     ]
	'''
	recievers_list = ["prasadk@notemonk.com"]
        sender, receivers = 'prasadk@notemonk.com', ','.join(recievers_list)
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
        s.login(sender, 'amma@nanna')
        s.sendmail(sender, (recievers_list + ccing), msg.as_string())
        s.quit()

    def get_date_values(self, date):
	try:
	    date_ = datetime.datetime.strptime(date, '%Y-%m-%d')
            bo_day, bo_month, bo_year = date_.day, date_.month, date_.year
            boarding_date = date_.strftime('%m/%d/%Y')
	except:
	    boarding_date, bo_day, bo_month, bo_year = ['']*4
	return (boarding_date, bo_day, bo_month, bo_year)

    def get_flight_fares(self, dict_):
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

