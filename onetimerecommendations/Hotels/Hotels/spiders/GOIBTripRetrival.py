import scrapy
from scrapy.selector import Selector
from scrapy.http import Request
from scrapy.http import FormRequest
import datetime
import json
import os
import time
import re
import sys
import MySQLdb
import logging
from scrapy import log
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from Hotels.utils import *
from Hotels.items import *
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class GOICrawltreterive(scrapy.Spider):
	name = "GOIBTRIP_terminal"
	handle_httpstatus_list = [400,404,500,503]

	def __init__(self,*args,**kwargs):
        	super(GOICrawltreterive,self).__init__(*args,**kwargs)
        	self.name = 'Goibibotrip'
        	self.log = create_logger_obj(self.name)
        	self.crawl_type = kwargs.get('crawl_type','keepup')
        	self.content_type = kwargs.get('content_type','hotels')
        	self.limit = kwargs.get('limit',1000)
        	self.out_put_file =get_gobtrip_file(self.name)
        	self.cursor = create_crawl_table_cusor()
		self.aux_info={}
		reload(sys)
		sys.setdefaultencoding("utf-8")
        	dispatcher.connect(self.spider_closed, signals.spider_closed)


	def spider_closed(self,spider):
        	self.cursor.close()
        	gob_crawlout_processing(self.out_put_file)

	def start_requests(self):
		headers = {'Content-Type': 'application/json'}
		rows = terminal_goibibo_requests(self.cursor, self.name, self.crawl_type, self.content_type, self.limit)
		if rows:
			for city_name,main_url,dx,los,pax,start_date,end_date,city_code,hotel_ids,hotel_name, meta_data in rows:
				if main_url:
                                        ct_id = ''
                                        try:
                                                ct_id = json.loads(meta_data).get('ct_id', '')
                                        except: 
                                                pass

					yield Request(main_url,callback=self.parse_innerpage1,headers=headers,meta={'city_name':city_name.split("_")[0].strip(),'dx':dx,'los':los,'pax':pax,'start_date':start_date,'end_date':end_date,'city_code':city_code,'hotel_ids':hotel_ids,'hotel_name':hotel_name, 'crawl_sk':city_name, "ct_id":str(ct_id)})


	def parse_innerpage1(self,response):
		crawl_sk = response.meta.get('crawl_sk', '')
		try:
			ct_id = response.meta.get('ct_id', '')
			headers = {'Content-Type': 'application/json'}
			city_name=response.meta.get('city_name','').title()
			dx=response.meta.get('dx','')
			los = response.meta.get('los','')
			pax = response.meta.get('pax','')
			check_in = response.meta.get('start_date','')
			stdt=datetime.datetime.strptime(check_in, '%Y%m%d').date()
			check_out= response.meta.get('end_date','')
			etdt=datetime.datetime.strptime(check_out, '%Y%m%d').date()
			city_code = response.meta.get('city_code','')
			goid = response.meta.get('hotel_ids','')
			hotel_name = response.meta.get('hotel_name','')
			content_type='hotels'
			adults= pax.split("-")[1].split("_")[0].strip()
			main_url = response.url
			formdata=''
			total_stay=(etdt-stdt).days
			aux_info={}	
			prime_rtc,prime_rpc, cancellation_policy ='','', 'NA'
			if response.status==200:
				data = json.loads(response.body)
				if data and data!='':
					main_node = data.get('data',{})
					parent_node = main_node.get('reg',{})
					if main_node is not None and parent_node is not None:
						if isinstance(parent_node,list):
							prime_rtc= str(parent_node[0].get('rtc','')).replace(",","")
							prime_rpc =str(parent_node[0].get('rpc','')).replace(",","")
							if prime_rtc and prime_rpc and prime_rtc!='' and prime_rpc!='':

								formdata1 = [
								('ajax', 'true'),
								('code', 'GETSETGO'),
								('version', 'v2'),
								('querydata', '{"reprice_new": 1, "user_latitude": "", "destination": "%s, India", "fwdParams": "{\\"vhid\\":\\"%s\\"}", "vertical": "%s", "v": "v3", "checkin": "%s", "noOfNights": "%s", "pah": "", "rooms": [{"childs": [], "adults": "%s"}], "country_code": "IN", "voyagerid": "%s", "hc": "%s",  "vcid": "%s", "city": "%s",  "noofAdults": %s, "pax": "%s", "country": "India", "pay_mode": "1", "rtc": "%s", "rpc": "%s", "newui": "True", "chkoutdate": "%s", "noofChildren": 0, "strQry": "hotels-%s-%s-%s-%s", "chkindate": "%s", "sb": "0", "noofRooms": "1", "checkout": "%s", "HotelRating": [0, 1, 2], "user_longitude": ""}'%(city_name,goid,content_type,check_in,total_stay,adults,goid,goid,city_code,city_name,adults,pax,prime_rtc,prime_rpc,check_out,city_code,check_in,check_out,pax,check_in,check_out)),
								]
										
								url ="https://www.goibibo.com/hotels/personalized-getHotelDescBlock/?per=1"
								cancellation_policy = str(parent_node[0].get('cltxt',''))
								yield FormRequest(url,callback=self.parse_innerpage2,formdata=formdata1,meta={'city_name':city_name,'dx':dx,'los':los,'pax':pax,'check_in':check_in,'check_out':check_out,'city_code':city_code,'goid':goid,'hotel_name':hotel_name,'ref_url':main_url,'adults':adults,'prime_rtc':prime_rtc,'prime_rpc':prime_rpc,'formdata':json.dumps(formdata1), 'cancellation_policy':cancellation_policy, "ct_id":ct_id})


					else:

						aux_info.update({'Exception':'No RTC and RPC CODES'})
						gob_items = GOBTRIPItem()
                                		gob_items.update({'city':normalize(city_name),'gbthotelname':normalize(hotel_name),'gbthotelid':goid,'check_in':check_in,'dx':dx,'los':los,'gbtpax':adults,'gbtroomtype':'CLOSED','gbtrate':'Sold Out','gbtb2cdiff':'NA','gbtinclusions':'NA','gbtapprate':'N/A','mobilediff':'NA','gbtb2csplashedprice':'N/A','gbtappsplashedprice':'N/A','gbtb2ctaxes':'N/A','gbtapptaxes':'N/A','child':'0','gbtcouponcode':'N/A','gbtcoupondescription':'N/A','gbtcoupondiscount':'N/A','rmtc':'N/A','check_out':check_out,'gstincluded':'N/A','totalamtaftergst':'N/A','reference_url':main_url, 'cancellation_policy': 'NA', "ct_id":ct_id})
						if aux_info:
							gob_items.update({'aux_info':json.dumps(aux_info)})
						yield gob_items


				else:
					
					aux_info.update({'Exception': 'No data available'})
					gob_items = GOBTRIPItem()
					gob_items.update({'city':normalize(city_name),'gbthotelname':normalize(hotel_name),'gbthotelid':goid,'check_in':check_in,'dx':dx,'los':los,'gbtpax':adults,'gbtroomtype':'N/A','gbtrate':'N/A','gbtb2cdiff':'N/A','gbtinclusions':'N/A','gbtapprate':'N/A','mobilediff':'N/A','gbtb2csplashedprice':'N/A','gbtappsplashedprice':'N/A','gbtb2ctaxes':'N/A','gbtapptaxes':'N/A','child':'0','gbtcouponcode':'N/A','gbtcoupondescription':'N/A','gbtcoupondiscount':'N/A','rmtc':'N/A','check_out':check_out,'gstincluded':'N/A','totalamtaftergst':'N/A','reference_url':main_url, 'cancellation_policy': 'NA', "ct_id":ct_id})
					if aux_info:
						gob_items.update({'aux_info':json.dumps(aux_info)})

					yield gob_items


			else:
				aux_info.update({'Exception':'Response Status ERROR[503,400,404]'})
				gob_items = GOBTRIPItem()
				gob_items.update({'city':normalize(city_name),'gbthotelname':normalize(hotel_name),'gbthotelid':goid,'check_in':check_in,'dx':dx,'los':los,'gbtpax':adults,'gbtroomtype':'N/A','gbtrate':'N/A','gbtb2cdiff':'N/A','gbtinclusions':'N/A','gbtapprate':'N/A','mobilediff':'N/A','gbtb2csplashedprice':'N/A','gbtappsplashedprice':'N/A','gbtb2ctaxes':'N/A','gbtapptaxes':'N/A','child':'0','gbtcouponcode':'N/A','gbtcoupondescription':'N/A','gbtcoupondiscount':'N/A','rmtc':'N/A','check_out':check_out,'gstincluded':'N/A','totalamtaftergst':'N/A',
'reference_url':main_url, 'cancellation_policy': 'NA', "ct_id":ct_id})
				if aux_info:
                                                gob_items.update({'aux_info':json.dumps(aux_info)})
				yield gob_items
			self.cursor.execute("update %s_crawl set crawl_status=1 where sk = '%s'" % (self.name, crawl_sk))

		except Exception, e:
			print str(e)
			self.cursor.execute("update %s_crawl set crawl_status=8 where sk = '%s'" % (self.name, crawl_sk))


	def parse_innerpage2(self,response):
		try:
			ct_id = response.meta.get('ct_id', '')
			data = json.loads(response.body)
			cancellation_policy = response.meta.get('cancellation_policy', '')
			city_name = response.meta.get('city_name','')
			dx = response.meta.get('dx','')
			los = response.meta.get('los','')
			pax = response.meta.get('pax','')
			check_in = response.meta.get('check_in','')
			check_out = response.meta.get('check_out','')
			city_code = response.meta.get('city_code','')
			goid = response.meta.get('goid','')
			hotel_name = response.meta.get('hotel_name','')
			ref_url = response.url
			adults = response.meta.get('adults','')
			prime_rtc = response.meta.get('prime_rtc','')
			prime_rpc = response.meta.get('prime_rpc','')
			formdata = "".join(response.meta.get('formdata',''))
			formdata = formdata[1:-1]
			aux_info={}
			gst_include='Yes'
			if data and data!='':
				main_node = data.get('cdata',{})
                                coupon_description = main_node.get('applicablepromolist',[])
                                if coupon_description:
                                        try:
						coupon_description = coupon_description[0].get('msg', '')
					except:
						coupon_description = 'N/A'
                                else:   
                                        coupon_description = 'N/A'
				goib_inclusions = ', '.join(main_node.get('Inclusions',[]))
				goib_roomtype = main_node.get('RoomTypeName','')
				total_keys = main_node.get('personalized_keys',{})
				taxsaving_discount = str(total_keys.get('ts','')).replace(",","")
				total_amount= str(total_keys.get('tp','')).replace(",","")
				coupon_code= str(total_keys.get('c',''))
				fare_breakup = main_node.get('farebreakup',{})
				gst_payable = main_node.get('fb_list',{})
				for gst_pay in gst_payable:
					gst_included=str(gst_pay.get('k',''))
					if ("Payable" in gst_included):
						gst_include="No"
				gst= str(fare_breakup.get('TotalTaxCharges_pah','0')).replace(",","")
				total_after_gst= str(fare_breakup.get('totalRoomRent','0')).replace(",","")
				splashed_price = str(fare_breakup.get('gocashcalculate_on_amount','0')).replace(",","")
				aux_info.update({'Status':'Success'})
				aux_info.update({'formdata':formdata})
				gob_items = GOBTRIPItem()
				gob_items.update({'city':normalize_clean(city_name),'gbthotelname':normalize_clean(hotel_name),'gbthotelid':goid,
				'check_in':check_in,'dx':dx,'los':los,'gbtpax':adults,'gbtroomtype':goib_roomtype,'gbtrate':total_after_gst,
				'gbtb2cdiff':total_after_gst,'gbtinclusions':normalize_clean(goib_inclusions),'gbtapprate':'N/A','mobilediff':'N/A',
				'gbtb2csplashedprice':splashed_price,'gbtappsplashedprice':'N/A','gbtb2ctaxes':'N/A','gbtapptaxes':'N/A',
				'child':'0','gbtcouponcode':coupon_code,'gbtcoupondescription':normalize(coupon_description),'gbtcoupondiscount':taxsaving_discount,
				'rmtc':prime_rtc,'check_out':check_out,'gstincluded':gst_include,'totalamtaftergst':total_after_gst,
				'reference_url':ref_url, 'cancellation_policy':normalize_clean(cancellation_policy), "ct_id":ct_id})
				if aux_info:
					gob_items.update({'aux_info':json.dumps(aux_info)})
				yield gob_items

			else:
				print "NO Price Details",data

		except Exception, e:
			print str(e)
