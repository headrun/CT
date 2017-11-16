import os
import re
import json
import md5
import MySQLdb
import hashlib
import datetime
import logging
from utils import *
from scrapy import log
from scrapy import signals
from ast import literal_eval
from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher
from scrapy_splash import SplashRequest
from utils import *
import sys
reload(sys)
sys.setdefaultencoding('utf-8')  

class ArabicBrowse(Spider):
    name = "arabic_browse"
    start_urls = ["https://sa.wego.com/"]

    def __init__(self, *args, **kwargs):
        super(ArabicBrowse, self).__init__(*args, **kwargs)
	self.fin_lst = []
	dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
	open('arabic_names.json', 'w+').write('%s'%json.dumps(self.fin_lst, ensure_ascii=False, encoding="utf-8"))

    def parse(self, response):
        sel = Selector(response)
	codes = ['RUH','JED','DMM','HBE','ELQ','YNB','AHB','IST','CAI','BAH','MED','HOF','SZB','SAW','HYD','TIF','GIZ','ATZ','COK','DEL','TZX','MAA','DXB','HAS','BOM','KRT','KUL','KTM','CCJ','TUU','CGK','DMK','HMB','SHJ','LGK','TRV','URY','SSH','SHW','MNL','AJF','RUJ','BLR','KHI','BEY','CDG','KWI','ABT','VIE','IXE','MUC','PEN','ISB','SXR','AYT','AQI','LHE','ATH','HKT','BHH','MAD','MRS','JHB','HRG','MCO','CMN','GYD','BUS','PDX','JFK','TBS','LIS','BCN','AMM','KBP','EJH','BRU','GOI','MCT','CMB','LYS','FCO','LHR','DWD','DWC','IXM','IAH','RAE','LGA','LKO','MIA','AMD','IBZ','ORY','SLL','PEW','CCU','TRZ','AGP','SUB','DLM','MSQ','MAN','MXP','PAT','VGA','BKK','NAP','KBV','DME','JTR','ADB','GVA','MUX','LGW','CEB','LIN','SKT','HGH','CZL','DMS','DOH','YOW','DPS','SXF','IXJ','DTW','BGW','NRT','DFW','PNS','DAC','VTZ','LYP','JNB','LAX','OSL','YYZ','ZRH','EWR','PRG','ESB','MLE','HAN','NCE','ZAM','RAH','TAC','RBA','FRA','MHD','UDR','DUS','SMF','TOL','HKG','NLA','JMK','CNX','KBR','AMS','KHV','ATL','CAN','CPH','ICN','CRK','AUH','MEL','TUI','VCE','VNS','ARN','GMP','ORD','IAS','NAG','BJV','TUN','KCH','BBI','BGY','YEG','SYX','PZU','YUL','LAS','ILO','RJA','SFO','YYC','CPT','DKR','BOS','KIX','JAI','HGA','MLA','MLX','SGN']
	url = 'https://srv.wego.com/places/search?language=ar&domain=sa.wego.com&site_code=SA&locales[]=ar&locales[]=en&query=%s&min_airports=1'
	for i in codes:
	    yield Request(url%i, callback=self.parse_next, meta={'airport_code':i})

    def parse_next(self, response):
	sel = Selector(response)
	air_code = response.meta['airport_code']
	body = json.loads(response.body)
	eng_names_lst, arabic_names_lst, keyword = [], [], []
	fin_dict, code_lst = {}, []
	citypermalink_eng = []
	cityname_ar = []
	for idx, dic in enumerate(body):
	    #city_dict, air_dict = {}, {}
	    airportpermalink = dic.get('airportPermalink', '').replace('-', ' ').title()
	    airportname = dic.get('airportName', '')
	    citypermalink = dic.get('cityPermalink', '').replace('-', ' ').title()
	    cityname = dic.get('cityName', '')
	    #countryname = dic.get('countryName', '')
	    #countrypermalink = dic.get('countryPermalink', '').replace('-', ' ').title()
	    code = dic.get('code', '')
	    if airportpermalink:
		if air_code == code:
		    eng_names_lst.append(normalize(citypermalink))
		    eng_names_lst.append(normalize(airportpermalink))
		    arabic_names_lst.append(normalize(cityname))
		    arabic_names_lst.append(normalize(airportname))
		    code_lst.append(air_code)
	    elif air_code == code:
		    eng_names_lst.append(normalize(citypermalink))
                    arabic_names_lst.append(normalize(cityname))
                    code_lst.append(air_code)
	code_lst = set(code_lst)
	key_list = []; ori_lst = []
	for i in arabic_names_lst:
	    #if u'\u0627\u0644' in i:
	    #	import pdb;pdb.set_trace()
	    if u'\u0643\u0648\u0627\u0644\u0627\u0644\u0645\u0628\u0648\u0631' in i: import pdb;pdb.set_trace()
	    i = i.replace(u'\u0645\u0637\u0627\u0631', '').\
                        replace(u'\u0627\u0644\u062f\u0648\u0644\u064a', '').strip()
	    print 'check'
	    i_lst = i.split(' ')
	    for k in i_lst:
		key_list.append(k.strip())
		k = k.lstrip(u'\u0627\u0644').strip()
		if u'\u0622\u0644' in k:
		    k = k.lstrip(u'\u0622\u0644').strip()	
		key_list.append(k)
	key_list = list(set(key_list))
	
	for i in eng_names_lst:
	    i = i.replace('International', '').replace('Airport', '').replace('The', '')
	    lst = i.split(' ')
	    key_list.extend(lst)
	key_list.append('<>'.join(code_lst))
	key_list = [x for x in key_list if x.strip()]
	if '<>'.join(code_lst):
	    fin_dict.update({'arabic':list(set(arabic_names_lst)), 'english':list(set(eng_names_lst)), 'code':'<>'.join(code_lst), 'keywords':list(set(key_list))})
	    self.fin_lst.append(fin_dict)
