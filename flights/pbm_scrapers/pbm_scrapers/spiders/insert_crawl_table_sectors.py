#!/usr/bin/env python
import sys
import optparse
import MySQLdb
import datetime
from pbm_scrapers.utils import *
import hashlib
import md5

class CrawlSectorsInput(object):

    def __init__(self, options):
        self._input = options.file_name 
        self.crawl_type = options.crawl_type
	self.trip_type = options.trip_type
	self.source = options.source_name
	self.main()

    def create_crawl_table_cursor():
        conn = MySQLdb.connect(host="localhost", user = "root", db = "urlqueue_dev", charset="utf8", use_unicode=True)
        cur = conn.cursor()
        return cur

    def check_options(self):
        if not self._input or not self.crawl_type or not self.trip_type:
            print "Parse input file and crawl_type and trip_type"
            sys.exit(-1)

    def main(self):
        self.check_options()
	cur = create_crawl_table_cursor()
	ensure_crawl_table(cur, self.source)
	file_data = open(self._input, 'r+').readlines()
	date_lst = []
	trip_type = self.trip_type
	date_now = datetime.datetime.now()
	DX = [0, 7, 15, 30]
	for data_ in file_data:
	    dict_, re_dx = {}, ''
	    for i in DX:
		sk_date_time = datetime.datetime.now() + datetime.timedelta(days=i)
	        data, re_dx = data_.split('\t')
	        try: re_dx = int(re_dx.replace('\n', '').strip())
	        except: continue
	        from_, to_ = data.replace('\n', '').strip().split('-')
	        date = sk_date_time
	        if self.trip_type == 'roundtrip':
		    retun_date = date_now + datetime.timedelta(days=re_dx)
		    retun_date = str(retun_date.date())
	        else: retun_date = ''
	        sk = str(hashlib.md5('%s%s%s%s%s%s%s'%(date, from_, to_, self.crawl_type, trip_type, sk_date_time, i)).hexdigest())
	        dict_.update({'sk':sk, 'date':date, 'from':from_, 'to':to_,
			'crawl_type':self.crawl_type, 'crawl_status': '0',
			'trip_type':trip_type, 'return_date':retun_date, 'dx':i})
	        insert_crawl_tables_data(cur, self.source, dict_)
	cur.close()		


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-f', '--file-name', default='', help = 'filename')
    parser.add_option('-d', '--crawl-type', default='', help= 'crawltype')
    parser.add_option('-i', '--trip-type', default='', help= 'triptype')
    parser.add_option('-s', '--source-name', default='', help= 'sourcename')
    (options, args) = parser.parse_args()
    CrawlSectorsInput(options)
