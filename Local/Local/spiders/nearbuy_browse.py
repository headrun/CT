from handle_utils import *
from scrapy.spider import BaseSpider
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.http import HtmlResponse
from scrapy.http.request import Request
import json
import MySQLdb

def get_cursor():
    conn = MySQLdb.connect(db='NEARBUY',
                    user = 'root',
                    charset="utf8",
                    host='localhost',
                    use_unicode=True)
    cursor = conn.cursor()
    return conn,cursor

class NearbuyBrowse(BaseSpider):
    name = 'nearbuy_browse'
    start_urls = ['https://www.nearbuy.com/']

    def __init__(self, *args, **kwargs):
        super(NearbuyBrowse, self).__init__(*args, **kwargs)
        self.conn,self.cursor=get_cursor()

    def parse(self,response):
        sel = Selector(response)
	cities_list = ['bangalore','hyderabad','chennai','mumbai','pune','kolkata','chandigarh','mysore','agra','jaipur','goa','ahmedabad','kochi','trivandrum','munnar','coorg','pondicherry','ooty','jodhpur','udaipur','guwahati','darjeeling','shillong','gangtok','dehradun','manali','kullu','rishikesh','tehri','shimla','corbett','nainital','dharamshala','srinagar','mahabaleshwar','matheran','alibag','lavasa','lonavala']

        for city in cities_list:
            spa_link = 'https://www.nearbuy.com/offers/' + city + '/spa-and-massage?list=LSF_Category%20Icon_Spa'
            category = 'spa-and-massage'
            yield Request(spa_link, callback=self.listing, meta={'city':city, 'category':category})
            
            eat_out_link = 'https://www.nearbuy.com/offers/' + city + '/food-and-drink?list=LSF_Category%20Icon_Eat%20Out'
            category = 'food-and-drink'
            yield Request(eat_out_link, callback=self.listing, meta={'city':city, 'category':category})
            
            movies_link = 'https://www.nearbuy.com/offers/' + city + '/movies-and-events?list=LSF_Category%20Icon_Movies'
            category = 'movies-and-events'
            yield Request(movies_link, callback=self.listing, meta={'city':city, 'category':category})

            activity_link = 'https://www.nearbuy.com/offers/' + city + '/activities?list=LSF_Category%20Icon_Activities'
            category = 'activities'
            yield Request(activity_link, callback=self.listing, meta={'city':city, 'category':category})

            salon_link = 'https://www.nearbuy.com/offers/' + city + '/beauty-and-salon?list=LSF_Category%20Icon_Salon'
            category = 'beauty-and-salon'
            yield Request(salon_link, callback=self.listing, meta={'city':city, 'category':category})

            health_link = 'https://www.nearbuy.com/offers/' + city + '/health?list=LSF_Category%20Icon_Health'
            category = 'health'
            yield Request(health_link, callback=self.listing, meta={'city':city, 'category':category})

            shopping_link = 'https://www.nearbuy.com/offers/' + city + '/in-store?list=LSF_Category%20Icon_Shopping'
            category = 'in-store'
            yield Request(shopping_link, callback=self.listing, meta={'city':city, 'category':category})
            
            hobbie_link = 'https://www.nearbuy.com/offers/' + city + '/hobbies-and-learning?list=LSF_Category%20Icon_Hobbies'
            category = 'hobbies-and-learning'
            yield Request(hobbie_link, callback=self.listing, meta={'city':city, 'category':category})

            home_auto_link = 'https://www.nearbuy.com/offers/' + city + '/home-and-auto?list=LSF_Category%20Icon_Home%20%26%20Auto'
            category = 'home-and-auto'
            yield Request(home_auto_link, callback=self.listing, meta={'city':city, 'category':category})
        
            hotel_link = 'https://www.nearbuy.com/search/offers/travel/' + city + '?suggestion=' + city + '&v=travel&q=' + city
            category = 'hotels'
            yield Request(hotel_link, callback=self.listing, meta={'city':city, 'category':category})

    def listing(self,response):
        sel = Selector(response)
        url_key = response.url.split('?')[-1]
        city = response.meta['city']
        start_count = 0
        category = response.meta['category']
        headers = {
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.8,fil;q=0.6',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
            'content-type': 'application/json',
            'accept': '*/*',
            }
        cookies = {
            'cookie': '_ceg.s=ou4166; _ceg.u=ou4166; _nb.cc=true; __asc=ac5a9ee515dc0419248d9214371; __auc=ebec598415da82949042565019f; _nb.rvl=10868%2C34005%2C44624; _nb.c=11353; _nb.cn=Bengaluru; _nb.cpl=bangalore; divisionChanged=false; groupon.divisionId=bangalore; _dc_gtm_UA-64425041-3=1; _gat_UA-64425041-3=1; _ga=GA1.2.1626946988.1501764847; _gid=GA1.2.1395125233.1502075442',
                }
        payload = {"category":category,"count":9,"vertical":"LOCAL","isFavourite":False,"city":"bangalore","pushEvent":False,"offset":0}
        
        if '/search/offers/travel/' in response.url:
            payload = {"searchKey": city, "count": 9, "vertical": "TRAVEL", "isFavourite": False, "pushEvent": False, "offset":0}

        api_link = 'https://www.nearbuy.com/api/deal/deals-list'
        yield Request(api_link, self.parse_meta_links, method="POST", body=json.dumps(payload),headers=headers, meta={'city':city, 'category':category, 'url_key':url_key})

        for i in range(100):
            start_count = start_count + 9
            payload.update({'offset':start_count})
            yield Request(api_link, self.parse_meta_links,  method="POST", body=json.dumps(payload), headers=headers, cookies=cookies, meta={'start_count':start_count, 'city' :city, 'category':category,'payload':payload, 'url_key':url_key},dont_filter=True)

    def parse_meta_links(self,response):
        sel = Selector(response)
        city = response.meta['city']
        category = response.meta['category']
        url_key = response.meta['url_key']
        body = json.loads(response.body)
        main_info = body.get('deals',{})
        for deal in main_info:
            deal_id = deal.get('id',{})
            url = deal.get('urlParams','')
            html_url = 'https://www.nearbuy.com' + '/'.join([normalize(str(i)) for i in url])+'?'+url_key
            deal_link = 'https://www.nearbuy.com/api/deal/deal-detail/' + str(deal_id)
            yield Request(deal_link, callback=self.metadata_parse, meta={'city':city, 'category':category, 'html_url':html_url})

    def metadata_parse(self,response):
        sel = Selector(response)
	table_category = response.meta['category']
        city = response.meta['city'].title()
        html_url = response.meta['html_url']
        body = json.loads(response.body)
        place_id = body.get('id','')
        place_name = normalize(body.get('merchantName',''))
        place_categories = body.get('mappedCategories',[])
        place_category = ''
        for category in place_categories:
            place_category = normalize(category.get('name',''))

        images = body.get('carousalImages',{})
        place_images = normalize('<>'.join(images))
        
        how_to_use_offer = body.get('redemptionSteps',{})
        desc = Selector(text=''.join(how_to_use_offer))
        how_to_use = normalize(' '.join(desc.xpath('//p/text()').extract()))
        
        cancelletion = body.get('cancellationPolicy',{})
        cancelletion_policy = normalize(cancelletion.get('name',''))
        
        addresses = body.get('redemptionLocations',{})
        address = []
        for add in addresses:
            single_address = normalize(add.get('address',''))
            address.append(single_address)
        place_addresses = '<>'.join(address)

        description = normalize(body.get('merchantDescription','')).replace('&nbsp;','').replace('amp;','').replace('<div>','').replace('</div>','')
        location = normalize(body.get('merchantLocation',''))

        things_to_remember = body.get('finePrint',{})
        things_to_rem = normalize(' '.join(things_to_remember))

        rating_info = body.get('rating',{})
        if not rating_info or rating_info == None:
            rating_info = {}
        rating = normalize(rating_info.get('avgRating',''))
        rating_type = normalize(rating_info.get('imageUrl',''))
        
        terms_conditions = body.get('redemptionSteps',[])
        desc = Selector(text=''.join(terms_conditions))
        terms1 = normalize(''.join(desc.xpath('//div//text()').extract())).replace('\xc2\xa0',' ')
        terms2 = normalize(''.join(desc.xpath('//p//text()').extract())).replace('\xc2\xa0',' ')
        terms = terms1 + ' ' + terms2

        offers = body.get('offers',{})
        for offer in offers:
            offer_id = offer.get('id','')
            offer_title = offer.get('title','')
            price_info = offer.get('price',{})
            price_original = price_info.get('mrp','')
            price_discount = price_info.get('msp','')
            
            validity_info = offer.get('offerValidity',{})
            valid_for = normalize(validity_info.get('validFor',''))
            validity_timings = validity_info.get('validTimings',[])
            if not validity_timings or validity_timings == None:
                validity_timings = []
            validity_time = ''
            for timings in validity_timings:
                validity_from = timings.get('from','')
                validity_to = timings.get('to','')
                validity_time = str(validity_from) + '-' +str(validity_to)
            
            validity_dates = validity_info.get('redeemDates','')
            for dates in validity_dates:
                validity_from = dates.get('fromDate','')
                validity_to  = dates.get('toDate','')
                validity_dates = str(validity_from) + '-' + str(validity_to)

            offer_validity = 'validity_dates' + ' - ' + validity_dates + ','  + 'validity_timings' + ' - ' + validity_time
            
            validity_details = normalize(validity_info.get('vd','')).replace('br','')
                
            offer_description = normalize(offer.get('offerDescription',''))
            
            offer_inclusions_info = offer.get('nearbuyMenu',{})
            if not offer_inclusions_info or offer_inclusions_info == None:
                offer_inclusions_info = {}
            offer_inclusions = normalize(offer_inclusions_info.get('value',''))
            desc = Selector(text=offer_inclusions)
            inclu1 = ','.join(desc.xpath('//p//text()').extract())
            inclu2 = ','.join(desc.xpath('//li//text()').extract())
            offer_inclusion = inclu1 + ' ' + inclu2

            if table_category == 'spa-and-massage' and place_name:
                query = 'insert into Spa(id, name, reference_url, city, place_category, location, description, addresses, how_to_use_offer, things_to_remember, cancelletion_policy, rating, rating_type, image_urls, created_at, modified_at, last_seen' 
                query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now(), reference_url=%s, last_seen=now()'
                values = ((place_id), (place_name), (html_url), (city), (place_category), (location), (description), (place_addresses), (how_to_use), (things_to_rem), (cancelletion_policy), (rating), (rating_type), (place_images), (html_url))
                self.cursor.execute(query,values)
            
            if table_category == 'food-and-drink' and place_name:
                query = 'insert into Eatout(id, name, reference_url, city, place_category, location, description, addresses, how_to_use_offer, things_to_remember, cancelletion_policy, rating, rating_type, image_urls, created_at, modified_at, last_seen'
                query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now(), reference_url=%s, last_seen=now()'
                values = ((place_id), (place_name), (html_url), (city), (place_category), (location), (description), (place_addresses), (how_to_use), (things_to_rem), (cancelletion_policy), (rating), (rating_type), (place_images), (html_url))
                self.cursor.execute(query,values)

            if table_category == 'movies-and-events' and place_name:
                query = 'insert into Theatre(id, name, reference_url, city, place_category, location, description, addresses, how_to_use_offer, things_to_remember, cancelletion_policy, rating, rating_type, image_urls, created_at, modified_at, last_seen'
                query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now(), reference_url=%s, last_seen=now()'
                values = ((place_id), (place_name), (html_url), (city), (place_category), (location), (description), (place_addresses), (how_to_use), (things_to_rem), (cancelletion_policy), (rating), (rating_type), (place_images), (html_url))
                self.cursor.execute(query,values)
                
            if table_category == 'activities' and place_name:
                query = 'insert into Activity(id, name, reference_url, city, place_category, location, description, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, image_urls, created_at, modified_at, last_seen'
                query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now(), reference_url=%s, last_seen = now()'
                values = ((place_id), (place_name), (html_url), (city), (place_category), (location), (description), (place_addresses), (how_to_use), (cancelletion_policy), (things_to_rem), (rating), (rating_type), (place_images), (html_url))
                self.cursor.execute(query,values)

            if table_category == 'beauty-and-salon' and place_name:
                query = 'insert into Salon(id, name, reference_url, city, place_category, location, description, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, image_urls, created_at, modified_at, last_seen'
                query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now(), reference_url=%s, last_seen=now()'
                values = ((place_id), (place_name), (html_url), (city), (place_category), (location), (description), (place_addresses), (how_to_use), (cancelletion_policy), (things_to_rem), (rating), (rating_type), (place_images), (html_url))
                self.cursor.execute(query,values)

            if table_category == 'health' and place_name:
                query = 'insert into Health(id, name, reference_url, city, place_category, location, description, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, image_urls, created_at, modified_at, last_seen'
                query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now(), reference_url=%s, last_seen=now()'
                values = ((place_id), (place_name), (html_url), (city), (place_category), (location), (description), (place_addresses), (how_to_use), (cancelletion_policy), (things_to_rem), (rating), (rating_type), (place_images), (html_url))
                self.cursor.execute(query,values)
           
            if table_category == 'in-store' and place_name:
                query = 'insert into Shopping(id, name, reference_url, city, place_category, location, description, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, terms_conditions, image_urls, created_at, modified_at, last_seen'
                query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now(), reference_url=%s, last_seen=now()'
                values = ((place_id), (place_name), (html_url), (city), (place_category), (location), (description), (place_addresses), (how_to_use), (cancelletion_policy), (things_to_rem), (rating), (rating_type), (terms), (place_images), (html_url))
                self.cursor.execute(query,values)

            if table_category == 'hobbies-and-learning' and place_name:
                query = 'insert into Hobbie(id, name, reference_url, city, place_category, location, description, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, image_urls, created_at, modified_at, last_seen'
                query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now(), reference_url=%s, last_seen=now()'
                values = ((place_id), (place_name), (html_url), (city), (place_category), (location), (description), (place_addresses), (how_to_use), (cancelletion_policy), (things_to_rem), (rating), (rating_type), (place_images), (html_url))
                self.cursor.execute(query,values)

            if table_category == 'home-and-auto' and place_name:
                query = 'insert into Homeauto(id, name, reference_url, city, place_category, location, description, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, image_urls, created_at, modified_at, last_seen'
                query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now(), reference_url=%s, last_seen=now()'
                values = ((place_id), (place_name), (html_url), (city), (place_category), (location), (description), (place_addresses), (how_to_use), (cancelletion_policy), (things_to_rem), (rating), (rating_type), (place_images), (html_url))
                self.cursor.execute(query,values)
            
            if table_category == 'hotels' and place_name:
                query = 'insert into Hotel(id, name, reference_url, city, place_category, location, description, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, image_urls, created_at, modified_at, last_seen'
                query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now(), reference_url=%s, last_seen=now()'
                values = ((place_id), (place_name), (html_url), (city), (place_category), (location), (description), (place_addresses), (how_to_use), (cancelletion_policy), (things_to_rem), (rating), (rating_type), (place_images), (html_url))
                self.cursor.execute(query,values)
            
	    if table_category and offer_id:
                query = 'insert into Offer(program_id, id, price_original, price_discounted, price_notes, offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, created_at, modified_at, last_seen'
                query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now()'
                values = ((place_id), (offer_id), (price_original), (price_discount), (valid_for), (offer_title), (offer_description), (offer_inclusion), (offer_validity), (validity_details))
                self.cursor.execute(query,values)

