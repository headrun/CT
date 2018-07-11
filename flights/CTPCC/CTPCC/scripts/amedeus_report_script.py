import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ast import literal_eval
from email.mime.base import MIMEBase
from datetime import datetime
from email import encoders
import smtplib,ssl
import collections
import MySQLdb
import optparse
import datetime
import time
import json
import csv
import sys
import os

class RehlatOrder(object):

    def __init__(self, options):
        self.source = options.source_name
        self.ip     = 'localhost'
        self.CSV_PATH = '/nfs/data/FLIGHTS_SCRAPED_DATA/%s'
        self.csv_path = '/root/meta_dev/CTPCC/CTPCC/spiders/OUTPUT/csv_file'
        self.csv_mv_path = '/root/meta_dev/CTPCC/CTPCC/spiders/OUTPUT/processed'
        self.ct_data_query = "select * from %s_availability where date(modified_at)=subdate(curdate(), 0)"
        self.ow_headers = ["Flight number", "Sector", "Airline", "Origin & Destination", "Departure datetime", "Dx", "Stops Count", "No.of Passengers", "OW/RT", "Price(QAR)"]
        self.rt_headers = ["Flight number", "Sector", "Airline", "Origin & Destination", "Departure datetime", "Return Flight number", "Return Departure datetime", "Dx", "Stops Count", "Return Stops Count", "No.of Passengers", "OW/RT", "Price(QAR)"]
        self.main()

    def check_options(self):
        if not self.source or not self.ip:
            print "Souce, Db and Ip cant be empty. For more check python send_csv_mail.py --help"
            sys.exit(-1)

    def open_excel_files(self, source, seg_type):
        if source == 'amedeus_roundtrip':
            source = 'amedeus'
        CSV_PATH = self.CSV_PATH%source.upper()
        mydir = os.path.join(CSV_PATH, datetime.datetime.now().strftime('%Y/%m/%d'))
        try:os.makedirs(mydir)
        except:pass
        excel_file_name = '%s_%s.csv'%(source, seg_type)
        oupf = open(os.path.join(mydir, excel_file_name), 'wb+')
        todays_excel_file  = csv.writer(oupf)
        return (todays_excel_file, excel_file_name)

    def get_compressed_file(self):
        os.chdir(self.csv_path)
        gz_file = 'rehlat_price_%s.tar.gz'%str(datetime.datetime.now().date())
        gz_cmd = 'tar -czf %s *' %gz_file
        os.system(gz_cmd)
        return gz_file

    def move_compressed_file(self):
        os.chdir(self.csv_path)
        mc_cmd = 'mv * %s'%self.csv_mv_path
        os.system(mc_cmd)

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

    def create_cursor(self, host, db):
        try:
            conn = MySQLdb.connect(user='root',host='localhost', db=db, passwd='root')
            conn.set_character_set('utf8')
            cursor = conn.cursor()
            cursor.execute('SET NAMES utf8;')
            cursor.execute('SET CHARACTER SET utf8;')
            cursor.execute('SET character_set_connection=utf8;')
        except:
            import traceback; print traceback.format_exc()
            sys.exit(-1)

        return conn, cursor

    def get_db_data(self, cursor, source, seg_type_):
        cursor.execute(self.ct_data_query%source)
        records = cursor.fetchall()
        data_list = []
        for record in records:
            if  source == 'amedeus' and seg_type_ == "Oneway":
                sk, sector, segment, depature_datetime, arrival_datetime, airline, no_of_stops, flight_id, base_fare, tax_fare, discount_price,\
                    total_price_slashed, on_price, rank, dx, seg_type, trip_type, aux_info, cra_at, mod_at = record

                no_of_passengers = '1'
                data_list.append((flight_id, sector, airline, segment, depature_datetime, dx, no_of_stops, no_of_passengers, trip_type, on_price))

            elif source == 'amedeus_roundtrip' and seg_type_ =='RoundTrip':
                no_of_passengers = '1'
                sk, sector, on_segment, on_depature_datetime, on_arrival_datetime, on_airline, on_no_of_stops, on_flight_id , rt_segment,rt_depature_datetime, rt_arrival_datetime, rt_airline, rt_no_of_stops, rt_flight_id , base_fare, tax_fare, discount_price, total_price_slashed, rt_price, rank, dx, seg_type, trip_type, aux_info, cra_at, mod_at = record


                data_list.append((on_flight_id, sector, on_airline, on_segment, on_depature_datetime, rt_flight_id, rt_depature_datetime, dx, on_no_of_stops, rt_no_of_stops, no_of_passengers, trip_type, rt_price))
        return data_list


    def get_cvs_file(self, rehlat_list, excel_file):
        for vals_lst in rehlat_list:
	        excel_file.writerow(vals_lst)
        #return file_name

    def main(self):
        self.check_options()
        table_names = {'amedeus': 'amedeus_availability','amedeus_roundtrip':'amedeus_roundtrip_availability'}
        inputs = self.source.split(',')
        csv_lst = []
        seg_list = ['Oneway', 'RoundTrip']
        conn, cursor = self.create_cursor(self.ip, 'CTPCCDB')
        for source in inputs:
            for seg in seg_list:
                if not self.ensure_db_exists(self.ip, 'CTPCCDB'):
                    print 'Enter valid DB and Ip'
                    pass
                rehlat_list = self.get_db_data(cursor, source, seg)
                if rehlat_list:
                    excel_file, file_name = self.open_excel_files(source, seg.lower())
                if seg == 'Oneway' and source == 'amedeus':
                    excel_file.writerow(self.ow_headers)

                elif source == 'amedeus_roundtrip' and seg == 'RoundTrip':
                    excel_file.writerow(self.rt_headers)

                self.get_cvs_file(rehlat_list, excel_file)

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--source-name', default='', help = 'sourcename')
    (options, args) = parser.parse_args()
    RehlatOrder(options)
