import re
import time
import urllib
import random
import json
import md5
import smtplib
import MySQLdb
import datetime
from random import randint
import smtplib, ssl
from email import encoders
from ast import literal_eval
from scrapy import signals
from scrapy.spider import Spider
from collections import OrderedDict
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from scrapy.http import FormRequest, Request
from email.mime.multipart import MIMEMultipart
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher
from ConfigParser import SafeConfigParser
from scrapy.conf import settings

from airasiaamend_utils import *
from airasiaamend_constants import agency_viewstate
from amend_scrapers.utils import *
from amend_scrapers.items import AmendScrapersItem

from scrapy.conf import settings

import sys
sys.path.append(settings['ROOT_PATH'])
from airasia_login_cookie import airasia_login_cookie_list

from root_utils import Helpers

_cfg = SafeConfigParser()
_cfg.read(settings['BOOK_PCC_PATH'])

from airasia_login_cookie import airasia_login_cookie_list

class AirAsiaAmendBookingBrowse(Spider, AirAsiaAmendUtils):
    name = "airasiaamend_booking_browse"
    start_urls = ["https://booking2.airasia.com/AgentHome.aspx"]
    handle_httpstatus_list = [404, 500, 400]

    def __init__(self, *args, **kwargs):
        super(AirAsiaAmendBookingBrowse, self).__init__(*args, **kwargs)
        self.log = create_logger_obj('airasiaamend_booking')
        self.booking_dict = ast.literal_eval(kwargs.get('jsons', '{}'))
        self.proceed_to_book = 0
        self.tolerance_amount = 0
        self.book_using = ''
        self.pnr_no = ''
        self.multiple_pcc = False
        self.pcc_name = ''
        self.user_name = ''
        self.user_psswd = ''
        self.insert_query = 'insert into airasiaamend_booking_report(sk, airline, flight_number, auto_pnr, pnr, triptype, cleartrip_price, airline_price, status_message, tolerance_amount, error_message, paxdetails, price_details, created_at, modified_at) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now()) on duplicate key update modified_at=now(), sk=%s, status_message=%s, price_details=%s, error_message=%s, pnr=%s'

        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('amendbooking', 'IP')
        passwd = db_cfg.get('amendbooking', 'PASSWD')
        user = db_cfg.get('amendbooking', 'USER')
        db_name = db_cfg.get('amendbooking', 'DBNAME')
        self.conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()

        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()


    def parse(self, response):
        '''Login to AirAsia'''
        sel = Selector(response)

        login_data_list = [('__VIEWSTATE', '/wEPDwUBMGRktapVDbdzjtpmxtfJuRZPDMU9XYk=')]
        login_data_list.append(('__VIEWSTATEGENERATOR', '05F9A2B0'))
        login_data_list.append(('pageToken', ''))
        login_data_list.append(('ControlGroupLoginAgentView$AgentLoginView$HFTimeZone', '330'))
        login_data_list.append(('__EVENTTARGET', 'ControlGroupLoginAgentView$AgentLoginView$LinkButtonLogIn'))
        self.pcc_name = self.get_pcc_name()
        self.pnr_no = self.booking_dict['details'][0].get('pnr','')
        cookie = random.choice(airasia_login_cookie_list)
        cookies = {'i10c.bdddb': cookie}
        try:
            self.user_name = _cfg.get(self.pcc_name, 'username')
            self.user_psswd = _cfg.get(self.pcc_name, 'password')
            self.log.debug('Booking using: %s' % self.user_name)
            login_data_list.append(('ControlGroupLoginAgentView$AgentLoginView$TextBoxUserID', str(self.user_name)))
            login_data_list.append(('ControlGroupLoginAgentView$AgentLoginView$PasswordFieldPassword', str(self.user_psswd)))
            yield FormRequest('https://booking2.airasia.com/LoginAgent.aspx', cookies=cookies, formdata=login_data_list, callback=self.parse_next, dont_filter=True)
        except:
             self.insert_error(err='PCC credentials not found')
             return

    def parse_next(self, response):
        '''
        Parse the request to my bookings or manage my booking
        '''
        sel = Selector(response)
        if 'AgentHome.aspx' in response.url:
            manage_booking = ''.join(sel.xpath('//a[@id="MyBookings"]/@href').extract())
            url = 'https://booking2.airasia.com' + manage_booking
            yield Request(url, callback=self.parse_bookinglist)

    def parse_bookinglist(self, response):
        sel = Selector(response)
        view_state = ''.join(sel.xpath('//input[@id="viewState"]/@value').extract())
        gen = ''.join(sel.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value').extract())
        search_data_list = {'__VIEWSTATE': str(view_state)}
	search_data_list.update({'__VIEWSTATEGENERATOR':str(gen)})
        search_data_list.update({'__EVENTTARGET' : 'ControlGroupBookingListView$BookingListSearchInputView$LinkButtonFindBooking'})
        search_data_list.update({'__EVENTARGUMENT' : ''})
        search_data_list.update({'pageToken' : ''})
        search_data_list.update({'ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword' : self.pnr_no})
        search_data_list.update({'ControlGroupBookingListView$BookingListSearchInputView$Search' : 'ForAgency'})
        search_data_list.update({'ControlGroupBookingListView$BookingListSearchInputView$DropDownListTypeOfSearch' : '1'})
        if 'BookingList.aspx' in response.url:
            url = "https://booking2.airasia.com/BookingList.aspx"
            yield FormRequest(url, formdata=search_data_list, callback=self.parse_search, dont_filter=True)

    def parse_search(self, response):
        sel = Selector(response)
        view_state = ''.join(sel.xpath('//input[@id="viewState"]/@value').extract())
        gen = ''.join(sel.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value').extract())
        search_data_list = {'__VIEWSTATE': str(view_state)}
        search_data_list.update({'__VIEWSTATEGENERATOR':str(gen)})
        search_data_list.update({'__EVENTTARGET' : 'ControlGroupBookingListView$BookingListSearchInputView'})
        search_data_list.update({'__EVENTARGUMENT' : 'Edit:%s' % self.pnr_no})
        search_data_list.update({'pageToken' : ''})
        search_data_list.update({'ControlGroupBookingListView$BookingListSearchInputView$TextBoxKeyword' : self.pnr_no})
        search_data_list.update({'ControlGroupBookingListView$BookingListSearchInputView$Search' : 'ForAgency'})
        search_data_list.update({'ControlGroupBookingListView$BookingListSearchInputView$DropDownListTypeOfSearch' : '1'})
        if 'BookingList.aspx' in response.url:
            url = "https://booking2.airasia.com/BookingList.aspx"
            yield FormRequest(url, formdata=search_data_list, callback=self.parse_modify, dont_filter=True)

    def parse_modify(self, response):
        sel = Selector(response)
        print sel.xpath('//div[@id="atAGlanceContent"]//li/a[contains(@href, "ChangeControl$LinkButtonChangeFlights")]/@href').extract()
        if 'ChangeItinerary' in response.url:
            view_state = ''.join(sel.xpath('//input[@id="viewState"]/@value').extract())
            gen = ''.join(sel.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value').extract())
            change_data_list = {'__VIEWSTATE': str(view_state)}
            change_data_list.update({'__VIEWSTATEGENERATOR':str(gen)})
            change_data_list.update({'HiddenFieldPageBookingData' : self.pnr_no})
            change_data_list.update({'MemberLoginChangeItineraryView2$PasswordFieldPassword' : self.user_psswd})
            change_data_list.update({'MemberLoginChangeItineraryView2$TextBoxUserID' : self.user_name})
            change_data_list.update({'__EVENTARGUMENT' : ''})
            change_data_list.update({'__EVENTTARGET' : 'ChangeControl$LinkButtonChangeFlights'})
            change_data_list.update({'hdRememberMeEmail' : self.user_name})
            change_data_list.update({'memberLogin_chk_RememberMe' : 'on'})
            change_data_list.update({'pageToken' : ''})
            url = 'https://booking2.airasia.com/ChangeItinerary.aspx'
            yield FormRequest(url, callback=self.parse_changeflight, formdata=change_data_list)

    def parse_changeflight(self, response):
        sel = Selector(response)
        view_state = ''.join(sel.xpath('//input[@id="viewState"]/@value').extract())
        gen = ''.join(sel.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value').extract())
        change_data_list = {'__VIEWSTATE': str(view_state)}
        change_data_list.update({'__VIEWSTATEGENERATOR':str(gen)})
        change_data_list.update({'HiddenFieldPageBookingData' : self.pnr_no})
        change_data_list.update({'__EVENTARGUMENT' : ''})
        change_data_list.update({'__EVENTTARGET' : 'ControlGroupSearchChangeView$LinkButtonSubmit'})
        change_data_list.update({'pageToken' : ''})
        change_data_list.update({'ControlGroupSearchChangeView$MultiCurrencyConversionViewSearchChangeView$DropDownListCurrency' : 'default'})
        if self.booking_dict['trip_type'] == 'OW':
            day, year_mon, dest, org, status = self.find_oneway_details()
            print day, year_mon, dest, org, status

            if status:
                change_data_list.update({'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$CheckBoxChangeMarket_1' : 'on'})
                change_data_list.update({'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$DropDownListMarketDay1' : day})
                change_data_list.update({'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$DropDownListMarketMonth1' : year_mon})
                change_data_list.update({'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$TextBoxMarketDestination1' : dest})
                change_data_list.update({'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$TextBoxMarketOrigin1' : org})
            else:
                #insert into db of error status
                print "Fail return"
        elif self.booking_dict['trip_type'] == 'RT':
            day1, year_mon1, dest1, org1, day2, year_mon2, dest2, org2, status = self.find_rt_details()
            if status:
                change_data_list.update({'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$CheckBoxChangeMarket_1' : 'on'})
                change_data_list.update({'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$CheckBoxChangeMarket_2' : 'on'})
                change_data_list.update({'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$DropDownListMarketDay1' : day1})
                change_data_list.update({'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$DropDownListMarketDay2' : day2})
                change_data_list.update({'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$DropDownListMarketMonth1' : year_mon1})
                change_data_list.update({'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$DropDownListMarketMonth2' : year_mon2})
                change_data_list.update({'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$TextBoxMarketDestination1' : dest1})
                change_data_list.update({'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$TextBoxMarketDestination2' : dest2})
                change_data_list.update({'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$TextBoxMarketOrigin1' : org1})
                change_data_list.update({'ControlGroupSearchChangeView$AvailabilitySearchInputSearchChangeView$TextBoxMarketOrigin2' : org2})
            else:
                #insert into db of error status
                #Fail return
                print "insert into db of error status"
        url = 'https://booking2.airasia.com/SearchChange.aspx'
        print change_data_list
        yield FormRequest(url, callback=self.parse_select, formdata=change_data_list, dont_filter=True)

    def parse_select(self, response):
        sel = Selector(response)
        form_data = {}
        fare_class_dict = {'Regular': 'Regular', 'PremiumFlex': 'PremiumFlex', 'PremiumFlatbed':'PremiumFlatbed', "Econamy":"Lowfare", "Economy": "Lowfare"}
        view_state = normalize(''.join(sel.xpath('//input[@id="viewState"]/@value').extract()))
        gen = normalize(''.join(sel.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value').extract()))
        fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price, rt_flt_no = [''] * 5
        refin_fare_id, refin_fare_name, refin_fare_vlue, refin_price = [''] * 4
        table_nodes = sel.xpath('//table[@id="fareTable1_4"]//tr')
        retable_nodes = sel.xpath('//table[@id="fareTable2_4"]//tr')
        field_tab_index = sel.xpath('//div[@class="tabsHeader"][1]//input//@id').extract()
        field_tab_value = sel.xpath('//div[@class="tabsHeader"][1]//input//@value').extract()
        print field_tab_value
        if self.booking_dict.get('trip_type', '') ==  'RT':
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
             err = 'No Flights found'
             logging.debug('Flights  not found')
        if not retable_nodes and self.booking_dict.get('triptype', '') ==  'RT':
            err = 'No Flights found'
            logging.debug('Flights  not found')
        if not retable_nodes and self.booking_dict.get('triptype', '') ==  'RT':
            err = 'No Flights found'
            logging.debug('Flights  not found')
        member_time_zone = ''.join(sel.xpath('//input[@id="MemberLoginSelectView_HFTimeZone"]/@value').extract())
        #Get fares of trip types here
        flight_oneway_fares = self.get_flight_fares(table_nodes)
        flight_return_fares = self.get_flight_fares(retable_nodes)
        #Change the below propery

        ct_flight_id = self.booking_dict.get('onewayflightid', [])
        ct_ticket_class = self.booking_dict.get('onewayclass', []).replace(' ', '').strip()
        aa_keys = flight_oneway_fares.keys()
        fin_fare_dict, ow_flt_no = self.get_fin_fares_dict(flight_oneway_fares, ct_flight_id)
        final_flt_tuple = fin_fare_dict.get(fare_class_dict.get(ct_ticket_class, ''), ['']*4)
        fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price = final_flt_tuple
        if not fin_fare_vlue:
            final_flt_tuple = fin_fare_dict.get('Regular', ['']*4)
            fin_fare_id, fin_fare_name, fin_fare_vlue, fin_price = final_flt_tuple
        refin_fare_dict = {}
        rect_ticket_class = self.booking_dict.get('returnclass', '').replace(' ', '').strip()
        if self.booking_dict.get('trip_type', '') ==  'RT':
            rect_flight_id = self.booking_dict.get('returnflightid', [])
            refin_fare_dict, rt_flt_no = self.get_fin_fares_dict(flight_return_fares, rect_flight_id)
            refinal_flt_tuple = refin_fare_dict.get(fare_class_dict.get(rect_ticket_class, ''), ['']*4)
            refin_fare_id, refin_fare_name, refin_fare_vlue, refin_price = refinal_flt_tuple
            if not refin_fare_vlue:
                refinal_flt_tuple = refin_fare_dict.get('Regular', ['']*4)
                refin_fare_id, refin_fare_name, refin_fare_vlue, refin_price = refinal_flt_tuple
        self.booking_dict.update({'ow_flt':ow_flt_no, 'rt_flt':rt_flt_no})
        if fin_fare_vlue:
            form_data.update({
                             'ControlGroupSelectChangeView$AvailabilityInputSelectChangeView$HiddenFieldTabIndex1' : str(field_tab_value),
                             'ControlGroupSelectChangeView$AvailabilityInputSelectChangeView$market1' : str(fin_fare_vlue),
                             'ControlGroupSelectChangeView$ButtonSubmit': 'Continue',
                             'ControlGroupSelectChangeView$SpecialNeedsInputSelectChangeView$RadioButtonWCHYESNO':'RadioButtonWCHNO',
                             'HiddenFieldPageBookingData' : self.pnr_no,
                             '__VIEWSTATE':view_state,
                             '__VIEWSTATEGENERATOR':gen,

                        })
            url = 'https://booking2.airasia.com/SelectChange.aspx'
            if self.booking_dict.get('trip_type', '') == 'RT' and refin_fare_vlue:
                form_data.update({      refield_tab_index:refield_tab_value,
                                    'ControlGroupSelectView$AvailabilityInputSelectView$market2':refin_fare_vlue,
                                })
                yield FormRequest(url, callback=self.parse_travel, formdata=form_data, \
                        meta={'form_data':form_data, 'book_dict':self.booking_dict}, dont_filter=True)

            elif fin_fare_vlue and self.booking_dict.get('trip_type', '') == 'OW':
                yield FormRequest(url, callback=self.parse_travel, formdata=form_data,  dont_filter=True, meta={'form_data':form_data})
            else:
                print "Couldnt find flights"
        else:
            print "No flights in selected class"

    def parse_travel(self, response):
        sel = Selector(response)
        hiflyerfare = ''.join(sel.xpath('//input[@name="HiFlyerFare"]/@value').extract())
        view_state = normalize(''.join(sel.xpath('//input[@id="viewState"]/@value').extract()))
        gen = normalize(''.join(sel.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value').extract()))
        token_name = 'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE_CONTROLGROUPTRAVELERFLIGHTCHANGE_ContactInputTravelerFlightChangeViewHtmlInputHiddenAntiForgeryTokenField'
        token = ''.join(sel.xpath('//input[@name="%s"]/@value' % token_name).extract())
        contact_titlekey = 'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$DropDownListTitle'
        contact_title = ''.join(sel.xpath('//div[@class="contactInputContainer"]/p/select[contains(@name, "DropDownListTitle")]/option[@selected]/@value').extract())
        agent_first_name = ''.join(sel.xpath('//div[@class="contactInputContainer"]/p/label[contains(text(), "Agent full name")]/../input[contains(@id, "TextBoxFirstName")]/@value').extract())
        agent_last_name = ''.join(sel.xpath('//div[@class="contactInputContainer"]/p/label[contains(text(), "Agent full name")]/../input[contains(@id, "TextBoxLastName")]/@value').extract())
        agent_mail = ''.join(sel.xpath('//div[@class="contactInputContainer"]/p/input[contains(@name, "TextBoxEmailAddress")]/@value').extract())
        guest_phone = ''.join(sel.xpath('//div[@class="contactInputContainer"]/p/input[contains(@name, "TextBoxOtherPhone")]/@value').extract())

        travel_data_list = {'HiFlyerFare' : hiflyerfare}
        travel_data_list.update({'__VIEWSTATE' : view_state})
        travel_data_list.update({'__VIEWSTATEGENERATOR' : gen})
        travel_data_list.update({'HiddenFieldPageBookingData' : self.pnr_no})
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ButtonSubmit' : 'Continue'})
        travel_data_list.update({token_name : token})
        #check box hardcodes
        travel_data_list.update({'checkBoxAUSNoInsuranceId' : 'InsuranceInputControlAddOnsViewAjax_CheckBoxAUSNo'})
        travel_data_list.update({'checkBoxInsuranceId' : 'CONTROLGROUP_InsuranceInputControlAddOnsViewAjax_CheckBoxInsuranceAccept'})
        travel_data_list.update({'checkBoxInsuranceName' : 'InsuranceInputControlAddOnsViewAjax$CheckBoxInsuranceAccept'})
        #addons - check and do this

        #insure
        travel_data_list.update({'declineInsuranceLinkButtonId' : 'InsuranceInputControlAddOnsViewAjax_LinkButtonInsuranceDecline'})
        travel_data_list.update({'insuranceLinkCancelId' : 'InsuranceInputControlAddOnsViewAjax_LinkButtonInsuranceDecline'})
        travel_data_list.update({'isAutoSeats' : 'false'})
        travel_data_list.update({'radioButton' : 'on'})
        travel_data_list.update({'drinkcountname' : '0'})

        travel_data_list.update({'radioButtonNoInsuranceId' : 'InsuranceInputControlAddOnsViewAjax_RadioButtonNoInsurance'})
        travel_data_list.update({'radioButtonYesInsuranceId' : 'InsuranceInputControlAddOnsViewAjax_RadioButtonYesInsurance'})

        #Emergency details
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$DropDownListRelationship':'Other'})
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$TextBoxFax' : ''})
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$HiddenSelectedCurrencyCode' : 'INR'})

        #Agency details
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$TextBoxWorkPhone' : '022 4055 4000'})



        #Contact agent details
        travel_data_list.update({contact_titlekey : contact_title })
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$TextBoxFirstName' : agent_first_name })
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$TextBoxLastName' : agent_last_name })
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$TextBoxEmailAddress' : agent_mail})
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$TextBoxOtherPhone' : guest_phone })
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$TextBoxHomePhone' : '' })
        home_phone_idc  = ''.join(sel.xpath('//select[contains(@name, "DropDownListHomePhoneIDC")]/option[@selected]/@value').extract())
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$DropDownListHomePhoneIDC' : home_phone_idc})
        other_phone_idc = ''.join(sel.xpath('//select[contains(@name, "DropDownListOtherPhoneIDC")]/option[@selected]/@value').extract())
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$DropDownListOtherPhoneIDC' : other_phone_idc})

        #Emergency contact name
        gn_name = 'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$EmergencyTextBoxGivenName'
        sir_name = 'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$EmergencyTextBoxSurname'
        em_mobile_code = 'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$DropDownListMobileNo'
        em_mobile_no = 'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$EmergencyTextBoxMobileNo'
        travel_data_list.update({gn_name : self.booking_dict['details'][0]['amend_pax_details'][0][1]})
        travel_data_list.update({sir_name : self.booking_dict['details'][0]['amend_pax_details'][0][-1]})

        travel_data_list.update({em_mobile_code : '93'})
        travel_data_list.update({em_mobile_no : self.booking_dict.get('mobile', '')})
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$DropDownListRelationship' : 'Other'})


        #passenger for loop details
        passengers = sel.xpath('//div[@id="passengerInputContent"]/div')
        counts = len(passengers)
        for i in range(0, counts):
            travel_data_list.update({'ctl00$BodyContent$ucTravelerForm1_form$addOnsPanel1$mealPanel2$SelectedMeal_%s' % i : ''})
        gender_check = {'MR' : '1', 'MRS' : '0', 'MS' : '0'}
        for index, passenger in enumerate(passengers):
            pass_gender_title = ''.join(passenger.xpath('./div[contains(@id, "passengerInputContainer")]/p/label[contains(text(), "Gender")]/../select/option[@selected]/@value').extract())
            pass_first_name = ''.join(passenger.xpath('./div[contains(@id, "passengerInputContainer")]/p/label[contains(text(), "Full name")]/../input[contains(@id, "TextBoxFirstName")]/@value').extract())
            pass_last_name = ''.join(passenger.xpath('./div[contains(@id, "passengerInputContainer")]/p/label[contains(text(), "Full name")]/../input[contains(@id, "TextBoxLastName")]/@value').extract())
            nationality = ''.join(passenger.xpath('./div[contains(@id, "passengerInputContainer")]/p/label[contains(text(), "Nationality")]/../select[contains(@id, "DropDownListNationality")]/option[@selected]/@value').extract())
            day = ''.join(passenger.xpath('./div[contains(@id, "passengerInputContainer")]/p/label[contains(text(), "Date of birth")]/../select[contains(@id, "DropDownListBirthDateDay")]/option[@selected]/@value').extract())
            month = ''.join(passenger.xpath('./div[contains(@id, "passengerInputContainer")]/p/label[contains(text(), "Date of birth")]/../select[contains(@id, "DropDownListBirthDateMonth")]/option[@selected]/@value').extract())
            year = ''.join(passenger.xpath('./div[contains(@id, "passengerInputContainer")]/p/label[contains(text(), "Date of birth")]/../select[contains(@id, "DropDownListBirthDateYear")]/option[@selected]/@value').extract())
            print pass_gender_title, pass_first_name, pass_last_name, nationality, day, month, year
            travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$PassengerInputTravelerFlightChangeView$DropDownListBirthDateDay_%s' % index : day})
            travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$PassengerInputTravelerFlightChangeView$DropDownListBirthDateMonth_%s' % index : month})
            travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$PassengerInputTravelerFlightChangeView$DropDownListBirthDateYear_%s' % index : year})
            travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$PassengerInputTravelerFlightChangeView$DropDownListGender_%s' % index : gender_check.get(pass_gender_title, '1')})
            travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$PassengerInputTravelerFlightChangeView$DropDownListNationality_%s' % index : nationality})
            travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$PassengerInputTravelerFlightChangeView$DropDownListTitle_%s' % index : pass_gender_title})
            travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$PassengerInputTravelerFlightChangeView$TextBoxFirstName_%s' % index : pass_first_name})
            travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$PassengerInputTravelerFlightChangeView$TextBoxLastName_%s' % index : pass_last_name})

        #Baggages coded
        baggages = sel.xpath('//div[@class="ssrWrapper"]//li[@class="baggageContainer"]/div/select')
        for bags in baggages:
            key = ''.join(bags.xpath('./@name').extract())
            value = bags.xpath('./@ssr-data').extract()[0].split('|')[0].split()[0]
            data_value = key.split('$')[-1].replace('journey_1', 'ssrCode_%s_ssrNum_1' % value)
            travel_data_list.update({key : data_value})

        #Meals coded
        meals = sel.xpath('//div[contains(@class, "ucmealpanel")]//input[contains(@name, "dropDown")]')
        for meal in meals:
            key = ''.join(meal.xpath('./@name').extract())
            travel_data_list.update({key : '0'})

        dummy = sel.xpath('//div[contains(@class, "ucmealpanel")]//select')
        for i in dummy:
            key = ''.join(i.xpath('./@name').extract())
            value = i.xpath('./option/@value').extract()[0]
            travel_data_list.update({key : value})

        #SportsEquip
        sports = sel.xpath('//div[@class="SSRInput"]//li/select[contains(@name, "SportEquipInputTravelerFlightChangeView")]/@name').extract()
        for sport in sports:
            travel_data_list.update({sport : ''})


        #comfort kits
        comforts = sel.xpath('//input[@class="uccomfortkitpanel-item-sf-count-input"]/@name').extract()
        for i in comforts:
            travel_data_list.update({i : '0'})

        #GST Details
        gst_country = ''.join(sel.xpath('//select[contains(@name, "ListGSTCountry")]/option[@selected]/@value').extract())
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$DropDownListGSTCountry' : gst_country})
        gst_state = 'JHB'#sel.xpath('//select[contains(@name, "ListGSTState")]/option/@value').extract()[0]
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$DropDownListGSTState' : gst_state})
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$DropDownListSelectedGSTState' : ''})
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$GSTTextboxRegistrationNumber' : ''})
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$GSTTextboxCompanyEmail' : ''})
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$GSTTextBoxCompanyStreet' : ''})
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$GSTTextBoxCompanyPostalCode' : ''})
        travel_data_list.update({'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$ContactInputTravelerFlightChangeView$GSTTextBoxCompanyName' : ''})

        travel_data_list.update({'__EVENTTARGET' : ''})#'CONTROLGROUP_OUTERTRAVELERFLIGHTCHANGE$CONTROLGROUPTRAVELERFLIGHTCHANGE$LinkButtonSkipToSeatMap'})
        travel_data_list.update({'__EVENTARGUMENT' : ''})

        url = 'https://booking2.airasia.com/TravelerFlightChange.aspx'
        yield FormRequest(url, callback=self.parse_addons, formdata=travel_data_list, dont_filter=True)

    def parse_addons(self, response):
        sel = Selector(response)
        pickup_date = datetime.datetime.strptime(self.booking_dict['details'][0]['amend_segment_details'][0]['departure_date'], '%d-%b-%y').strftime('%Y-%m-%d')
        drop_date = datetime.datetime.strptime(self.booking_dict['details'][0]['amend_segment_details'][-1]['arrival_date'], '%d-%b-%y').strftime('%Y-%m-%d')
        addons_data_list = {'CONTROLGROUPADDONSFLIGHTVIEW$ButtonSubmit' : 'Continue'}
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$DriverAgeTextBox' : 'Please enter your age'})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedCarDateTime' : ''})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedCarModel' : ''})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedCarPosition' : ''})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedCarPrice' : ''})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedCarTotalPrice' : ''})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedReferenceDateTime' : ''})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedReferenceID' : ''})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedReferenceIDContext' : ''})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedReferenceType' : ''})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedReferenceUrl' : ''})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedSearchPickUpDate' : pickup_date})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedSearchPickUpHour' : ''})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedSearchPickUpMin' : ''})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedSearchReturnDate' : drop_date})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedSearchReturnHour' : ''})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$HiddenTextBoxSelectedSearchReturnMin' : ''})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$SelectedDropDownSearchPickUpHour' : '00'})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$SelectedDropDownSearchPickUpMin' : '00'})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$SelectedDropDownSearchReturnHour' : '00'})
        addons_data_list.update({'CONTROLGROUPADDONSFLIGHTVIEW$CarTrawlerAddOnsFlightView$SelectedDropDownSearchReturnMin' : '00'})
        view_state = normalize(''.join(sel.xpath('//input[@id="viewState"]/@value').extract()))
        gen = normalize(''.join(sel.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value').extract()))
        ct_dropoff_date = ''.join(sel.xpath('//input[@name="ct_dropoff_date"]/@value').extract())
        ct_dropoff_loc = ''.join(sel.xpath('//input[@name="ct_dropoff_loc"]/@value').extract())
        ct_pickup_date = ''.join(sel.xpath('//input[@name="ct_pickup_date"]/@value').extract())
        ct_pickup_loc = ''.join(sel.xpath('//input[@name="ct_pickup_loc"]/@value').extract())
        addons_data_list.update({'HiddenFieldPageBookingData' : self.pnr_no})
        addons_data_list.update({'__EVENTTARGET' : ''})
        addons_data_list.update({'__EVENTARGUMENT' : ''})
        addons_data_list.update({'__VIEWSTATE' : view_state})
        addons_data_list.update({'__VIEWSTATEGENERATOR' : gen})
        addons_data_list.update({'ct_driver_age_confirm' : '1'})
        addons_data_list.update({'ct_dropoff_date' : ct_dropoff_date})
        addons_data_list.update({'ct_pickup_date' : ct_pickup_date})
        addons_data_list.update({'ct_dropoff_loc': ct_dropoff_loc})
        addons_data_list.update({'ct_pickup_loc' : ct_pickup_loc})
        addons_data_list.update({'pageToken' : ''})
        url = 'https://booking2.airasia.com/AddOnsFlightChange.aspx'
        yield FormRequest(url, callback=self.parse_unitmap, formdata=addons_data_list, dont_filter=True)

    def parse_unitmap(self, response):
        sel = Selector(response)
        view_state = normalize(''.join(sel.xpath('//input[@id="viewState"]/@value').extract()))
        gen = normalize(''.join(sel.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value').extract()))
        unitmap_data_list = {'__EVENTARGUMENT': ''}
        unitmap_data_list.update({'__EVENTTARGET' : 'ControlGroupUnitMapView$UnitMapViewControl$LinkButtonAssignUnit'})
        unitmap_data_list.update({'__VIEWSTATE' : view_state})
        unitmap_data_list.update({'__VIEWSTATEGENERATOR' : gen})
        unitmap_data_list.update({'pageToken' : ''})
        unitmap_data_list.update({'HiddenFieldPageBookingData' : self.pnr_no})
        url = 'https://booking2.airasia.com/UnitMap.aspx'
        yield FormRequest(url, callback=self.parse_unitmap_next, formdata=unitmap_data_list)

    def parse_unitmap_next(self, response):
        sel = Selector(response)
        ct_price = self.booking_dict['cleartrip_price']
        amount = ''.join(sel.xpath('//table[@id="agCreditTable"]//tr/td[contains(text(), "Estimated amount")]/../td[2]/input/@value').extract())
        #view_state = normalize(''.join(sel.xpath('//input[@id="viewState"]/@value').extract()))
        #Hardcoded viw state as I5 does not work without hardcoding it here in this part of the code
        gen = normalize(''.join(sel.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value').extract()))
        tolerance_value, is_proceed = self.check_tolerance(ct_price, amount)
        payment_data = [('CONTROLGROUPPAYMENTBOTTOM$ButtonSubmit', 'Submit payment')]
        payment_data.append(('CONTROLGROUPPAYMENTBOTTOM$PaymentInputViewPaymentView$AgencyAccount_AG_AMOUNT', amount))
        payment_data.append(('HiddenFieldPageBookingData', self.pnr_no))
        payment_data.append(('MCCOriginCountry', 'IN'))
        payment_data.append(('PriceDisplayPaymentView$CheckBoxTermAndConditionConfirm', 'on'))
        payment_data.append(('__EVENTARGUMENT', ''))
        payment_data.append(('__EVENTTARGET', ''))
        payment_data.append(('__VIEWSTATE', agency_viewstate))
        payment_data.append(('__VIEWSTATEGENERATOR', gen))
        payment_data.append(('eventArgument', ''))
        payment_data.append(('eventTarget', ''))
        payment_data.append(('pageToken', ''))
        payment_data.append(('pageToken', ''))
        payment_data.append(('viewState', agency_viewstate))
        if is_proceed:
            url = 'https://booking2.airasia.com/Payment.aspx'
            #yield FormRequest(url, callback=self.parse_commit, formdata=payment_data, dont_filter=True, meta={'tolerance' : tolerance_value})
        else:
            self.log.debug('Tolerance fail: %s' % tolerance_value)
            self.send_mail(sub="Tolerance fail for %s : %s" % (self.booking_dict.get('trip_ref', ''), tolerance_value), error_msg='', airline='AirAsia', config='airasia', receiver='airasia_common')

    def parse_commit(self, response):
        url = 'https://booking2.airasia.com/Itinerary.aspx'
        time.sleep(10)
        yield Request(url, callback=self.parse_final, dont_filter=True, meta={'tolerance' : response.meta.get('tolerance', '')} )

    def parse_final(self, response):
        open('%s_amend.html' % self.booking_dict.get('trip_ref', ''), 'w').write(response.body)
        pnr = ''.join(sel.xpath('//div[@class="itinerary-title"]//span[contains(@id, "BookingNumber")]/text()').extract())
        if pnr:
            amount_paid = ''.join(sel.xpath('//div[@class="itinerary-title"]//span[contains(@id, "TotalPaid")]/text()').extract()).strip('INR')
            flight_no = ''.join(sel.xpath('//table[@class="rgMasterTable"]//td[1]/div[1]/text()').extract())
            agency_payments = sel.xpath('//div[@class="booking-details-table"]//td[2]/div[@class="left"]/text()').extract()
            fare_details = [i.xpath('.//td//text()').extract() for i in sel.xpath('//table[@class="priceDisplay"]//tr')]
            price_details = {'agency_payments' : agency_payments, 'fare_details' : fare_details, 'amount_paid' : amount_paid, 'flight_no' : flight_no}
            self.insert_error(pnr=pnr, mesg='Amend success', tolerance=tolerance, p_details=json.dumps(price_details), a_price=amount_paid)
        else:
            self.insert_error(err='Payment failed')
