import json
import scrapy
import MySQLdb
from scrapy.selector import Selector
from scrapy.http import Request
from datetime import datetime
import time
import os
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from Hotels.utils import *
from Hotels.items import *
from Hotels.auto_config import CLEARTRIP_HEADERS

class TajawalContent(scrapy.Spider):
    name = 'Tajawalcontentscore_browse'
    start_urls = []

    def __init__(self, Configfile='', *args, **kwargs):
        super(TajawalContent, self).__init__(*args, **kwargs)
        self.check = kwargs.get('check', '')
        self.today_url_list = [('https://www.tajawal.ae/en/hotels-in/city/singapore-sin', 'singapore'), ('https://www.tajawal.ae/en/hotels-in/city/manama-bah', 'manama'), ('https://www.tajawal.sa/ar/hotels-in/city/jeddah-jed', 'jeddah'), ('https://www.tajawal.sa/ar/hotels-in/city/makkah-jih', 'makkah'), ('https://www.tajawal.sa/ar/hotels-in/city/madina-med', 'madina'), ('https://www.tajawal.sa/ar/hotels-in/city/riyadh-ruh', 'riyadh'), ('https://www.tajawal.ae/en/hotels-in/city/dubai-dxb', 'dubai')]
        #self.today_url_list = [('https://www.tajawal.sa/ar/hotels-in/city/riyadh-ruh', 'riyadh')]
        self.name = 'Tajawalcontentscore'
        self.cursor = create_crawl_table_cusor()
        ensure_crawlct_table(self.cursor, self.name)
        drop_crawlct_table(self.cursor, self.name)
        self.metacursor = create_ct_table_cusor()
        ensure_content_table(self.metacursor,self.name)
        self.out_put_file = get_ctrip_file(self.name)
        drop_ct_table(self.metacursor, self.name)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self,spider):
        self.cursor.close()
        ct_crawlout_processing(self.out_put_file)

    def start_requests(self):
        for tda in self.today_url_list:
            for val in range(1,4):
                dat = datetime.datetime.now().date()
                ctycode =  ''.join(re.findall('tajawal\.(.*?)\/', tda[0]))
                link = 'https://www.tajawal.%s/api/hotel/ahs/aSearch?profile=%s&query=%s/%s'%(ctycode, str(val), tda[1], str(dat))
                yield Request(link, callback=self.parse, meta = {"city_name":tda[1], "hotel_main_url":tda[0], "ctycode":ctycode})

    def parse(self, response):
        ctycode = response.meta.get('ctycode', '')
        hotel_main_url = response.meta.get('hotel_main_url', '')
        json_body = json.loads(response.body)
        if json_body:
            uuid = json_body.get('uuid', '')
            if uuid:
                epoch = str(time.mktime(datetime.datetime.now().timetuple())).split('.')[0]
                link = 'https://www.tajawal.%s/api/hotel/ahs/aResults?_pc=2&_t=%s&uuid=%s'%(ctycode, str(epoch), uuid)
                yield Request(link, self.parse_next, meta={'uuid':uuid, 'city':response.meta['city_name'], "hotel_main_url":hotel_main_url, "ctycode":ctycode})

    def parse_next(self, response):
        print response.url
        ctycode = response.meta.get('ctycode', '')
        hotel_main_url = response.meta.get('hotel_main_url', '')
        json_body = json.loads(response.body)
        if json_body:
            hotels = json_body.get('hotel', [])
            uuid = response.meta.get('uuid', '')
            city = response.meta.get('city', '')
            if hotels:
                for hotel in hotels:
                    h_id = hotel.get('hotelId', '')
                    details_link = 'https://www.tajawal.%s/api/hotel/ahs/info/%s?hotelId=%s&searchUuid=%s'%(ctycode, h_id, h_id, uuid)
                    yield Request(details_link, self.parse_hotel, meta={'hotel_id':h_id, 'city':city, "hotel_main_url":hotel_main_url, "ctycode":ctycode})

    def parse_hotel(self, response):
        main_url = response.meta.get('hotel_main_url', '')
        page_url = ''
        hotel = json.loads(response.body)
        if hotel:
            h_name = hotel.get('summary', {}).get('hotelName', '')
            h_id = response.meta.get('hotel_id', '')
            hotel_url = ''.join([main_url.split('hotels-in')[0], "hotels/details/",str(h_id)])
            h_address = hotel.get('location', {}).get('address', '')
            h_lat = hotel.get('location', {}).get('latitude', '')
            h_long = hotel.get('location', {}).get('longitude', '')
            ratings = hotel.get('rating', {})
            star_rating = '0'
            for rat in ratings:
                typ = rat.get('type', '')
                if typ == 'starRating':
                    star_rating = rat.get('value', '')
            amenities = hotel.get('amenities', {})
            amenties_data = ''
            for key, list_ in amenities.iteritems():
                for lis in list_:
                    desc = lis.get('desc', '')
                    if desc:
                        amenties_data = '%s<>%s'%(amenties_data, desc)
            amenties_data = amenties_data.strip().strip('<>').strip()
            details = hotel.get('details', [])
            description = ''
            for detail in details:
                title = detail.get('title', '')
                if title == 'General Description':
                    description = detail.get('description', '').replace('\n', '').replace('<br />', '').replace('<p>', '').replace('</p>', '')
            city_ = hotel.get('location', {}).get('cityName', '')
            ct_item = ContentScore()
            ct_item.update({"sk":h_id, "hotel_id":h_id, "hotel_name":h_name, "address":h_address, "city":city_, "locality_latitude":h_lat, "locality_longitude":h_long, "star_rating":star_rating, "description":description, "amenities":amenties_data, "reference_url":response.url, "html_hotel_url":hotel_url, "main_listing_url":main_url, "navigation_url":page_url})
            yield ct_item

