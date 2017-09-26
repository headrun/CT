import urllib
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest
import json
import MySQLdb
from handle_utils import *

def get_cursor():
    conn = MySQLdb.connect(db = 'LITTLE', host = 'localhost', user = 'root',
    charset ='utf8', use_unicode = True)
    cursor = conn.cursor()
    return conn, cursor

class Little(BaseSpider):
    name = 'little_browse'
    start_urls = ['https://littleapp.in/api/popularlocalities']
    handle_httpstatus_list = [503, 400]


    def __init__(self, *args, **kwargs):
        super(Little, self).__init__(*args, **kwargs)
        self.conn, self.cursor = get_cursor()

    def parse(self, response): 
        json_data = json.loads(response.body)   
        x = json_data['c']
        handle_httpstatus_list = [503, 400]
        list1 = ['fdr','ss','ttd']
        for k in list1:
            for i in x:
                lat  = i['lat']
                lon = i['lon']
                city = i['cy']
                if city:
                    link = 'https://littleapp.in/api/search/v5?q=%7B%22who%22:%7B%22p%22:%22+919999999999%22%7D,%22s%22:%7B%22c%22:%7B%22l%22:%7B%22lat%22:'+str(lat)+',%22lon%22:'+str(lon)+'%7D,%22gkw%22:%22'+k+'%22,%22pg%22:0%7D%7D%7D'
                    yield Request(link, callback = self.parse_next)
    
    def parse_next(self, response):
        handle_httpstatus_list = [503, 400]
        try:
            json_data = json.loads(response.body)
            s = json_data.get('s',{})
            results = s.get('results',{})
            m = results.get('m','')
            for i in m:
                name = i.get('mn', '')
                sk = i.get('mc', '')
                if name and sk != '':
                    description = i.get('md', '')
                    image_url = i.get('mpic', '')
                    contact_numbers = i.get('mp', '')
                    state = i.get('ms', '')  
                    city = i.get('my', '')
                    location  = i.get('ml', '')
                    address = i.get('msa', '') 
                    zipcod = i.get('mz', '')
                    zipcode = str(zipcod)
                    if zipcode == '':
                        zipcode = '0'
                    else:
                        zipcode = zipcode
                    longitud = i['loc']['lon']
                    longitude = str(longitud)
                    latitude = i['loc']['lat']
                    no_of_ratings = i.get('mrt', '')
                    if no_of_ratings == '':
                        no_of_ratings = 0
                    else:
                        no_of_ratings = no_of_ratings
                    no_of_reviews = i.get('tnrt', '')
                    if no_of_reviews == '':
                        no_of_reviews = 0
                    else:
                        no_of_reviews = no_of_reviews
                    type1 = i.get('dt','')
                    re_term = i.get('mtc', '')
                    term = str(re_term).strip("[u'").strip("']")
                    terms_conditions = term.replace(".', u'", ". ")
                    x = i['deals']     
                    for k in x:
                        deal_sk = k['pdc']
                        item_name = k['dn']
                        available_timings = k.get('rtod','')
                        if available_timings != '':
                            available_timings = available_timings
                        else:
                            available_timings = ''
                        delivery_status = k.get('ds', '')
                        price = k['mrp']
                        offer = k['sp']
                        discount = k['pd']
                        weeks = k.get('rdow', '')
                        reference_url = response.url
                        week = str(weeks).strip("[u'").strip("']")   
                        available_weeks = week.replace("', u'", ",")
                        deal_term = k['dtc']
                        deal_ter = str(deal_term).strip("[u'").strip("']")
                        deal_terms_conditions = deal_ter.replace("', u'",', ')
                        if 'fdr' in response.url:
                            query = 'insert into Food_Drinks(sk,deal_sk,name,image_url,terms_conditions,contact_numbers,description,zipcode,latitude,longitude,state,city,location,address,no_of_ratings,no_of_reviews,item_name,price,offer,discount,available_weeks,available_timings,delivery_status,deal_terms_conditions,reference_url,created_at,modified_at,last_seen'
                            query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now())on duplicate key update modified_at = now()'
                            values = (sk,deal_sk,name,image_url,terms_conditions,contact_numbers,description,zipcode,latitude,longitude,state,city,location,address,no_of_ratings,no_of_reviews,item_name,price,offer,discount,available_weeks,available_timings,delivery_status,deal_terms_conditions,reference_url)
                            self.cursor.execute(query, values)
                        if 'ttd' in response.url:
                            query = 'insert into ThingsToDo(sk,deal_sk,name,image_url,terms_conditions,contact_numbers,description,zipcode,latitude,longitude,state,city,location,address,no_of_ratings,no_of_reviews,item_name,price,offer,discount,available_weeks,available_timings,deal_terms_conditions,reference_url,created_at,modified_at,last_seen'
                            query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now())on duplicate key update modified_at = now()'
                            values = (sk,deal_sk,name,image_url,terms_conditions,contact_numbers,description,zipcode,latitude,longitude,state,city,location,address,no_of_ratings,no_of_reviews,item_name,price,offer,discount,available_weeks,available_timings,deal_terms_conditions,reference_url)
                            self.cursor.execute(query, values)
                        if 'ss' in response.url:     
                            query = 'insert into Spas_Salons(sk,deal_sk,name,image_url,terms_conditions,contact_numbers,description,zipcode,latitude,longitude,state,city,location,address,no_of_ratings,no_of_reviews,item_name,price,offer,discount,available_weeks,available_timings,deal_terms_conditions,reference_url,created_at,modified_at,last_seen'
                            query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now())on duplicate key update modified_at = now()'   
                            values = (sk,deal_sk,name,image_url,terms_conditions,contact_numbers,description,zipcode,latitude,longitude,state,city,location,address,no_of_ratings,no_of_reviews,item_name,price,offer,discount,available_weeks,available_timings,deal_terms_conditions,reference_url)
                            self.cursor.execute(query, values)
        except:
            yield Request(response.url, callback = self.parse_next)

