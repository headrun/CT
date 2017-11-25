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
	self.path   = "/root/headrun/CTPCC/CTPCC/spiders/OUTPUT/processing"
	self.processed = '/root/headrun/CTPCC/CTPCC/spiders/OUTPUT/processed'
        self.main()

    def ensure_files_exists(self, source):
        files = glob.glob(self.path+'/%s_*.queries'%source)
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
	cmd = 'mysql -uroot ' + '-h localhost' + ' -A ' + 'CTPCCDB' + ' --local-infile=1 -e "%s"'
        query =  "LOAD DATA LOCAL INFILE '%s' REPLACE INTO TABLE %s CHARACTER SET utf8 FIELDS TERMINATED BY '#<>#'" % (query_file, table)
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
			}
	sources = self.source.split(',')
	for source in sources:
	    table = table_names.get(source, '')
	    if not table: continue
	    pro_files = 'cleartrip%s'%source
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
