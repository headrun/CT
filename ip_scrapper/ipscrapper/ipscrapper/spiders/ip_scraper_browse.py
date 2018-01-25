import csv
import json
import scrapy
import psycopg2
from scrapy.selector import Selector
from scrapy.http import Request
from ipscrapper.utils import *
from datetime import datetime, timedelta

def create_ctaws_table_cursor(x, query_str):
    hostname,database,username,password,prt = x.split("|")
    conn = psycopg2.connect( host=hostname, user=username, password=password, dbname=database, port = prt)
    cur = conn.cursor()
    cur.execute(query_str)
    rows = cur.fetchall()
    cur.close()
    return rows

class Ipscraper(scrapy.Spider):
    name = 'ipscraper_browse'
    start_urls = ['https://www.cleartrip.com/hotels']
    
    def __init__(self, *args,**kwargs):
        super(Ipscraper,self).__init__(*args,**kwargs)
	self.current_machine = kwargs.get('machine', 'local')
	self.wantips_csv = kwargs.get('input_csv', 'y')
	self.back_dated_by = 100
	self.offset = 1000000
	self.excel_file_name = 'INPUT_IPS.csv' 
	self.query_check_ips = 'select ip from ipmeta'
	self.cursor1 = create_ct_table_cusor()
	#self.cursor1.execute("delete from ip_crawl")
	if self.current_machine == 'local':
		self.yday = datetime.now() - timedelta(days=1)
		self.wb_yday = datetime.now() - timedelta(days=2)
		#self.query_str = 'select ip from (select ip, count(*) from analytics.air_search_data where date_time >= \''+self.wb_yday.strftime("%Y-%m-%d")+'\' and date_time < \''+self.yday.strftime("%Y-%m-%d")+'\' and (ip is not null or ip != \'""\' ) and channel = \'CHANNEL_SITE\' and international_flag = 0 and selling_country = \'IN\' and user_agent != \'Java/1.8.0_51\' and http_status = 200 GROUP BY ip ORDER BY count desc) OFFSET ' + str(self.offset)
		#self.query_str = 'select distinct ip from analytics.air_book_data where date_time >= \''+self.wb_yday.strftime("%Y-%m-%d")+'\' and date_time < \''+self.yday.strftime("%Y-%m-%d")+'\' and ip is not null and channel in ("CHANNEL_SITE", "CHANNEL_SITE") and stage in ("AIR_UI_STEP1")'
		self.query_str = 'select distinct ip from analytics.air_search_data where date_time between '+self.wb_yday.strftime("%Y-%m-%d")+ ' and '+self.yday.strftime("%Y-%m-%d")+ ' and ip is not null'
		
		#self.query_str = 'select sk from ip_crawl'
		self.file = open("ip_scraper.txt", "r")
		self.x = self.file.read()

    def __del__(self):
	self.cursor1.close()

    def is_path_file_name(self, excel_file_name):
        if os.path.isfile(excel_file_name):
            os.system('rm %s' % excel_file_name)
        oupf = open(excel_file_name, 'ab+')
        todays_excel_file = csv.writer(oupf)
        return todays_excel_file

    def get_from_csv_file(self):
	file_name = 'INPUT_IPS.csv'
	rows = []
	with open(file_name, 'rb') as csvfile:
		lines = csv.reader(csvfile, delimiter=',')
		for line in lines:
			rows.append(line[1])
	#os.system('rm %s' % file_name)
	return rows
	
    def dump_to_csv_file(self, rows):
	csv_file = self.is_path_file_name(self.excel_file_name)
	headers = ["count", "IP"]
	csv_file.writerow(headers)
	for index, row in enumerate(rows):
		if row:
			csv_file.writerow([index, row[0]])

    def check_in_meta(self, rows):
	self.cursor1.execute(self.query_check_ips)
	rows_present = self.cursor1.fetchall()
	for row in rows_present:
		if row[0] in rows:
			rows = filter(lambda a: a != row[0], rows)
	return rows	
	
    def parse(self, response):
	rows = []
	if self.current_machine == 'local':
		rows = create_ctaws_table_cursor(self.x, self.query_str)
		print len(rows)
		#self.cursor1.execute(self.query_str)
		#rows = self.cursor1.fetchall()
		if self.wantips_csv == 'y':
			self.dump_to_csv_file(rows)
			rows = []
	else:
		rows = self.get_from_csv_file()
	rows =self.check_in_meta(rows)
	for row in rows:
		if row and row != 'IP':
			if isinstance(row, str):
				row = [row]
			urls =  'http://www.ip-tracker.org/locator/ip-lookup.php?ip={}'.format(row[0])
			dict_  = {'sk': str(row[0]), 'crawl_type':'keepup', 'content_type':'ip', 'meta_data':'', 'aux_info':'', 'reference_url':urls}
			insert_crawlct_tables_data(self.cursor1, 'ip', dict_)
