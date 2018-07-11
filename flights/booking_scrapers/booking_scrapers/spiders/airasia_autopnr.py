from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
import unittest, time, re
import datetime
from datetime import datetime
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import ast
import json
import csv
import sys
import datetime
import operator
import logging
import requests
from airasia_utils import *
from scrapy import log
from scrapy import signals
from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher
from itertools import groupby

class AirAsia(Spider, AirAsiaUtils):

    name = "airasia"
    start_urls = ["https://booking2.airasia.com/AgentHome.aspx"]

    def __init__(self, *args, **kwargs):
        super(AirAsia, self).__init__(*args, **kwargs)
        self.inputdict = kwargs.get('dict', '')
	self.output_list = []
	self.matched_dict = {}

    def parse(self,response):
        profile = webdriver.FirefoxProfile()
        driver = webdriver.Firefox(profile)
        time.sleep(4)
        driver.get(response.url)
        username = driver.find_element_by_xpath("//*[@id='ControlGroupLoginAgentView_AgentLoginView_TextBoxUserID']").send_keys("OTAINCLEAN_ADMIN")
        password=driver.find_element_by_xpath("//*[@id='ControlGroupLoginAgentView_AgentLoginView_PasswordFieldPassword']").send_keys("Cleartrip$2015")
        driver.find_element_by_id("ControlGroupLoginAgentView_AgentLoginView_LinkButtonLogIn").click()
	source_page = driver.page_source
        sel = Selector(text=source_page)
	logincheck = ''.join(sel.xpath("//div[@id='errorSectionContent']").extract())
	if not logincheck:
            time.sleep(8)
            driver.find_element_by_id("MyBookings").click()
            time.sleep(3)
            driver.wait = WebDriverWait(driver, 3)
            time.sleep(3)
            driver.find_element_by_id("ControlGroupBookingListView_BookingListSearchInputView_RadioForAgency").click()
            driver.find_element_by_xpath("//select[@id='ControlGroupBookingListView_BookingListSearchInputView_DropDownListTypeOfSearch']/option[@value='5']").click()
            driver.find_element_by_id("ControlGroupBookingListView_BookingListSearchInputView_TextBoxKeyword").clear()
            driver.find_element_by_id("ControlGroupBookingListView_BookingListSearchInputView_TextBoxKeyword").send_keys("DUGGIRALA,PRIYANKA")
            #driver.find_element_by_id("ControlGroupBookingListView_BookingListSearchInputView_TextBoxKeyword").send_keys("MOHAPATRA , MANOJKUMAR")
            #driver.find_element_by_id("ControlGroupBookingListView_BookingListSearchInputView_TextBoxKeyword").send_keys("sharma,sakshi")
            driver.find_element_by_id("ControlGroupBookingListView_BookingListSearchInputView_LinkButtonFindBooking").click()
            time.sleep(6)
            time.sleep(8)
            source_page = driver.page_source
            sel = Selector(text=source_page)
            searchedcheck = ''.join(sel.xpath("//div[@id='errorSectionContent']").extract())
            if not searchedcheck:

                try:
                    rows = sel.xpath('//div[@class="redSectionHeader"]/div[contains(.,"Current bookings")]/../following-sibling::table/tbody')[0]
                    try:
                        data = json.dumps(ast.literal_eval(self.inputdict))
                        input_dict = json.loads(data)
                        input_dict = input_dict
                        final_dict = {}
                        mapping_node = sel.xpath('//div[contains(.,"Current bookings")]/../following-sibling::table')[0]
                        if mapping_node:
                            mapping_node = mapping_node.xpath('./tbody/tr')
                        for node in mapping_node:
                            output_dict = {}
                            departure_date = ''.join(node.xpath(".//td[1]//text()").extract())
                            origin = ''.join(node.xpath(".//td[2]//text()").extract())
                            destination = ''.join(node.xpath(".//td[3]//text()").extract())
                            booking_no = ''.join(node.xpath(".//td[4]//text()").extract())
                            guest_name = ''.join(node.xpath(".//td[5]//text()").extract())
                            modify_id = ''.join(node.xpath(".//td[6]/a/text()[contains(.,'Modify')]/../@id").extract())
                            output_dict.update({'departure_date':departure_date,'origin':origin,'destination':destination,'booking_no':booking_no,'guest_name':guest_name})
                            final_dict[modify_id] = output_dict
                        for key,value in final_dict.iteritems():
                            output_date = value.get('departure_date','').split(',')[1].strip()
                            output_date = datetime.datetime.strptime(output_date,  '%d %B %Y')
                            input_date = input_dict.get('departure_date','')
                            input_date = datetime.datetime.strptime(input_date,  '%d-%b-%y')
                            if input_date == output_date:
                                    modify_id = key
                                    driver.find_element_by_id(modify_id).click()
                                    time.sleep(8)
                                    time.sleep(6)
                                    source_page = driver.page_source
                                    self.parse_ne(source_page,input_dict,driver)
                                    break
                            else:
                                    print "Not Matched"
                    except:
                            print "Inputs values are not there"
                except:
                        print "No bookings found"
            else:
                    print "Please enter valid lastname , firstname "
	else:
		print "Please enter valid username and password"
    def parse_ne(self,response,input_dict,driver):
    	output_dict = {}
	input_dict = input_dict
	source_page = driver.page_source
	rt_fullinput_dict,ow_fullinput_dict = self.get_input_segments(input_dict)
	if bool(ow_fullinput_dict):
	    input_dict.update({'oneway_dict':ow_fullinput_dict})
	if bool(rt_fullinput_dict):
	    input_dict.update({'return_dict':rt_fullinput_dict})
	sel = Selector(text=source_page)
	return_details_node = sel.xpath('//div[@id="ctl00_OptionalHeaderContent_radGridDepartTable"]//table//text()[contains(.,"Return")]/../../../..')
	oneway_details_node = sel.xpath('//div[@id="ctl00_OptionalHeaderContent_radGridDepartTable"]//table//text()[contains(.,"Depart")]/../../../..')
	booking_number = ''.join(sel.xpath("//span[@id='OptionalHeaderContent_lblBookingNumber']/text()").extract())
	if booking_number:
	    output_dict.update({"booking_number":booking_number})
	if return_details_node:
	    return_dict = self.details(return_details_node)
	    output_dict.update({'return_dict':return_dict})
	if oneway_details_node:
	    oneway_dict = self.details(oneway_details_node)
	    output_dict.update({'oneway_dict':oneway_dict})
	names = sel.xpath('//span[@class="guest-detail-name"]//text()').extract()
        name_dict = {}
        count = 0
        for name in names:
            count = count + 1
            if '+' in name:
                    name = name.split('+')[0].strip()
            name_dict.update({'adult'+str(count):name.strip()})
        if bool(name_dict):
            no_of_passengers = len(names)
            output_dict.update({'no_of_passengers':no_of_passengers})
            output_dict.update({'pax_details':name_dict})
        email = ''.join(sel.xpath('//div[@class="RadGrid RadGrid_AirAsiaBooking2"]/table/tbody/tr/td//p[contains(.,"Email")]/text()').extract())
        if email:
            if ':' in email:
                email = email.split(':')[1].strip()
            output_dict.update({'email':email})
        date_of_birth = ''.join(sel.xpath('//div[@class="RadGrid RadGrid_AirAsiaBooking2"]/table/tbody/tr/td//p[contains(.,"Date of Birth")]/text()').extract()).replace(': ','').strip()
        if date_of_birth:
            date_of_birth = date_of_birth
            output_dict.update({'date_of_birth':date_of_birth})
        self.output_list.append(output_dict)
        self.segmentschecking(input_dict,output_dict)
        self.flightsnochecking(input_dict,output_dict)
        self.departuretimechecking(input_dict,output_dict)
        self.guestdetailschecking(input_dict,output_dict)
        finalcheck_result = self.finalcheck(input_dict,output_dict)
        print finalcheck_result
    def details(self,node):
	output_dict = {}
	output_final_dict = []
	segment_list = []
	segment_name = ''.join(node.xpath('./thead/tr/th/text()').extract()[1]).replace(' ','')
	if segment_name:
	    segment_name = segment_name
	    output_dict.update({'segment_name':segment_name})
	nodes = node.xpath('./tbody/tr')
	for nod in nodes:
            details_node = nod.xpath('./td')
            flight_details = {}
            flight_no = ''.join(details_node[0].xpath('./div/text()').extract()).replace(' ','')
            if flight_no and '\n' not in flight_no:
                    flight_no = flight_no
                    flight_details.update({'flight_no':flight_no})
            departure_dates = ''.join(details_node[1].xpath('.//div[@class="left itineraryCustom4"]//text()[contains(.,", ")]').extract())
            if departure_dates:
                    departure_date = departure_dates.split(',')[0].strip()
                    dep_time = departure_dates.split(', ')[1].split('(')[0].strip()
                    flight_details.update({'departure_date':departure_date , 'dep_time':dep_time})
            arrival_dates = ''.join(details_node[2].xpath('.//div[@class="left itineraryCustom4"]//text()[contains(.,", ")]').extract())
            if arrival_dates:
                    arrival_date = arrival_dates.split(',')[0].strip()
                    arr_time = arrival_dates.split(', ')[1].split('(')[0].strip()
                    flight_details.update({'arrival_date':arrival_date,'arr_time':arr_time})
            segment_list.append(flight_details)
	output_dict.update({'segment_details':segment_list})
	return output_dict
    def finalcheck(self,input_dict,output_dict):
	matchedcount = 0
	notmatched_list = []
	for key,value in self.matched_dict.iteritems():
            if value == False:
                    notmatched_list.append(key + " " +  "not matched")
            else:
                    matchedcount = matchedcount+1
	if matchedcount == len(self.matched_dict.values()):
	    return  output_dict['booking_number'] + " " +  "matched"
	else:return ' '.join(notmatched_list)
	
 
    def guestdetailschecking(self,input_dict,output_dict):
	input_passengerscount = int(input_dict['no_of_infants']) + int(input_dict['no_of_children']) + int(input_dict['no_of_adults'])
	output_passengerscount = output_dict['no_of_passengers']
	input_names_dict = {}
	input_passengers = input_dict['pax_details']
	count = 0
	matchedno = 0
	for key in input_passengers.keys():
            count = count +1
            name_list = input_passengers[key]
            name = name_list[1:(len(name_list)-3)]
            input_names_dict.update({'adult'+str(count):' '.join(name)})
	output_names_dict = output_dict['pax_details']
	if input_passengerscount == output_passengerscount:
            input_names_list = input_names_dict.values()
            output_names_list = output_names_dict.values()
            for name1 in input_names_list:
                for name2 in output_names_list:
                    reversename_list = name2.lower().split(' ')
                    reversename_list = [x for x in reversename_list if x]
                    reveresename = reversename_list[1].strip() + ' ' + reversename_list[0].strip()
                    if name1.lower().replace(' ','') == name2.lower().replace(' ','') or name1.lower().replace(' ','') == reveresename.lower().replace(' ',''):
                        matchedno = matchedno+1
		if matchedno == input_passengerscount:
			is_matched = True
		else:
			is_matched = False
	else:
		is_matched = False
	return self.matched_dict.update({'guest_details': is_matched})
    def departuretimechecking(self,input_dict,output_dict):
	input_deptime_list = []
	output_deptime_list = []
	trip_type = input_dict['trip_type']
	try:
            for i in input_dict['oneway_dict']['segments']:
                input_deptime = i['dep_time'].replace(' ','')
                input_deptime = datetime.datetime.strptime(input_deptime, '%H:%M')
                input_deptime_list.append(input_deptime)
	except:
            for i in input_dict['oneway_dict']:
                input_deptime = i['dep_time']
                input_deptime = datetime.datetime.strptime(input_deptime, '%H:%M')
                input_deptime_list.append(input_deptime)
        for nod in output_dict['oneway_dict']['segment_details']:
            output_deptime = nod['dep_time']
            output_deptime = self.convert24(output_deptime)	
            output_deptime_list.append(input_deptime)
        final_data  = [x for x in input_deptime_list if x not in output_deptime_list]
        if final_data:is_matched =False
        else:is_matched =True
	if trip_type == 'RT' and is_matched == True:
            input_deptime_list = []
            output_deptime_list = []
            for i in input_dict['return_dict']['segments']:
                input_deptime= i['dep_time']
                input_deptime = datetime.datetime.strptime(input_deptime, '%H:%M')
                input_deptime_list.append(input_deptime)
            for nod in output_dict['return_dict']['segment_details']:
                output_deptime = nod['dep_time']
                output_deptime = self.convert24(output_deptime)
                output_deptime_list.append(output_deptime)
            final_data  = [x for x in input_deptime_list if x not in output_deptime_list]
            if final_data:is_matched =False
            else: is_matched =True
            return self.matched_dict.update({'return_flightno':is_matched})
        else:return self.matched_dict.update({'departure_time': is_matched})
    def convert24(self,str1):
	hour = str1[:2]
	str1 = str1[:2] + ':' + str1[-5:]
        if hour > 12 and 'am' in str1 or hour > 12 and 'AM' in str1 :
           try:
               slot_time = datetime.datetime.strptime(str1, '%H:%M%p')
           except:
               slot_time = datetime.datetime.strptime(str1, '%H:%M %p')
        else:
           try:
               slot_time = datetime.datetime.strptime(str1, '%I:%M%p')
           except:
               try:
                   slot_time = datetime.datetime.strptime(str1, '%H:%M%p')
               except:
                   slot_time = datetime.datetime.strptime(str1, '%H:%M %p')

	return slot_time	
    	
    def flightsnochecking(self,input_dict,output_dict):
	trip_type = input_dict['trip_type']
	input_flightno_list = []
	output_flightno_list = []
	try:
            for i in input_dict['oneway_dict']['segments']:
                input_flightno = i['flight_no'].replace(' ','')
                input_flightno_list.append(input_flightno)
	except:
	    for i in input_dict['oneway_dict']:
		input_flightno = i['flight_no']
                input_flightno_list.append(input_flightno)
	for nod in output_dict['oneway_dict']['segment_details']:
	    output_flightno = nod['flight_no'].replace(' ','')
	    output_flightno_list.append(input_flightno)
	final_data  = [x for x in input_flightno_list if x not in output_flightno_list]
	if final_data:is_matched =False
        else:is_matched =True
	if trip_type == 'RT' and is_matched == True:
            input_flightno_list = []
            output_flightno_list = []
            for i in input_dict['return_dict']['segments']:
                input_flightno = i['flight_no'].replace(' ','')
                input_flightno_list.append(input_flightno)
            for nod in output_dict['return_dict']['segment_details']:
                output_flightno = nod['flight_no'].replace(' ','')
                output_flightno_list.append(input_flightno)
            final_data  = [x for x in input_flightno_list if x not in output_flightno_list]
            if final_data:is_matched =False
            else: is_matched =True
            return self.matched_dict.update({'return_flightno':is_matched})
	else:return self.matched_dict.update({'flight_no': is_matched})
    def segmentschecking(self,input_dict,output_dict):
	trip_type = input_dict['trip_type']
	input_segment = input_dict['origin_code'] + '-' + input_dict['destination_code']
	output_segment = output_dict['oneway_dict']['segment_name']
	if ''.join(input_segment) == ''.join(output_segment):is_matched = True
	else:is_matched =False
	if trip_type == 'RT' and is_matched == True:
            input_segment = input_dict['destination_code'] + '-' + input_dict['origin_code']
            output_segment = output_dict['return_dict']['segment_name'].replace(' ','')
            if ''.join(input_segment) == ''.join(output_segment):is_matched = True
            else: is_matched =False
            return self.matched_dict.update({'return_segment':is_matched})
	else:return self.matched_dict.update({'segment':is_matched})
