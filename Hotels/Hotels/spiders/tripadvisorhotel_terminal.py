import scrapy
import json
import re
import datetime
import  MySQLdb
import csv
import unittest, time, re
from datetime import datetime
from scrapy.selector import Selector
from scrapy.http import Request, FormRequest
con = MySQLdb.connect(db   = 'urlqueue_dev', \
    host = 'localhost', charset="utf8", use_unicode=True, \
    user = 'root', passwd ='root')
cur = con.cursor()
select_query = "select sk,url from tripadvisor_crawl where crawl_status=0 limit 20" 
update_query = 'update tripadvisor_crawl set crawl_status=1 where crawl_status=0 and url= "%s"'
class TripAdvisorFinal(scrapy.Spider):
        name = "trip_advisor"
        def start_requests(self):
            cur.execute(select_query)
            data = cur.fetchall()
	    headers = {
                'authority': 'www.tripadvisor.in',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            }
            for row in data:
                sk,url = row
                yield Request(url, callback=self.parse, headers=headers, meta={'sk':sk})
	def __init__(self,*args, **kwargs):
                super(TripAdvisorFinal, self).__init__(*args, **kwargs)
		self.checkin = kwargs.get('checkin','')
                self.checkout = kwargs.get('checkout','')
                self.adults = kwargs.get('adults','')
                self.rooms = kwargs.get('rooms','')
		self.excel_file_name = 'tripadvisor_metadata_%s.csv' %str(datetime.now().date())
                self.oupf = open(self.excel_file_name, 'ab+')
                self.todays_excel_file  = csv.writer(self.oupf)
                self.headers = ['hotel_id','hotel_name','checkin','checkout','rooms','adults','Price_Agoda', 'Price_BookingCom', 'Price_ClearTrip', 'Price_Expedia', 'Price_Goibibo', 'Price_HotelsCom2', 'Price_MakeMyTrip', 'Price_Yatra', 'Price_TG','tax_price_Agoda','tax_price_BookingCom','tax_price_ClearTrip','tax_price_Expedia','tax_price_Goibibo','tax_price_HotelsCom2','tax_price_MakeMyTrip','tax_price_Yatra','tax_price_TG']
                self.todays_excel_file.writerow(self.headers)
	def parse(self, response):
                checkin = self.checkin
                checkout = self.checkout
                adults = self.adults
                rooms = self.rooms
                staydates = checkin + "_" + checkout
                uguests = rooms + "_" + adults
                sel = Selector(response)
                data =''.join(response.xpath('//script[@type="text/javascript"]//text()[contains(. , "define(")]').extract())
                if data:
                        uid = ''.join(re.findall(r'"uid":(.*)',data)).split(',')[0].replace('"','')
                headers = {
                'x-puid':   uid,
                'origin': 'https://www.tripadvisor.in',
                'accept-language': 'en-US,en;q=0.9',
                'x-requested-with': 'XMLHttpRequest',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
                'accept': 'text/html, */*',
                'authority': 'www.tripadvisor.in',
                'referer': response.url,
		}

                data = [
                        ('staydates', staydates),
                        ('uguests', uguests),
                        ('reqNum', '1'),
                        ('changeSet', 'TRAVEL_INFO'),
                        ('puid', uid),
                ]
                time.sleep(5)
                yield FormRequest(response.url, callback=self.parse_next, formdata = data, headers=headers,meta={'headers':headers,'data':data,'counter':0})

        def parse_next(self, response):
                hotelid = re.findall(r'-d\d+',response.url)
                url = "https://www.tripadvisor.in/Hotel_Review" + ''.join(hotelid) + ".html"
                sel = Selector(response)
                if "UID" in response.body:
                    node = sel.xpath('//div[@class="secondary "]//div[@class="mobile_textlink "]')
                    hotel_id = ''.join(set(response.xpath('//div[@class="secondary "]//div[@class="mobile_textlink "]//@data-locationid').extract()))
                    count = 0
                    vendor_dict = {}
                    hotel_id = response.url.split('-d')[1].split('-')[0] 
                    data = ''.join(sel.xpath('//div[@class="data irg-data"]/text()').extract())
                    json_data = json.loads(data)
                    checkin = json_data['checkIn']
                    checkout = json_data['checkOut']
                    hotel_name = json_data['roomSelectionModel']['hotelName']
                    rooms = json_data['roomSelectionModel']['polling']['rooms']
                    adults = json_data['roomSelectionModel']['polling']['adults']
                    tax_dict = {}
                    vendors_list = ['Agoda','BookingCom','ClearTrip','Expedia','Goibibo','HotelsCom2','MakeMyTrip','Yatra','TG']
                    for nod in node:
                            count = count+1
                            vendor_name = ''.join(nod.xpath('.//@data-provider').extract())
                            for i in vendors_list:
                                if i.lower() in vendor_name.lower():
                                    price = ''.join(nod.xpath('.//@data-pernight').extract())
                                    tax = ''.join(nod.xpath('.//@data-taxesvalue').extract())
                                    tax_dict.update({i:tax})
                                    vendor_dict.update({i:price})
                    values = (hotel_id,hotel_name,checkin,checkout,rooms,adults,vendor_dict.get('Agoda','NA'),vendor_dict.get('BookingCom','NA'),vendor_dict.get('ClearTrip','NA'),vendor_dict.get('Expedia','NA'),vendor_dict.get('Goibibo','NA'),vendor_dict.get('HotelsCom2','NA'),vendor_dict.get('MakeMyTrip','NA'),vendor_dict.get('Yatra','NA'),vendor_dict.get('TG','NA'),tax_dict.get('Agoda','NA'),tax_dict.get('BookingCom','NA'),tax_dict.get('ClearTrip','NA'),tax_dict.get('Expedia','NA'),tax_dict.get('Goibibo','NA'),tax_dict.get('HotelsCom2','NA'),tax_dict.get('MakeMyTrip','NA'),tax_dict.get('Yatra','NA'),tax_dict.get('TG','NA'))
                    cur.execute(update_query % ''.join(url))
                    self.todays_excel_file.writerow(values)
