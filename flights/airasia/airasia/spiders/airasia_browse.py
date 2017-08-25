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
from scrapy.spider import Spider
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from scrapy.http import FormRequest, Request
from email.mime.multipart import MIMEMultipart
from scrapy.selector import Selector
from ConfigParser import SafeConfigParser
from scrapy.xlib.pydispatch import dispatcher
_cfg = SafeConfigParser()
_cfg.read('airline_names.cfg')


class AirAsiaBrowse(Spider):
    name = "airasia_browse"
    start_urls = ["https://booking2.airasia.com/AgentHome.aspx"]

    def __init__(self, *args, **kwargs):
        super(AirAsiaBrowse, self).__init__(*args, **kwargs)
        self.source_name = 'airasia'
        self.cancellation_dict = kwargs.get('jsons', '')
	self.report_insert = 'insert into cancellation_report (sk, airline, cancellation_message, cancellation_status, destination, flight_id, manual_refund_queue, origin, pax_name, payment_status, cancellation_status_mesg, past_dated_booking, refund_computation_queue, tripid, error, created_at, modified_at) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), sk=%s, cancellation_status=%s, cancellation_status_mesg=%s, error=%s, cancellation_message=%s'
	self.insert_error = 'insert into error_report (source, pnr, error_message, created_at, modified_at) values(%s,%s,%s,now(),now()) on duplicate key update modified_at=now()'
	self.update_status_query = 'update cancellation_report set cancellation_status_mesg=%s, payment_status=%s where sk=%s'
	self.conn = MySQLdb.connect(host="localhost", user = "root", db = "TICKETCANCELLATION", charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()
	dispatcher.connect(self.spider_closed, signals.spider_closed)

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
	    self.insert_error_msg('', 'Scraper unable to login AirAsia')
	if self.cancellation_dict:
            try:
                cnl_dict = json.loads(self.cancellation_dict)
            except Exception as e:
                cnl_dict = {}
	        self.insert_error_msg('', e.message)
            if cnl_dict:
                url = 'https://booking2.airasia.com/BookingList.aspx'
                yield Request(url, callback=self.parse_search, dont_filter=True, meta={'cnl_dict':cnl_dict})

    def parse_search(self, response):
        sel = Selector(response)
	cnl_dict = response.meta['cnl_dict']
        view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
        search_data_list.update({'__VIEWSTATE': str(view_state)})
        search_data_list.update({'__VIEWSTATEGENERATOR':str(gen)})
	pnr_no = cnl_dict.get('pnr', '')
	if pnr_no:
            search_data_list.update({'ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword':pnr_no})
            url = "http://booking2.airasia.com/BookingList.aspx"
            yield FormRequest(url, formdata=search_data_list, callback=self.parse_pnr_deatails, meta={'cnl_dict':cnl_dict})

    def parse_pnr_deatails(self, response):
        sel = Selector(response)
        cnl_dict = response.meta['cnl_dict']
        view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
        res_headers = json.dumps(str(response.headers))
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
        cookies = {}
        for i in my_dict.get('Set-Cookie', []):
            data = i.split(';')[0]
            if data:
                try:key, val = data.split('=', 1)
                except: continue
                cookies.update({key.strip():val.strip()})
        nodes = sel.xpath(table_nodes_path)
        if not nodes:
            error_msg = "No details found with PNR %s"%cnl_dict.get('pnr', '')
	    self.insert_error_msg(cnl_dict.get('pnr', ''), error_msg)  
        elif len(nodes) >= 2:
            error_msg = "More than one results found with PNR %s"%cnl_dict.get('pnr', '')
	    self.insert_error_msg(cnl_dict.get('pnr', ''), error_msg)
        elif len(nodes) == 1:
            for node in nodes:
                data_dict = {}
                ids = ''.join(node.xpath(table_row_id_path).extract())
		if not ids:
		    self.insert_error_msg(cnl_dict.get('pnr', ''), 'It does not have modify option')
		    continue
                href = ''.join(node.xpath(table_row_href_path).extract())
                date_lst = node.xpath(flight_date_path).extract()
                origin = ''.join(node.xpath(flight_origin_path).extract())
                desti = ''.join(node.xpath(flight_dest_path).extract())
                book_id = ''.join(node.xpath(flight_booking_id_path).extract())
                guest_name = ''.join(node.xpath(pax_name_path).extract())
                data_dict.update({'origin':origin, 'destination':desti,
                                'booking_id':book_id, 'guest_name': guest_name})
                edit_key = 'Edit:' + ''.join(re.findall('Edit:(.*)', href)).strip(")'")
                cookies.update({'_gali':ids})
                booking_headers.update({'cookie': '_gali=%s'%ids})
                if ids:
                    booking_data_list.update({'__EVENTARGUMENT':edit_key})
                    booking_data_list.update({'__VIEWSTATE':view_state})
                    booking_data_list.update({'ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword':book_id})
                    url = 'https://booking2.airasia.com/BookingList.aspx'
                    yield FormRequest(url, callback=self.parse_details, headers=booking_headers,\
                        formdata=booking_data_list, meta={'data_dict':data_dict, 'cnl_dict':cnl_dict})
	else:
	    error_msg = "No details found with PNR %s"%cnl_dict.get('pnr', '')
	    self.insert_error_msg(cnl_dict.get('pnr', ''), error_msg)


    def parse_details(self, response):
        sel = Selector(response)
        url = 'http://booking2.airasia.com/ChangeItinerary.aspx'
        yield FormRequest.from_response(response, callback=self.parse_next1, \
                meta={'url':url, 'data_dict':response.meta['data_dict'],
                        'cnl_dict':response.meta['cnl_dict']})

    def parse_next1(self, response):
        sel = Selector(response)
        data_dict = response.meta['data_dict']
        cnl_dict = response.meta['cnl_dict']
        cancellation_status = 0
        check_resposne, pnr_status, loc_status, flight_status = False, False, False, False
        airasia_dict, vals = {}, {}
        booking_id = normalize(''.join(sel.xpath(pax_page_booking_id_path).extract()))
        total_paid = normalize(''.join(sel.xpath(pax_page_amount_path).extract()))
        depart = normalize(''.join(sel.xpath(pax_page_depart_loc_path).extract()))
        flight_id = normalize(''.join(sel.xpath(pax_page_flight_id_path).extract()))
        from_airport_details = normalize(' '.join(sel.xpath(pax_page_fr_air_path).extract()))
        to_airport_details = normalize(' '.join(sel.xpath(pax_page_to_air_path).extract()))
        guest_name = normalize('<>'.join(sel.xpath(pax_page_guest_name_path).extract()))
        mobile_no = normalize(''.join(sel.xpath(pax_page_mo_no_path).extract()))
        email = normalize(''.join(sel.xpath(pax_page_email_path).extract()))
        payment_details_lst = normalize(' '.join(sel.xpath(pax_page_payment_path).extract()))
        airasia_depart_date_text = ''.join(re.findall('\d{2} \w+ \d{4}', from_airport_details)).strip()
        airasia_depart_time = ''.join(re.findall('\((\d+:.*)\)', from_airport_details))
        if airasia_depart_date_text:
            try:
                air_depart_date = datetime.datetime.strptime(airasia_depart_date_text, '%d %b %Y').date()
            except:
		self.insert_error_msg(cnl_dict.get('pnr', ''), 'Regex not matched with AirAsia date format')
            try:
                air_depart_date = str(air_depart_date) + ' ' + airasia_depart_time
                air_depart_date = datetime.datetime.strptime(air_depart_date, '%Y-%m-%d %I:%M %p') 
            except: 
		self.insert_error_msg(cnl_dict.get('pnr', ''), 'Regex not matched with AirAsia time format')
        else:
            air_depart_date = ''
	    self.insert_error_msg(cnl_dict.get('pnr', ''), "AirAsia travel date not found")
        airasia_dict.update({'booking_id':booking_id, 'total_paid':total_paid,
                'depart':depart, 'flight_id':flight_id, 'from_airport_details':from_airport_details,
                'to_airport_details':to_airport_details, 'guest_name':guest_name,
                'mobile_no':mobile_no, 'email':email})
        if data_dict.get('booking_id', '') != booking_id:
	    self.insert_error_msg(cnl_dict.get('pnr', ''), 'scraper faild to fetch details')
        else:
            if normalize(cnl_dict.get('pnr', '')) == normalize(booking_id): pnr_status = True
	    input_flt_id = cnl_dict.get('flightid', '').replace(' ', '').replace('-', '').replace(u'\u2010', '').strip()
	    airasia_flt_id = flight_id.replace(' ', '').replace('-', '').replace(u'\u2010', '').strip()
            if normalize(input_flt_id) == normalize(airasia_flt_id):
                flight_status = True
            else:
		 self.insert_error_msg(cnl_dict.get('pnr', ''), 'Flight Id not matched')
            travel_date_status, past_dated_booking, refund_computation_queue, \
				 manual_refund_queue = self.check_travel_date(cnl_dict, air_depart_date)

            loc_status, depart_loc, arrival_loc = self.check_depart_arrival_loc(cnl_dict, depart)
            pax_oneway_status, pax_return_status, ignore_oneway_pax_check, \
			ignore_return_pax_check = self.check_pax_status(cnl_dict, guest_name)
            cancle_msg, pax_count, pax_cnl_status = self.get_cancellation_type(cnl_dict)
            if past_dated_booking: past_dated = 1
            else: past_dated = '0'
            if refund_computation_queue: refund_com_q = 1
            else: refund_com_q = 0
            if not travel_date_status:
		self.insert_error_msg(cnl_dict.get('pnr', ''), 'itinerary does not matched')
            if flight_status and pnr_status and loc_status and travel_date_status and manual_refund_queue==0:
		if ignore_oneway_pax_check == 1 and ignore_return_pax_check == 1:
                    cancellation_status = '0'
		    self.insert_error_msg(cnl_dict.get('pnr', ''), 'Two Pax presented with same name')
		else:
		    cancellation_status = 1
		    self.insert_error_msg(cnl_dict.get('pnr', ''), 'Pax name not matched with AirAsia')
	    if pax_cnl_status == 0: cancellation_status = 0
	    view_state = ''.join(sel.xpath(view_state_path).extract())
            gen = ''.join(sel.xpath(view_generator_path).extract())
	    cancel_data = { 
  			'__EVENTTARGET':'ChangeControl$LinkButtonCancelFlight',
  			'__EVENTARGUMENT':'',
 	 		'__VIEWSTATE':view_state,
  			'pageToken':'',
  			'MemberLoginChangeItineraryView2$TextBoxUserID':'',
  			'hdRememberMeEmail':'',
  			'MemberLoginChangeItineraryView2$PasswordFieldPassword':'',
  			'memberLogin_chk_RememberMe':'on',
  			'HiddenFieldPageBookingData':normalize(booking_id),
  			'__VIEWSTATEGENERATOR':gen,
			}
	    cancel_url = 'https://booking2.airasia.com/ChangeItinerary.aspx'
	    insert_vals = (normalize(booking_id), cnl_dict.get('airline', ''), normalize(cancle_msg),
                                cancellation_status, arrival_loc.strip(), flight_id, manual_refund_queue,
                                depart_loc.strip(), guest_name, payment_details_lst, 'going to cancellation', past_dated, refund_com_q,
                                cnl_dict.get('tripid', ''), '',
                                normalize(booking_id), cancellation_status, 'going to cancellation', '',
                                normalize(cancle_msg),
                           )
	    import pdb;pdb.set_trace()
	    if cancellation_status == 1:
	        yield FormRequest(cancel_url, callback=self.parse_cancel_pnr, formdata=cancel_data,\
				 method="POST", meta={'view_state':view_state})
            self.cur.execute(self.report_insert, insert_vals)
            self.conn.commit()


    def parse_cancel_pnr(self, response):
	sel = Selector(response)
	prv_v_state = response.meta['view_state']
        gen = ''.join(sel.xpath(view_generator_path).extract())
	cnl_form_data = {
  		'__EVENTTARGET':'ControlGroupFlightCancelView$FlightDisplayFlightCancelView$LinkButtonSubmit',
  		'__EVENTARGUMENT':'',
  		'__VIEWSTATE':normalize(prv_v_state),
  		'pageToken':'',
  		'pageToken':'',
  		'eventTarget':'ControlGroupFlightCancelView$FlightDisplayFlightCancelView$LinkButtonSubmit',
  		'eventArgument':'',
  		'viewState':normalize(prv_v_state),
  		'ControlGroupFlightCancelView$FlightDisplayFlightCancelView$CheckBoxCancel_0':'on',
  		'ControlGroupFlightCancelView$FlightDisplayFlightCancelView$OthersBox':'',
  		'__VIEWSTATEGENERATOR':normalize(gen),
		}
	url = 'https://booking2.airasia.com/FlightCancel.aspx'
	yield FormRequest(url, callback=self.parse_final_cancellation, formdata=cnl_form_data)

    def parse_final_cancellation(self, response):
	sel = Selector(response)
	status = sel.xpath('//div[@id="cancelContent"]//text').extract()
	fin_cnl_status = normalize(''.join(sel.xpath('//div[@id="cancelContent"]//text()').extract()))
	cnl_pnr = normalize(''.join(sel.xpath('//span[@id="OptionalHeaderContent_lblBookingNumber"]//text()').extract()))
	pay_due_amount = normalize(''.join(sel.xpath('//div[contains(text(), "Payment amount due")]\
			/../following-sibling::td/div/text()').extract()))
	up_vals = (fin_cnl_status, pay_due_amount, cnl_pnr)
	import pdb;pdb.set_trace()
	self.cur.execute(self.update_status_query, up_vals)
	self.conn.commit()
	

    def check_travel_date(self, cnl_dict, airasia_date):
        dep_date = cnl_dict.get('departuredatetime', '')
        pax_cnl_date = cnl_dict.get('cancellationdatetime', '')
        a_day, a_month, a_year, a_minute, a_hour = airasia_date.day, \
                airasia_date.month, airasia_date.year, airasia_date.minute, airasia_date.hour
	cur_date_ = datetime.datetime.now()
	
        past_dated_booking, refund_computation_queue, tr_datetime_cnl_status = False, False, False
        if not pax_cnl_date:
	    self.insert_error_msg(cnl_dict.get('pnr', ''), 'cancellation date not found in input')
            return (False, False)
        if not dep_date:
	    self.insert_error_msg(cnl_dict.get('pnr', ''), 'Departure date not found in input')
            return (False, False)
        else:
	    manual_refund_queue = 0
            cnt_date = datetime.datetime.strptime(dep_date, '%Y-%m-%d %H:%M:%S')
            pax_cnl_date = datetime.datetime.strptime(pax_cnl_date, '%Y-%m-%d %H:%M:%S')
            if cnt_date.day == a_day and cnt_date.month == a_month and cnt_date.year == a_year and \
                cnt_date.minute == a_minute and cnt_date.hour == a_hour:
                travel_datetime_status = True
            else: travel_datetime_status = False
            if pax_cnl_date:
                if pax_cnl_date.date() > airasia_date.date():
                    past_dated_booking = True
	    diff_bw_curdate_airdate = pax_cnl_date - airasia_date #time diff b/w current date to flight 
	    ca_diff_days = diff_bw_curdate_airdate.days
	    ca_diff_second = diff_bw_curdate_airdate.seconds
	    if ca_diff_days == 0:
		if ca_diff_second <= 14400:
		    refund_computation_queue = True
		else:
		    tr_datetime_cnl_status = True
	    if not travel_datetime_status:
		if tr_datetime_cnl_status:
		    manual_refund_queue = 1
		    travel_datetime_status = True
            return (travel_datetime_status, past_dated_booking, refund_computation_queue, manual_refund_queue)
                
    def check_pax_status(self, cnl_dict, pax_names):
        pax_oneway_status, pax_return_status = False, False
        p_names = cnl_dict.get('cancellationdetails', {}).get('oneway', {})
        p_r_names = cnl_dict.get('cancellationdetails', {}).get('return', {})
        oneway_pax_lst = p_names.get('audlt', []) + p_names.get('children', []) + p_names.get('infants', [])
        return_pax_lst = p_r_names.get('audlt', []) + p_r_names.get('children', []) + p_r_names.get('infants', [])
        for pax in oneway_pax_lst:
            if normalize(pax.lower()) in normalize(pax_names.lower()):
                pax_oneway_status = True
        for pax in return_pax_lst:
            if normalize(pax.lower()) in normalize(pax_names.lower()):
                pax_return_status = True
	test_oneway_pax_lst = []
	for i in oneway_pax_lst:
	    i = i.replace('Mrs.', '').replace('Mr.', '')\
		.replace('Ms.', '').replace('Miss.', '').strip()
	    test_oneway_pax_lst.append(i)
	test_return_pax_lst = []
        for i in return_pax_lst:
            i = i.replace('Mrs.', '').replace('Mr.', '')\
                .replace('Ms.', '').replace('Miss.', '').strip()
            test_return_pax_lst.append(i)
	if len(test_oneway_pax_lst) != len(set(test_oneway_pax_lst)):
	    ignore_oneway_pax_check = 1
	else: ignore_oneway_pax_check = 0
	if len(test_return_pax_lst) != len(set(test_return_pax_lst)):
	    ignore_return_pax_check = 1
	else: ignore_return_pax_check = 0
        return (pax_oneway_status, pax_return_status, ignore_oneway_pax_check, ignore_return_pax_check)

    def get_cancellation_type(self, cnl_dict):
        full, partial = ['']*2
        pax_booked = cnl_dict.get('paxdetails', {}).get('oneway', {})
        pax_cancle = cnl_dict.get('cancellationdetails', {}).get('oneway', {})
        pax_booked_return = cnl_dict.get('paxdetails', {}).get('return', {})
        pax_cancled_return = cnl_dict.get('cancellationdetails', {}).get('return', {})
        total_pax_oneway_count = len(pax_booked.get('audlt', [])) + \
                len(pax_booked.get('children', [])) + len(pax_booked.get('infants', []))
        total_pax_oneway_cancled = len(pax_cancle.get('audlt', [])) + \
                len(pax_cancle.get('children', [])) + len(pax_cancle.get('infants', []))
        total_pax_return_count = len(pax_booked_return.get('audlt', []))\
                                + len(pax_booked_return.get('children', []))\
                                + len(pax_booked_return.get('infants', []))
        total_pax_return_cancled = len(pax_cancled_return.get('audlt', []))\
                                + len(pax_cancled_return.get('children', []))\
                                + len(pax_cancled_return.get('infants', []))
	if total_pax_oneway_cancled == 0 and total_pax_return_cancled == 0:
	    return ("No cancellations found", total_pax_oneway_cancled)
 
        if total_pax_return_count == 0 and total_pax_oneway_cancled !=0:
	    if total_pax_oneway_count == 1 and total_pax_oneway_cancled == 1:
		return ("One way single pax cancellation", total_pax_oneway_cancled, 1)

            if total_pax_oneway_count == total_pax_oneway_cancled:
                return ("One way  multiple pax full cancellation", total_pax_oneway_cancled, 1)

            elif total_pax_oneway_count > total_pax_oneway_cancled:
                return (" One way Split PNR partial pax cancellation", total_pax_oneway_cancled, 0)
            else:
		self.send_mail("scraper faild to fetch cancellation_type on oneway-trip", '')
		self.insert_error_msg(cnl_dict.get('pnr', ''), 'scraper faild to fetch cancellation_type on oneway-trip')

        else:
	    
            if (total_pax_oneway_count == total_pax_oneway_cancled) and (total_pax_return_cancled == 0):
                return ("should do oneway trip full cancellation but not return trip", total_pax_oneway_cancled, 1)

            elif (total_pax_oneway_cancled == 0) and (total_pax_return_count == total_pax_return_cancled):
                return ("should do return trip full cancellation but not oneway trip", total_pax_return_cancled, 0)

            elif (total_pax_oneway_count > total_pax_oneway_cancled) and (total_pax_return_cancled == 0):
                return ("should do oneway trip partial cancellation but not return trip", total_pax_oneway_cancled, 0)

            elif (total_pax_oneway_cancled == 0) and (total_pax_return_count > total_pax_return_cancled):
                return ("should do return trip partial cancellation but not oneway trip", total_pax_return_cancled, 0)

            elif (total_pax_oneway_count == total_pax_oneway_cancled) and (total_pax_return_count == total_pax_return_cancled):
                return ("should do both return and oneway trip full sector cancellation", total_pax_oneway_cancled, 1)

	    elif (total_pax_oneway_count > total_pax_oneway_cancled) and (total_pax_return_count > total_pax_return_cancled):
		return ("return trip partial pax cancellation", total_pax_oneway_cancled+total_pax_return_cancled, 0)

            else:
                self.send_mail("scraper faild to fetch cancellation_type on round-trip", '')
		self.insert_error_msg(cnl_dict.get('pnr', ''), 'scraper faild to fetch cancellation_type on round-trip')

    def check_depart_arrival_loc(self, cnl_dict, air_data):
        from_, to_ = [''] *2
        from_status, to_status = False, False
        if '-' in air_data:
            from_, to_ = air_data.split('-')
        if normalize(cnl_dict.get('origin', '').lower()) == normalize(from_.lower()):
            from_status = True
        if  normalize(cnl_dict.get('destination', '').lower()) == normalize(to_.lower()):
            to_status = True
        if from_status and to_status:
            status = True
        else: status = False
        return (status, from_, to_)

    def send_mail(self, sub, error_msg):
	recievers_list = []
	if 'Scraper unable to login AirAsia' == sub:
	    recievers_list = ['Ivy.pinto@cleartrip.com',
				'Dhruvi.kothari@cleartrip.com',
				'Tauseef.farooqui@cleartrip.com',
				'Satish.desai@cleartrip.com',
				'Sheba.antao@cleartrip.com',
			     ]
	else:
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

    def insert_error_msg(self, pnr, msg):
	vals = ('airasia', pnr, msg)
        self.cur.execute(self.insert_error, vals)
	self.conn.commit()
