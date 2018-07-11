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
import csv
from datetime import datetime
import md5
import  MySQLdb
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from scrapy.selector import Selector
import os
import re
import ast
import json
import csv
import sys
import md5
import MySQLdb
import hashlib
import datetime
import operator
import logging
import requests
#from CTPCC.utils import *
from scrapy import log
from scrapy import signals
from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher
from itertools import groupby

class AirAsia(Spider):
    name = "airasia"
    start_urls = ["https://booking2.airasia.com/AgentHome.aspx"]

    def __init__(self, *args, **kwargs):
        super(AirAsia, self).__init__(*args, **kwargs)
        self.inputdict = kwargs.get('dict', '')
	self.output_list = []

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
		driver.find_element_by_id("MyBookings").click()
		time.sleep(3)
		driver.wait = WebDriverWait(driver, 3)
		time.sleep(3)
		driver.find_element_by_id("ControlGroupBookingListView_BookingListSearchInputView_RadioForAgency").click()
		driver.find_element_by_xpath("//select[@id='ControlGroupBookingListView_BookingListSearchInputView_DropDownListTypeOfSearch']/option[@value='5']").click()
		driver.find_element_by_id("ControlGroupBookingListView_BookingListSearchInputView_TextBoxKeyword").clear()
		driver.find_element_by_id("ControlGroupBookingListView_BookingListSearchInputView_TextBoxKeyword").send_keys("sharma,sakshi")
		driver.find_element_by_id("ControlGroupBookingListView_BookingListSearchInputView_LinkButtonFindBooking").click()
		time.sleep(6)
		time.sleep(8)
		source_page = driver.page_source
		sel = Selector(text=source_page)
		searchedcheck = ''.join(sel.xpath("//div[@id='errorSectionContent']").extract())
		if not searchedcheck:
			rows = sel.xpath('//div[@class="redSectionHeader"]/div[contains(.,"Current bookings")]/../following-sibling::table/tbody')[0]
			modify_ids = rows.xpath('.//a[contains(@id,"ControlGroupBookingListView_BookingListSearchInputView_HyperLinkModify_currentTravel")]/@id').extract()
			if not ''.join(modify_ids):
				print "Current bookings are not available for your searched name"
			if self.inputdict:
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
					print key , value
					input_date = input_dict.get('departure_date','')
					input_date = datetime.datetime.strptime(input_date,  '%d-%b-%y')
					if input_date == output_date:
						modify_id = key
						driver.find_element_by_id(modify_id).click()
						source_page = driver.page_source
						self.parse_ne(source_page,input_dict,driver)
						break
					else:
						print "Not Matched"
									
			else:
				print "Inputs values are not there"
		else:
			print "Please enter valid lastname , firstname "
	else:
		print "Please enter valid username and password"
    def parse_ne(self,response,input_dict,driver):
    	output_dict = {}
	input_dict = [input_dict]
	source_page = driver.page_source
	sel = Selector(text=source_page)
	booking_number = ''.join(sel.xpath("//span[@id='OptionalHeaderContent_lblBookingNumber']/text()").extract())
	if booking_number:
		output_dict.update({"booking_number":booking_number})
	segment_name = ''.join(sel.xpath('//table[@class="rgMasterTable"]/thead/tr/th/text()').extract()[1])
	if segment_name:
		segment_name = segment_name
		output_dict.update({'segment_name':segment_name})
	details_node = sel.xpath('//div[@id="ctl00_OptionalHeaderContent_radGridDepartTable"]/table/tbody/tr/td')
		
	flight_no = ''.join(details_node[0].xpath('./div/text()').extract())
	if flight_no and '\n' not in flight_no:
		flight_no = flight_no
		output_dict.update({'flight_no':flight_no})
	departure_dates = ''.join(details_node[1].xpath('.//div[@class="left itineraryCustom4"]//text()[contains(.,", ")]').extract())
	if departure_dates:
		departure_date = departure_dates.split(',')[0].strip()
		dep_time = departure_dates.split(',')[1].split('(')[1].replace(')','').replace('AM','').replace('PM','').strip()
		output_dict.update({'departure_date':departure_date , 'dep_time':dep_time})
	arrival_dates = ''.join(details_node[2].xpath('.//div[@class="left itineraryCustom4"]//text()[contains(.,", ")]').extract())
	if arrival_dates:
		arrival_date = arrival_dates.split(',')[0].strip()
		arr_time = arrival_dates.split(',')[1].split('(')[1].replace(')','').replace('AM','').replace('PM','').strip()
		output_dict.update({'arrival_date':arrival_date,'arr_time':arr_time})
	names = sel.xpath('//span[@class="guest-detail-name"]//text()').extract()
	name_dict = {}
	count = 0
	for name in names:
		count = count + 1
		name_dict.update({'adult'+str(count):name.strip()})
	if bool(name_dict):
		no_of_passengers = len(names)
		output_dict.update({'no_of_passengers':no_of_passengers})
		output_dict.update({'pax_details':name_dict})
	email = ''.join(sel.xpath('//div[@class="RadGrid RadGrid_AirAsiaBooking2"]/table/tbody/tr/td//p[contains(.,"Email")]/text()').extract())
	no_of_passengers = len(names)
	
	if email:
		if ':' in email:
			email = email.split(':')[1].strip()
		output_dict.update({'email':email})
	date_of_birth = ''.join(sel.xpath('//div[@class="RadGrid RadGrid_AirAsiaBooking2"]/table/tbody/tr/td//p[contains(.,"Date of Birth")]/text()').extract()).replace(': ','').strip()
	if date_of_birth:
		date_of_birth = date_of_birth
		output_dict.update({'date_of_birth':date_of_birth})
	self.output_list.append(output_dict)
	for i in input_dict:
                input_no_of_passengers = int(i['no_of_infants']) + int(i['no_of_children']) + int(i['no_of_adults'])
                input_passengers = i['pax_details']
                input_names_dict = {}
                count = 0
                for key in input_passengers.keys():
                        count = count +1
                        name_list = input_passengers[key]
                        name = ' '.join(name_list[1:(len(name_list)-3)])
                        input_names_dict.update({'adult'+str(count):name})


                for i1 in self.output_list:
                        output_passengers =i1['no_of_passengers']
                        if i['all_segments'][0]['default']['segments'][0]['segment_name'] == i1['segment_name'].replace(' - ','-'):
                                if i['all_segments'][0]['default']['segments'][0]['flight_no'] == i1['flight_no']:
                                        if i['departure_date'] == i1['departure_date'].replace(' ','-').replace('20',''):
                                                if i1['dep_time'] in i['all_segments'][0]['default']['segments'][0]['dep_time']:
                                                        if input_no_of_passengers == output_passengers:
                                                                names_list1 = input_names_dict.values()
                                                                names_list2 = name_dict.values()
                                                                for name1 in names_list1:
                                                                        for name2 in names_list2:
                                                                                if name2.replace('  ',' ') != name1:
                                                                                        print "No of passengers are not matched"
                                                                if i['emailid'] == i1['email']:
                                                                        print booking_number + "Matched"
                                                                else:
                                                                        print "Email id is not matched"


                                                        else:
                                                                print "No of passengers are not matched"

                                                else:
                                                        print "Departure time not matched"
                                        else:
                                                print "Departure date not matched"
                                else:
                                        print "Filght number not matched"
                        else:
					print " Not matched "
