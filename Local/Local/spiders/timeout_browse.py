from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest
import MySQLdb
from timeout_xpath import *
import re
from handle_utils import *
URL = 'https://www.timeout.com%s?partial=true&offset=%s&page_size=24'

def get_cursor():
    conn = MySQLdb.connect(db = 'TIMEOUT', host = 'localhost', user = 'root',
    charset ='utf8', use_unicode = True)
    cursor = conn.cursor()
    return conn, cursor

class TimeOut(BaseSpider):
    name = 'timeout_browse'
    start_urls = ['https://www.timeout.com/ahmedabad']
    handle_httpstatus_list = [404]

    def __init__(self, *args, **kwargs):
        super(TimeOut, self).__init__(*args, **kwargs) 
        self.conn, self.cursor = get_cursor()

    def parse(self, response): 
        sel = Selector(response)
        links = ['food-drink', 'theatre-arts','shopping-style','music-nightlife','city-guide','movie-theatres','classes','sports','kids','attractions-museums','things-to-do/upcoming','things-to-do/this-week','things-to-do/this-weekend','things-to-do/today']
        cities = ['ahmedabad','bangalore','chennai','delhi','hyderabad','jaipur','kolkata','mumbai','pune','surat']
        for m in cities:
            for l in links:
                lists = 'https://www.timeout.com/'+m+'/'+ l
                yield Request(lists, callback = self.details)
    def details(self, response):
        sel = Selector(response)
        kk = 1
        urls = response.url.split('https://www.timeout.com')[-1]
        if 'https://www.timeout.com/' in response.url:
             for j in range(1, 50):
                kk = kk+24
                url = URL % (urls, kk)
                yield Request(url, callback = self.details_next)

    def details_next(self, response):
        sel = Selector(response)
        x = response.url 
        listing = sel.xpath(listing_b)
        for k in listing:
            xx = k.extract()
            links_ = 'https://www.timeout.com' + xx
            yield Request(links_, callback = self.details_next1, meta= {'x':x})

    def details_next1(self, response):         
        sel = Selector(response)
        cit = response.url
        x = response.meta['x']
        y = re.compile(r'.com/(\D+)/\D+/')
        city = ''.join(y.findall(cit))
        price = ''
        description1 = ''.join(sel.xpath(description_b).extract()) or \
                      ''.join(sel.xpath(description_bb).extract()) 
        description = description1.encode('ascii', 'ignore').decode('ascii')
        

        name = ''.join(sel.xpath(name_b).extract()) or \
               ''.join(sel.xpath(name_bb).extract()) 
        image_url = ''.join(sel.xpath(image_urlb).extract())
        latitud = ''.join(sel.xpath(latitude_b).extract())
        if latitud != '':
            latitude = latitud.strip()
        else:
            latitude = 0
        longitud = ''.join(sel.xpath(longitude_b).extract())
        if longitud != '':
            longitude = longitud.strip()
        else:
            longitude = 0
        address = ''.join(sel.xpath(address_b).extract())
        contact_numbers = ''.join(sel.xpath(contact_numbers_b).extract())
        Website_name = ''.join(sel.xpath(website_name_b).extract())
        available_timings = ''.join(sel.xpath(available_timings_b).extract())
        check_likes = normalize(''.join(sel.xpath(check_likes_b).extract()))
        if '(' in  check_likes:
            price1 =  check_likes.strip(')').strip('\n')
            price = price1.split('(')[-1]
            if price == '':
                price = ''
            else:
                price = price
        check_like = ''.join(check_likes.replace(',', ''))
        y = re.compile(r'\d+ likes')
        no_of_likes = ''.join(y.findall(check_like))
        z = re.compile(r'\d+ checkins')
        no_of_checkins = ''.join(z.findall(check_like))
        if no_of_checkins == '':
            no_of_checkins = 0
        else:
            no_of_checkins= no_of_checkins.split(' ')[0]
        if no_of_likes =='':
            no_of_likes = 0
        else:
            no_of_likes = no_of_likes.split(' ')[0]
        reference_url = response.url
        sk = response.url
        if 'food-drink' in x:
            if name != '':
                zz =x
                query = 'insert into Food_Drinks(sk,name,image_url,contact_numbers,price,description,latitude,longitude,city ,address,Website_name,no_of_likes,no_of_checkins,available_timings,reference_url,created_at,modified_at ,last_seen'
                query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now())on duplicate key update modified_at = now()'
                values = (sk,normalize(name),image_url,normalize(contact_numbers),normalize(price),normalize(description),latitude,longitude,city,normalize(address),Website_name,no_of_likes,no_of_checkins,normalize(available_timings),zz)
                self.cursor.execute(query, values)
        if 'theatre-arts' in x:
            if name != '':
                zz = x
                query = 'insert into Theatre_Arts(sk,name,image_url,contact_numbers,price,description,latitude,longitude,city ,address,Website_name,no_of_likes,no_of_checkins,available_timings,reference_url,created_at,modified_at ,last_seen'
                query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now())on duplicate key update modified_at = now()'
                values = (sk,normalize(name),image_url,normalize(contact_numbers),normalize(price),normalize(description),latitude,longitude,city,normalize(address),Website_name,no_of_likes,no_of_checkins,normalize(available_timings),zz)
                self.cursor.execute(query, values)
        if 'music-nightlife' in x:
            if name != '':
                zz = x
                query = 'insert into Music_Nightlife(sk,name,image_url,contact_numbers,price,description,latitude,longitude,city ,address,Website_name,no_of_likes,no_of_checkins,available_timings,reference_url,created_at,modified_at ,last_seen'
                query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now())on duplicate key update modified_at = now()'
                values = (sk,normalize(name),image_url,normalize(contact_numbers),normalize(price),normalize(description),latitude,longitude,city,normalize(address),Website_name,no_of_likes,no_of_checkins,normalize(available_timings),zz)
                self.cursor.execute(query, values)
        if 'city-guide' in x:
            if name != '':
                zz = x 
                query = 'insert into City_Guide(sk,name,image_url,contact_numbers,price,description,latitude,longitude,city ,address,Website_name,no_of_likes,no_of_checkins,available_timings,reference_url,created_at,modified_at ,last_seen'
                query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now())on duplicate key update modified_at = now()'
                values = (sk,normalize(name),image_url,normalize(contact_numbers),normalize(price),normalize(description),latitude,longitude,city,normalize(address),Website_name,str(no_of_likes),str(no_of_checkins),normalize(available_timings),zz)
                self.cursor.execute(query, values)
        if 'shopping-style' in x:
            if name != '': 
                zz = x 
                query = 'insert into Shopping_Style(sk,name,image_url,contact_numbers,price,description,latitude,longitude,city ,address,Website_name,no_of_likes,no_of_checkins,available_timings,reference_url,created_at,modified_at ,last_seen'
                query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now())on duplicate key update modified_at = now()'
                values = (sk,normalize(name),image_url,normalize(contact_numbers),normalize(price),normalize(description),latitude,longitude,city,normalize(address),Website_name,no_of_likes,no_of_checkins,normalize(available_timings),zz)
                self.cursor.execute(query, values)
        if 'movie-theatres' in x:
            if name != '':  
                zz = x 
                query = 'insert into Movie_Theatres(sk,name,image_url,contact_numbers,price,description,latitude,longitude,city ,address,Website_name,no_of_likes,no_of_checkins,available_timings,reference_url,created_at,modified_at ,last_seen'
                query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now())on duplicate key update modified_at = now()'
                values = (sk,normalize(name),image_url,normalize(contact_numbers),normalize(price),normalize(description),latitude,longitude,city,normalize(address),Website_name,no_of_likes,no_of_checkins,normalize(available_timings),zz)
                self.cursor.execute(query, values)
        if 'things-to-do' or 'classes' or 'attractions-museums' or 'classes' or 'kids' in x:
            if name:
                zz = x 
                query = 'insert into Things_To_Do(sk,name,image_url,contact_numbers,price,description,latitude,longitude,city ,address,Website_name,no_of_likes,no_of_checkins,available_timings,reference_url,created_at,modified_at ,last_seen'
                query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now())on duplicate key update modified_at = now()'
                values = (sk,normalize(name),image_url,normalize(contact_numbers),normalize(price),normalize(description),latitude,longitude,city,normalize(address),Website_name,no_of_likes,no_of_checkins,normalize(available_timings),zz)
                self.cursor.execute(query, values)

    
