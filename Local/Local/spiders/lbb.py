from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from handle_utils import *
import json
import MySQLdb

def get_cursor():
    conn = MySQLdb.connect(db='LBB', host='localhost', user='root', passwd='',
    charset='utf8', use_unicode=True)
    cursor = conn.cursor()
    return conn, cursor

class LbbBrowse(BaseSpider):
    name = 'lbb_browse'
    start_urls = ['https://lbb.in']
    
    
    def __init__(self, *args, **kwargs):
        super(LbbBrowse, self).__init__(*args, **kwargs)
        self.conn, self.cursor = get_cursor()
    
    def parse(self,response):
        sel = Selector(response)
        food_api_keys = ['&provider=delhi&skipArticles=delhi62397,delhi147335,delhi153741&taxonomies=food-drinks', '&provider=bangalore&skipArticles=bangalore62624,bangalore62521,bangalore1434&taxonomies=food-drinks', '&provider=mumbai&skipArticles=mumbai60047,mumbai60256,mumbai60089&taxonomies=food-drinks', '&provider=goa&skipArticles=goa1927,goa1828,goa1840&taxonomies=food-drinks', '&provider=kolkata&skipArticles=&taxonomies=food-drinks', '&provider=pune&skipArticles=&taxonomies=food-drinks', '&provider=gurgaon&skipArticles=&taxonomies=food-drinks', '&provider=chennai&skipArticles=&taxonomies=food-drinks']
        for key in food_api_keys:
            for i in range(100): 
                food_drinks_link = 'https://api.lbb.in/web/cards?page=' + str(i) + key
                city = key.split('&')[1].split('=')[-1]
                yield Request(food_drinks_link, callback=self.listing,meta={'city':city}) 
           
        lifestyle_api_keys = ['&provider=delhi&skipArticles=delhi153675,delhi152300,delhi43518&taxonomies=lifestyle', '&provider=bangalore&skipArticles=bangalore62279,bangalore58730,bangalore61962&taxonomies=lifestyle', '&provider=mumbai&skipArticles=mumbai60027,mumbai60117,mumbai59275&taxonomies=lifestyle', '?page=1&provider=kolkata&skipArticles=&taxonomies=lifestyle', '&provider=pune&skipArticles=&taxonomies=lifestyle', '&provider=gurgaon&skipArticles=&taxonomies=lifestyle', '&provider=chennai&skipArticles=&taxonomies=lifestyle']
        for key in lifestyle_api_keys:
            for i in range(100):
                lifestyle_link = 'https://api.lbb.in/web/cards?page=' + str(i) + key
                city = key.split('&')[1].split('=')[-1]
                yield Request(lifestyle_link, callback=self.listing,meta={'city':city})

        culture_api_keys = ['&provider=delhi&skipArticles=delhi147226,delhi44299,delhi152585&taxonomies=features-culture', '&provider=bangalore&skipArticles=bangalore62711,bangalore62279,bangalore61957&taxonomies=features-culture', '&provider=mumbai&skipArticles=mumbai19355,mumbai59677,mumbai23249&taxonomies=features-culture', '&provider=kolkata&skipArticles=&taxonomies=features-culture', '&provider=pune&skipArticles=&taxonomies=features-culture', '&provider=gurgaon&skipArticles=&taxonomies=features-culture', '&provider=chennai&skipArticles=&taxonomies=features-culture']
        for key in culture_api_keys:
            for i in range(100):
                culture_link = 'https://api.lbb.in/web/cards?page=' + str(i) + key
                city = key.split('&')[1].split('=')[-1]
                yield Request(culture_link, callback=self.listing, meta={'city':city})
            
        tavel_api_keys = ['&provider=delhi&skipArticles=delhi153822,delhi153751,delhi153614&taxonomies=travel', '&provider=bangalore&skipArticles=bangalore62397,bangalore62544,bangalore62456&taxonomies=travel', '&provider=mumbai&skipArticles=mumbai60211,mumbai55695,mumbai59693&taxonomies=travel', '&provider=kolkata&skipArticles=&taxonomies=travel', '&provider=pune&skipArticles=&taxonomies=travel', '&provider=gurgaon&skipArticles=&taxonomies=travel', '&provider=chennai&skipArticles=&taxonomies=travel']
        for key in tavel_api_keys:
            for i in range(100):
                travel_link = 'https://api.lbb.in/web/cards?page=' + str(i) + key
                city = key.split('&')[1].split('=')[-1]
                yield Request(travel_link, callback=self.listing, meta={'city':city})

        shopping_fashion_api_keys = ['&provider=delhi&skipArticles=delhi108319,delhi153795,delhi153668&taxonomies=shopping-fashion', '&provider=bangalore&skipArticles=bangalore62520,bangalore62432,bangalore62620&taxonomies=shopping-fashion', '&provider=mumbai&skipArticles=mumbai52990,mumbai6972,mumbai54900&taxonomies=shopping-fashion', '&provider=goa&skipArticles=goa1511,goa1284&taxonomies=shopping-fashion', '&provider=kolkata&skipArticles=&taxonomies=shopping-fashion', '&provider=pune&skipArticles=&taxonomies=shopping-fashion', '&provider=gurgaon&skipArticles=&taxonomies=shopping-fashion', '&provider=chennai&skipArticles=&taxonomies=shopping-fashion']
        for key in shopping_fashion_api_keys:
            for i in range(100):
                fashion_link = 'https://api.lbb.in/web/cards?page=' + str(i) + key
                city = key.split('&')[1].split('=')[-1]
                yield Request(fashion_link, callback=self.listing, meta={'city':city})

        activity_api_keys = ['&provider=delhi&skipArticles=delhi153728,delhi153645,delhi153296&taxonomies=activities-classes', '&provider=bangalore&skipArticles=bangalore61119,bangalore62429,bangalore44394&taxonomies=activities-classes', '&provider=mumbai&skipArticles=mumbai60030,mumbai59932,mumbai59924&taxonomies=activities-classes', '&provider=goa&skipArticles=goa1806,goa1906,goa1832&taxonomies=activities-classes', '&provider=kolkata&skipArticles=&taxonomies=activities-classes', '&provider=pune&skipArticles=&taxonomies=activities-classes', '&provider=gurgaon&skipArticles=&taxonomies=activities-classes', '&provider=chennai&skipArticles=&taxonomies=activities-classes']
        for key in activity_api_keys:
            for i in range(100):
                activity_link = 'https://api.lbb.in/web/cards?page=' + str(i) + key
                city = key.split('&')[1].split('=')[-1]
                yield Request(activity_link, callback=self.listing, meta={'city':city})
            
        fitness_api_keys = ['&provider=delhi&skipArticles=delhi152989,delhi122721,delhi55356&taxonomies=fitness-health', '&provider=bangalore&skipArticles=bangalore40114,bangalore46598,bangalore45995&taxonomies=fitness-health', '&provider=mumbai&skipArticles=mumbai6972,mumbai19880,mumbai33799&taxonomies=fitness-health', '&provider=kolkata&skipArticles=&taxonomies=fitness-health', '&provider=pune&skipArticles=pune51243,pune45075,pune50707,pune52059,pune52047,pune51243', '&provider=gurgaon&skipArticles=&taxonomies=fitness-health',]
        for key in fitness_api_keys:
            for i in range(100):
                fitness_link = 'https://api.lbb.in/web/cards?page=' + str(i) + key
                city = key.split('&')[1].split('=')[-1]
                yield Request(fitness_link, callback=self.listing, meta={'city':city})


    def listing(self, response):
        city = response.meta['city']
        reference_url = normalize(response.url)
        activity_category = reference_url.split('=')[-1]
        json_data = json.loads(response.body)
        for single_data in json_data:
            article_data = single_data.get('data',{})
            article_id = normalize(article_data.get('_id'))
            article = article_data.get('providerData',{})
            article_id = normalize(article_data.get('_id'))
            article_user_info = article_data.get('user',{})
            article_posted_by = article_user_info.get('displayName')
            article_title = normalize(article.get('title','')) or  normalize(article_data.get('title',''))
            article_sections = article_data.get('sections',{})
            
            other_article_sections = article.get('sections',{})
            if other_article_sections:
                article_sections = other_article_sections
            
            content = []
            
            for section in article_sections:
                sub_title = normalize(section.get('title',''))
                content_text = section.get('content','')
                article_content = normalize(content_text.replace('<a>','').replace('</a>','').replace('<p>','').replace('</p>','').split('>')[-1]).replace('\xc2\xa0','').replace('\xe2\x80\x99','').replace('\xe2\x80\x93','').replace('\xc3\x97','x').replace('<em>','').replace('</em>','').replace('\xF0\x9F\x8D\xBB','').replace('\xF0\x9F\x98\x8B','').replace('\xF0\x9F\x8D\x89','').replace('\xF0\x9F\x8D\x93','').replace('\xF0\x9F\x98\x8A','').replace('\xF0\x9F\x98\x9C','').replace('\xF0\x9F\x98\x8D','').replace('\xF0\x9F\x98\x81','').replace('\xF0\x9F\xA4\xA4','').replace('\xF0\x9F\xA4\xA4\xF0\x9F','').replace('\xF0\x9F\xA5\x90','').replace('\xF0\x9F\x98\xB1','').replace('\xF0\x9F\x99\x8B\xF0\x9F','').replace('\xF0\x9F\x8D\xBA','').replace('\xF0\x9F\x98\x89','').replace('\xF0\x9F\x98\x83','').replace('\xF0\x9F\x92\x96','').replace('\xF0\x9F\x8F\xBC','').replace('\xF0\x9F\x8D\x94','').replace('\xF0\x9F\x98\x88','').replace('\xF0\x9F\x8D\x89','').replace('\xF0\x9F\x98\x8B','').replace('\xF0\x9F\x8D\xBB','').replace('\xF0\x9F\x98\x80\xF0\x9F','').replace('\xF0\x9F\xA5\x92','').replace('\xF0\x9F\xA5\x9E\xF0\x9F','').replace('\xF0\x9F\x8E\xBC\xF0\x9F','').replace('\xF0\x9F\x98\x8C\xF0\x9F','').replace('\xF0\x9F\xA5\x98','').replace('\xF0\x9F\x98\x8B','').replace('\xF0\x9F\x99\x8A','').replace('\xF0\x9F\xA5\x82\xF0\x9F','').replace('\xF0\x9F\x98\x8B\xF0\x9F','').replace('\xF0\x9F\x8D\x9D','').replace('\xF0\x9F\x8D\x9C','').replace('\xF0\x9F\x92\x96','').replace('\x8F\xBB\xE2\x80\x8D\xE2','').replace('\xF0\x9F\x91\x85','').replace('\xF0\x9F\xA4\xA4\xF0\x9F','').replace('\xF0\x9F\xA4\xA4','').replace('\xF0\x9F\x8D\xB0','').replace('\xF0\x9F\x98\x86','').replace('\xA5\x93','').replace('\x98\x80','').replace('\x8E\xB5\xF0\x9F\x8E\xB7','').replace('\xF0\x9F\x98\x8C\xF0\x9F','').replace('\x91\x8C','').replace('\xF0\x9F\x98\x8B\xF0\x9F','').replace('\xF0\x9F\x8D\xAB','').replace('\xF0\x9F\x92\x96','').replace('\x99\x82\xEF\xB8\x8F','').replace('\xF0\x9F\xA4\xA4','').replace('\xF0\x9F\x98\x8B','')
                main_context = sub_title + ' : ' + article_content
                content.append(main_context)

            place = article_data.get('data',{})

            other_places = article_data.get('places')
            if other_places:
                place = other_places[0]
            
            place_name = normalize(place.get('name',''))
            place_category = normalize(place.get('classification',''))
            place_sub_category = normalize(place.get('subClassification',''))
            article_provider_city = normalize(place.get('provider',''))
            article_working_hours = place.get('workingHours','')
            working_hours = []
            for working in article_working_hours:
                day = normalize(working.get('dayOfTheWeek',''))
                working_timings = working.get('timings','')
                for time in working_timings:
                    time_open = time.get('open','')
                    time_close = time.get('close','')
                    working_times_days = day + ' ' +  str(time_open) + ' - ' + str(time_close)
                    working_hours.append(working_times_days)
            
            article_meta = place.get('meta',{})
            article_delivery_status = article_meta.get('delivery',{})
            article_delivery_status = article_delivery_status.get('available','')
            if article_delivery_status == True:
                article_delivery_status = 'available'

            article_budget = place.get('budget',{})
            price = normalize(article_budget.get('cost',''))
            price_notes = normalize(article_budget.get('notes',''))

            article_contact_details = place.get('contact',{})
            contact_number = normalize(article_contact_details.get('contactNumber',''))
            email = normalize(article_contact_details.get('email',''))
            fb_link = normalize(article_contact_details.get('fbLink',''))
            web_link = normalize(article_contact_details.get('webLink',''))
            twitter_link = normalize(article_contact_details.get('twitterLink',''))
            instagram_link = normalize(article_contact_details.get('instagramLink',''))
                
            activity_location_info = place.get('location',{})
            activity_nearest_railway_station = normalize(activity_location_info.get('nearestRailwayStation',''))
            activity_nearest_metro = normalize(activity_location_info.get('nearestMetro',''))
            activity_state = normalize(activity_location_info.get('state',''))
            activity_city = normalize(activity_location_info.get('city','')) or normalize(city).title()
            activity_location = normalize(''.join(activity_location_info.get('locality','')))
            activity_street = normalize(activity_location_info.get('street','')) 
            activity_address = normalize(activity_location_info.get('address',''))

            activity_image_info = article_data.get('media','')
            images = []
            for image in activity_image_info:
                activity_image = normalize(image.get('source',''))
                images.append(activity_image)
            activity_more_info = article_data.get('more',{})
            activity_image_info = activity_more_info.get('featured_image',{})
            activity_image = activity_image_info.get('source','')
            activity_link = activity_image_info.get('link','')
            if activity_link:
                images.append(activity_link)
            if article_title and article_id:
                if activity_category=='food-drinks':
                    query = 'insert into Food(id, article_name, posted_by, city, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_image, place_url, reference_url, created_at, modified_at, last_seen'
                    query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(), now(), now())on duplicate key update modified_at = now()'
                    values = ((article_id),(article_title), article_posted_by, activity_city, activity_state, (' '.join(content)), (place_name), (place_category), (place_sub_category), ','.join(working_hours), (article_delivery_status), (price), (price_notes), (contact_number), (email), (fb_link), (web_link), (twitter_link), (instagram_link), (activity_nearest_railway_station), (activity_nearest_metro), (activity_location), (activity_street), (activity_address), ('<>'.join(images)), (activity_link), (reference_url))
                    self.cursor.execute(query, values)
            
            if article_title and article_id:
                if activity_category=='lifestyle':
                    query = 'insert into Lifestyle(id, article_name, posted_by, city, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_image, place_url, reference_url, created_at, modified_at, last_seen'
                    query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(), now(), now())on duplicate key update modified_at = now()'
                    values = ((article_id),(article_title), article_posted_by, activity_city, activity_state, (' '.join(content)), (place_name), (place_category), (place_sub_category), ','.join(working_hours), (article_delivery_status), (price), (price_notes), (contact_number), (email), (fb_link), (web_link), (twitter_link), (instagram_link), (activity_nearest_railway_station), (activity_nearest_metro), (activity_location), (activity_street), (activity_address), ('<>'.join(images)), (activity_link), (reference_url))
                    self.cursor.execute(query, values)
            
            if article_title and article_id:
                if activity_category=='features-culture':
                    query = 'insert into Culture(id, article_name, posted_by, city, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_image, place_url, reference_url, created_at, modified_at, last_seen'
                    query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(), now(), now())on duplicate key update modified_at = now()'
                    values = ((article_id),(article_title), article_posted_by, activity_city, activity_state, (' '.join(content)), (place_name), (place_category), (place_sub_category), ','.join(working_hours), (article_delivery_status), (price), (price_notes), (contact_number), (email), (fb_link), (web_link), (twitter_link), (instagram_link), (activity_nearest_railway_station), (activity_nearest_metro), (activity_location), (activity_street), (activity_address), ('<>'.join(images)), (activity_link), (reference_url))
                    self.cursor.execute(query, values)

            if article_title and article_id:
                if activity_category=='travel':
                    query = 'insert into Travel(id, article_name, posted_by, city, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_image, place_url, reference_url, created_at, modified_at, last_seen'
                    query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(), now(), now())on duplicate key update modified_at = now()'
                    values = ((article_id),(article_title), article_posted_by, activity_city, activity_state, (' '.join(content)), (place_name), (place_category), (place_sub_category), ','.join(working_hours), (article_delivery_status), (price), (price_notes), (contact_number), (email), (fb_link), (web_link), (twitter_link), (instagram_link), (activity_nearest_railway_station), (activity_nearest_metro), (activity_location), (activity_street), (activity_address), ('<>'.join(images)), (activity_link), (reference_url))
                    self.cursor.execute(query, values)

            if article_title and article_id:
                if activity_category=='shopping-fashion':
                    query = 'insert into Shopping(id, article_name, posted_by, city, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_image, place_url, reference_url, created_at, modified_at, last_seen'
                    query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(), now(), now())on duplicate key update modified_at = now()'
                    values = ((article_id),(article_title), article_posted_by, activity_city, activity_state, (' '.join(content)), (place_name), (place_category), (place_sub_category), ','.join(working_hours), (article_delivery_status), (price), (price_notes), (contact_number), (email), (fb_link), (web_link), (twitter_link), (instagram_link), (activity_nearest_railway_station), (activity_nearest_metro), (activity_location), (activity_street), (activity_address), ('<>'.join(images)), (activity_link), (reference_url))
                    self.cursor.execute(query, values)

            if article_title and article_id:
                if activity_category=='activities-classes':
                    query = 'insert into Activity(id, article_name, posted_by, city, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_image, place_url, reference_url, created_at, modified_at, last_seen'
                    query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(), now(), now())on duplicate key update modified_at = now()'
                    values = ((article_id),(article_title), article_posted_by, activity_city, activity_state, (' '.join(content)), (place_name), (place_category), (place_sub_category), ','.join(working_hours), (article_delivery_status), (price), (price_notes), (contact_number), (email), (fb_link), (web_link), (twitter_link), (instagram_link), (activity_nearest_railway_station), (activity_nearest_metro), (activity_location), (activity_street), (activity_address), ('<>'.join(images)), (activity_link), (reference_url))
                    self.cursor.execute(query, values)

            if article_title and article_id:
                if activity_category=='fitness-health':
                    query = 'insert into Fitness(id, article_name, posted_by, city, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_image, place_url, reference_url, created_at, modified_at, last_seen'
                    query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(), now(), now())on duplicate key update modified_at = now()'
                    values = ((article_id),(article_title), article_posted_by, activity_city, activity_state, (' '.join(content)), (place_name), (place_category), (place_sub_category), ','.join(working_hours), (article_delivery_status), (price), (price_notes), (contact_number), (email), (fb_link), (web_link), (twitter_link), (instagram_link), (activity_nearest_railway_station), (activity_nearest_metro), (activity_location), (activity_street), (activity_address), ('<>'.join(images)), (activity_link), (reference_url))
                    self.cursor.execute(query, values)
