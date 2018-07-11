#!/usr/bin/env python
import os
import glob
import sys
import json
import optparse
import MySQLdb
import datetime

class LoadFiles(object):
    def __init__(self, options):
        self.ip     = 'localhost'
	self.source = options.source_name
	#self.db     = '%s%s'%(self.source.upper(), 'DB')
	self.path   = "/root/meta_dev/CTPCC/CTPCC/spiders/OUTPUT/processing"
	self.processed = '/root/meta_dev/CTPCC/CTPCC/spiders/OUTPUT/processed'
        self.main()

    def ensure_files_exists(self, source):
        files = glob.glob(self.path+'/*%s_*.queries'%source)
        if len(files) != 0:
            return files
        else:
	    return "empty"
            #import traceback; print traceback.format_exc()
            #sys.exit(-1)

    def move_file_crawled(self, file_nane):
        os.chdir(self.path)
        q_mv = "mv %s %s"%(file_nane, self.processed)
        os.system(q_mv)

    def dump_file_into_db(self, query_file, table):
	cmd = 'mysql -uroot -proot ' + '-h localhost' + ' -A ' + 'CTPCCDB' + ' --local-infile=1 -e "%s"'
        query =  "LOAD DATA LOCAL INFILE '%s' INTO TABLE %s CHARACTER SET utf8 FIELDS TERMINATED BY '#<>#'" % (query_file, table)
        query += "SET created_at=NOW(), modified_at=NOW();"
	try:
	    os.system(cmd % query)
	    return True
	except:
	    print "%s fail to load"%query_file
	    return False

    def main(self):
	table_names = {'ind':'ind_availability',
			'uae':'uae_availability',
			'ksa':'ksa_availability',
			'foreign' : 'foreign_availability',
			'foreignrt' : 'foreignrt_availability',
			'art1949' : 'art1949_availability',
			'art1949kiwi' : 'art1949kiwi_availability',
			'art1949rt' : 'art1949rt_availability',
			'art1949kiwirt' : 'art1949kiwirt_availability',
			'air280' : 'air280_availability',
			'air280rt' : 'air280rt_availability',
			'rehlat': 'rehlat_availability',
			'citybookers': 'citybookers_availability',
			'gomosafer': 'gomosafer_availability',
            'myholidays' : 'myholidays_availability',
            'amedeus' : 'amedeus_availability',
            'amedeusrt' : 'amedeus_roundtrip_availability'
			}
	sources = self.source.split(',')
	for source in sources:

	    table = table_names.get(source, '')
	    if not table: continue
	    pro_files = '%s'%source#'cleartrip%s'%source
	    files = self.ensure_files_exists(pro_files)
	    if files != "empty":
	        for fi in files:
	            fi_name = fi.split('/')[-1]
		    status = self.dump_file_into_db(fi, table)
		    if status:
	                self.move_file_crawled(fi_name)

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--source-name', default='', help = 'sourcename')
    (options, args) = parser.parse_args()
    LoadFiles(options)
