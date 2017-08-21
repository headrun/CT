import re
import json
import md5
import smtplib
import MySQLdb
import datetime
import smtplib,ssl
from email import encoders
from airasia_xpaths import *
from ast import literal_eval
#from datetime import datetime
from scrapy.spider import Spider
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from scrapy.http import FormRequest, Request
from email.mime.multipart import MIMEMultipart
from scrapy.selector import Selector
from ConfigParser import SafeConfigParser
_cfg = SafeConfigParser()
_cfg.read('airline_names.cfg')


class AirAsiaBrowse(Spider):
    name = "airasia_browse"
    start_urls = ["https://booking2.airasia.com/AgentHome.aspx"]

    def __init__(self, *args, **kwargs):
        super(AirAsiaBrowse, self).__init__(*args, **kwargs)
        self.source_name = 'airasia'
	self.error_msg = ''
	self.out_put_file = open('airasia_cancellation_output.txt', 'ab+')
	self.cancellation_file = kwargs.get('cancellation_file', '')
	self.cancellation_list = open(self.cancellation_file, 'r+').readlines()

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
        url = 'https://booking2.airasia.com/BookingList.aspx'
        yield Request(url, callback=self.parse_search)

    def parse_search(self, response):
        sel = Selector(response)
	view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
	search_data_list.append(('__VIEWSTATE', str(view_state)))
	search_data_list.append(('__VIEWSTATEGENERATOR', str(gen)))
	for cancle_rec in self.cancellation_list:
	    try:
	        cnl_dict = json.loads(cancle_rec.strip('\n'))
	    except Exception as e:
		cnl_dict = {}
		self.send_mail("Failed to load input dict", e.message)
	    if cnl_dict:
		self.cnt_dict = cnl_dict
		pnr_no = cnl_dict.get('pnr', '')
		if pnr_no:
		    search_data_list.append(('ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword', pnr_no))
	            url = "http://booking2.airasia.com/BookingList.aspx"
	            yield FormRequest(url, formdata=search_data_list, callback=self.parse_pnr_deatails, meta={'cnl_dict':cnl_dict})
		    search_data_list.remove(('ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword', pnr_no))

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
                try : key, val = data.split('=', 1)
                except : import pdb;pdb.set_trace()
                cookies.update({key.strip():val.strip()})
	nodes = sel.xpath(table_nodes_path)
	if not nodes or len(nodes)==1:
	    error_msg = "No details found with PNR %s"%cnl_dict.get('pnr', '')
	    self.send_mail(error_msg, '')    
	elif len(nodes) > 2:
	    error_msg = "More than one results found with PNR %s"%cnl_dict.get('pnr', '')
	    self.send_mail(error_msg, '')
	elif len(nodes) == 2:
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
	        edit_key = 'Edit:' + ''.join(re.findall('Edit:(.*)', href)).strip(")'")
	        cookies.update({'_gali':ids})
	        booking_headers.update({'cookie': '_gali=%s'%ids})
	        if ids:
		    booking_data_list.append(('__EVENTARGUMENT', edit_key))
		    booking_data_list.append(('__VIEWSTATE', view_state))
                    booking_data_list.append(('ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword', book_id))
		    url = 'https://booking2.airasia.com/BookingList.aspx'
	            yield FormRequest(url, callback=self.parse_details, headers=booking_headers,\
			formdata=booking_data_list, meta={'data_dict':data_dict, 'cnl_dict':cnl_dict})
		    booking_data_list.remove(('__EVENTARGUMENT', edit_key))
		    booking_data_list.remove(('__VIEWSTATE', view_state))
                    booking_data_list.remove(('ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword', book_id))

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
		self.send_mail("Regx not matched with AirAsia date format", airasia_depart_date_text)
	    try:
		air_depart_date = str(air_depart_date) + ' ' + airasia_depart_time
		air_depart_date = datetime.datetime.strptime(air_depart_date, '%Y-%m-%d %I:%M %p') 
	    except: 
		self.send_mail("Regx not matched with AirAsia time format", airasia_depart_date_text)
	else:
	    air_depart_date = ''
	    self.send_mail("AirAsia travel date not found PNR-%s"%data_dict.get('booking_id', ''), \
				airasia_depart_date_text)
	airasia_dict.update({'booking_id':booking_id, 'total_paid':total_paid,
		'depart':depart, 'flight_id':flight_id, 'from_airport_details':from_airport_details,
		'to_airport_details':to_airport_details, 'guest_name':guest_name,
		'mobile_no':mobile_no, 'email':email})
	if data_dict.get('booking_id', '') != booking_id:
	    self.send_mail("scraper faild to fetch details", "PNR - %s"%(data_dict.get('booking_id', '')))
	else:
	    if normalize(cnl_dict.get('pnr', '')) == normalize(booking_id): pnr_status = True
	    if normalize(cnl_dict.get('flightId', '')) == normalize(flight_id):
		flight_status = True
	    else:
		self.send_mail("Flight Id not matched for PNR-%s"%booking_id, \
			'AirAsia Flight Id %s'%(normalize(flight_id)))
	    travel_date_status, past_dated_booking, refund_computation_queue = self.check_travel_date(cnl_dict, air_depart_date)
	    loc_status, depart_loc, arrival_loc = self.check_depart_arrival_loc(cnl_dict, depart)
	    pax_oneway_status, pax_return_status = self.check_pax_status(cnl_dict, guest_name)
	    cancle_msg, pax_count = self.get_cancellation_type(cnl_dict)
	    if past_dated_booking: past_dated = 1
	    else: past_dated = '0'
	    if refund_computation_queue: refund_com_q = 1
	    else: refund_com_q = 0
	    if not travel_date_status:
		self.send_mail("itinerary does not match PNR-%s"%booking_id, '')
	    if flight_status and pnr_status and loc_status and travel_date_status:
		if pax_oneway_status or pax_return_status:
		    cancellation_status = '1'
	    vals.update({'pnr':normalize(booking_id), 'origin':depart_loc.strip(),
		    		'destination':arrival_loc.strip(), 'tripid':cnl_dict.get('tripid', ''),
		    		'flightid':flight_id, 'payment_status': payment_details_lst,
				'cancellation_massage': cancle_msg, 'cancellation_status':cancellation_status,
				'pax_name':guest_name, 'airline':cnl_dict.get('airline', ''),
				'Past_dated_booking':past_dated,'refund_computation_queue': refund_com_q,
			      })
	    self.out_put_file.write(json.dumps(vals))

    def check_travel_date(self, cnl_dict, airasia_date):
	dep_date = cnl_dict.get('DepartureDateTime', '')
	pax_cnl_date = cnl_dict.get('cancellationdatetime', '')
	a_day, a_month, a_year, a_minute, a_hour = airasia_date.day, \
		airasia_date.month, airasia_date.year, airasia_date.minute, airasia_date.hour
	past_dated_booking, refund_computation_queue = False, False
	if not pax_cnl_date:
	    self.send_mail("cancellation date not found in input", '')
	    return (False, False)
	if not dep_date:
	    self.send_mail("Departure date not found in input", '')
	    return (False, False)
	else:
	    cnt_date = datetime.datetime.strptime(dep_date, '%Y-%m-%d %H:%M:%S')
	    pax_cnl_date = datetime.datetime.strptime(pax_cnl_date, '%Y-%m-%d %H:%M:%S')
	    if cnt_date.day == a_day and cnt_date.month == a_month and cnt_date.year == a_year and \
		cnt_date.minute == a_minute and cnt_date.hour == a_hour:
		travel_date_status = True
	    else: travel_date_status = False
	    if pax_cnl_date:
		if pax_cnl_date.date() > airasia_date.date():
		    past_dated_booking = True
	    time_diff = pax_cnl_date - airasia_date
	    diff_days = time_diff.days
	    diff_seconds = time_diff.seconds
	    if diff_days == 0 and diff_seconds < 14400:
		refund_computation_queue = True
		print "Movie it refund computation queue"
	    return (travel_date_status, past_dated_booking, refund_computation_queue)
		
    def check_pax_status(self, cnl_dict, pax_names):
        pax_oneway_status, pax_return_status = False, False
	p_names = cnl_dict.get('cancellationdetails', {}).get('oneway', {})
	p_r_names = cnl_dict.get('cancellationdetails', {}).get('return', {})
	oneway_pax_lst = p_names.get('Audlt', []) + p_names.get('Children', []) + p_names.get('Infants', [])
	return_pax_lst = p_r_names.get('Audlt', []) + p_r_names.get('Children', []) + p_r_names.get('Infants', [])
	for pax in oneway_pax_lst:
	    if normalize(pax.lower()) in normalize(pax_names.lower()):
		pax_oneway_status = True
	for pax in return_pax_lst:
	    if normalize(pax.lower()) in normalize(pax_names.lower()):
		pax_return_status = True
	return (pax_oneway_status, pax_return_status)

    def get_cancellation_type(self, cnl_dict):
	full, partial = ['']*2
	pax_booked = cnl_dict.get('paxdetails', {}).get('oneway', {})
	pax_cancle = cnl_dict.get('cancellationdetails', {}).get('oneway', {})
	pax_booked_return = cnl_dict.get('paxdetails', {}).get('return', {})
	pax_cancled_return = cnl_dict.get('cancellationdetails', {}).get('return', {})
	total_pax_oneway_count = len(pax_booked.get('Audlt', [])) + \
		len(pax_booked.get('Children', [])) + len(pax_booked.get('Infants', []))
	total_pax_oneway_cancled = len(pax_cancle.get('Audlt', [])) + \
		len(pax_cancle.get('Children', [])) + len(pax_cancle.get('Infants', []))
	total_pax_return_count = len(pax_booked_return.get('Audlt', []))\
				+ len(pax_booked_return.get('Children', []))\
				+ len(pax_booked_return.get('Infants', []))
	total_pax_return_cancled = len(pax_cancled_return.get('Audlt', []))\
                                + len(pax_cancled_return.get('Children', []))\
                                + len(pax_cancled_return.get('Infants', []))
	if (total_pax_return_count) == 0:
	    if total_pax_oneway_count == total_pax_oneway_cancled:
		return ("One-way trip full cancellation", total_pax_oneway_cancled)
	    elif total_pax_oneway_count > total_pax_oneway_cancled:
		return (" One-way Split PNR partial pax cancellation", total_pax_oneway_cancled)
	    else: self.send_mail("scraper faild to fetch cancellation_type on oneway-trip", '') 
	else:
	    if (total_pax_oneway_count == total_pax_oneway_cancled) and (total_pax_return_cancled == 0):
		return ("should do oneway trip full cancellation but not return trip", total_pax_oneway_cancled)

	    elif (total_pax_oneway_cancled == 0) and (total_pax_return_count == total_pax_return_cancled):
		return ("should do return trip full cancellation but not oneway trip", total_pax_return_cancled)

	    elif (total_pax_oneway_count > total_pax_oneway_cancled) and (total_pax_return_cancled == 0):
		return ("should do oneway trip partial cancellation but not return trip", total_pax_oneway_cancled)

	    elif (total_pax_oneway_cancled == 0) and (total_pax_return_count > total_pax_return_cancled):
		return ("should do return trip partial cancellation but not oneway trip", total_pax_return_cancled)

	    elif (total_pax_oneway_count == total_pax_oneway_cancled) and (total_pax_return_count == total_pax_return_cancled):
		return ("should do both return and oneway trip full sector cancellation", total_pax_oneway_cancled)
	    else:
		self.send_mail("scraper faild to fetch cancellation_type on round-trip", '')

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
        recievers_list = ["prasadk@notemonk.com"]
        sender, receivers  = 'prasadk@notemonk.com', ','.join(recievers_list)
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
