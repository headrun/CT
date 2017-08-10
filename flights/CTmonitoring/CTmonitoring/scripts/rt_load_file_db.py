#!/usr/bin/env python
import os
import glob
import sys
import json
import optparse
import MySQLdb
import datetime

class RTLoadFiles(object):
    def __init__(self, options):
        self.ip     = 'localhost' 
	self.source = options.source_name
	#self.db     = '%s%s'%(self.source.upper(), 'DB')
	self.path   = "/root/headrun/CTmonitoring/CTmonitoring/spiders/OUTPUT/processing"
	self.processed = '/root/headrun/CTmonitoring/CTmonitoring/spiders/OUTPUT/processed'
	self.insert_query = 'insert into RTAvailability (sk, flight_id, date, type, dx, no_of_passengers, is_available, airline, departure_time, arrival_time, from_location, to_location, providers, aux_info, reference_url, return_flight_id, return_departure_time, return_airline, trip_type, created_at, modified_at) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now()) on duplicate key update sk=%s, providers=%s, is_available=%s'
        self.main()

    def check_options(self, db):
        if not db or not self.ip:
            print "Souce, Db and Ip cant be empty. For more check load_files_db.py --help"
            sys.exit(-1)
    def create_cursor(self, host, db):
        try:
            conn = MySQLdb.connect(user='root',host='localhost', db=db)
            conn.set_character_set('utf8')
            cursor = conn.cursor()
            cursor.execute('SET NAMES utf8;')
            cursor.execute('SET CHARACTER SET utf8;')
            cursor.execute('SET character_set_connection=utf8;')
        except:
            import traceback; print traceback.format_exc()
            sys.exit(-1)
    
        return conn, cursor

    def ensure_db_exists(self, ip, dbname):
        conn, cursor = self.create_cursor(ip, dbname)
        stmt = "show databases like '%s';" % dbname
        cursor.execute(stmt)
        result = cursor.fetchone()
        if result:
            is_existing = True
        else:
            is_existing = False

        cursor.close()
        conn.close()

        return is_existing

    def get_file_data(self, file_nane):
        xml_f = open(file_nane, 'rb+').readlines()
        return xml_f

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

    def insert_data_into_db(self, cursor, data):
	for rec in data:
	    rec = rec.strip().strip('\n')
	    if rec:
	        dic = json.loads(rec)
	        vals = (
				dic['sk'], dic['flight_id'], dic['date'], dic['type'], dic['dx'],
				dic['no_of_passengers'], dic['is_available'],
				dic['airline'], dic['departure_time'],
				dic["arrival_time"], dic['from_location'], dic['to_location'],
				dic['providers'], dic['aux_info'], dic['reference_url'],
				dic['return_flight_id'], dic['return_departure_time'],
				dic['return_airline'], 'roundtrip', dic['sk'], dic['providers'],
				dic['is_available'],
			)
		cursor.execute(self.insert_query, vals)	

    def main(self):
	sources = self.source.split(',')
	for source in sources:
	    db = source.upper() + 'DB'
	    self.check_options(db)
            conn, cursor = self.create_cursor(self.ip, db)
	    if not self.ensure_db_exists(self.ip, db):
                print 'Enter valid Source Name and Ip'
                pass
	    files = self.ensure_files_exists(source)
	    if files != "empty":
	        for fi in files:
	            fi_name = fi.split('/')[-1]
	            data = self.get_file_data(fi)
	            if data: self.insert_data_into_db(cursor, data)
	            self.move_file_crawled(fi_name)

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--source-name', default='', help = 'sourcename')
    (options, args) = parser.parse_args()
    RTLoadFiles(options)

