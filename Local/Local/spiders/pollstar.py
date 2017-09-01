import json
import MySQLdb
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.http import Request, FormRequest 
from handle_utils import *
import md5
import re
import datetime

class PollstarBrowse(BaseSpider):
    name = 'pollstarnew_browse'
    start_urls  = ['https://www.pollstar.com/concert-pulse']
    handle_httpstatus_list = [403, 404]

    def __init__(self, *args, **kwargs):
        super(PollstarBrowse, self).__init__(*args, **kwargs)
        self.pattern1 = re.compile('ddDates = (\[.*\])')
        self.pattern2 = re.compile('value:(.*)')
        self.pattern3 = re.compile('\((.*)\)')
        
    def parse(self,response):
        sel  = Selector(response)
        import pdb;pdb.set_trace()
        login_url = 'https://www.pollstar.com/login?returnUrl=%2F'
        headers = {
			'accept-encoding': 'gzip, deflate, br',
			'accept-language': 'en-US,en;q=0.8,fil;q=0.6',
			'upgrade-insecure-requests': '1',
			'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
			'content-type': 'application/x-www-form-urlencoded',
			'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
			'cache-control': 'max-age=0',
			'authority': 'www.pollstar.com',
			'referer': 'https://www.pollstar.com/login?returnUrl=%2Flogin%3FreturnUrl%3D%252F'
			}
        form_data = {'Email':'rosymaria.ramirez@tivo.com',
                    'Password':'Musicgroup18'}
        handle_httpstatus_list = [404, 403]
        yield FormRequest(login_url, self.login_parse, method='POST', formdata=form_data)
    
    def login_parse(self, response):
        import pdb;pdb.set_trace()
        sel = Selector(response)
        yield Request('https://www.pollstar.com/concert-pulse', self.meta_link)
    
    def meta_link(self, response):
        sel = Selector(response)
        if 'concert' in response.url:
            import pdb;pdb.set_trace()
            dates_data = data_get(sel, '//script[@type="text/javascript"][contains(text(), "value")]/text()')
            data = self.pattern1.findall(dates_data.replace('\n' , '').replace('\t', '').replace('\r', ''))
            data = ''.join(data).split('},')
            for v_date in data:
                ddate = ''.join(self.pattern2.findall(v_date)).replace("'", '').strip()
                if ddate:
                    link = "https://www.pollstar.com/concertpulsejson/?pageIndex=0&pageSize=100&concertPulseDateTime=%s"%ddate
                    date_info = datetime.datetime.strptime(ddate, '%m/%d/%Y').strftime('%Y-%m-%d')
                    yield Request(link, self.parse_next1, meta={'ddate':date_info, 'ref_url':response.url})

    def parse_next1(self,response):
	    sel = Selector(response)
	    import pdb;pdb.set_trace()       

