import scrapy
from scrapy.selector import Selector
from scrapy.http import Request
import datetime
import json
import os
import time
import re
import MySQLdb
import logging
from scrapy import log
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from Hotels.utils import *
from Hotels.items import *


class MMTCrawltreterive(scrapy.Spider):
    name = "MMTRIP_terminal"
    handle_httpstatus_list=[400,404,500]
    start_urls=['https://www.makemytrip.com/hotels']


    def __init__(self,*args,**kwargs):
        super(MMTCrawltreterive,self).__init__(*args,**kwargs)
        self.name = 'Makemytrip'
        self.log = create_logger_obj(self.name)
        self.crawl_type = kwargs.get('crawl_type','keepup')
        self.content_type = kwargs.get('content_type','hotels')
        self.limit = kwargs.get('limit',1000)
        self.out_put_file =get_mmtrip_file(self.name)
        self.cursor = create_crawl_table_cusor()
        dispatcher.connect(self.spider_closed, signals.spider_closed)
    
    def spider_closed(self,spider):
        self.cursor.close()
        mmt_crawlout_processing(self.out_put_file)
               
    def parse(self,response):
        headers = {'Content-Type': 'application/json'}
        rows = terminal_requests(self.cursor, self.name, self.crawl_type, self.content_type, self.limit)
        for city_name, main_url, dx, los, pax, start_date, end_date, city_code, hotel_ids, hotel_name in rows:
            if main_url:
                yield Request(main_url, callback=self.parse_innerpage1, headers=headers, meta={'city_name':city_name.split('_')[0].strip(),'dx':dx,'los':los,
                              'pax':pax,'start_date':start_date,'end_date':end_date,'city_code':city_code,'hotel_ids':hotel_ids,'hotel_name':hotel_name})


    def parse_innerpage1(self,response):
        city_name= response.meta.get('city_name','')
        city_code = response.meta.get('city_code','')
        dx= response.meta.get('dx','')
        los = response.meta.get('los','')
        start_date = response.meta.get('start_date','')
        check_in = datetime.datetime.strptime(start_date, '%m%d%Y').strftime('%Y-%m-%d')
        end_date = response.meta.get('end_date','')
        check_out = datetime.datetime.strptime(end_date, '%m%d%Y').strftime('%Y-%m-%d')
        pax_ac = response.meta.get('pax','')
        adult = pax_ac.split("e")[0]
        child = pax_ac.split("e")[1]
        h_id = response.meta.get('hotel_ids','')
        hot_name = response.meta.get('hotel_name','')

        actual_price, splashed_price, coupon_code, coupon_description='','','',''
        coupon_value, inclusions, tariffIdentifierFork, reviewUrl, urls, rmtc='','','','','',''

        if response.status == 200:
            data = json.loads(response.body)
            soldout = "".join(data.keys())

            if data and data !='':
                if "sold_out" in soldout:
                    mmt_items= MMTRIPItem()
                    mmt_items.update({'city':normalize(city_name),'mmthotelname':normalize(hot_name),'mmthotelid':h_id,'check_in':check_in,
                    'dx':dx,'los':los,'mmtpax':adult,'mmtroomtype':'CLOSED','mmtrate':'Sold Out','mmtb2cdiff':'NA','mmtinclusions':'NA',
                    'mmtapprate':'N/A','mobilediff':'NA','mmtb2csplashedprice':'0','mmtappsplashedprice':'N/A',
                    'mmtb2ctaxes':'CLOSED','mmtapptaxes':'N/A','child':child,'mmtcouponcode':'N/A','mmtcoupondescription':'N/A',
                    'mmtcoupondiscount':'N/A','rmtc':'CLOSED','check_out':check_out,'gstincluded':'N/A','totalamtaftergst':'N/A'})
                    yield mmt_items

                else:
                    main_node = data.get('room_details_section',{})
                    if main_node:
                        room_details  = main_node.get("room_details",{})
                        room_opens = room_details[0].get("room_details_open_section",{})
                        room_codes = room_opens.get("room_static_info",{})
                        room_vailables = room_opens.get("room_details_visible",{})

                        rmtc = room_codes.get('room_code','')
                        room_vailable = room_vailables[0]
                        actual_room_infos = room_vailable.get('tarrif_details',{})

                        actual_price = actual_room_infos.get('actual_price','')
                        splashed_price = actual_room_infos.get('splashed_price','')
                        coupon_code = actual_room_infos.get('coupon_code','')
                        coupon_description = actual_room_infos.get('coupon_description','')
                        coupon_value = actual_room_infos.get('coupon_value','')
                        inclusions = actual_room_infos.get('inclusions','')
                        tariffIdentifierFork = actual_room_infos.get('tariffIdentifierFork','')

                        traffic_split= tariffIdentifierFork.split("_")
                        traffic_code1=traffic_split[0].strip()
                        traffic_code2 = traffic_split[1].strip()
                        up_checkIn=datetime.datetime.strptime(start_date, '%m%d%Y').strftime('%m/%d/%Y')
                        up_checkout=datetime.datetime.strptime(end_date, '%m%d%Y').strftime('%m/%d/%Y')

                        urls = 'https://dtr-hoteldom.makemytrip.com/mmthtl/site/hotels/review/getMultiRoomPriceBreakup?session_cId=null&hotelRefId=%s&roomTypeCode=null&ratePlanCode=null&payModSelected=null&countryCode=IN&searchCountryCode=IN&searchCityCode=%s&startDate=%s&endDate=%s&visitorID=null&nat=null&lang=null&forkEnabled=true&mtkeys=null&payMode=PAS&roomCriteria=%s-~%s-~-~%s&searchType=E&roomStayQualifier=%s&originalRoomStayQualifier=%s'%(h_id,city_code,up_checkIn,up_checkout,pax_ac,traffic_code1,traffic_code2,pax_ac,pax_ac)

                        yield Request(urls,callback=self.parse_innerpage4,meta={'city_name':city_name,'city_code':city_code,'dx':dx,
                        'los':los,'start_date':check_in,'end_date':check_out,'pax_ac':pax_ac,'h_id':h_id,'actual_price':actual_price,
                        'splashed_price':splashed_price,'coupon_code':coupon_code,'coupon_description':coupon_description,
                        'room_code':rmtc,'coupon_value':coupon_value,'inclusions':inclusions,'hot_name':hot_name})

        else:
            mmt_items= MMTRIPItem()
            mmt_items.update({'city':normalize(city_name),'mmthotelname':normalize(hot_name),'mmthotelid':h_id,'check_in':check_in,
            'dx':dx,'los':los,'mmtpax':adult,'mmtroomtype':'N/A','mmtrate':'N/A','mmtb2cdiff':'NA','mmtinclusions':'NA',
            'mmtapprate':'N/A','mobilediff':'NA','mmtb2csplashedprice':'N/A','mmtappsplashedprice':'N/A','mmtb2ctaxes':'N/A',
            'mmtapptaxes':'N/A','child':child,'mmtcouponcode':'N/A','mmtcoupondescription':'N/A','mmtcoupondiscount':'N/A',
            'rmtc':'N/A','check_out':check_out,'gstincluded':'N/A','totalamtaftergst':'N/A'})
            yield mmt_items

    def parse_innerpage4(self,response):
        data = json.loads(response.body)

        city_name = response.meta.get('city_name','')
        city_code = response.meta.get('city_code','')
        dx= response.meta.get('dx','')
        los = response.meta.get('los','')
        check_in = response.meta.get('start_date','')
        check_out = response.meta.get('end_date','')
        pax_ac = response.meta.get('pax_ac','')
        adult = pax_ac.split("e")[0]
        child = pax_ac.split("e")[1]
        h_id = response.meta.get('h_id','')
        room_code = response.meta.get('room_code','')
        coupon_code = response.meta.get('coupon_code','')
        coupon_description= response.meta.get('coupon_description','')
        coupon_value = response.meta.get('coupon_value','')
        inclusions = response.meta.get('inclusions','')
        hot_name = response.meta.get('hot_name','')
        sold_outs=''

        if data and data!='':
		error_node = data.get('error_dto',{})
		error_parent_node = error_node.get('data',{})
		sold_outs = error_parent_node.get('displayMsg','')
		if "sold out" in sold_outs:
			mmt_items= MMTRIPItem()
			mmt_items.update({'city':normalize(city_name),'mmthotelname':normalize(hot_name),'mmthotelid':h_id,'check_in':check_in,
				'dx':dx,'los':los,'mmtpax':adult,'mmtroomtype':'CLOSED','mmtrate':'Sold Out','mmtb2cdiff':'NA',
				'mmtinclusions':'NA','mmtapprate':'N/A','mobilediff':'NA','mmtb2csplashedprice':'0','mmtappsplashedprice':'N/A',
				'mmtb2ctaxes':'CLOSED','mmtapptaxes':'N/A','child':child,'mmtcouponcode':'N/A','mmtcoupondescription':'N/A',
				'mmtcoupondiscount':'N/A','rmtc':'CLOSED','check_out':check_out,'gstincluded':'N/A','totalamtaftergst':'N/A'})
			yield mmt_items

		main_node = data.get('aggr_view_price',{})
		if main_node:
			parent_node= main_node.get('data',{})
			supplier_datas = parent_node.get('supplierDetails',{})
			total,discount_amt, final_amt, gst_data, gst_included, total_after_gst,gst_amt='','0','','','','','0'

		    	suppliercode = supplier_datas.get('supplierCode','')
		    	costprice = supplier_datas.get('costPrice','')
			dynamic_price = parent_node.get('dynamic_price_view',{})
			data_infos = dynamic_price.get('data',{})
		    	subprice = data_infos.get('subPrice','')
		    	discount = data_infos.get('discount','')
		    	totaltax = data_infos.get('totalTax','').replace(",","")
		    	total = data_infos.get('total','').replace(",","")
		    	gst_data = data_infos.get('taxExcludedInstruction','')
			if "excluded" in gst_data:
				gst_included='No'
				gst_amt = "".join(re.findall(r'\d+\.\d+',gst_data))
				total_after_gst=int(total)+float(gst_amt)
			elif "added" in gst_data:
				gst_included='Yes'
				total_after_gst='N/A'
			elif gst_data =='':
				gst_included='N/A'
				total_after_gst='N/A'

			mmtrate = int(total)+float(gst_amt)
			
			room_cd = data_infos.get('multiRoomWiseView',{})
			room_data_infos = room_cd.get('data',{})
			room_data_info= room_data_infos[0].get('data',{})
			room_type_name = room_data_info.get('roomTypeName','')
			child_type_no = room_data_info.get('numberOfChildren','')

			discount_price = parent_node.get('aggr_coupons_view',{})
			data_dis_infos = discount_price.get("data",{})
			agv_infos = data_dis_infos.get('twoPasCpns',{}) or data_dis_infos.get('threePasCpns',{}) or \
			data_dis_infos.get('onePasCpn',{}) or data_dis_infos.get('fourPasCpns',{}) or data_dis_infos.get('fivePasCpns',{})
                        cpns_info = agv_infos.get('data', {})
                        if isinstance(cpns_info, list):
			    premire_discounts= cpns_info[0].get('data',{})
		    	    discount_amt = str(premire_discounts.get('discountAmount','0')).replace(",","")
                        elif isinstance(cpns_info, dict):
                            discount_amt = str(cpns_info.get('discountAmount','0')).replace(",","")
			mmtsplashed_amt = int(total)-int(discount_amt)
			mmt_items= MMTRIPItem()
			mmt_items.update({'city':normalize(city_name),'mmthotelname':normalize(hot_name),'mmthotelid':h_id,'check_in':check_in,
		    				'dx':dx,'los':los,'mmtpax':adult,'mmtroomtype':room_type_name,'mmtrate':mmtrate,'mmtb2cdiff':mmtrate,
		    				'mmtinclusions':normalize(inclusions),'mmtapprate':'N/A','mobilediff':'N/A','mmtb2csplashedprice':mmtsplashed_amt,
		    				'mmtappsplashedprice':'N/A','mmtb2ctaxes':totaltax,'mmtapptaxes':'N/A','child':child,'mmtcouponcode':coupon_code,
		    				'mmtcoupondescription':normalize(coupon_description),'mmtcoupondiscount':discount_amt,'rmtc':room_code,
		    				'check_out':check_out,'gstincluded':gst_included,'totalamtaftergst':total_after_gst})

			yield mmt_items
			
                



















