#!/usr/bin/env python
import sys
import optparse
import MySQLdb
import datetime
from utils import *
import hashlib
import md5

class WegoSaInput(object):

    def __init__(self, options):
        self._input = options.file_name 
        self.crawl_type = options.crawl_type
	self.source_name = 'wegosa'
	self.main()

    def create_crawl_table_cursor():
        conn = MySQLdb.connect(host="localhost", user = "root", db = "urlqueue_dev", charset="utf8", use_unicode=True)
        cur = conn.cursor()
        return cur

    def check_options(self):
        if not self._input or not self.crawl_type:
            print "Parse inpit file and crawl_type"
            sys.exit(-1)

    def main(self):
        self.check_options()
	cur = create_crawl_table_cursor()
	ensure_crawl_table(cur, self.source_name)
	file_data = open(self._input, 'r+').readlines()
	date_lst = []
	trip_type = 'one_way'
	date = datetime.datetime.now()
	for i in range(5):
	    date += datetime.timedelta(days=i+1)
	    date_lst.append(str(date.date()))
	if file_data:
	    for date in date_lst:
	        for data in file_data:
		    dict_ = {}
		    from_, to_ = data.replace('\n', '').strip().split('-')
		    sk = str(hashlib.md5('%s%s%s%s%s'%(date, from_, to_, self.crawl_type, trip_type)).hexdigest())
		    dict_.update({'sk':sk, 'date':date, 'from':from_, 'to':to_,
			'crawl_type':self.crawl_type, 'crawl_status': '0', 'trip_type':trip_type, 'return_date':''})
		    insert_crawl_tables_data(cur, self.source_name, dict_)
	cur.close()		


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-f', '--file-name', default='', help = 'filename')
    parser.add_option('-d', '--crawl-type', default='', help= 'crawltype')
    (options, args) = parser.parse_args()
    WegoSaInput(options)
