from handle_utils import *
from scrapy.spider import BaseSpider
from scrapy.http import Request, FormRequest
from explara_xpath import *
from scrapy.selector import Selector
from scrapy.http import HtmlResponse
import MySQLdb

def get_cursor():
    conn = MySQLdb.connect(db='EXPLARA',
                    user = 'root',
                    charset="utf8",
                    host='localhost',
                    use_unicode=True)
    cursor = conn.cursor()
    return conn,cursor

class ExplaraBrowse(BaseSpider):
    name = 'explara_browse'
    start_urls = ['https://in.explara.com/']

    def __init__(self, *args, **kwargs):
        super(ExplaraBrowse, self).__init__(*args, **kwargs)
        self.conn,self.cursor=get_cursor()

    def parse(self,response):
        sel = Selector(response)
        cities_list = ['bengaluru', 'hyderabad', 'delhi', 'chennai','mumbai','pune','kolkata','chandigarh','mysore','agra','jaipur','goa','ahmedabad','kochi','trivandrum','munnar','coorg','pondicherry','ooty','jodhpur','udaipur','guwahati','darjeeling','shillong','gangtok','dehradun','manali','kullu','rishikesh','tehri','shimla','corbett','nainital','dharamshala','srinagar','mahabaleshwar','matheran','alibag','lavasa','lonavala']
        for city in cities_list:
            adventure_link = 'https://in.explara.com/' + city + '/adventure-and-outdoor'
            category = 'adventure-and-outdoor'
            yield Request(adventure_link, callback=self.listing, meta={'city':city, 'category':category})
            
            entertainment_link = 'https://in.explara.com/' + city + '/entertainment'
            category = 'entertainment'
            yield Request(entertainment_link, callback=self.listing, meta={'city':city, 'category':category})

            alumni_campus_link = 'https://in.explara.com/' + city + '/alumni-and-campus'
            category = 'alumni-and-campus'
            yield Request(alumni_campus_link, callback=self.listing, meta={'city':city, 'category':category})
            
            biz_tech_link = 'https://in.explara.com/' + city + '/biz-and-tech'
            category = 'biz-and-tech'
            yield Request(biz_tech_link, callback=self.listing, meta={'city':city, 'category':category})

            sports_link = 'https://in.explara.com/' + city + '/sports-and-fitness'
            category = 'sports-and-fitness'
            yield Request(sports_link, callback=self.listing, meta={'city':city, 'category':category})

            food_baverages_food_link = 'https://in.explara.com/' + city + '/food-and-beverage/food'
            category = 'food'
            yield Request(food_baverages_food_link, callback=self.listing, meta={'city':city, 'category':category})

            food_baverages_drink_link = 'https://in.explara.com/' + city + '/food-and-beverage/drinks'
            category = 'drinks'
            yield Request(food_baverages_drink_link, callback=self.listing, meta={'city':city, 'category':category})

            interests_link = 'https://in.explara.com/' + city + '/interests'
            category = 'interests'
            yield Request(interests_link, callback=self.listing, meta={'city':city, 'category':category})

    def listing(self, response):
        sel = Selector(response)
        city = response.meta['city']
        category = response.meta['category']
        desc = ''
        if '/application/experience/load-more-events' in response.url:
            desc = Selector(text=response.body)
        adventure_links = data_list_get(sel, adventure_outdoor_links_xpath)
        if desc and category == 'adventure-and-outdoor':
            adventure_links = adventure_links+ desc.xpath('//a[@itemprop="url"]/@href').extract()
        if adventure_links and category =='adventure-and-outdoor':
            for link in adventure_links:
                yield Request(normalize(link), self.metapage, meta={'city':city, 'category':category}, dont_filter=True)
            adventure_load_more = data_get(sel,adventure_load_more_xpath)
            if adventure_load_more:
                form_data = {'category':category, 'page':'1'}
                if city:
                    form_data.update({'city':city})
                load_more_link = 'https://in.explara.com/application/experience/load-more-events'
                yield FormRequest(load_more_link, callback=self.listing, method="POST", formdata=form_data, meta={'city':city, 'category':category})

        entertainment_links = data_list_get(sel, entertainment_links_xpath)  
        if desc and category == 'entertainment':
            entertainment_links = desc.xpath('//a[@itemprop="url"]/@href').extract()

        if entertainment_links and category == 'entertainment':
            for link in entertainment_links:
                yield Request(normalize(link), self.metapage, meta={'city':city, 'category':category})
            entertainment_load_more = data_get(sel,entertainment_load_more_xpath)
            if entertainment_load_more:
                form_data = {'category':category, 'page':'1'}
                if city:
                    form_data.update({'city':city})
                load_more_link = 'https://in.explara.com/application/experience/load-more-events'
                yield FormRequest(load_more_link, callback=self.listing, method="POST", formdata=form_data, meta={'city':city})

        alumni_campus_links = data_list_get(sel, alumni_campus_lnks_xpath) 
        if desc and category =='alumni-and-campus':
            alumni_campus_links = desc.xpath('//a[@itemprop="url"]/@href').extract()

        if alumni_campus_links and category =='alumni-and-campus':
            for link in alumni_campus_links:
                yield Request(normalize(link), self.metapage, meta={'city':city, 'category':category})
            alumni_campus_load_more = data_get(sel,alumni_campus_load_more_xpath)
            if alumni_campus_load_more:
                form_data = {'category':category, 'page':'1'}
                if city:
                    form_data.update({'city':city})
                load_more_link = 'https://in.explara.com/application/experience/load-more-events'
                yield FormRequest(load_more_link, callback=self.listing, method="POST", formdata=form_data, meta={'city':city})

        biz_tech_links = data_list_get(sel, biz_tech_links_xpath) 
        if desc and category == 'biz-and-tech':
            biz_tech_links = desc.xpath('//a[@itemprop="url"]/@href').extract()
        if biz_tech_links and category == 'biz-and-tech':
            for link in biz_tech_links:
                yield Request(normalize(link), self.metapage, meta={'city':city, 'category':category})
            biz_load_more = data_get(sel,biz_load_more_xpath)
            if biz_load_more:
                category = 'biz-and-tech'
                form_data = {'category':category, 'page':'1'}
                if city:
                    form_data.update({'city':city})
                load_more_link = 'https://in.explara.com/application/experience/load-more-events'
                yield FormRequest(load_more_link, callback=self.listing, method="POST", formdata=form_data, meta={'city':city, 'category':category})

        sports_fitness_links = data_list_get(sel,sports_fitness_links_xpath) 
        if desc and category=='sports-and-fitness':
            sports_fitness_links = desc.xpath('//a[@itemprop="url"]/@href').extract()

        if sports_fitness_links and category=='sports-and-fitness':
            for link in sports_fitness_links:
                yield Request(normalize(link), self.metapage, meta={'city':city, 'category':category})
            sports_fitness_load_more = data_get(sel,sports_fitness_load_more_xpath)
            if sports_fitness_load_more:
                form_data = {'category':category, 'page':'1'}
                if city:
                    form_data.update({'city':city})
                load_more_link = 'https://in.explara.com/application/experience/load-more-events'
                yield FormRequest(load_more_link, callback=self.listing, method="POST", formdata=form_data, meta={'city':city})

        food_baverages_food_links = data_list_get(sel,food_baverages_food_links_xpath) 
        if desc and category == 'food':
            food_baverages_food_links = desc.xpath('//a[@itemprop="url"]/@href').extract()

        if food_baverages_food_links and category == 'food':
            for link in food_baverages_food_links:
                yield Request(normalize(link), self.metapage, meta={'city':city, 'category':category})
            food_baverages_food_load_more = data_get(sel,food_baverages_food_load_more_xpath)
            if food_baverages_food_load_more:
                form_data = {'category':category, 'page':'1'}
                if city:
                    form_data.update({'city':city})
                load_more_link = 'https://in.explara.com/application/experience/load-more-events'
                yield FormRequest(load_more_link, callback=self.listing, method="POST", formdata=form_data, meta={'city':city})

        food_baverages_drink_links = data_list_get(sel,food_baverages_drink_links_xpath) 
        if desc and category == 'drinks':
            food_baverages_drink_links = desc.xpath('//a[@itemprop="url"]/@href').extract()

        if food_baverages_drink_links and category == 'drinks':
            for link in food_baverages_drink_links:
                yield Request(normalize(link), self.metapage, meta={'city':city, 'category':category})
            food_baverages_drink_load_more = data_get(sel,food_baverages_drink_load_more_xpath)
            if food_baverages_drink_load_more:
                form_data = {'category':category, 'page':'1'}
                if city:
                    form_data.update({'city':city})
                load_more_link = 'https://in.explara.com/application/experience/load-more-events'
                yield FormRequest(load_more_link, callback=self.listing, method="POST", formdata=form_data, meta={'city':city})

        interests_links = data_list_get(sel,interests_links_xpath) 
        if desc and category == 'interests':
            interests_links = desc.xpath('//a[@itemprop="url"]/@href').extract()

        if interests_links and category == 'interests':
            for link in interests_links:
                yield Request(normalize(link), self.metapage, meta={'city':city, 'category':category})
            interets_load_more = data_get(sel,interets_load_more_xpath)
            if interets_load_more:
                form_data = {'category':category, 'page':'1'}
                if city:
                    form_data.update({'city':city})
                load_more_link = 'https://in.explara.com/application/experience/load-more-events'
                yield FormRequest(load_more_link, callback=self.listing, method="POST", formdata=form_data, meta={'city':city})


    def metapage(self, response):
        sel = Selector(response)
        event_id = response.url.split('/')[-1]
        city = response.meta['city'].title()
        category = response.meta['category']
        title = normalize(data_get(sel, title_xpath))
        dates = normalize(data_get(sel, dates_xpath))
        timings = normalize(data_get(sel, timings_xpath)).replace(dates,'')
        location = normalize(data_get(sel, location_xpath))
        address = normalize(' '.join(data_list_get(sel, address_xpath)))
        organizer = normalize(data_get(sel, organizer_xpath))
        details = normalize(data_get(sel, details_xpath)).replace(organizer,'')
        webpage = normalize(data_get(sel, webpage_xpath))
        images = normalize('<>'.join(data_list_get(sel, images_xpath))) or normalize(data_get(sel,image_xpath))
        price = normalize(''.join(data_list_get(sel, price_xpath))).replace('onwards','')
        
        if category == 'entertainment':
            query = 'insert into Entertainment(id, name, reference_url, city, location, address, details, organizer, dates, timings, image_urls, price, webpage, created_at, modified_at, last_seen'
            query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now()'
            values = ((event_id), (title), (response.url), (city), (location), (address), (details), (organizer), (dates), (timings), (images), (price), (webpage))
            self.cursor.execute(query,values)

        if category == 'alumni-and-campus':
            query = 'insert into Alumni(id, name, reference_url, city, location, address, details, organizer, dates, timings, image_urls, price, webpage, created_at, modified_at, last_seen'
            query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now()'
            values = ((event_id), (title), (response.url), (city), (location), (address), (details), (organizer), (dates), (timings), (images), (price), (webpage))
            self.cursor.execute(query,values)

        if category == 'adventure-and-outdoor':
            query = 'insert into Adventure(id, name, reference_url, city, location, address, details, organizer, dates, timings, image_urls, price, webpage, created_at, modified_at, last_seen'
            query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now()'
            values = ((event_id), (title), (response.url), (city), (location), (address), (details), (organizer), (dates), (timings), (images), (price), (webpage))
            self.cursor.execute(query,values)

        if category == 'biz-and-tech':
            query = 'insert into BizTech(id, name, reference_url, city, location, address, details, organizer, dates, timings, image_urls, price, webpage, created_at, modified_at, last_seen'
            query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now()'
            values = ((event_id), (title), (response.url), (city), (location), (address), (details), (organizer), (dates), (timings), (images), (price), (webpage))
            self.cursor.execute(query,values)

        if category == 'sports-and-fitness':
            query = 'insert into Sports(id, name, reference_url, city, location, address, details, organizer, dates, timings, image_urls, price, webpage, created_at, modified_at, last_seen'
            query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now()'
            values = ((event_id), (title), (response.url), (city), (location), (address), (details), (organizer), (dates), (timings), (images), (price), (webpage))
            self.cursor.execute(query,values)

        if category == 'food':
            query = 'insert into Food(id, name, reference_url, city, location, address, details, organizer, dates, timings, image_urls, price, webpage, created_at, modified_at, last_seen'
            query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now()'
            values = ((event_id), (title), (response.url), (city), (location), (address), (details), (organizer), (dates), (timings), (images), (price), (webpage))
            self.cursor.execute(query,values)

        if category == 'drinks':
            query = 'insert into Food(id, name, reference_url, city, location, address, details, organizer, dates, timings, image_urls, price, webpage, created_at, modified_at, last_seen'
            query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now()'
            values = ((event_id), (title), (response.url), (city), (location), (address), (details), (organizer), (dates), (timings), (images), (price), (webpage))
            self.cursor.execute(query,values)

        if category == 'interests':
            query = 'insert into Interest(id, name, reference_url, city, location, address, details, organizer, dates, timings, image_urls, price, webpage, created_at, modified_at, last_seen'
            query+=') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on duplicate key update modified_at=now()'
            values = ((event_id), (title), (response.url), (city), (location), (address), (details), (organizer), (dates), (timings), (images), (price), (webpage))
            self.cursor.execute(query,values)
