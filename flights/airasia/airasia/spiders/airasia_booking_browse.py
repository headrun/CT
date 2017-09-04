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
_cfg = SafeConfigParser()
_cfg.read('airline_names.cfg')


class AirAsiaBookingBrowse(Spider):
    name = "airasiabooking_browse"
    start_urls = ["https://booking2.airasia.com/AgentHome.aspx"]

    def __init__(self, *args, **kwargs):
        super(AirAsiaBookingBrowse, self).__init__(*args, **kwargs)
        self.source_name = 'airasia'
        self.booking_dict = kwargs.get('jsons', {})

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
	#if response.status !=200 and not manage_booking:
	    #self.insert_error_msg('', 'Scraper unable to login AirAsia')
	if self.booking_dict:
            try:
                book_dict = json.loads(self.booking_dict)
		#cnl_dict = eval(self.booking_dict)
            except Exception as e:
                book_dict = {}
	        #self.insert_error_msg('', e.message)
            if book_dict:
                url = 'https://booking2.airasia.com/BookingList.aspx'
                yield Request(url, callback=self.parse_search, dont_filter=True, meta={'book_dict':book_dict})

    def parse_search(self, response):
        sel = Selector(response)
	book_dict = response.meta['book_dict']
        view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
        search_data_list.update({'__VIEWSTATE': str(view_state)})
        search_data_list.update({'__VIEWSTATEGENERATOR':str(gen)})
	#pnr_no = cnl_dict.get('pnr', '')
	pnr_no = 'KEYWORD'
	if pnr_no:
            search_data_list.update({'ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword':pnr_no})
            url = "http://booking2.airasia.com/BookingList.aspx"
            yield FormRequest(url, formdata=search_data_list, callback=self.parse_pnr_deatails, meta={'book_dict':book_dict})

    def parse_pnr_deatails(self, response):
        sel = Selector(response)
        book_dict = response.meta['book_dict']
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
	    yield Request(search_flights, callback=self.parse_search_flights, headers=headers, dont_filter=True, meta={'book_dict':book_dict})

    def parse_search_flights(self, response):
	sel = Selector(response)
	book_dict = response.meta['book_dict']
	view_state = normalize(''.join(sel.xpath(view_state_path).extract()))
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
	origin = book_dict.get('origin', '')
	dest = book_dict.get('destination', '')
	trip_type = book_dict.get('triptype', '')
	oneway_date = book_dict.get('oneway_date', '')
	return_date = book_dict.get('return_date', '')
	oneway_date_ = datetime.datetime.strptime(oneway_date, '%Y-%m-%d')
	bo_day, bo_month, bo_year = oneway_date_.day, oneway_date_.month, oneway_date_.year
	boarding_date = oneway_date_.strftime('%m/%d/%Y')
	return_date_ = datetime.datetime.strptime(return_date, '%Y-%m-%d')
	re_day, re_month, re_year = return_date_.day, return_date_.month, return_date_.year,
	return_date = return_date_.strftime('%m/%d/%Y')
	no_of_adt = book_dict.get('pax_details', {}).get('adult', '0')
	import pdb;pdb.set_trace()
	no_of_chd = book_dict.get('pax_details', {}).get('child', '0')
	no_of_infant = book_dict.get('pax_details', {}).get('infant', '0')
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
  		#'oneWayOnly':'1',
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

			
			'date_picker': str(boarding_date), #'09/11/2017',
        	        'date_picker': '',
	                'date_picker': str(return_date), #'09/05/2017',
                	'date_picker': '',

			'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListMarketDay1': str(bo_day),
                	'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListMarketMonth1': '%s-%s'%(bo_year, bo_month),
                	'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListMarketDay2': str(re_day),
                	'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListMarketMonth2': '%s-%s'%(re_year,re_month),
                	'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListPassengerType_ADT': no_of_adt,
                	'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListPassengerType_CHD': no_of_chd,
                	'ControlGroupSearchView$AvailabilitySearchInputSearchView$DropDownListPassengerType_INFANT': no_of_infant,

			})
	import pdb;pdb.set_trace()	
	select_url = 'http://booking2.airasia.com/Search.aspx'
	yield FormRequest(select_url, callback=self.parse_select_fare, formdata=form_data, meta={'form_data':form_data})

    def parse_select_fare(self, response):
	sel = Selector(response)
	import pdb;pdb.set_trace()
	form_data = response.meta['form_data']
	view_state = normalize(''.join(sel.xpath(view_state_path).extract()))
        gen = normalize(''.join(sel.xpath(view_generator_path).extract()))
	low_lst, regular_lst, premium_lst = [], [], []
	fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price = [''] * 4
	table_nodes = sel.xpath('//table[@id="fareTable1_4"]//tr')
	field_tab_index = ''.join(sel.xpath('//div[@class="tabsHeader"][1]//input//@id').extract())
	field_tab_value = ''.join(sel.xpath('//div[@class="tabsHeader"][1]//input//@value').extract())
	member_time_zone = ''.join(sel.xpath('//input[@id="MemberLoginSelectView_HFTimeZone"]/@value').extract())
	for node in table_nodes:
	    for i in range(2, 5):
	        fare_id = ''.join(node.xpath('.//td[%s]//div[@id="fareRadio"]//input/@id'%i).extract())
	        fare_name = ''.join(node.xpath('.//td[%s]//div[@id="fareRadio"]//input/@name'%i).extract())
	        fare_vlue = ''.join(node.xpath('.//td[%s]//div[@id="fareRadio"]//input/@value'%i).extract())
	        price = '<>'.join(node.xpath('.//td[%s]//div[@class="price"]//div[@id="originalLowestFare"]//text()'%i).extract())
		if fare_id:
		    if i == 2:
		        low_lst.append((fare_id, fare_name, fare_vlue, price))
		    elif i == 3:
		        regular_lst.append((fare_id, fare_name, fare_vlue, price))
		    elif i == 4:
		        premium_lst.append((fare_id, fare_name, fare_vlue, price))
	if low_lst:
	    fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price = self.get_lower_fares(low_lst)
	elif regular_lst:
	     fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price = self.get_lower_fares(regular_lst)
	elif premium_lst:
	    fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price = self.get_lower_fares(premium_lst)
	if fin_fare_vlue:
	    form_data.update({field_tab_index:field_tab_value,
			     fin_fare_name:fin_fare_vlue,
			     'ControlGroupSelectView$SpecialNeedsInputSelectView$RadioButtonWCHYESNO':'RadioButtonWCHNO',
			     '__VIEWSTATEGENERATOR':gen,
			     '__VIEWSTATE':view_state,
			     'ControlGroupSelectView$ButtonSubmit': 'Continue',
			     'MemberLoginSelectView$TextBoxUserID':'',
  			     'hdRememberMeEmail': '',
  			     'MemberLoginSelectView$PasswordFieldPassword': '',
  			     'memberLogin_chk_RememberMe': 'on',
  			     'MemberLoginSelectView$HFTimeZone': '330',
			})
	    url = 'https://booking2.airasia.com/Select.aspx'
	    yield FormRequest(url, callback=self.parse_tevel, formdata=form_data, meta={'form_data':form_data}, method="POST")

    def parse_tevel(self, response):
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
		    i = int(i.replace(',', '').strip())
		    price_int += i
		lower_dict.update({price_int:(fare_id, fare_name, fare_vlue, price_int)})
	min_price = min(lower_dict.keys())
	lower_details = lower_dict.get(min_price, ['']*4)
	return lower_details

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
