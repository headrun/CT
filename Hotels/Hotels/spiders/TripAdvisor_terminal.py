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
import re
import MySQLdb
import collections
import csv
import logging
from scrapy import log
from scrapy import signals


def Strp_times(dx, los):
    date_ = datetime.datetime.now() + datetime.timedelta(days=int(dx))
    dx = date_.strftime('%Y_%m_%d')
    los_date = date_ + datetime.timedelta(days=int(los))
    los = los_date.strftime('%Y_%m_%d')
    return (dx, los)

def create_crawl_table_cursor():
    conn = MySQLdb.connect(host='localhost', user='root', db='urlqueue_dev', charset='utf8', use_unicode=True)
    cur = conn.cursor()
    return cur



class TripAdvisor(scrapy.Spider):
    name = 'tripadvisoro_terminal'
    handle_httpstatus_list = [400,404,500,503,403]
    start_urls = ['https://www.tripadvisor.in/']

    def __init__(self, *args, **kwargs):
        super(TripAdvisor, self).__init__(*args, **kwargs)
        self.name='Tripadvisor'
	self.update_query_ta = "update Tripadvisor_crawl set crawl_status=%s where sk = '%s'"
	self.headers = {
       'Accept-Encoding': 'gzip, deflate, br',
       'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
       'Upgrade-Insecure-Requests': '1',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
       'Connection': 'keep-alive',
       }
	self.cursor = create_crawl_table_cusor()
        self.log = create_logger_obj(self.name)
        self.crawl_type = kwargs.get('crawl_type','keepup')
        self.content_type = kwargs.get('content_type','hotels')
        self.limit = kwargs.get('limit',1000)
	self.dx_val = kwargs.get('dx', '')
	self.out_put_file =get_gobtrip_file(self.name)
	dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self,spider):
	self.cursor.close()
	gob_crawlout_processing(self.out_put_file)

    def parse(self, response):
	rows = terminal_tripadvisor_requests(self.cursor, self.name, self.crawl_type, self.content_type, self.dx_val, self.limit)
	if rows:
		for row_inner in rows:
			sk, ta_url, dx, los, pax, start_date, end_date,\
			ctid, hotel_id, hotel_name, aux_info = row_inner
			DX_num = str(dx)
			LOS_num = str(los)
			PAX_val = str(pax)
			ctid = str(ctid)
			hotel_id = str(hotel_id)
			dxs, loss = str(start_date), str(end_date)
			city_name = json.loads(aux_info).get('city_name', '')
			date_time_ = time.time()
			full_ti = str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(date_time_)))
			date_time = str(date_time_).split('.')[0]
			index_count = True
			counter_number = 0
			while index_count:
				trip_advisor_url = "https://www.tripadvisor.in/MiniMetaCRAjax?detail=%s&staydates=%s_%s&rooms=1&adults=%s&child_rm_ages=&area=QC_Meta_Mini&returnAllOffers=true&imp=true&metaReferer=Hotel_Review&baseLocId=%s&metaRequestTiming=%s&finalRequest=true" % (hotel_id, dxs, loss, PAX_val, hotel_id, date_time)
				yield Request(trip_advisor_url, callback = self.parse_next, headers = self.headers, meta ={"req":counter_number, "ta_url":ta_url, "city_name":city_name, "hotel_name":hotel_name, "hotel_id":hotel_id, "dxs":dxs.replace('_', '-'), "DX_num" : DX_num, "PAX_val":PAX_val, "full_time": full_ti, 'ta_url':ta_url, 'sk':sk, 'loss':loss}, dont_filter = True)
				counter_number += 1
				if counter_number == 3:
					index_count = False
				
    def parse_next(self, response):
	if response.meta.get('req') == 2:
		sel = Selector(response)
		check_loading = sel.xpath('//div[@class="loading"]/img[@class="rightSprite loading_bubbles_gry"]/@src').extract()
		tracking_check = ''.join(sel.xpath('//div[@class="impressionTrackingTree"]/comment()').extract())
		if (check_loading and '\PP:' in tracking_check) or (check_loading):
			self.cursor.execute(self.update_query_ta % ('8', response.meta.get('sk')))
		else:
			final_dict = {}
			if tracking_check and not check_loading:
				tracking_check_ = tracking_check.split('\\\\N')
				for tch in tracking_check_:
					rank = ''.join(re.findall(':(\d+)/PT', tch))
					vendor = ''.join(re.findall('\\PN:(.*?)\\\\', tch))
					price = ''.join(re.findall('\\PP:(.*?)\\\\', tch))
					tax = ''.join(re.findall('\\PF:(.*?)\\\\',tch))
					status = ''.join(re.findall('\\PA:(.*?)\\\\',tch))
					if not rank:
						rank = '-'
					if not vendor:
						vendor = '-'
					if not price:
						price = '0'
					if not tax:
						tax = '0'
					if not status:
						status = '-'
					total = int(price)+int(tax)
					final_dict.update({vendor:[rank, vendor, price, tax, status, total]})
			if not tracking_check:
				self.log.info("Not getting data for the response url : %s" % response.url)
				self.cursor.execute(self.update_query_ta % ('10', response.meta.get('sk')))
			if check_loading:
				self.log.info("More time taking to get response : %s" % response.url)
				self.cursor.execute(self.update_query_ta % ('7', response.meta.get('sk')))
			if final_dict:
				to_find_cheaper = [(int(val[2]), val[1]) for val in final_dict.values() if val[2] != '0']
				min_fin = {}
				if to_find_cheaper:
					min_fin = min(to_find_cheaper, key = lambda t: t[0])
				if min_fin:
					min_fin = { min_fin[1] : min_fin[0]}
				for keyf, valuf in final_dict.iteritems():
					if keyf in min_fin.keys():
						cheaper = 'Y'
					else:
						cheaper = 'N'
					final_dict[keyf].extend(cheaper)
				agoda = final_dict.get('Agoda', ['-', '-', '-', '-', '-', '-', '-'])
				booking_com = final_dict.get('BookingCom', ['-', '-', '-', '-', '-', '-', '-'])
				cleartrip = final_dict.get('ClearTrip', ['-', '-', '-', '-', '-', '-', '-'])
				expedia = final_dict.get('Expedia', ['-', '-', '-', '-', '-', '-', '-'])
				goibibo = final_dict.get('Goibibo', ['-', '-', '-', '-', '-', '-', '-'])
				hotelscom = final_dict.get('HotelsCom2', ['-', '-', '-', '-', '-', '-', '-'])
				makemytrip = final_dict.get('MakeMyTrip', ['-', '-', '-', '-', '-', '-', '-'])
				yatra = final_dict.get('Yatra', ['-', '-', '-', '-', '-', '-', '-'])
				tg = final_dict.get('TG', ['-', '-', '-', '-', '-', '-', '-'])
				stayzilla = final_dict.get('Stayzilla', ['-', '-', '-', '-', '-', '-', '-'])
				total_dict = TRIPADVISORItem()
				total_dict.update({"sk":response.meta.get('sk', ''), "city_name":response.meta.get('city_name', ''), 
				"property_name":response.meta.get('hotel_name', ''),
				 "TA_hotel_id":response.meta.get('hotel_id', ''),
				 "checkin":response.meta.get('dxs'), "DX":response.meta.get('DX_num'),
				 "Pax":response.meta.get('PAX_val'), "Ranking_Agoda":agoda[0],
				 "Ranking_BookingCom":booking_com[0], "Ranking_ClearTrip":cleartrip[0],
				 "Ranking_Expedia":expedia[0], "Ranking_Goibibo":goibibo[0], 
				"Ranking_HotelsCom2":hotelscom[0], "Ranking_MakeMyTrip":makemytrip[0],
				 "Ranking_Yatra":yatra[0], "Ranking_TG":tg[0], "Price_Agoda":agoda[2],
				 "Price_BookingCom":booking_com[2], "Price_ClearTrip":cleartrip[2],
				 "Price_Expedia":expedia[2], "Price_Goibibo":goibibo[2],
				 "Price_HotelsCom2":hotelscom[2], "Price_MakeMyTrip":makemytrip[2],
				 "Price_Yatra":yatra[2], "Price_TG":tg[2], "Tax_Agoda":agoda[3],
				 "Tax_BookingCom":booking_com[3], "Tax_ClearTrip":cleartrip[3], 
				"Tax_Expedia":expedia[3], "Tax_Goibibo":goibibo[3], "Tax_HotelsCom2":hotelscom[3], 
				"Tax_MakeMyTrip":makemytrip[3], "Tax_Yatra":yatra[3], 
				"Tax_TG":tg[3], "Total_Agoda":agoda[5], "Total_BookingCom":booking_com[5],
				 "Total_ClearTrip":cleartrip[5], "Total_Expedia":expedia[5],
				 "Total_Goibibo":goibibo[5], "Total_HotelsCom2":hotelscom[5],
				 "Total_MakeMyTrip":makemytrip[5], "Total_Yatra":yatra[5], "Total_TG":tg[5], 
				"Cheaper_Agoda":agoda[6], "Cheaper_BookingCom":booking_com[6],
				 "Cheaper_ClearTrip":cleartrip[6], "Cheaper_Expedia":expedia[6],
				 "Cheaper_Goibibo":goibibo[6], "Cheaper_HotelsCom2":hotelscom[6],
				 "Cheaper_MakeMyTrip":makemytrip[6], "Cheaper_Yatra":yatra[6], 
				"Cheaper_TG":tg[6], "Status_Agoda":agoda[4], 
				"Status_BookingCom":booking_com[4], "Status_ClearTrip":cleartrip[4],
				 "Status_Expedia":expedia[4], "Status_Goibibo":goibibo[4], 
				 "Status_HotelsCom2":hotelscom[4], "Status_MakeMyTrip":makemytrip[4],
				 "Status_Yatra":yatra[4], "Status_TG":tg[4], 
				 "Ranking_Stayzilla":stayzilla[0], "Price_Stayzilla":stayzilla[2],
				 "Tax_Stayzilla":stayzilla[3], "Total_Stayzilla":stayzilla[5],
				 "Cheaper_Stayzilla":stayzilla[6], "Status_Stayzilla":stayzilla[4],
				 "Time" :response.meta.get('full_time', ''), "reference_url":response.url})
				yield total_dict
				self.cursor.execute(self.update_query_ta % ('1', response.meta.get('sk')))
