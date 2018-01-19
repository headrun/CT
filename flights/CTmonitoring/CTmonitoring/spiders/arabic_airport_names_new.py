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
class ArabicBrowse3(Spider):
    name = "arabicnew3_browse"
    start_urls = ["https://www.tajawal.com/"]

    def __init__(self, *args, **kwargs):
        super(ArabicBrowse3, self).__init__(*args, **kwargs)
	self.fin_lst = []
	dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
	open('arabic_names_fin.json', 'w+').write('%s'%json.dumps(self.fin_lst, ensure_ascii=False, encoding="utf-8"))

    def parse(self, response):
        sel = Selector(response)
	codes = ['CLE','ADL','ABV','CKY','BKO','CLT','AUS','BNA','DEA','ASB','BWN','FLL','DCA','BHD','CKG','BHV','BXU','JIB','BUS','FRU','HNL','ALC','BUF','COO','BND','DGT','EZE','CGN','BJM','CVG','HAJ','IND','BSL','BOD','CTA','GZT','AWZ','CMH','ELP','ASR','TIP','BGO','GIG','CUN','LAD','BIO','CXB','BKI','CHC','FLR','CCS','HRK','LIN','JAX','DLC','CBR','KGL','DBV','BDJ','DPL','DAY','BJL','BOI','OOL','HAV','DSE','BPN','CAG','GWD','PHX','CSX','BRE','BTH','JRO','IFN','HAH','KAN','ORF','BJR','MCI','IXA','BLL','MEX','BRI','KLO','CWL','KRK','CHS','ANC','GEG','CGQ','AQJ','GRJ','GBE','LIM','GDN','AEP','GNY','CNS','CLJ','LUN','DYU','FNA','ABQ','PRI','BDS','CAE','AAL','AAE','AEX','AZO','GRK','CTS','OPO','BDL','CJU','LUX','BES','FAO','DAD','BTS','LJU','FNC','FUK','CNF','BLZ','BSB','BRS','LAO','HBA','NIM','DRS','KIV','LBA','BDO','PIT','HDQ','JUB','CWB','CRC','JSR','YHZ','KRR','BHM','LFW','DIR','IOM','MQX','FIH','BFN','ICT','HME','COS','CIT','BGI','NDJ','MSY','DRW','AXU','BZV','SPU','MAR','BIQ','OKC','LCG','NAN','ASU','GDL','YWG','BGF','GOA','CGH','BZN','PNH','ISU','KZN','FAT','CUZ','NUE','GSO','GZP','INN','AAR','BTV','LPA','OUA','LOP','DQA','FAY','EUG','BZL','AGS','JJN','AAQ','MPM','LEJ','ABI','CRP','RDU','AOR','GPT','ODS','HSV','GRX','BTU','DJE','AOI','AHO','GUW','DSM','HER','ELS','JOG','ASF','CID','NOU','PMI','INC','QQS','CRL','KUF','KUA','AUA','PRN','BUQ','JER','MEM','CLO','BGA','RIX','KIN','FOC','HUY','GRZ','FWA','GCM','ALB','GRR','JAN','INV','BDA','DNK','CAK','OMA','KMG','MRA','PUW','BAQ','BME',]
	codes2 = ['PUS','MRV','SHA','LBV','GUM','FEZ','EAS','LST','KGD','RNO','LEX','APL','CTG','AES','AKX','GUA','BTR','DIY','GBB','YQR','GYE','ROV','PTY','KYA','MGQ','GDQ','KNO','HRB','FDH','MPL','SIP','KOA','AVP','JIM','FLN','MFM','RST','NKT','ORN','LLW','KIS','LIT','MKE','CUR','ANU','CND','LTN','NSI','CFU','POZ','FSD','CFE','ASP','CEK','HOU','DUD','EVV','FMO','KRS','JGA','ARM','PLZ','BLA','ORK','KWE','DNZ','DJB','BVA','FOR','LWO','AMA','GSP','LBB','NKG','CRW','STR','YXE','ERI','BAL','NGO','TLV','GNV','ALO','CHA','KJA','BFS','MCX','SAT','YYJ','NTE','CFS','AJL','FAI','ARH','REP','ROC','BEW','GFK','DHN','LEI','EZS','KHH','KTW','FBM','AJA','BIL','MQM','GTR','LHW','PSA','BGR','YLW','MCY','PQC','JRH','AVL','HOR','CHQ','OUD','LAN','PSC','CLL','DAL','BEN','DIB','OGG','DBQ','POM','HTI','COR','CXR','DAB','SZX','BFL','HIJ','LDE','REN','BIA','OVB','CRM','OKA','KTA','YQT','PPS','ULH','TPA','TNR','ZVH','UET','TLS','STL','TIA','SLC','XMN','SRG','SKZ','WUH','SKG','VLC','TAG','SCL','TAO','WNZ','SKP','TUS','UPG','SHE','TUG','TNG','MYY','SVG','XIY','WLG','VNO','SZG','OZC','URC','WDH','NWI','POS','TLL','SAV','TGD','YIW','VAR','USN','SOC','RXS','ULN','UIO','WRO','TRN','SYR','UFA','TFN','RIC','WNP','SVQ','VTE','TUL','PMO','PJG','LRR','VRN','SJC','PKU','OLB','PUF','PEE','SJO','SVX','VPS','KHE','MME','SAL','SJU','SHV','TRD','TGG','NAS','OZH','SDQ','ZQN','SDF','MDE','SNN','SZF','YYT','SBW','MJD','SNA','OVD','POA','LFT','TIV','SCO','MVD','RHO','TSV','NGB','RUN','NLA','MOB','TRS','VGO','TYS','ROB','YNT','MTY','PNR','ZYR','SGF','XNA','XRY','TNA','VOG','TSN','SSG','VVO','SJD','PPT','TBZ','QKL','HLA','TJM','RSW','UTN','MHK','PLM','LBU','MQP','SCQ','VVI','MDC','TKG','TCR','IXG','TSR','IXD','DMU','SAG','OHS','HBX','HRI','HHN','KUU','RVN','PGH','RRG','CIA','MWZ','YYG','BHU','BMA','IXY','OMS','TSF','FAR','YFC','KSC','NNG','PDG','HJR','NRN','LDB','PBD']	
	url = 'https://www.tajawal.com/api/air/airport/search?query=%s'
	codes2.extend(codes)
	for i in codes2:
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
	    air = ['Weeze Airport', 'Oman Sohar', 'Malabo Airport',  'Saudi Arabia Al Ula', 'Puerto Princesa International Airport', ' Cam Ranh International Airport', 'Phu Quoc Airport', 'Turkey Cizre', 'Sri Lanka Hambantota', 'Cam Ranh International Airport']
	    for k in air:
		arbic_name = arbic_name.replace(k, '').strip()
	    cities_lst = ['Aktyubinsk', 'Kandla', 'Mwanza', 'Kulu', 'Hahn', 'Hubli', 'Dimapur', 'Tuticorin', 'Ar', 'mo', 'Pakistan', 'Zaporozhye', 'Durham Tees Valley', 'United States', 'Naga', 'and Tobago', 'Abdulaziz', 'Aizawl', 'Tel Aviv-Yafo', 'WV', 'Lubbock', 'SC', 'Indonesia', 'Gondar']
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
	    for j in cities_lst:
		city = city.replace(j, '').strip()
	    ci = ['Misurata', 'Grand Rapids', 'Islands', 'Pristina', 'AL', 'GA', 'OR', 'Axum', 'Kingdom', 'Ethiopia', 'Cartago', 'Juba', 'PA', 'LA', 'Bahar Dar', 'Coolangatta (Gold Coast)', 'OH', 'France', 'NY', ]
	    for h in ci:
		city = city.replace(h, '').strip()
	    air1 = ['Galeao Antonio Carlos Jobim International Airport', 'Brasilia International Airport', 'Turkey Golgen', 'J. Paul II International Airport Krakow-Balice', 'China', 'Indonesia Praya', 'Turkey Gazipasa', 'Iraq', 'Perm International Airport']
	    for j in air1:
		arbic_name= arbic_name.replace(j, '').strip()
	    empty_air = ['GWD','DSE','AWZ','BND','GBB','RRG','HHN','KHE','PJG','FBM']
	    if site_code in empty_air:
		city, arbic_name = '', ''
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
