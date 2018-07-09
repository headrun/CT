import re
import json
import base64
import smtplib
import MySQLdb
import datetime
from ast import literal_eval
from scrapy import signals
from webcheckin_scrapers.utils import *
from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher

from selenium import webdriver
from selenium.webdriver.common.by import By #1
from selenium.webdriver.support.ui import WebDriverWait #2
from selenium.webdriver.support import expected_conditions as EC #3
from pyvirtualdisplay import Display
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from ConfigParser import SafeConfigParser
import signal
from lxml import html
import time
from webcheckin_scrapers.utils import *
from scrapy.conf import settings

class SpiceJetCheckinBrowse(Spider):
    name = "spicejetcheckin_selenium"
    start_urls = ["https://book.spicejet.com/searchwebcheckin.aspx"]
    handle_httpstatus_list = [404, 500]

    def __init__(self, *args, **kwargs):
        super(SpiceJetCheckinBrowse, self).__init__(*args, **kwargs)
	self.log = create_logger_obj('spicejet_webcheckin')
	self.check_dict = kwargs.get('jsons', {})
	self.ckeckin_dict = {}

        db_cfg = SafeConfigParser()
        db_cfg.read(settings['BOOK_DB_PATH'])
        host = db_cfg.get('webcheckin', 'IP')
        passwd = db_cfg.get('webcheckin', 'PASSWD')
        user = db_cfg.get('webcheckin', 'USER')
        db_name = db_cfg.get('webcheckin', 'DBNAME')
        self.conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = db_name, charset="utf8", use_unicode=True)
        self.cur = self.conn.cursor()
	self.insert_query = 'insert into spicejet_webcheckin_status (sk, tripid, airline, status_message, error_message, created_at, modified_at) values(%s,%s,%s,%s,%s,now(),now())  on duplicate key update modified_at=now(), sk=%s, tripid=%s, status_message=%s, error_message=%s'
	#driver = self.get_driver()
	self.driver = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs')
        self.base_url = "https://book.spicejet.com/searchwebcheckin.aspx"
	dispatcher.connect(self.spider_closed, signals.spider_closed)

    def get_driver(self):
    	self.display = Display(visible=0, size=(800,600))
    	self.display.start()
    	chrome_options = Options()
    	chrome_options.add_argument("--dns-prefetch-disable")
    	chrome_options.add_argument('headless')
    	chrome_options.add_argument('no-sandbox')
    	driver = webdriver.Chrome('/usr/local/bin/chromedriver', chrome_options=chrome_options)
    	driver.set_page_load_timeout(15)
    	self.driver = driver
	return self.driver

    def spider_closed(self, spider):
	#self.display.stop()
        self.cur.close()
        self.conn.close()
	self.driver.service.process.send_signal(signal.SIGTERM)
	self.driver.quit()

    def insert_into_db(self, input_dict, error):
	pnr = input_dict.get('pnr', '')
	status_message = input_dict.get('status', 'Failed')
	trip_id = input_dict.get('trip_ref', '')
	vals = (pnr, trip_id, 'SpiceJet', status_message, error, pnr, trip_id, status_message, error)
	self.cur.execute(self.insert_query, vals)

    def parse(self, response):
	sel = Selector(response)
	try: input_dict = eval(self.check_dict)
	except: input_dict = {}
	if input_dict:
	    pnr = input_dict.get('pnr', '').strip()
	    last_name = input_dict.get('last_name', '').strip()
	    email = input_dict.get('email', '').strip()
	    if not email:
		self.insert_into_db(input_dict, 'Email is mandatory')
		self.driver.quit()
		return
	else:
	    self.driver.quit()
	    return
	driver = self.driver
	try:
		driver.get(self.base_url)
		driver.wait = WebDriverWait(driver, 15)
	except Exception as e:
		self.log.debug('Something wrong %s' % e)
		self.insert_into_db(input_dict, "Failed to open the checkin url")
		driver.quit()
	time.sleep(3)
	self.log.debug('Came here succussfully')
	try:
		driver.find_element_by_id("CONTROLGROUPSEARCHWEBCHECKINVIEW_BookingRetrieveInputSearch1WebCheckinView_ConfirmationNumber").clear()
	except Exception as e:
		self.log.debug(e)
		self.insert_into_db(input_dict, "Failed to open the checkin url")
		driver.quit()
	time.sleep(4)
	driver.find_element_by_id("CONTROLGROUPSEARCHWEBCHECKINVIEW_BookingRetrieveInputSearch1WebCheckinView_CONTACTEMAIL1").clear()
	driver.find_element_by_id("CONTROLGROUPSEARCHWEBCHECKINVIEW_BookingRetrieveInputSearch1WebCheckinView_ConfirmationNumber").send_keys(pnr)
	driver.find_element_by_id("CONTROLGROUPSEARCHWEBCHECKINVIEW_BookingRetrieveInputSearch1WebCheckinView_CONTACTEMAIL1").send_keys(email)
        try:
                driver.find_element_by_id("CONTROLGROUPSEARCHWEBCHECKINVIEW_BookingRetrieveInputSearch1WebCheckinView_ButtonRetrieve").click()
		driver.wait = WebDriverWait(driver, 15)
        except:
                self.insert_into_db(input_dict, "Failed to fetch PNR details")
		driver.quit()
                return
        try:
		time.sleep(5)
		if 'T & Cs' in driver.page_source:
                	driver.find_element_by_name("T & Cs").click()
                	driver.find_element_by_id("WebcheckinTermsAccept").click()
			driver.wait = WebDriverWait(driver, 15)
		else: pass
        except:
                self.insert_into_db(input_dict, "Terms & Conditions not found")
		driver.quit()
                return

	time.sleep(5)
	source_page = driver.page_source
        sel = Selector(text=source_page)
        alert_message = ''.join(sel.xpath('//div[@id="errorSectionContent"]/p/text()').extract())
	if 'ViewFlight' not in driver.current_url:
		self.insert_into_db(input_dict, alert_message)
		driver.quit()
		return
        checkin_done = sel.xpath('//div[@class="boarding-pass-conatiner"]/a[@id="BoardingPassRequest"]/text()').extract()
        if checkin_done:
		input_dict['status'] = "Web checkin successful"
        	self.insert_into_db(input_dict, "")
		driver.quit()
        	return
        canceled_pnr = sel.xpath('//span[@id="changeSeat"]/a/text()').extract()
        pax_table = sel.xpath('//table[@id="checkinPassengerTable"]//tr')
        view_state = ''.join(sel.xpath('//input[@id="viewState"]//@value').extract())
        seat_dict = {}
        for pax in pax_table:
            pax_checkin_id = ''.join(pax.xpath('.//div[@id="webCheckinPaxDetails"]//span[@class="chkbx"]/input/@id').extract())
            seat_no = ''.join(pax.xpath('.//td[@class="seatAssignmentsSeatColumn"]/text()').extract())
            if pax_checkin_id:
                seat_dict[pax_checkin_id] = seat_no
        pax_keys = seat_dict.keys()
        if not pax_keys and canceled_pnr:
        	#self.insert_into_db(input_dict, "User Already checked in")
		input_dict['status'] = "Web checkin successful"
		self.insert_into_db(input_dict, "")
		driver.close()
		driver.quit()
        	return
        seat_check = seat_dict.values()
        if '' in seat_check:
        	self.insert_into_db(input_dict, "Assign Seat to Begin Check-in")
		driver.quit()
        	return
        if not pax_keys:
                self.insert_into_db(input_dict, "PNR got cancelled")
		driver.quit()
                return
	time.sleep(5)
        try:
		if "ControlGroupViewFlightView_LinkButtonAddOn" in driver.page_source:
			#driver.find_element_by_id("ControlGroupViewFlightView_LinkButtonAddOn").click()
        		#driver.find_element_by_xpath("//div[@id='continue-to-addons-page']").click()
			driver.find_element_by_id("ControlGroupViewFlightView_LinkButtonAddOn").click()
			time.sleep(5)
			#driver.find_element_by_xpath("//div[@id='continue-to-addons-page']/span").click()
			driver.find_element_by_xpath('//span[@class="forward-icon"]').click()
		else: pass
	except:
		self.insert_into_db(input_dict, "Failed to navigate Addons page")
		driver.quit()
		return
	sel = Selector(text=driver.page_source)
	ph_no = ''.join(sel.xpath('//input[@name="ControlGroupContactChangeConfirmView$ContactInputContactChangeConfirmView$TextBoxHomePhone"]/@value').extract())
	if len(ph_no) == 12:
		ph_no = ph_no[2:]
		driver.find_element_by_id("ControlGroupContactChangeConfirmView_ContactInputContactChangeConfirmView_TextBoxHomePhone").clear()
		driver.find_element_by_id("ControlGroupContactChangeConfirmView_ContactInputContactChangeConfirmView_TextBoxHomePhone").send_keys(ph_no)
	try:
		driver.find_element_by_id("ControlGroupContactChangeConfirmView_LinkButtonSubmit").click()
	except:
		self.insert_into_db(input_dict, "Failed to submit webcheckin")
		driver.quit()
		return
	time.sleep(10)
	sel = Selector(text=driver.page_source)
	boading_pass = ''.join(sel.xpath('//div[@class="boardingPass top"]//div//h2/text()').extract())
	if not boading_pass:
		self.insert_into_db(input_dict, "Failed to submit webcheckin")
		with open('sg_%s'%input_dict.get('trip_ref', ''), 'w+') as f:
		    f.write('%s'%driver.page_source)
		driver.quit()
		return
        else:
		input_dict['status'] = "Web checkin successful"
        	self.insert_into_db(input_dict, "")
		driver.quit()
