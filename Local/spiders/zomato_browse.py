from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
import scrapy 
import re
import MySQLdb

def get_cursor():
    conn = MySQLdb.connect(db = 'ZOMATO', host = 'localhost', user = 'root',
    charset ='utf8', use_unicode = True)
    cursor = conn.cursor()
    return conn, cursor

class Zomato(scrapy.Spider):
    name = 'zomato_browse'
    start_urls = []
    def __init__(self, *args, **kwargs):
        super(Zomato, self).__init__(*args, **kwargs)
        self.conn, self.cursor = get_cursor()
      
    list1 = ['top-restaurants','best-new-restaurants','function-venues','arabian-nights','vegetarian-restaurants','great-breakfast','romantic-restaurants','best-buffet','biryani','bengali-sweets','themed-restaurants','dhabas','hidden-restaurants','pizza-restaurants','south-indian-restaurants','street-food','dessert-places','best-beer-bars','outdoor-dining','fine-dining-restaurants','night-clubs','delivery-only-restaurants','late-night-restaurants','best-thali','bengali-cuisine','legendary-places','student-restaurants','great-chinese-restaurants','hilsa']
    city = ['kolkata','pune','ncr','kochi','goa','guwahati','mumbai','ahmedabad','bangalore','udaipur','jaipur','chandigarh','dehradun','agra','chennai','hyderabad']
    for k in city:
        for j in list1:
            url = 'https://www.zomato.com/'+k+'/%s'%j
            start_urls.append(url)
    def parse(self, response):
        sel = Selector(response)
        y  =re.compile(r'com/(\D+)/')
        x = response.url
        city = ''.join(y.findall(x))
        category = response.url.split('/')[-1]
        linkss = sel.xpath('//div[@data-entity-type="restaurant"]/a[@data-link-type="restaurant"]/@href').extract()
        for url in linkss:
            yield Request(url, self.parse_next, dont_filter = True,meta = {'category':category,'city':city})
    def parse_next(self, response):
        sel = Selector(response)
        reference_url = response.url
        title = ''.join(sel.xpath('//h1[@class="res-name left mb0"]//text()[1]').extract()).strip()
        sk = title
        restaraunt_type =''.join(sel.xpath('//span[@class="res-info-estabs grey-text fontsize3"]//text()').extract()).strip().encode('utf-8')
        contact_number = ''.join(sel.xpath('//span[@class="fontsize2 bold zgreen"]//text()').extract()).strip(' ').strip().encode('utf-8')
        cost = ''.join(sel.xpath('//div[contains(text(), "%s")]/following-sibling::text()'%u'Average').extract()).encode('utf-8')
        if cost != '':
            price = cost
        else:
            price = ''
        open_hr =  ''.join(sel.xpath('//div[@class="medium"]//text()').extract()).strip().encode('utf-8')
        open_hrs = str(open_hr)
        votes = ''.join(sel.xpath('//span[@itemprop="ratingCount"]//text()').extract()).strip()
        rating = ''.join(sel.xpath('//div[@class="res-rating pos-relative clearfix mb5"]//text()').extract()).strip().replace('/5','')
        if  'NEW' in rating:
            ratings = ''
        else:
            ratings = rating
        address = ''.join(sel.xpath('//div[@class="borderless res-main-address"]//text()').extract()).strip().encode('utf-8')
        highlights = ''.join(sel.xpath('//div[@class="res-info-feature-text"]//text()[1]').extract())
        cusiness= ''.join(sel.xpath('//div[@class="res-info-cuisines clearfix"]//text()').extract())
        longitude = ''.join(sel.xpath('//meta[@property="place:location:longitude"]/@content').extract())
        latitude = ''.join(sel.xpath('//meta[@property="place:location:latitude"]/@content').extract())
        discount_date = ''.join(sel.xpath('//div[@class="clearfix res-promo-dates"]//text()').extract()).encode('utf-8').strip()
        category = response.meta['category']
        city = response.meta['city']
        discount_text = ''.join(sel.xpath('//div[@class="res-promo-text"]//text()').extract()).encode('utf-8').strip()
        review = sel.xpath('//div[@id="selectors"]//span//text()').extract()
        if review:
            reviews_ = review[1]
            review_ = ''.join(reviews_)
            if 'Date' in review_:
                reviews = ''
            else:
                reviews = review_
            query = 'insert into Restaraunt(sk,title,city,cusiness,restaraunt_type,contact_number,\
            ratings,reviews,votes,latitude,longitude,discount_date,discount_text,address,opening_hours,highlights,\
            category,price,reference_url,created_at,modified_at,last_seen'
            query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now()) on\
            duplicate key update modified_at = now()'
            values = ((sk),(title),(city),(cusiness),(restaraunt_type),(contact_number),(ratings),\
            (reviews),(votes),(str(latitude)),(str(longitude)),(discount_date),(discount_text),(address),\
            (str(open_hrs)),(highlights),(category),(price),(reference_url))
            self.cursor.execute(query, values)
