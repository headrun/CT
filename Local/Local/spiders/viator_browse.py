from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest
import MySQLdb
import re
from handle_utils import *
from viator_xpath import *

def get_cursor():
    conn = MySQLdb.connect(db = 'VIATOR', host = 'localhost', user = 'root',
    charset ='utf8', use_unicode = True)
    cursor = conn.cursor()
    return conn, cursor

class Viator(BaseSpider):
    name = 'viator_browse'
    start_urls = ['https://www.viator.com/Chennai/d4624-ttd']
    def __init__(self, *args, **kwargs):
        super(Viator, self).__init__(*args, **kwargs)
        self.conn, self.cursor = get_cursor()

    def parse(self, response):
        sel = Selector(response)
        list1 = ['Bangalore/d5310-ttd','Hyderabad/d22442-ttd','Chennai/d4624-ttd','New-Delhi/d804-ttd','Mumbai/d953-ttd','Pune/d26473-ttd','Kolkata/d4924-ttd','Mysore/d25746-ttd','Agra/d4547-ttd','Jaipur/d4627-ttd','Goa/d4594-ttd','Ahmedabad/d24558-ttd','Kochi/d952-ttd','Trivandrum/d4629-ttd','Munnar/d25293-ttd','Pondicherry/d22690-ttd','Jodhpur/d22142-ttd','Udaipur/d5106-ttd','Guwahati/d24307-ttd','Darjeeling/d22035-ttd','Rishikesh/d22733-ttd','Haridwar/d22303-ttd','Shimla/d25944-ttd','Dharmasala/d25979-ttd','Jaisalmer/d24761-ttd','Srinagar/d23017-ttd']
        for m in list1:
            if 'http' not in list1:
                linkss = 'https://www.viator.com/' + m
                yield Request(linkss, callback = self.parse1)
    def parse1(self, response):
        sel = Selector(response)
        listing = sel.xpath(listing_b)
        if listing != []:
            for i in listing:
                listing_ = i.extract()
                if 'http' not in listing_:
                    link = 'https://www.viator.com' +listing_
                    yield Request(link, callback = self.details)
        else:
            listing3 = sel.xpath(listing3_b)
            for i in listing3:
                listing_ = i.extract()
                if 'http' not in listing_:
                    link = 'https://www.viator.com' +listing_
                    yield Request(link, callback = self.details_next)

    def details(self, response):
        sel = Selector(response)
        next_ = sel.xpath(next_b).extract()
        for j in next_:
            next_link = 'https://www.viator.com' + j   
            yield Request(next_link, callback = self.details_next)

    def details_next(self, response):
        sel = Selector(response)
        highlights = ', '.join(sel.xpath(highlights_b).extract())
        expect = ','.join(sel.xpath(expect_b).extract())
        description1 = ''.join(sel.xpath(description1_b).extract()) or \
                      ''.join(sel.xpath(description2_b).extract())
        expext_image = ''.join(sel.xpath(except_imageb).extract())
        links = sel.xpath(links_b)
        for k in links:
            i = k.extract()
            next1 = 'https://www.viator.com' + i
            if next1:
                yield Request(next1, callback = self.details_next1, meta={'description': description1,'expect': expect, 'highlights':highlights,'expect_image' : expext_image},dont_filter=True)

    def details_next1(self, response):
        sel = Selector(response)
        description = response.meta['description']
        expectations = response.meta['expect']
        highlights =  response.meta['highlights']
        expect_image = response.meta['expect_image']
        category = ''.join(sel.xpath(category_b).extract()[-1])
        name = ''.join(sel.xpath(name_b).extract())
        duration = ''.join(sel.xpath(duration_b).extract()).strip()
        location = ''.join(sel.xpath(location_b).extract()).strip()
        tour_code = ''.join(sel.xpath(tour_codeb).extract()).strip()
        no_of_reviews = ''.join(sel.xpath(no_of_reviewsb).extract())
        if no_of_reviews != '':
            no_of_reviews = no_of_reviews
        else:
            no_of_reviews = 0
        no_of_ratings = ''.join(sel.xpath(no_of_ratingsb).extract()).strip()
        y = re.compile(r'\d+')
        no_of_ratings = ''.join(y.findall(no_of_ratings))
        if no_of_ratings != '':
            no_of_ratings = no_of_ratings
        else:
            no_of_ratings = '0'
        image_url = ''.join(sel.xpath(image_urlb).extract())
        inclusions = ','.join(sel.xpath(inclusionsb).extract())
        exclusions = ','.join(sel.xpath(exclusionsb).extract())
        additional_info = ','.join(sel.xpath(additional_infob).extract())
        voucher_info = ','.join(sel.xpath(voucher_infob).extract())
        local_operatorinfo = ''.join(sel.xpath(local_operator_infob).extract())
        cancellation_policy = ''.join(sel.xpath(cancellation_policyb).extract())
        departure_time = ' '.join(sel.xpath(departure_timeb).extract())
        return_details = ' '.join(sel.xpath(return_detailsb).extract())
        departure_point = ' '.join(sel.xpath(departure_pointb).extract())
        reference_url = response.url
        cit = re.compile(r'/tours/(\D+)/')
        city = ''.join(cit.findall(reference_url))
        if '/' in city:
            city = city.split('/')[0]
        else:
            city = city
        sk = response.url
        nodes = sel.xpath(nodes_b)
        if nodes != []:
            for i in nodes:
                about_travel = ''.join(i.xpath(about_travelb).extract())
                travel_code = ''.join(i.xpath(travel_code_b).extract())
                travel_description = ''.join(i.xpath(travel_descriptionb).extract())
                price = ''.join(i.xpath(price_b).extract())
                query = 'insert into Things_To_Do(sk,tour_code,travel_code,name,image_url,description, no_of_ratings,expectations,no_of_reviews,city,location,duration,highlights,departure_time,category,departure_point,price,about_travel,travel_description,return_details,cancellation_policy,inclusions,exclusions,additional_info,local_operatorinfo,voucher_info,reference_url,created_at,modified_at,last_seen'
                query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now())on duplicate key update modified_at = now()'
                values = (sk,(tour_code),(travel_code),normalize(name),(image_url),normalize(description),int(no_of_ratings),normalize(expectations), int(no_of_reviews),normalize(city),(location),duration,normalize(highlights),normalize(departure_time),category,normalize(departure_point),normalize(price),normalize(about_travel), normalize(travel_description),normalize(return_details),normalize(cancellation_policy),normalize(inclusions),normalize(exclusions),normalize(additional_info),normalize(local_operatorinfo),normalize(voucher_info),normalize(reference_url))
                self.cursor.execute(query, values)
        else:
            travel_code = ''
            travel_description = ''
            about_travel = ''
            price = ''.join(sel.xpath(price_bb).extract())
            query = 'insert into Things_To_Do(sk,tour_code,travel_code,name,image_url,description, no_of_ratings,expectations,no_of_reviews,city,location,duration,highlights,departure_time,category,departure_point,price,about_travel,travel_description,return_details,cancellation_policy,inclusions,exclusions,additional_info,local_operatorinfo,voucher_info,reference_url,created_at,modified_at,last_seen'
            query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now())on duplicate key update modified_at = now()'
            values = (sk,(tour_code),(travel_code),normalize(name),(image_url),normalize(description),int(no_of_ratings),normalize(expectations), int(no_of_reviews),normalize(city),(location),duration,normalize(highlights),normalize(departure_time),category,normalize(departure_point),normalize(price),normalize(about_travel), normalize(travel_description),normalize(return_details),normalize(cancellation_policy),normalize(inclusions),normalize(exclusions),normalize(additional_info),normalize(local_operatorinfo),normalize(voucher_info),normalize(reference_url))
            self.cursor.execute(query, values)

