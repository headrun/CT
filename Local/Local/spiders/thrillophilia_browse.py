from handle_utils import *
from scrapy.spider import BaseSpider
from scrapy.http import Request
from thrillophilia_xpath import *
from scrapy.selector import Selector
from scrapy.http import HtmlResponse
import MySQLdb

def get_cursor():
    conn = MySQLdb.connect(db='THRILLOPHILIA',
                    user = 'root',         
                    charset="utf8",
                    host='localhost',
                    use_unicode=True)
    cursor = conn.cursor()
    return conn,cursor

class ThrillophiliaBrowse(BaseSpider):
    name = 'thrillophilia_browse'
    start_urls = ['https://www.thrillophilia.com/']
    handle_httpstatus_list = [302]

    def __init__(self, *args, **kwargs):
        super(ThrillophiliaBrowse, self).__init__(*args, **kwargs)
        self.conn,self.cursor=get_cursor()
       
    def parse(self,response):
        sel = Selector(response)
        cities_list = ['bangalore','hyderabad','chennai','mumbai','pune','kolkata','chandigarh','mysore','agra','jaipur','goa','ahmedabad','kochi','trivandrum','munnar','coorg','pondicherry','ooty','jodhpur','udaipur','guwahati','darjeeling','shillong','gangtok','dehradun','manali','kullu','rishikesh','tehri','shimla','corbett','nainital','dharamshala','srinagar','mahabaleshwar','matheran','alibag','lavasa','lonavala']
        for city in cities_list:
            activity_link = 'https://www.thrillophilia.com/cities/' + city + '/things-to-do'
            yield Request(activity_link,callback=self.listing)

            stays_link = 'https://www.thrillophilia.com/cities/' + city + '/stays'
            yield Request(stays_link,callback=self.listing)

            rentals_link = 'https://www.thrillophilia.com/cities/' + city + '/rentals'
            yield Request(rentals_link,callback=self.listing)

    def listing(self,response):
        sel = Selector(response)
        top_page = normalize(data_get(sel,top_page_xpath))
        if top_page:
            if 'http' not in top_page:
                top_page = 'https://www.thrillophilia.com' + top_page
                yield Request(top_page, callback=self.top_page, dont_filter=True)
        
    def top_page(self,response):
        sel = Selector(response)
        city = normalize(response.url.split('/')[-2]).title()
        if 'Activity' in response.url:
            program_type = 'Activity'
        elif 'Stay' in response.url:
            program_type = 'Stay'
        else:
            program_type = 'Rental'
        activities_links = data_list_get(sel,activities_links_xpath)
        for link in activities_links:
            if 'http' not in link:
                link = 'https://www.thrillophilia.com' + normalize(link)
                yield Request(link, callback=self.meta_data_parse, meta={'city':city,'program_type':program_type}, dont_filter=True)

        load_more_collection = normalize(data_get(sel,load_more_collection_link_xpath))
        if load_more_collection:
            yield Request(load_more_collection, callback=self.top_page, dont_filter=True)

    def meta_data_parse(self,response):
        sel = Selector(response)
        city = response.meta['city']
        program_type = response.meta['program_type']
        reference_url = normalize(response.url)
        sk = normalize(response.url).split('/')[-1]
        title = normalize(data_get(sel,title_xpath))
        location = normalize(data_get(sel,location_xpath))
        rating = normalize(data_get(sel,rating_xpath))
        price = normalize(data_get(sel,price_xpath))
        no_of_days_nights = normalize(' & '.join(data_list_get(sel,no_of_days_nights_xpath)))
        other_inclusions = normalize(','.join(data_list_get(sel,other_inclusions_xpath)))
        cashback = normalize(data_get(sel,cashback_xpath))
        special_offer = normalize(data_get(sel,special_offer_xpath))
        overview = normalize(' '.join(data_list_get(sel,overview_xpath))).replace('\xc2\xa0','')
        itinerary = normalize(','.join(data_list_get(sel,itinerary_xpath)))
        stay = normalize(','.join(data_list_get(sel,stay_xpath)))
        meal = normalize(','.join(data_list_get(sel,meal_xpath)))
        activities_available = normalize(','.join(data_list_get(sel,activity_xpath))).replace('\xe2\x80\x93','-')
        things_to_carry = normalize(','.join(data_list_get(sel,things_to_carry_xpath)))
        advisory = normalize(','.join(data_list_get(sel,advisory_xpath))).replace('.','')
        tour_type = normalize(','.join(data_list_get(sel,tour_type_xpath)))
        cancellation_policy = normalize(' '.join(data_list_get(sel,cancellation_policy_xpath)))
        refund_policy = normalize(' '.join(data_list_get(sel,refund_policy_xpath)))
        confirmation_policy = normalize('<>'.join(data_list_get(sel,confirmation_policy_xpath)))
        images = normalize('<>'.join(data_list_get(sel,images_xpath)))
        reviews_page = normalize(data_get(sel,reviews_page_xpath))
        if reviews_page:
            if 'http' not in reviews_page:
                reviews_page = 'https://www.thrillophilia.com' + reviews_page
        reviews_count = normalize(data_get(sel,reviews_count_xpath)).replace('reviews','').replace('review','')


        if program_type == 'Activity':
            query='insert into Activity(id, name, activity_url, city, location, itinerary, overview, no_of_days_nights, stay, meal, activities_available, other_inclusions, things_to_carry, advisory, tour_type, cancellation_policy, refund_policy, confirmation_policy, price, cashback, special_offer, rating, image_urls, review_url, reviews_count, created_at, modified_at, last_seen' 
            query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now()' 
            values=((sk), (title),(reference_url),(city),(location),(itinerary),(overview),(no_of_days_nights),(stay),(meal),(activities_available),(other_inclusions),(things_to_carry),(advisory),(tour_type),(cancellation_policy),(refund_policy), (confirmation_policy),(price), (cashback), (special_offer),(rating),(images), reviews_page, reviews_count)
            self.cursor.execute(query,values)
        
        
        if program_type == 'Stay':
            query='insert into Stay(id, name, stay_url, city, location, itinerary, overview, no_of_days_nights, stay, meal, activities_available, other_inclusions, things_to_carry, advisory, tour_type, cancellation_policy, refund_policy, confirmation_policy, price, cashback, special_offer, rating, image_urls, review_url, reviews_count, created_at, modified_at, last_seen'
            query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now()'
            values=((sk), (title),(reference_url),(city),(location),(itinerary),(overview),(no_of_days_nights),(stay),(meal),(activities_available),(other_inclusions),(things_to_carry),(advisory),(tour_type),(cancellation_policy),(refund_policy), (confirmation_policy),(price), (cashback), (special_offer),(rating),(images),reviews_page, reviews_count)
            self.cursor.execute(query,values)

        
        if program_type == 'Rental':
            query='insert into Rentals(id, name, rental_url, city, location, itinerary, overview, no_of_days_nights, other_inclusions, things_to_carry, advisory, tour_type, cancellation_policy, refund_policy, confirmation_policy, price, cashback, special_offer, rating, image_urls, review_url, reviews_count, created_at, modified_at, last_seen'
            query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now()'
            values=((sk), (title),(reference_url),(city),(location), (itinerary), (overview), (no_of_days_nights), (other_inclusions), (things_to_carry), (advisory),(tour_type), (cancellation_policy), (refund_policy),(confirmation_policy),(price),(cashback),(special_offer),(rating),(images),(reviews_page),(reviews_count))
            self.cursor.execute(query,values)
