from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
import MySQLdb
from handle_utils import *
import re
import json

def get_cursor():
    conn = MySQLdb.connect(db = 'ZOLIDAY', host = 'localhost', user = 'root',
    charset ='utf8', use_unicode = True)
    cursor = conn.cursor()
    return conn, cursor

class Zoliday(BaseSpider):
    name = 'zoliday_browse'
    start_urls = ['https://zoliday.com']
    handle_httpstatus_list = [410, 500]
    def __init__(self, *args, **kwargs):
        super(Zoliday, self).__init__(*args, **kwargs)
        self.conn, self.cursor = get_cursor()
            
    def parse(self,response):
        sel = Selector(response)
        #list1 = ['coorg-packages', 'hampi-packages','chikmagalur-packages','ooty-packages','coonoor-packages','kabini-packages','kotagiri-packages','kodaikanal-packages','sakleshpur-packages','yercaud-packages','wayanad-packages','tirupati-packages','goa-packages']
        #list1 = ['luxury-stay','tree-house-stay','lake-side-stay','heritage-stay','wooden-house-stay','riverside-stay','naturistic-stay']
        #list1 = ['hilltop-view-stay','farm-stay','country-house-stay','cottage-stay','spa-retreat','ayurveda-retreat','yoga-retreat']
        list1 = ['detox-retreat']
        for i in list1:
            x = 'https://zoliday.com/activities?cat='+str(i)+'&loc=Across-Coorg&coords=&time=Anytime&sort=Latest&start=0&offset=100&api=1&exclude=&cityid=12&pr=&group=1'

            yield Request(x, callback = self.parse_next) 
    def parse_next(self,response):
        sel = Selector(response)
        print response.url
        linkss = sel.xpath('//div[@class="pull-right"]//button//@href')
        for i in linkss:
           
            #lim = 'https://zoliday.com' + i.extract()
            lim = 'https://zoliday.com/experience/zoliday-trip-with-peacock-residency-in-chikamagalur-15fe2'
            yield Request(lim, callback = self.parse_next1, dont_filter = True)
    def parse_next1(self,response):
        sel = Selector(response)
        ref = response.url
        city = ''.join(sel.xpath('//div[@class="row"]//h1[@class="page-header col-lg-12 itemTitle"]/small/text()').extract()).strip('\n')
        name = ''.join(sel.xpath('//div[@class="row"]//h1[@class="page-header col-lg-12 itemTitle"]/text()').extract()).strip('\n')
        id_ = ''.join(sel.xpath('//form[@id="estimate_form"]/input[@type="hidden"]/@value').extract())
        url = response.url.split('/')[-1]
        print id_
        #x = 'https://zoliday.com/retreat/prices?itemid=83c94197-43bd-494b-9cd1-6250773fe6d5&urltext=zoliday-trip-to-serene-blossom-stay-in-chikmagalur-83c94&destination=chikmagalur&auto=1'
        x = 'https://zoliday.com/retreat/prices?itemid='+str(id_)+'&urltext='+str(url)+'&destination=bangalore&auto=1'
        cookies = {
                'cur': '2|1:0|10:1503989917|3:cur|144:eyJjb252ZXJzaW9uIjogMS4wLCAic3ltYm9sIjogIiYjODM3NzsiLCAidGF4IjogMS4wLCAiY291bnRyeV9jb2RlIjogIklOIiwgImlkIjogMSwgImN1cnJlbmN5X2NvZGUiOiAiSU5SIn0=|27d39012f569e0923826417d4c773332e1d5299f7987ec5b40e5ca5adbc6a47c',
                'pnext': '2|1:0|10:1504176640|5:pnext|56:L2dyb3VwLUNvb3JnL3lvZ2EtcmV0cmVhdC9Bbnl0aW1lLUxhdGVzdA==|326a627966e76c3aae297b85187cc5ed2f0890957867be14c57f24afcc284a63',
                'cityid': '2|1:0|10:1504178650|6:cityid|4:MTI=|a9eab805f9507f50c5719771516ecc2355790c1f1f6c265fe974e55de29e8d0c',
                'city': '2|1:0|10:1504178650|4:city|8:Q29vcmc=|08521988a2097842f227c196ea4d75dfb5c7e682d4a76b5820555f6040bee60b',
                '_ga': 'GA1.2.995541325.1503725070',
                '_gid': 'GA1.2.83443143.1503981321',
                'dinner_included': '1',
                'nights': '',
                'adults': '1',
                'airport_drop_off': '0',
                'p_scity': 'Bangalore',
                'airport_pick_up': '0',
                'jdate': '01-09-2017',
                'children': '0',
                'phone': '8977992727',
                'kms': '750',
                'transport1': 'pickupdrop',
                'destination': 'chikmagalur',
                'indestinationcab': 'Dzire-Etios-AC',
                'cab1': 'Dzire-Etios-AC',
                'email': 'anupriya18513@gmail.com',
                'jdate2': '02-09-2017',
                'indestinationDays': '3',
                'ref': '2|1:0|10:1504178876|3:ref|4:bmE=|01e8af938469dad8579ce152c7d31fd7db307a90ec03a009578857bc30db0a5d',
        }
        """cookies = {
            'cur': '2|1:0|10:1503989917|3:cur|144:eyJjb252ZXJzaW9uIjogMS4wLCAic3ltYm9sIjogIiYjODM3NzsiLCAidGF4IjogMS4wLCAiY291bnRyeV9jb2RlIjogIklOIiwgImlkIjogMSwgImN1cnJlbmN5X2NvZGUiOiAiSU5SIn0=|27d39012f569e0923826417d4c773332e1d5299f7987ec5b40e5ca5adbc6a47c',
            'dinner_included': '0',
            'nights': '',
            'adults': '1',
            'airport_drop_off': '0',
            'p_scity': 'Bangalore',
            'airport_pick_up': '0',
            'jdate': '01-09-2017',
            'children': '0',
            'phone': '89779927272',
            'transport1': 'pickupdrop',
            'destination': 'bangalore',
            'indestinationcab': 'Dzire-Etios-AC',
            'cab1': 'Indica-AC',
            'email': 'anupriya18513@gmail.com',
            'jdate2': '02-09-2017',
            'indestinationDays': '1',
            'cityid': '2|1:0|10:1504096700|6:cityid|4:MTI=|4a623a84ca334479982f3f64f1ebb54da5956b0890853a860f312c670d240098',
            'city': '2|1:0|10:1504096700|4:city|8:Q29vcmc=|f6c83b5e707322e52ffc9b934859460edd99ce5800e62546cd307e7e610c3336',
            'pnext': '2|1:0|10:1504096699|5:pnext|64:L2dyb3VwLUNvb3JnL2NoaWttYWdhbHVyLXBhY2thZ2VzL0FueXRpbWUtTGF0ZXN0|18eb5034f16486e49aebce59193b5235d7d17bacc021ae946d5f03b7d08b0e6f',
            '_ga': 'GA1.2.995541325.1503725070',
            '_gid': 'GA1.2.83443143.1503981321',
            'kms': '750',
            'ref': '2|1:0|10:1504096813|3:ref|4:bmE=|38e1250afaaa3643a5cbc5489e3e30f0234df1c057211b923a7231534075aac1',
        }"""
        yield Request(x, callback = self.parse_next2, cookies = cookies, meta = {'city':city, 'name':name, 'id_': id_, 'ref':ref})           
        
    def parse_next2(self,response):
        city = response.meta['city']
        name = response.meta['name']
        activity_id = response.meta['id_']
        reference_url = response.meta['ref']
        #import pdb;pdb.set_trace()
        print response.url
        print reference_url
        sk = reference_url
        data = json.loads(response.body)
        end_data = data['jdateEndDetails']
        start_date = data['jdateDetails']
        travelerDetails = data['travelerDetails']
        dd = data['data']['packages']
        for d in dd:
            type1 = d['type']
            actual_price = d['total_formatted']
            price = d['price']
            description = d['description']
            no_of_rooms = d['stay_comment']
            discount = 'bhanu'
            query = 'insert into Things_To_Do(sk, travel_code,name,city,package_name,price ,offer,discount,package_description,reference_url,created_at ,modified_at,last_seen' 
            query += ') values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),now())on duplicate key update modified_at = now()'
            values = (sk, activity_id, name,city,type1,actual_price,price,discount,description,reference_url)
            self.cursor.execute(query, values)
