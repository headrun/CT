import re
import json
import md5
import smtplib
import MySQLdb
import datetime
import smtplib, ssl
from email import encoders
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

import base64
from scrapy_splash import SplashRequest, SplashFormRequest
view_state_path = '//input[@id="viewState"]/@value'

view_generator_path = '//input[@id="__VIEWSTATEGENERATOR"]/@value'

class AirAsiaBookBrowse(Spider):
    name = "airasiamulti_browse"
    start_urls = ["http://booking2.airasia.com/Search.aspx"]
    handle_httpstatus_list = [404, 500]
    def __init__(self, *args, **kwargs):
        super(AirAsiaBookBrowse, self).__init__(*args, **kwargs)
	self.price_patt = re.compile('\d+')


    def parse(self, response):
        sel = Selector(response)
        view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
	res_headers = json.dumps(str(response.request.headers))
        res_headers = json.loads(res_headers)
        my_dict = literal_eval(res_headers)
        cookies = {}
        for i in my_dict.get('Cookie', []):
            data = i.split(';')[0]
            if data:
                try : key, val = data.split('=', 1)
                except : import pdb;pdb.set_trace()
                cookies.update({key.strip():val.strip()})
	cookies.update({'_gali': 'ControlGroupSearchView_AvailabilitySearchInputSearchView_MultiCity'})
	yield SplashRequest('http://booking2.airasia.com/MultiCitySearch.aspx', callback=self.parse_next1, args={'wait': 0.5}, meta={'v':view_state, 'g':gen})

    def parse_next1(self, response):
	sel = Selector(response)
	view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
	cookies = {
			'_gali': 'ControlGroupMultiCitySearchView_ButtonSubmit',
		  }

	data = [
	  ('__EVENTTARGET', ''),
	  ('__EVENTARGUMENT', ''),
	  ('__VIEWSTATE', view_state),
	  ('pageToken', ''),
	  ('MemberLoginMultiCitySearchView$TextBoxUserID', ''),
	  ('hdRememberMeEmail', ''),
	  ('MemberLoginMultiCitySearchView$PasswordFieldPassword', ''),
	  ('memberLogin_chk_RememberMe', 'on'),
	  ('MemberLoginMultiCitySearchView$HFTimeZone', '330'),
	  ('ControlGroupSearchView$AKMultiCityAvailabilitySearchMultiCitySearchView$RadioButtonMarketStructure', 'MultiCity'),
	  ('AKMultiCityAvailabilitySearch.DateMarkets[0].OriginStation.MarketCode', 'MEL'),
	  ('AKMultiCityAvailabilitySearch.DateMarkets[0].DestinationStation.MarketCode', 'KUL'),
	  ('AKMultiCityAvailabilitySearch.DateMarkets[0].DepartureDate', '10/16/2017'),
	  ('AKMultiCityAvailabilitySearch.DateMarkets[1].OriginStation.MarketCode', 'KUL'),
	  ('AKMultiCityAvailabilitySearch.DateMarkets[1].DestinationStation.MarketCode', 'DEL'),
	  ('AKMultiCityAvailabilitySearch.DateMarkets[1].DepartureDate', '11/13/2017'),
	  ('AKMultiCityAvailabilitySearch.DateMarkets[2].OriginStation.MarketCode', 'DEL'),
	  ('AKMultiCityAvailabilitySearch.DateMarkets[2].DestinationStation.MarketCode', 'SYD'),
	  ('AKMultiCityAvailabilitySearch.DateMarkets[2].DepartureDate', '12/18/2017'),
	  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$TextBoxMarketOrigin1', 'MEL'),
	  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$DropDownListMarketDay1', '16'),
	  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$DropDownListMarketMonth1', '2017-10'),
	  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$TextBoxMarketOrigin2', 'KUL'),
	  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$DropDownListMarketDay2', '13'),
	  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$DropDownListMarketMonth2', '2017-11'),
	  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$TextBoxMarketOrigin3', 'DEL'),
	  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$DropDownListMarketDay3', '18'),
	  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$DropDownListMarketMonth3', '2017-12'),
	  ('Search.RetainedJourneyFareSellKeys', ''),
	  ('AKMultiCityAvailabilitySearch.PaxTypeCountDictionary[\'ADT\']', '1'),
	  ('AKMultiCityAvailabilitySearch.PaxTypeCountDictionary[\'CHD\']', '0'),
	  ('AKMultiCityAvailabilitySearch.PaxTypeCountDictionary[\'INFANT\']', '0'),
	  ('ControlGroupMultiCitySearchView$MultiCurrencyConversionViewMultiCitySearchView$DropDownListCurrency', 'default'),
	  ('__VIEWSTATEGENERATOR', gen),
	  ('ControlGroupMultiCitySearchView$ButtonSubmit', 'Search'),
	]

	'''
	data = [
		  ('__EVENTTARGET', ''),
		  ('__EVENTARGUMENT', ''),
		  ('__VIEWSTATE', view_state),
		  ('pageToken', ''),
		  ('ControlGroupSearchView$AKMultiCityAvailabilitySearchMultiCitySearchView$RadioButtonMarketStructure', 'MultiCity'),
		  ('AKMultiCityAvailabilitySearch.DateMarkets[0].OriginStation.MarketCode', 'DEL'),
		  ('AKMultiCityAvailabilitySearch.DateMarkets[0].DestinationStation.MarketCode', 'KUL'),
		  ('AKMultiCityAvailabilitySearch.DateMarkets[0].DepartureDate', '09/17/2017'),
		  ('AKMultiCityAvailabilitySearch.DateMarkets[1].OriginStation.MarketCode', 'KUL'),
		  ('AKMultiCityAvailabilitySearch.DateMarkets[1].DestinationStation.MarketCode', 'SYD'),
		  ('AKMultiCityAvailabilitySearch.DateMarkets[1].DepartureDate', '09/19/2017'),
		  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$TextBoxMarketOrigin1', 'DEL'),
		  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$DropDownListMarketDay1', '17'),
		  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$DropDownListMarketMonth1', '2017-09'),
		  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$TextBoxMarketOrigin2', 'KUL'),
		  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$DropDownListMarketDay2', '19'),
		  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$DropDownListMarketMonth2', '2017-09'),
		  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$TextBoxMarketOrigin3', ''),
		  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$DropDownListMarketDay3', '14'),
		  ('ControlGroupMultiCitySearchView$AKMultiCityAvailabilityMultiCitySearchView$DropDownListMarketMonth3', '2017-09'),
		  ('Search.RetainedJourneyFareSellKeys', ''),
		  ('AKMultiCityAvailabilitySearch.PaxTypeCountDictionary[\'ADT\']', '1'),
		  ('AKMultiCityAvailabilitySearch.PaxTypeCountDictionary[\'CHD\']', '0'),
		  ('AKMultiCityAvailabilitySearch.PaxTypeCountDictionary[\'INFANT\']', '0'),
		  ('ControlGroupMultiCitySearchView$MultiCurrencyConversionViewMultiCitySearchView$DropDownListCurrency', 'default'),
		  ('__VIEWSTATEGENERATOR', gen),
		  ('ControlGroupMultiCitySearchView$ButtonSubmit', 'Search'),
		]
	'''

	yield FormRequest('http://booking2.airasia.com/MultiCitySearch.aspx', callback=self.parse_next3, formdata=data, method="POST")

    def parse_next3(self, response):
	sel = Selector(response)
	yield SplashFormRequest.from_response(response, callback=self.prase_nex)

    def prase_nex(self, response):
	sel = Selector(response)
	view_state = ''.join(sel.xpath(view_state_path).extract())
        gen = ''.join(sel.xpath(view_generator_path).extract())
        check = ''.join(sel.xpath('//div[@class="dateMarketHead"]//text()').extract())
        if 'sold out' in check:
            print check
            #self.send_mail('Tickets Sold Out', json.dumps(book_dict))
	import pdb;pdb.set_trace()
        table_nodes = sel.xpath('//table[@class="rgMasterTable"][1]//tr')
        low_lst, regular_lst, premium_lst = [], [], []
        fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price = [''] * 4
	try:
	    import pdb;pdb.set_trace()
	    sctipt_text = sel.xpath('//script[@type="text/javascript"]').extract()[14]
	    jsons_text = re.findall('{"ErrorsOccured":0,"JourneyFareSellKeys":"","TripAvailabilityResponse":(.*)', sctipt_text)[0]
	    input_json = json.loads(jsons_text)
	    seg1_flt, seg2_flt, seg3_flt, seg4_flt, seg5_flt, seg6_flt = self.get_flight_fares(input_json)
	except : 
	    import pdb;pdb.set_trace()
        #need to add code for multiple flights
        for node in table_nodes:
	    for i in range(2, 5):
                fare_id = ''.join(node.xpath('.//td[%s]//div[@id="fareRadio"]//input/@id'%i).extract())
                onclick = ''.join(node.xpath('.//td[%s]//@onclick'%i).extract())
                fare_name = ''.join(node.xpath('.//td[%s]//div[@id="fareRadio"]//input/@name'%i).extract())
                fare_vlue = ','.join(node.xpath('.//td[%s]//div[@id="fareRadio"]//input/@value'%i).extract())
                price = '<>'.join(node.xpath('.//td[%s]//div[@class="price"]//text()'%i).extract())
                if fare_id:
                    if i == 2:
                        low_lst.append((fare_id, fare_name, fare_vlue, price, onclick))
                    elif i == 3:
                        regular_lst.append((fare_id, fare_name, fare_vlue, price, onclick))
                    elif i == 4:
                        premium_lst.append((fare_id, fare_name, fare_vlue, price, onclick))
        if low_lst:
            fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price, onclick= self.get_lower_fares(low_lst)
        elif regular_lst:
             fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price, onclick = self.get_lower_fares(regular_lst)
        elif premium_lst:
            fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price, onclick = self.get_lower_fares(premium_lst)
        else: trip_fare = int(fin_price)
	import pdb;pdb.set_trace()
        if fin_fare_vlue:
	    form_data = [
                  ('__EVENTTARGET', ''),
                  ('__EVENTARGUMENT', ''),
                  ('__VIEWSTATE', view_state),
                  ('pageToken', ''),
                  ('ControlGroupMultiCitySelectView$AvailabilityInputMultiCitySelectView$market2', fin_fare_vlue),
                  ('ControlGroupMultiCitySelectView$AvailabilityInputMultiCitySelectView$HiddenFieldTabIndex0', '2017-10-16'),
		  #('ControlGroupMultiCitySelectView$SpecialNeedsInputMultiCitySelectView$RadioButtonWCHYESNO', 'RadioButtonWCHYES'),
                  ('Select.JourneyFareSellKeys', fin_fare_vlue),
                  ('ControlGroupMultiCitySelectView$AvailabilityInputMultiCitySelectView$JourneyFareSellKey', fin_fare_vlue), 
                  ('ItinerarySummary.JourneyFareSellKeys', ''),
                  ('__VIEWSTATEGENERATOR', gen),
		  ('instart_disable_injection', 'true'),
                  #('ControlGroupMultiCitySelectView$ButtonSubmit', 'Continue'),
                ]
	    headers = {
    			'pragma': 'no-cache',
    			'accept-encoding': 'gzip, deflate, br',
    			'accept-language': 'en-US,en;q=0.8',
    			'accept': '*/*',
    			'cache-control': 'no-cache',
    			'authority': 'booking2.airasia.com',
			'cookie': '_gali=tripPlannerNextButton',
			'referer': 'https://booking2.airasia.com/MultiCitySelect.aspx',
			}
	    
	    #url = 'http://booking2.airasia.com/MultiCitySearch.aspx'
	    '''url = 'https://booking2.airasia.com/stickysession'
	    import pdb;pdb.set_trace()'''
	    params = (
		    ('flightKeys', fin_fare_vlue),
		    ('numberOfMarkets', '2'),
		    ('keyDelimeter', ','),
		    ('instart_disable_injection', 'true'),
		)
	    url = 'https://booking2.airasia.com/TaxAndFeeInclusiveDisplayAjax-resource.aspx'
            yield FormRequest(url, callback=self.parse_flight, formdata=params, headers=headers, method="GET")

    def parse_flight(self, response):
	sel = Selector(response)
	import pdb;pdb.set_trace()
	yield SplashFormRequest.from_response(response, callback=self.parse_flight2)

    def parse_flight2(self, response):
	sel = Selector(response)
	import pdb;pdb.set_trace()
	table_nodes = sel.xpath('//table[@class="rgMasterTable"][1]//tr')

    def get_lower_fares(self, lst_):
        lower_dict = {}
        if lst_:
            for lst in lst_:
                fare_id, fare_name, fare_vlue, price, onclick = lst
                price = price.split('<>')
                price_int = 0
                for i in price:
                    i = i.replace(',', '').strip()
                    i = ''.join(self.price_patt.findall(i))
                    if i:
                        price_int += int(i)
                lower_dict.update({price_int:(fare_id, fare_name, fare_vlue, price_int, onclick)})
        min_price = min(lower_dict.keys())
        lower_details = lower_dict.get(min_price, ['']*5)
        return lower_details

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
		    
