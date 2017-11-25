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

class CTrankOrder(object):
        
    def __init__(self, options):
	self.source = options.source_name
        self.ip     = 'localhost'
	self.csv_path = '/root/headrun/CTPCC/CTPCC/spiders/OUTPUT/csv_file'
	self.csv_mv_path = '/root/headrun/CTPCC/CTPCC/spiders/OUTPUT/processed'
        self.ct_data_query = "select * from %s where date(modified_at)=curdate() and trip_type = '%s' order by rank"
	self.headers = ["Flight number", "Airline", "Origin", "Destination", "Departure date", "Dx", "Stops Count", "No.of Passengers", "OW/RT", "India PCC Price", "UAE PCC Price", "KSA PCC Price"]
	self.main()

    def check_options(self):
        if not self.source or not self.ip:
            print "Souce, Db and Ip cant be empty. For more check python send_csv_mail.py --help"
            sys.exit(-1)

    def open_excel_files(self, source, seg_type):
	os.chdir(self.csv_path)
	excel_file_name = '%s_%s_pcc_%s_avail.csv'%(source, seg_type, str(datetime.datetime.now().date()))
	oupf = open(excel_file_name, 'wb+')
	todays_excel_file  = csv.writer(oupf)
	return (todays_excel_file, excel_file_name)

    def get_compressed_file(self):
	os.chdir(self.csv_path)
	gz_file = 'ct_pcc_price_%s.tar.gz'%str(datetime.datetime.now().date())
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


    def send_mails(self, file_lst):
	os.chdir(self.csv_path)
        if file_lst:
            #recievers_list = ['sudhir.mantena@cleartrip.com']
	    recievers_list = ["prasadk@notemonk.com", "aravind@headrun.com"]
            sender, receivers  = 'prasadk@notemonk.com', ','.join(recievers_list)
	    ccing = ['lakshmi.b@cleartrip.com', 'srinivas.v@cleartrip.com',
			'cleartrip@headrun.com','hareesh.r@cleartrip.com',
			'pallav.singhvi@cleartrip.com', 'chetan.sharma@cleartrip.com',
			'adhvaith.h@cleartrip.com', 'deepak.sharma@cleartrip.com',
			'ashwin.d@cleartrip.com', 'ankit.dutt@cleartrip.com',
			'neeraj.goswami@cleartrip.com'
		     ]
	    #ccing = []
            msg = MIMEMultipart('alternative')
            msg['Subject'] = '[IND, KSA, UAE] CT Multi-PCC Report On %s'%(str(datetime.datetime.now().date()))
            mas = '<h2>ROUNDTRIP & ONE-WAY Reports</h2>'
	    
	    for i in file_lst:
		part = MIMEBase('application', "octet-stream")
		part.set_payload(open(i, "rb").read())
		encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename=%s'%i)
                msg.attach(part)
            msg['From'] = sender
            msg['To'] = receivers
	    msg['Cc'] = ','.join(ccing)
            tem = MIMEText(''.join(mas), 'html')
            msg.attach(tem)
            s = smtplib.SMTP('smtp.gmail.com:587')
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(sender, 'amma@nanna')
            s.sendmail(sender, (recievers_list + ccing), msg.as_string())
            s.quit()

    def get_db_data(self, cursor, source, seg_type):
	cursor.execute(self.ct_data_query%(source, seg_type))
        records = cursor.fetchall()
	dict_ = {}; dict_ = collections.OrderedDict(dict_)
	for record in records:
	    sk, price, airline, depature_datetime, arrival_datetime, \
		rank, segment_type, segments, trip_type, flight_id, no_of_passengers, no_of_stops, dx, created_at, modified_at = record
	    key = '%s%s%s'%(segments.strip(), flight_id.strip(), dx)
	    origin, dest = segments.split('-')
	    depature_ = depature_datetime.date()
	    try: date = arrival_datetime.date()
	    except: date = depature_datetime.date()
	    dict_.update({key.lower():[flight_id, airline, origin, dest, depature_, dx, no_of_stops, no_of_passengers, trip_type, price]})
	return dict_

    def get_cvs_file(self, ind_dict, uae_dict, ksa_dict, excel_file):
        for key, ct_lst in ind_dict.iteritems():
	    uae_lst = uae_dict.get(key.lower(), ['']*10)
	    ksa_lst = ksa_dict.get(key.lower(), ['']*10)
	    airline_name = '<>'.join(list(set(ct_lst[1].split('<>'))))
	    vals = (ct_lst[0], airline_name, ct_lst[2], ct_lst[3], ct_lst[4], ct_lst[5], ct_lst[6], ct_lst[7], ct_lst[8], ct_lst[9], uae_lst[9], ksa_lst[9]) 
	    excel_file.writerow(vals)
        #return file_name

    def main(self):
        self.check_options()
	table_names = {'ind': 'ind_availability',
			'uae': 'uae_availability',
			'ksa': 'ksa_availability',
			}
	inputs = self.source.split(',')
	csv_lst = []
	seg_list = ['OneWay', 'RoundTrip']
	#seg_list = ['OneWay']
	#seg_list = ['RoundTrip']
	conn, cursor = self.create_cursor(self.ip, 'CTPCCDB')
	for seg in seg_list:
	    if not self.ensure_db_exists(self.ip, 'CTPCCDB'):
		    print 'Enter valid DB and Ip'
		    pass
	    ct_dict = mmt_dict = ya_dict = go_dict = {}
	    for table in inputs:
		table_ = table_names.get(table, '')
		data_dict = self.get_db_data(cursor, table_, seg)
	        if table == 'ind': ind_dict = data_dict
		if table == 'uae': uae_dict = data_dict
		if table == 'ksa': ksa_dict = data_dict
	    if ind_dict:
		excel_file, file_name = self.open_excel_files('ct', seg.lower())
		excel_file.writerow(self.headers)
		self.get_cvs_file(ind_dict, uae_dict, ksa_dict, excel_file)
	time.sleep(5)
	gz_file = self.get_compressed_file()
        self.send_mails([gz_file])
	self.move_compressed_file()
 	
if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--source-name', default='', help = 'sourcename')
    (options, args) = parser.parse_args()
    CTrankOrder(options)
