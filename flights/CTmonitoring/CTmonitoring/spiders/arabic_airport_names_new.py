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
    name = "arabicnew_browse"
    start_urls = ["https://www.tajawal.com/"]

    def __init__(self, *args, **kwargs):
        super(ArabicBrowse, self).__init__(*args, **kwargs)
	self.fin_lst = []
	dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
	open('arabic_names.json', 'w+').write('%s'%json.dumps(self.fin_lst, ensure_ascii=False, encoding="utf-8"))

    def parse(self, response):
        sel = Selector(response)
	#codes = ['RUH','JED','DMM','HBE','ELQ','YNB','AHB','IST','CAI','BAH','MED','HOF','SZB','SAW','HYD','TIF','GIZ','ATZ','COK','DEL','TZX','MAA','DXB','HAS','BOM','KRT','KUL','KTM','CCJ','TUU','CGK','DMK','HMB','SHJ','LGK','TRV','URY','SSH','SHW','MNL','AJF','RUJ','BLR','KHI','BEY','CDG','KWI','ABT','VIE','IXE','MUC','PEN','ISB','SXR','AYT','AQI','LHE','ATH','HKT','BHH','MAD','MRS','JHB','HRG','MCO','CMN','GYD','BUS','PDX','JFK','TBS','LIS','BCN','AMM','KBP','EJH','BRU','GOI','MCT','CMB','LYS','FCO','LHR','DWD','DWC','IXM','IAH','RAE','LGA','LKO','MIA','AMD','IBZ','ORY','SLL','PEW','CCU','TRZ','AGP','SUB','DLM','MSQ','MAN','MXP','PAT','VGA','BKK','NAP','KBV','DME','JTR','ADB','GVA','MUX','LGW','CEB','LIN','SKT','HGH','CZL','DMS','DOH','YOW','DPS','SXF','IXJ','DTW','BGW','NRT','DFW','PNS','DAC','VTZ','LYP','JNB','LAX','OSL','YYZ','ZRH','EWR','PRG','ESB','MLE','HAN','NCE','ZAM','RAH','TAC','RBA','FRA','MHD','UDR','DUS','SMF','TOL','HKG','NLA','JMK','CNX','KBR','AMS','KHV','ATL','CAN','CPH','ICN','CRK','AUH','MEL','TUI','VCE','VNS','ARN','GMP','ORD','IAS','NAG','BJV','TUN','KCH','BBI','BGY','YEG','SYX','PZU','YUL','LAS','ILO','RJA','SFO','YYC','CPT','DKR','BOS','KIX','JAI','HGA','MLA','MLX','SGN']
	#codes = ['RJA', 'NLA','TOL','RBA','RAH','ZAM','ATZ']
	#codes = ['HKT']
	codes = ['MED','ADD','CGP','BSR','AAN','ALG','ATQ','ACC','IAD','IKA','KHS','DAR','DVO','DMS','DUB','BHX','BNE','RAH','BWI','EBB','ASM','DQM','BUD','AKL','HTY','CGY','BEG','KBL','CGO','CBO','ABZ','PEK','PAT','DEN','BOG','BCD','DLA','AGA','ADA','ABJ','LOS','DUR','ASW','GES','ALA','BLQ','NBO','BDQ','EBL','EDI','GLA','CTU','HAM','SIN','ZYL','NJF','WAE','SJJ','XNB','PVG','SYD','TXL','LXR','OTP','SEZ','WAW','SEA','LCA','ZNZ','USM','RYK','ZAG','PNQ','TUK','EVN','ZVJ','RBA','YVR','NCL','MBA','MRU','ZAM','RAK','TAS','SVO','HAN','PER','HND','IXB','SYZ','TPE','MSP','GRU','SAN','RGN','NKC','PHL','TSE','CJB','IXC','IDR','RKT','BHO','IXR','DED','GAU','RPR','JDH','HRE','RUJ','LED','TIR','VKO','STN','IXU','RAJ','AER','STV','GOT','SOF','IXZ','MPH','IXL','JLR','DHM','GAY','TAC','IXS','LCY','HEL','IEV','BHJ','ECN','IMF','GOP','LGP','KEF','SLV','TFS','SZZ','PAG','YSJ','TOS','MDW','UTP','SWA','GAN','IKT','CYZ','VOZ','BRQ','YKS','YXU','USU','EDL','YKA','MGA','ALF','BHK','COU','MBT','PDL','UME','YQB','ONT','MYR','YQG','SDU','HDS','SCW','DIU','MFE','RZE','STS','MBS','SJW','NDC','CWA','JMU','THR','OAK','KHN','SSA','GRB','PBI','BOJ','USH','OSR','MMK','IFO','MBJ','SLZ','NTY','SEN','YXX','TIM','BLJ','CEI','RCB','JSA','FKB','LYI','KUN','UTH','VLI','CDP','ACE','PMR','BKS','NAT','KWL','UUS','TEZ','KRN','TRF','VDA','MDL','MMX','TXN','GEO','MGF','WEF','SNW','MLI','MZR','PNY','PTG','KAD','SHL','RTW','UVF','SZK','EIN','MSN','GOJ','JOI','GWL','PNI','SAP','MAF','AGU','IGR','KEJ','TIJ','ZSE','TLM','MGM','SJZ','ERC','TET','LKN','NOZ','TGR','MLG','NQY','BKB','PLQ','SPN','GIB','YTZ','DSA','MUB','AGR','ARK','TYN','BOO','RDM','ITM','GOM','YCD','NAV','LUH','VFA','TLH','CPR','LPQ','YTS','HTA','VAS','MYQ','MAO','AVV','TBU','FTE','SOU','KVA','MSU','DTM','STW','YQM','LPL','DLI','BAX','BJX','KTT','SDK','SXB','TOF','EQS','HDY',]
	#codes = ['STW', 'FTE', 'AVV', 'HTA', 'GOM', 'TGR']
	#codes = ['HTY', 'EBL', 'IXS', 'CYZ',  'ONT', 'NDC', 'IFO', 'SLZ', 'TEZ', 'SNW', 'MZR', 'PNY', 'SHL', 'UVF','ZSE', 'MGM', 'ERC', 'TET','NOZ', 'TGR', 'HTA', 'AVV', 'FTE']
	#codes = ['RPR', 'SZZ', 'STS', 'SSA', 'LYI', 'VLI', 'RTW', 'GOJ', 'SAP', 'LKN']
	#codes = ['YXU', 'PDL', 'YCD']
	#codes = ['NJF', 'YKS', 'MBT', 'GOM',]
	url = 'https://www.tajawal.com/api/air/airport/search?query=%s'
	for i in codes:
	    yield Request(url%i, callback=self.parse_next, meta={'airport_code':i})
	#yield Request(url, callback=self.parse_next, meta={'airport_code':'DEL'})

    def parse_next(self, response):
	sel = Selector(response)
	air_code = response.meta['airport_code']
	body = json.loads(response.body)
	eng_names_lst, arabic_names_lst, keyword = [], [], []
	fin_dict, code_lst = {}, []
	citypermalink_eng = []
	cityname_ar = []
	key_lst = []
	temp=False
	for idx, dic in enumerate(body):
	    #city_dict, air_dict = {}, {}
	    site_code = dic.get('iata', '')
	    if site_code != air_code:
		#print air_code
		continue
	    en_air_name = dic.get('name', '')
	    if not 'Airport' in en_air_name:
		#print "No airport ", air_code
		continue
	    key_lst = []
	    main_city_code = dic.get('main_city_code', '')
	    state_name = dic.get('main_city_name', '')
	    state_name_len = len(state_name.split(' '))
	    strring = dic.get('search_string', '')
	    country_code = dic.get('country_code', '')
	    cr_country = strring.split(air_code)[-1]
	    if not main_city_code: main_city_code = air_code
	    try:
	        ar_st = re.search('.*%s (.*) %s'%(main_city_code, air_code), strring).group()
	        arbic_name = re.findall('.*%s (.*) %s$'%(main_city_code, air_code),ar_st)[0]
		if state_name_len == 1:
	            city, arbic_name_c = re.findall('.* (.*) %s (.*) %s$'%(main_city_code, air_code),ar_st)[0]
		elif state_name_len == 2:
		    city, arbic_name_c = re.findall('.* (.* .*) %s (.*) %s$'%(main_city_code, air_code),ar_st)[0]
		elif state_name_len == 3:
		    city, arbic_name_c = re.findall('.* (.* .* .*) %s (.*) %s$'%(main_city_code, air_code),ar_st)[0]
		elif state_name_len == 4:
		    city, arbic_name_c = re.findall('.* (.* .* .* .*) %s (.*) %s$'%(main_city_code, air_code),ar_st)[0]
		elif state_name_len == 5:
		    city, arbic_name_c = re.findall('.* (.* .* .* .* .*) %s (.*) %s$'%(main_city_code, air_code),ar_st)[0]
	    except: import pdb;pdb.set_trace()
	    city_empty_codes = ['HTY', 'EBL', 'IXS', 'CYZ',  'ONT', 'NDC', 'IFO', 'SLZ', 'TEZ', 'SNW', 'MZR', 'PNY', 'SHL', 'UVF','ZSE', 'MGM', 'ERC', 'TET','NOZ', 'TGR', 'HTA', 'AVV', 'FTE']
	    if air_code in city_empty_codes:
		city = ''
	    empty_arabic_name = ['RPR', 'SZZ', 'STS', 'SSA', 'LYI', 'VLI', 'RTW', 'GOJ', 'SAP', 'LKN']
	    if air_code in empty_arabic_name:
		arbic_name = ''
	    city_and_name = ['VDA', 'EBB']
	    if air_code in city_and_name:
		city, arbic_name = ['']*2
    	    clean_city_list = ['AAN', 'STW', 'DAR', 'STW', 'PNI', 'BLJ', 'WAE', 'NJF', 'GOM', 'MBT', 'YKS',]
	    clean_text_lst = ["Arab Emirates", "Stavropol", "Tanzania", "Micronesia", "Batna", "Arabia", "Airport", "Goma", "Masbate", "Yakutsk", "Emirates"]
	    for i in clean_text_lst:
		city = city.replace(i, '').strip()
	    clean_name_code = ['GOM', 'MBT', 'YKS']
	    clean_name_lst = ["Yakutsk Airport", "Masbate Airport", "Goma Airport"]
	    for i in clean_name_lst:
		arbic_name = arbic_name.replace(i, '').strip()
	    if site_code == 'NJF': arbic_name = arbic_name.replace('Iraq Al-Najaf', '')
	    if site_code == 'EBL': arbic_name = arbic_name.replace('Iraq', '').strip()
	    if site_code == 'HTY': arbic_name = arbic_name.replace('Turkey', '').strip()
	    if site_code == 'PDL': city = city.replace('Portugal', '').strip()
	    if site_code == 'PDX' or site_code == 'TOL':
		city, tem, arbic_name_c = re.findall('.* (.*) (.*) %s (.*) %s$'%(main_city_code, air_code),ar_st)[0] 
	    if site_code == 'ATZ' or site_code == 'HKT':
		city, arbic_name_c = re.findall('.* (.*)  %s (.*) %s$'%(main_city_code, air_code),ar_st)[0]
	    if site_code == 'HMB' or site_code == 'RJA':
		city = ''
		arbic_name= arbic_name.replace('Egypt', '').strip()
	    print city, '*******', site_code, '*****', arbic_name
	    #arbic_name = arbic_name.lstrip(city).strip()
	    #arbic_name = '%s - %s, %s'%(arbic_name, cr_country.strip(), city.strip())
	    if 'Rajahmundry' in arbic_name: arbic_name = arbic_name.replace('Rajahmundry', '').strip().strip(',')
	    if 'India' in arbic_name: arbic_name = arbic_name.replace('India', '').strip().strip(',')
	    if 'Calgary International Airport' in arbic_name: arbic_name = arbic_name.replace('Calgary International Airport', '').strip().strip(',')
	    arbic_name = arbic_name.replace('Pearson International Airport', '').\
			replace('Suvarnabhumi Airport', '').replace('Salalah International Airport', '').strip()
	    
	    if 'India' in arbic_name or 'OH' in arbic_name: import pdb;pdb.set_trace()
	    #print arbic_name
	    key_lst.append(site_code)
	    key_lst.append(en_air_name)
	    key_lst.append(arbic_name)
	    key_lst.append(state_name)
	    fin_keys, fin_dict = [], {}
	    key_lst.append(city)
	    for i in key_lst:
		i = i.replace(' - ', '').strip()
		i= i.split(' ')
		for j in i:
		    j = j.replace(u'\u0645\u0637\u0627\u0631', '').replace(u'\ufee2\ufec3\ufe8d\ufead', '').\
                        replace(u'\u0627\u0644\u062f\u0648\u0644\u064a', '').replace(u'\ufea9\ufeee\ufedf\ufeef', '').strip().replace(' - ', '').strip()
		    j = j.replace('&lrm;', '').strip()
		    j = j.replace('International', '').replace('Airport', '').replace('The', '').strip()
		    j = j.strip().strip(',')
		    if j: fin_keys.append(j)
		    j = j.lstrip(u'\u0627\u0644').strip()
                    if u'\u0622\u0644' in j:
                        j = j.lstrip(u'\u0622\u0644').strip()
		    j = j.strip().strip(',')
		    if j: fin_keys.append(j)
	    arabic_name = arbic_name.strip(',').strip()
	    eng_format = ['%s, %s - %s (%s)'%(state_name, country_code, en_air_name, site_code)]
	    if arabic_name or city:
		arabic_name = ['%s, %s - %s (%s)'%(city, country_code, arabic_name, site_code)]
		#arabic_name = [arabic_name]
	    else: arabic_name = []
	    fin_dict.update({'arabic': arabic_name, 'english': eng_format, 'code':site_code, 'keywords':list(set(fin_keys))})
            self.fin_lst.append(fin_dict)
	    temp = True
	if not temp:
	    with open('no_airport.txt', 'a+') as f:
		f.write('%s\n'%air_code)
	    print air_code, '----------'
