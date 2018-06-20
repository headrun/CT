from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
from scrapy.http import Request, FormRequest
from datetime import datetime
import json
#import datetime
import time
import xlwt, csv
import hashlib
import MySQLdb
class HotelBrowse(BaseSpider):

    name = 'hotel_browse'
    city_dict = {'dubai':'https://www.tajawal.ae/en/hotels-in/city/dubai-dxb',
                  'makkah':'https://www.tajawal.sa/ar/hotels-in/city/makkah-jih',
                  'medina':'https://www.tajawal.sa/ar/hotels-in/city/madina-med',
                  'manama':'https://www.tajawal.ae/en/hotels-in/city/manama-bah',
                  'singapore':'https://www.tajawal.ae/en/hotels-in/city/singapore-sin',
		  'jeddah-western-province-saudi-arabia-kingdom':'https://www.tajawal.sa/ar/hotels-in/city/jeddah-jed',
                  'riyadh':'https://www.tajawal.sa/ar/hotels-in/city/riyadh-ruh'
		}
    def __init__(self, *args, **kwargs):
        super(HotelBrowse, self).__init__(*args, **kwargs)
	self.conn = MySQLdb.connect(db   = 'TAJAWALDB', \
                 host = 'localhost', charset="utf8", use_unicode=True, \
                 user = 'root', passwd ='root')
	self.insert_query = 'insert into Tajawalcontentscore(sk, hotel_id, hotel_name,address,city,locality_latitude,locality_longitude,star_rating,description,amenities,aux_info,reference_url,html_hotel_url,main_listing_url,navigation_url,created_on,modified_at) values(%s,%s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, now(), now()) on duplicate key update modified_at = now()'
        self.cur  = self.conn.cursor()
        self.conn.set_character_set('utf8')
        #self.cur.execute('SET NAMES utf8;')
        #self.cur.execute('SET CHARACTER SET utf8;')
        #self.cur.execute('SET character_set_connection=utf8;') 
    
    #excel_file_name = 'hotel_data_%s.csv' % str(datetime.now().date())
    #oupf = open(excel_file_name, 'ab+')
    #todays_excel_file  = csv.writer(oupf)
    #headers = ['Hotel_id', 'Hotel_name', 'City', 'Address', 'Latitude', 'Longitude', 'Star_rating', 'Amenities', 'Description']
    #todays_excel_file.writerow(headers)

    def start_requests(self):
        for city,city_link in self.city_dict.iteritems():
	    headers = {}
            for val in range(1,4):
		#dat = datetime.now().date()
		dat = '02-07-2018'
		re_date = ''
		if '.ae/' in city_link:
			link = "https://www.tajawal.ae/api/hotel/ahs/aSearch?profile=%s&query=%s/%s"%(str(val), city, str(dat))
		if '.sa/' in city_link:
			re_date = '15-07-2018'				
			#redate = datetime.datetime.strftime(re_date, '%d-%m-%Y')
			if 'makkah' in city:
				link = "https://www.tajawal.sa/api/hotel/ahs/aSearch?profile=%s&query=" %str(val) + "%D9%85%D9%83%D8%A9%D8%A7%D9%84%D9%85%D9%83%D8%B1%D9%85%D9%87-%D9%88%D9%8A%D8%B3%D8%AA%D8%B1%D9%86-%D8%A8%D8%B1%D9%88%D9%81%D8%A7%D9%86%D8%B3-%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A%D8%A9%2F" + "%s" % dat + "%2F" + "%s" % re_date + "%2F2_adult" 
			if 'jeddah-western-province-saudi-arabia-kingdom' in city:
				link = "https://www.tajawal.sa/api/hotel/ahs/aSearch?profile=%s&query=" % str(val) + "%D8%AC%D8%AF%D8%A9-%D9%88%D9%8A%D8%B3%D8%AA%D8%B1%D9%86-%D8%A8%D8%B1%D9%88%D9%81%D8%A7%D9%86%D8%B3-%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A%D8%A9%2F" + "%s" % dat +"%2F" + "%s" % re_date + "%2F2_adult"
			if 'riyadh' in city:
				link = "https://www.tajawal.sa/api/hotel/ahs/aSearch?profile=%s&query=" % str(val) +"%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6-%D8%B3%D9%86%D8%AA%D8%B1%D8%A7%D9%84-%D8%B3%D8%B9%D9%88%D8%AF%D9%8A-%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9-%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A%D8%A9%2F" +"%s" %dat + "%2F" + "%s" % re_date +"%2F2_adult"
			if 'medina' in city:
				link = "https://www.tajawal.sa/api/hotel/ahs/aSearch?profile=%s&query=" % str(val) + "%D8%A7%D9%84%D9%85%D8%AF%D9%8A%D9%86%D8%A9-%D8%A7%D9%84%D9%85%D9%86%D9%88%D8%B1%D9%87-%D9%88%D9%8A%D8%B3%D8%AA%D8%B1%D9%86-%D8%A8%D8%B1%D9%88%D9%81%D8%A7%D9%86%D8%B3-%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A%D8%A9%2F"+ "%s" % dat +"%2F" + "%s" % re_date +"%2F2_adult"
			headers = {'x-locale': 'ar', 'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8', 'accept-encoding': 'gzip, deflate, br', 'x-currency': 'SAR', 'authority': 'www.tajawal.sa', 'x-fp': '51f6f8eeccb5c9bd26d51bf4d1d794f4', 'referer': link, 'accept': 'application/json, text/javascript', 'pragma': 'no-cache', 'x-tz': 'Asia/Calcutta', 'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36', 'cache-control': 'no-cache'}
		if bool(headers): 
                	yield Request(link, self.parse, headers = headers,meta={'city':city, 'city_link':city_link,'keyword':'arabic'})
		else:
			yield Request(link, self.parse,meta={'city':city, 'city_link':city_link})


    def parse(self, response):
	headers = {}
        json_body = json.loads(response.body)
	main_listing_url = response.url
	arabic_check = response.meta.get('keyword','')
        if json_body:
            uuid = json_body.get('uuid', '')
            if uuid:
                epoch = str(time.mktime(datetime.now().timetuple())).split('.')[0]
		if arabic_check:
			link = 'https://www.tajawal.sa/api/hotel/ahs/aResults?_pc=1&_t=%s&uuid=%s'%(str(epoch), uuid)
		else:
			link = 'https://www.tajawal.ae/api/hotel/ahs/aResults?_pc=1&_t=%s&uuid=%s'%(str(epoch), uuid)
		if arabic_check:
			headers = {'x-locale': 'ar', 'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8', 'accept-encoding': 'gzip, deflate, br', 'x-currency': 'SAR', 'authority': 'www.tajawal.sa', 'x-fp': '51f6f8eeccb5c9bd26d51bf4d1d794f4', 'referer': response.url, 'accept': 'application/json, text/javascript', 'pragma': 'no-cache', 'x-tz': 'Asia/Calcutta', 'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36', 'cache-control': 'no-cache'}
		if arabic_check:
			yield Request(link, self.parse_next, headers=headers,  meta={'uuid':uuid, 'city':response.meta['city'],'navigation_url':link,'main_listing_url':main_listing_url,'keyword':'arabic'})
		else:
                	yield Request(link, self.parse_next,meta={'uuid':uuid, 'city':response.meta['city'],'navigation_url':link,'main_listing_url':main_listing_url})

    def parse_next(self, response):
        json_body = json.loads(response.body)
        if json_body:
            hotels = json_body['hotel']
            uuid = response.meta['uuid']
            city = response.meta['city']
	    arabic_check = response.meta.get('keyword','')
	    main_listing_url = response.meta['main_listing_url']
	    navigation_url = response.meta['navigation_url']
            if hotels:
                for hotel in hotels:
                    h_id = hotel['hotelId']
		    headers = {'x-locale': 'ar', 'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8', 'accept-encoding': 'gzip, deflate, br', 'x-currency': 'SAR', 'authority': 'www.tajawal.sa', 'x-fp': '51f6f8eeccb5c9bd26d51bf4d1d794f4', 'referer': response.url, 'accept': 'application/json, text/javascript', 'pragma': 'no-cache', 'x-tz': 'Asia/Calcutta', 'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36', 'cache-control': 'no-cache'}
                    details_link = 'https://www.tajawal.ae/api/hotel/ahs/info/%s?hotelId=%s&searchUuid=%s'%(h_id, h_id, uuid)
		    if arabic_check:
			details_link = 'https://www.tajawal.sa/api/hotel/ahs/info/%s?hotelId=%s&searchUuid=%s'%(h_id, h_id, uuid)
			yield Request(details_link, self.parse_hotel, headers=headers,meta={'hotel_id':h_id, 'city':city,'navigation_url':navigation_url,'main_listing_url':main_listing_url,'uuid':uuid})
		    else:
                    	yield Request(details_link, self.parse_hotel,meta={'hotel_id':h_id, 'city':city,'navigation_url':navigation_url,'main_listing_url':main_listing_url,'uuid':uuid})

    def parse_hotel(self, response):
        hotel = json.loads(response.body)
	reference_url = response.url
	main_listing_url = response.meta['main_listing_url']
	navigation_url = response.meta['navigation_url']
        if hotel:
            h_name = hotel['summary']['hotelName']
	    #sk =  hashlib.md5(h_name.encode('ascii', 'ignore').decode('ascii')+h_id).hexdigest()
            h_id = response.meta['hotel_id']
	    sk =  str(response.meta['uuid']) + str(h_id)
	    if '.ae/' in response.url:
	    	html_hotel_url = 'https://www.tajawal.com/en/hotel/details/' + str(h_id)
	    else:
		html_hotel_url = 'https://www.tajawal.sa/ar/hotel/details/' + str(h_id)
	    email = hotel.get('summary',{}).get('email','')
	    website = hotel.get('summary',{}).get('website','')
	    district = hotel.get('location',{}).get('districtName','')
	    countryName = hotel.get('location',{}).get('countryName','')
	    aux_info = {}
	    h_address = hotel['location']['address']
            h_lat = hotel['location']['latitude']
	    if email:
		aux_info.update({'email':email})
	    if website:
		aux_info.update({'website':website})
	    if district:
		aux_info.update({'district':district})
            h_long = hotel['location']['longitude']
            ratings = hotel['rating']
            star_rating = '0'
            for rat in ratings:
                typ = rat['type']
                if typ == 'starRating':
                    star_rating = rat['value']
            amenities = hotel['amenities']
            amenties_data = ''
            for key, list_ in amenities.iteritems():
                for lis in list_:
                    desc =lis['desc']
                    if desc:
                        amenties_data = '%s<>%s'%(amenties_data, desc)
            amenties_data = amenties_data.strip().strip('<>').strip()
            details = hotel['details']
            description = ''
            for detail in details:
                title = detail['title']
                if title == 'General Description':
                    description = detail['description'].replace('\n', '').replace('<br />', '').replace('<p>', '').replace('</p>', '')
            city = response.meta['city']
	    #city = hotel['location']['cityName']
            if not city:
                city = response.meta['city']
	    values = (sk,h_id, h_name,h_address, city, h_lat, h_long, star_rating, description,amenties_data,json.dumps(aux_info),reference_url,html_hotel_url,main_listing_url,navigation_url)
            #values = (sk,h_id, h_name.encode('ascii', 'ignore').decode('ascii'),h_address.encode('ascii', 'ignore').decode('ascii'), city.encode('ascii', 'ignore').decode('ascii'), h_lat, h_long, star_rating, description.encode('ascii', 'ignore').decode('ascii'),amenties_data.encode('ascii', 'ignore').decode('ascii'),json.dumps(aux_info),reference_url,html_hotel_url,main_listing_url,navigation_url)
            self.cur.execute(self.insert_query,values)
	    self.conn.commit()
            #self.todays_excel_file.writerow(values)

