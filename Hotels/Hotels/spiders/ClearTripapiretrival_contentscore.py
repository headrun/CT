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
from Hotels.auto_config import CLEARTRIP_HEADERS
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class CrawlCTreteriveapicontentscore(scrapy.Spider):
    name = "CLEARTRIPapicontentscore_terminal"
    handle_httpstatus_list=[400,404,500, 401]
    start_urls = []
    
    def __init__(self,*args,**kwargs):
        super(CrawlCTreteriveapicontentscore,self).__init__(*args,**kwargs)
	self.name = 'Cleartripcontentscore'
        self.log = create_logger_obj(self.name)
        self.crawl_type = kwargs.get('crawl_type','keepup')
        self.content_type = kwargs.get('content_type','hotels')
        self.limit = kwargs.get('limit', 1000)
        self.out_put_file =get_ctrip_file(self.name)
        self.cursor = create_crawl_table_cusor()
	self.headers = CLEARTRIP_HEADERS
	self.image_api = "https://ui.cltpstatic.com/places/hotels"
        dispatcher.connect(self.spider_closed, signals.spider_closed)
    
    def spider_closed(self,spider):
        self.cursor.close()
        ct_crawlout_processing(self.out_put_file)

    def start_requests(self):
	rows = terminal_clear_requests(self.cursor, self.name, self.crawl_type, self.content_type, self.limit)
	if rows:
		for city_name, main_url, dx, los, pax, start_date, end_date, h_name, h_id in rows:
			yield Request(
                                  main_url, callback=self.parse, headers = self.headers,
                                  meta = {'city_name':city_name.split('_')[0].strip(),'dx':dx,'los':los,'pax':pax,
                                  'start_date':start_date,'end_date':end_date,'h_name':h_name,'h_id':h_id, 'sk_crawl':city_name}
                                 )

    def parse(self,response):
	sk_crawl = response.meta.get('sk_crawl', '')
	city_name = response.meta.get('city_name','')
        dx = response.meta.get('dx','')
        los = response.meta.get('los','')
	pax = response.meta.get('pax','')
	start_date = response.meta.get('start_date','')
	check_in = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m-%d')
	end_date = response.meta.get('end_date','')
	check_out = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y-%m-%d')
	h_name = response.meta.get('h_name','')
	h_id = response.meta.get('h_id','')
        if response.status==200:
        	data =  Selector(text=response.body)
		h_id = ''.join(data.xpath('//hotel-id/text()').extract())
		h_name = ''.join(data.xpath('//hotel-name/text()').extract())
		gstin = ''.join(data.xpath('//gstin/text()').extract())
		gstin_enabled = ''.join(data.xpath('//gstin_enabled/text()').extract())
		tds_enabled = ''.join(data.xpath('//tds_enabled/text()').extract())
		tds_rate = ''.join(data.xpath('//tds_rate/text()').extract())
		lth_hotel = ''.join(data.xpath('//lth-hotel/text()').extract())
		ct_recommended = ''.join(data.xpath('//ct-recommended/text()').extract())
		address = ''.join(data.xpath('//address/text()').extract())
		locality = ''.join(data.xpath('//locality/text()').extract())
		locality_id = ''.join(data.xpath('//locality-id/text()').extract())
		city_ = ''.join(data.xpath('//city/text()').extract())
		state_ = ''.join(data.xpath('//state/text()').extract())
		country = ''.join(data.xpath('//country/text()').extract())
		country_code = ''.join(data.xpath('//country-code/text()').extract())
		locality_latitude = ''.join(data.xpath('//locality-latitude/text()').extract())
		locality_longitude = ''.join(data.xpath('//locality-longitude/text()').extract())
		zipcode = ''.join(data.xpath('//zip/text()').extract())
		thumb_nail_image = ''.join(data.xpath('//thumb-nail-image/text()').extract())
		if thumb_nail_image:
			thumb_nail_image = "%s%s" % (self.image_api, thumb_nail_image)
		view_360 = ''.join(data.xpath('//view-360/text()').extract())
		is_on_hold = ''.join(data.xpath('//is-on-hold/text()').extract())
		is_veg = ''.join(data.xpath('//is-veg/text()').extract())
		getaway_property = ''.join(data.xpath('//getaway-property/text()').extract())
		star_rating = ''.join(data.xpath('//star-rating/text()').extract())
		rating_agency_star = ''.join(data.xpath('//hotel-rating[rating-agency[contains(text(), "SUPPLIER")]]/rating/text()').extract())
		ta_rating = ''.join(data.xpath('//hotel-rating[rating-agency[contains(text(), "TA")]]/rating/text()').extract())
		no_of_ta_reviews = ''.join(data.xpath('//hotel-rating[rating-agency[contains(text(), "TA")]]/total-ratings/text()').extract())
		ta_hotel_id = ''.join(data.xpath('//hotel-rating[rating-agency[contains(text(), "TA")]]/rating-agency-hotel-id/text()').extract())
		ta_rating_image_url = ''.join(data.xpath('//hotel-rating[rating-agency[contains(text(), "TA")]]/rating-image-url/text()').extract())
		ta_rating_url = ''.join(data.xpath('//hotel-rating[rating-agency[contains(text(), "TA")]]/new-rating-url/text()').extract())
		ta_reviews_url = ''.join(data.xpath('//hotel-rating[rating-agency[contains(text(), "TA")]]/all-ratings-url/text()').extract())
		ta_rank = ''.join(data.xpath('//hotel-rating[rating-agency[contains(text(), "TA")]]/rating-detail/rank/text()').extract())
		ta_out_of = ''.join(data.xpath('//hotel-rating[rating-agency[contains(text(), "TA")]]/rating-detail/out-of/text()').extract())
		ta_rating_categories = data.xpath('//hotel-rating[rating-agency[contains(text(), "TA")]]//rating-categories/rating-category')
		ta_rating_category, ta_rating_triptypes, hotel_amenities_final = [], [], []
		for tarc in ta_rating_categories:
			category_type = ''.join(tarc.xpath('./category-type/text()').extract())
			category_value = ''.join(tarc.xpath('./value/text()').extract())
			if category_value:
				category_ = "%s%s%s" % (category_type, ' : ', category_value)
				ta_rating_category.append(category_)
		ta_rating_category = '<>'.join(ta_rating_category)
		ta_rating_trips = data.xpath('//hotel-rating[rating-agency[contains(text(), "TA")]]//rating-trip-types/rating-trip-type')
		for trt in ta_rating_trips:
			trip_type = ''.join(trt.xpath('./trip-type/text()').extract())
			trip_value = ''.join(trt.xpath('./value/text()').extract())
			if trip_value:
				trip_ = "%s%s%s" % (trip_type, ' : ', trip_value)
				ta_rating_triptypes.append(trip_)
		ta_rating_triptypes = '<>'.join(ta_rating_triptypes)
		hotel_phone = ''.join(data.xpath('//communication-info/phone/text()').extract())
		hotel_email = ''.join(data.xpath('//communication-info/email/text()').extract())
		hotel_website = ''.join(data.xpath('//communication-info/website/text()').extract())
		hotel_amenities = data.xpath('//hotel-amenities/hotel-amenity')
		for hame in hotel_amenities:
			h_name_category = ''.join(hame.xpath('./category/text()').extract())
			h_name_amenity = ', '.join(hame.xpath('./amenities/amenity/text()').extract())
			h_final_ac = '%s%s%s' % (h_name_category, ' : ', h_name_amenity)
			hotel_amenities_final.append(h_final_ac)
		hotel_amenities_final = '<>'.join(hotel_amenities_final)
		hotel_description = ''.join(data.xpath('//other-info/description/text()').extract())
		hotel_no_of_rooms = ''.join(data.xpath('//other-info/number-of-rooms/text()').extract())
		no_of_floors = ''.join(data.xpath('//other-info/number-of-floors/text()').extract())
		max_adults = ''.join(data.xpath('//other-info/max-adults/text()').extract())
		max_children = ''.join(data.xpath('//other-info/max-children/text()').extract())
		hotel_facilities = ''.join(data.xpath('//other-info/facilities/text()').extract())
		room_types_nodes = data.xpath('//rooms-info/room-info')
		no_of_room_types = str(len(room_types_nodes))
		room_typs = '<>'.join(data.xpath('//rooms-info/room-info/room-type/text()').extract()) 
		ct_destination_id = ''.join(data.xpath('//location-info/ct-destination-id/text()').extract())
		policy_info_check_in = ''.join(data.xpath('//policy-info/check-in-time/text()').extract())
		policy_info_check_out = ''.join(data.xpath('//policy-info/check-out-time/text()').extract())
		policy_card_acce_types = '<>'.join(data.xpath('//policy-info/cards-accepted/card-type/text()').extract())
		image_info = data.xpath('//image-info/image/wide-angle-image-url/text()').extract()
		image_count = str(len(image_info))
		images_wide = '<>'.join(["%s%s" % (self.image_api, x) for x in image_info])
		staff_speak_languages = '<>'.join(data.xpath('//staff-speaks/languages/language/text()').extract())
		ct_item = CTContentItem()
		ct_item.update({"crawl_table_sk":normalize_clean(sk_crawl), "hotel_id":normalize_clean(h_id), "hotel_name":normalize_clean(h_name), "gstin":normalize_clean(gstin),"gstin_enabled": normalize_clean(gstin_enabled), "tds_enabled" : normalize_clean(tds_enabled), "tds_rate" : normalize_clean(tds_rate), "lth_hotel" : normalize_clean(lth_hotel), "ct_recommended" : normalize_clean(ct_recommended), "address" : normalize_clean(address), "locality" : normalize_clean(locality), "locality_id" : normalize_clean(locality_id), "city" : normalize_clean(city_), "state" : normalize_clean(state_), "country" : normalize_clean(country), "country_code" : normalize_clean(country_code), "locality_latitude" : normalize_clean(locality_latitude), "locality_longitude" : normalize_clean(locality_longitude), "zipcode" : normalize_clean(zipcode), "thumb_nail_image" : normalize_clean(thumb_nail_image), "view_360" : normalize_clean(view_360), "is_on_hold" : normalize_clean(is_on_hold), "is_veg" : normalize_clean(is_veg), "getaway_property" : normalize_clean(getaway_property), "star_rating" : normalize_clean(rating_agency_star), "ta_rating" : normalize_clean(ta_rating), "no_of_ta_reviews" : normalize_clean(no_of_ta_reviews), "ta_hotel_id" : normalize_clean(ta_hotel_id), "ta_rating_image_url" : normalize_clean(ta_rating_image_url), "ta_rating_url" : normalize_clean(ta_rating_url), "ta_reviews_url" : normalize_clean(ta_reviews_url), "ta_rank" : normalize_clean(ta_rank), "ta_out_of" : normalize_clean(ta_out_of), "ta_rating_categories" : normalize_clean(ta_rating_category), "ta_rating_triptypes" : normalize_clean(ta_rating_triptypes), "phone" : normalize_clean(hotel_phone), "email" : normalize_clean(hotel_email), "website" : normalize_clean(hotel_website), "amenities" : normalize_clean(hotel_amenities_final), "description" : normalize_clean(hotel_description), "no_of_rooms" : normalize_clean(hotel_no_of_rooms), "no_of_floors" : normalize_clean(no_of_floors), "max_adults" : normalize_clean(max_adults), "max_children" : normalize_clean(max_children), "facilities" : normalize_clean(hotel_facilities), "no_of_room_types" : normalize_clean(no_of_room_types), "room_types" : normalize_clean(room_typs), "ct_destination_id" : normalize_clean(ct_destination_id), "check_in" : normalize_clean(policy_info_check_in), "check_out" : normalize_clean(policy_info_check_out), "accepted_card_types" : normalize_clean(policy_card_acce_types), "image_count" : normalize_clean(image_count), "images"  : normalize_clean(images_wide), "staff_speak_languages": normalize_clean(staff_speak_languages), "aux_info":'', "reference_url":response.url})
		yield ct_item
	self.cursor.execute("update %s_crawl set crawl_status=1 where sk = '%s'" % (self.name, sk_crawl))
