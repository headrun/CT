from configobj import ConfigObj
from scrapy.xlib.pydispatch import dispatcher
import scrapy
from scrapy.selector import Selector
from scrapy.http import Request
from scrapy.http import FormRequest
from Hotels.items import *
import os
import json
import datetime
import time
import urllib
from Hotels.utils import *
from Hotels.auto_config import AUTO_HTTP_PROXY
import re
import MySQLdb
import collections
import csv
import sys
from lxml import etree
import logging
from scrapy import log
from scrapy import signals
from selenium import webdriver
from trivago_hotel_mapper import dict_mapper
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
reload(sys)
sys.setdefaultencoding('utf-8')

class Trivago(scrapy.Spider):
    name = 'trivago_terminal'
    handle_httpstatus_list = [400,404,500,503,403]
    start_urls = ['https://www.trivago.in/']

    def __init__(self, *args, **kwargs):
        super(Trivago, self).__init__(*args, **kwargs)
        self.name='Trivago'
	self.delete_crawl = "delete from Trivago_crawl where "
	self.update_query_ta = "update Trivago_crawl set crawl_status=%s where sk = '%s'"
	self.cursor = create_crawl_table_cusor()
        self.log = create_logger_obj(self.name)
        self.crawl_type = kwargs.get('crawl_type','keepup')
        self.content_type = kwargs.get('content_type','hotels')
        self.limit = kwargs.get('limit',1000)
	self.out_put_file =get_gobtrip_file(self.name)
	self.update_query_ta = "update Trivago_crawl set crawl_status=%s where sk = '%s'"
	dispatcher.connect(self.spider_closed, signals.spider_closed)


    def get_driverc(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('headless')
        chrome_options.add_argument('no-sandbox')
        #chrome_options.add_argument('--proxy-server=%s' % PROXY)
        CHROME = {
        "browserName": "chrome",
                "version": "",
                "platform": "ANY",
                "javascriptEnabled": True,
                "chrome.prefs": {"profile.managed_default_content_settings.images": 2},
                "proxy": {
                    "httpProxy":AUTO_HTTP_PROXY.split('//')[-1],
                    "ftpProxy":None,
                    "sslProxy":None,
                    "noProxy":None,
                    #"socksUsername":AUTO_HTTP_PROXY.split('@')[-1].split('.')[0],
                    #"socksPassword":AUTO_HTTP_PROXY.split('@')[0].split(':')[-1],
                    "proxyType":"MANUAL",
                    "class":"org.openqa.selenium.Proxy",
                    "autodetect":False
                    },
                "chrome.switches": ["window-size=1003,719", "allow-running-insecure-content", "disable-web-security", "no-referrers"],
                }
        driver =  webdriver.Chrome('/usr/local/bin/chromedriver', chrome_options=chrome_options, desired_capabilities=CHROME)
        return driver


    def spider_closed(self,spider):
	self.cursor.close()
	gob_crawlout_processing(self.out_put_file)

    def parse(self, response):
	rows = terminal_trivago_requests(self.cursor, self.name, self.crawl_type, self.content_type, self.limit)
	if rows:
		for row in rows:
			sk, dx, los, city_name, city_id, latitude, longitude, crawl_type, content_type, start_date, end_date, crawl_status, reference_url = row
			aux_info = {"sk":sk , "dx":dx, "los":los, "city_name":city_name, "city_id":city_id, "latitude":latitude, "longitude":longitude, "crawl_type":crawl_type, "content_type":content_type, "start_date":start_date, "end_date":end_date, "crawl_status":crawl_status}
			driver = self.get_driverc()
			driver.get(reference_url)
			time.sleep(0.5)
			html_source = driver.page_source
			sel =  etree.HTML(html_source)
			nodes = sel.xpath('//li[@class="hotel item-order__list-item js_co_item"]')
			if nodes:
				toggle_buttons = driver.find_elements_by_xpath('//button[@class="deal-other__more btn--reset item__slideout-toggle"]')
                                if not toggle_buttons:
                                        toggle_buttons = driver.find_elements_by_xpath('//button[contains(@class, "deal-other__more")]')

				if toggle_buttons:
					for dea in toggle_buttons:
						try: dea.click()
						except:	pass
						time.sleep(0.5)
						if 'slideout-loader__shimmer' in driver.page_source or 'div class="dummy-loader"' in driver.page_source:
							time.sleep(1.5)
				show_more_buttons = driver.find_elements_by_xpath('//button[contains(text(),"Show more")]')
				if show_more_buttons:
					for shdea in show_more_buttons:
						try: shdea.click()
						except: pass
						time.sleep(0.5)
						if 'slideout-loader__shimmer' in driver.page_source or 'div class="dummy-loader"' in driver.page_source:
							time.sleep(0.5)
				html_source = driver.page_source
				sel =  etree.HTML(html_source)
				nodes = sel.xpath('//li[@class="hotel item-order__list-item js_co_item"]')
				for nod in nodes:
					hotel_name = ''.join(nod.xpath('.//div[@itemprop="name"]/h3/@title'))
					hotel_id = ''.join(nod.xpath('.//self::li/@data-item'))
					city_id = ''.join(nod.xpath('./self::li/@data-path'))
					city_name = nod.xpath('.//p[@class="details__paragraph"]//text()')
					if city_name:
						city_name = ''.join(city_name[0].strip().strip(','))
					rank1 = ''.join(nod.xpath('.//em[contains(@class, "item__deal-best-ota")]/text()'))
					alter_dic  = nod.xpath('.//ul[@class="deal-other__top-alternatives"]/li/button/text()')
					rank_dict = {}
					rank_dict.update({"rank1":rank1})
					rank_ = 2
					for alter_di in alter_dic:
						rank_dict.update({"%s%s"%("rank", str(rank_)):alter_di})
						rank_ += 1
					vendors_list = {"ct_price":"", "ct_type":"", "expedia_price":"", "expedia_type":"", "hotelsd_com_price":"", "hotelsd_com_type":"", "booking_com_price":"", "booking_com_type":"", "hotelsinfo_price":"", "hotelsinfo_type":"", "mmt_price":"", "mmt_type":"", "agoda_price":"", "agoda_type":"", "amoma_price":"", "amoma_type":"", "hrs_price":"", "hrs_type":""}
					below_nods = nod.xpath('.//div[@class="sl-box__content"]/div[contains(@class,"js_co_dea")]')
					if not below_nods:
						below_nods = nod.xpath('.//li[contains(@class,"js_co_dea")][@onclick]')
					for option in below_nods:
						option_name = ''.join(option.xpath('.//img[contains(@class, "deal__logo-img")]/@title'))
						option_price = ''.join(option.xpath('.//span[contains(@class, "deal__btn-lbl")]/text()'))
						if option_price:
							option_price = option_price.split(u'\u20b9')[-1]
						option_price = option_price.replace(u'\u200e', '')
						option_price = option_price.strip().replace(',', '')
						option_type = ''.join(option.xpath('.//span[contains(@class, "sl-deal__text-desc")]/text()'))
						if not option_type:
							option_type = ''.join(option.xpath('.//span[contains(@class, "block text-overflow")]/text()'))
						if option_name == "Cleartrip" and vendors_list['ct_price']=='':
							vendors_list['ct_price'] = option_price
							vendors_list['ct_type'] = option_type
						if option_name == "Expedia" and vendors_list['expedia_price'] == '':
							vendors_list['expedia_price'] = option_price
							vendors_list['expedia_type'] = option_type
						if option_name == "Hotels.com" and vendors_list['hotelsd_com_price'] == '':
							vendors_list['hotelsd_com_price'] = option_price
							vendors_list['hotelsd_com_type'] = option_type
						if option_name == "Booking.com" and vendors_list['booking_com_price'] == "":
							vendors_list['booking_com_price'] = option_price
							vendors_list['booking_com_type'] = option_type
						if option_name == "Hotel.info" and vendors_list['hotelsinfo_price'] == "":
							vendors_list['hotelsinfo_price'] = option_price
							vendors_list['hotelsinfo_type'] = option_type
						if option_name == "makemytrip" and vendors_list['mmt_price'] == "":
							vendors_list['mmt_price'] = option_price
							vendors_list['mmt_type'] = option_type
						if option_name == "Agoda" and vendors_list['agoda_price'] == "":
							vendors_list['agoda_type'] = option_type
							vendors_list['agoda_price'] = option_price
						if option_name == "Amoma.com" and vendors_list['amoma_price'] == "":
							vendors_list['amoma_price'] = option_price
							vendors_list['amoma_type'] = option_type
						if option_name == "HRS.com" and vendors_list['hrs_price'] == "":
							vendors_list['hrs_price'] = option_price
							vendors_list['hrs_type'] = option_type
					prices_list = [value for key,value in vendors_list.iteritems() if 'price' in key]
					except_ct_price = [value for key,value in vendors_list.iteritems() if '_price' in key and key != 'ct_price']
					except_ct_price = filter(None, except_ct_price)
					available_otas = filter(None, prices_list)
					available_count_otas = len(available_otas)
					price_difference, beaten_by_booking, to_find_cheaper = 0, 'No', []
					try:
						to_find_cheaper = [(key,int(value.replace(',',''))) for key,value in vendors_list.iteritems() if '_price' in key and value != '']
					except:
						to_find_cheaper = []
					if to_find_cheaper:
						key_value_of_cheaper_price = min(to_find_cheaper, key = lambda t: t[1])
						if key_value_of_cheaper_price:
							cheaper_price = key_value_of_cheaper_price[1]
							ct_price = vendors_list['ct_price']
							if ct_price and cheaper_price:
								price_difference = int(ct_price) - int(cheaper_price)
					if 'booking.com' in  rank_dict.get('rank1','').lower():
						beaten_by_booking = 'Yes'
					beaten_count = 0
					if except_ct_price:
						for non_ct in except_ct_price:
							if vendors_list['ct_price']:
								if int(vendors_list['ct_price']) > int(non_ct):
									beaten_count += 1
					inner_sk = '%s_%s' %(hotel_id, aux_info.get('sk', ''))
					cleartrip_hotel_id = dict_mapper.get(hotel_id, '')
					total_dict = TRIVAGOItem()
					total_dict.update({"sk":normalize(inner_sk),
		 "crawl_table_sk":normalize(aux_info.get('sk', '')), "city":normalize(city_name), "cleartrip_hotel_id":normalize(cleartrip_hotel_id), 
		"hotel_name":normalize(hotel_name), "trivago_hotel_id":normalize(hotel_id),
	 	"check_in":normalize(str(aux_info.get('start_date', ''))), "los":normalize(str(aux_info.get('los', ''))), 
		"rank1":normalize(rank_dict.get('rank1', 'NA')), "rank2":normalize(rank_dict.get('rank2', 'NA')), 
		"rank3":normalize(rank_dict.get('rank3', 'NA')), "rank4":normalize(rank_dict.get('rank4', 'NA')),
        	"ct_price":normalize(vendors_list.get('ct_price', "NA")), "ct_type":normalize(vendors_list.get('ct_type', "NA")), 
		"expedia_price":normalize(vendors_list.get('expedia_price', "NA")), "expedia_type":normalize(vendors_list.get('expedia_type', "NA")),
	 	"hotelsdot_com_price":normalize(vendors_list.get('hotelsd_com_price', "NA")), "hotelsdot_com_type":normalize(vendors_list.get('hotelsd_com_type', "NA")), 
		"bookingdot_com_price":normalize(vendors_list.get('booking_com_price', "NA")), "bookingdot_com_type":normalize(vendors_list.get('booking_com_type', "NA")),
		"hotel_info_price":normalize(vendors_list.get('hotelsinfo_price', "NA")), "hotel_info_type":normalize(vendors_list.get('hotelsinfo_type', "NA")),
		"mmt_price":normalize(vendors_list.get('mmt_price', "NA")), "mmt_type":normalize(vendors_list.get('mmt_type', "NA")),
		"agoda_price":normalize(vendors_list.get('agoda_price', "NA")), "agoda_type":normalize(vendors_list.get('agoda_type', "NA")),
		"amoma_price":normalize(vendors_list.get('amoma_price', "NA")), "amoma_type":normalize(vendors_list.get('amoma_type', "NA")),
		"hrs_price":normalize(vendors_list.get('hrs_price', "NA")), "hrs_type":normalize(vendors_list.get('hrs_type', "NA")),
		"available_otas": normalize(str(available_count_otas)), "price_difference":normalize(str(price_difference)), "beaten_by_booking_com":normalize(str(beaten_by_booking)),"beaten_by_price":normalize(str(beaten_count)),  "aux_info":"", "check_out":normalize(str(aux_info.get('end_date', ''))), "reference_url":normalize(reference_url)})
					yield total_dict
			if nodes:
				self.cursor.execute(self.update_query_ta % ('1', aux_info.get('sk')))
			else:
				self.cursor.execute(self.update_query_ta % ('10', aux_info.get('sk')))
			if nodes:
				next_navigation_page = sel.xpath('//div[@class="pagination__pages"]/strong/following-sibling::button[1]/text()')
				if not next_navigation_page:
					try:
						list_of_other_sk = []
						off_date = re.findall('_(\d+)_(\d+-\d+-\d+)', sk)[0]
						current_page_offset = int(off_date[0])+25
						for ofse in range(current_page_offset, 500, 25):
							other_sk = re.sub('_(\d+)_\d+-\d+-\d+', '%s%s%s%s' %('_', str(ofse), '_', off_date[1]), sk)
							if other_sk:
								list_of_other_sk.append(other_sk)
						if list_of_other_sk:
							other_delete = "%s%s" % (self.delete_crawl, ' or '.join(['sk="%s"'  %lio for lio in list_of_other_sk]))
							self.cursor.execute(other_delete)
					except: 
						pass
			driver.quit()			
