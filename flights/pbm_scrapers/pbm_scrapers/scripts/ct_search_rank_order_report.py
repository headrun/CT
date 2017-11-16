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
import json
import csv
import sys
import os

class CTrankOrder(object):
        
    def __init__(self, options):
	self.source = options.source_name
        self.ip     = 'localhost'
	self.csv_path = '/root/headrun/pbm_scrapers/pbm_scrapers/spiders/OUTPUT/cvs_file'
	self.csv_mv_path = '/root/headrun/pbm_scrapers/pbm_scrapers/spiders/OUTPUT/processed'
        self.ct_data_query = "select * from %s_availability where date(modified_at)=curdate() and segment_type='%s' order by rank"
	self.headers = ["Airline", "Segments", "Trip Type", "Segment Type", "Date", "Flight Number", "CT Rank", "CT Price", "MMT Rank", "MMT Price"]
	self.main()

    def check_options(self):
        if not self.source or not self.ip:
            print "Souce, Db and Ip cant be empty. For more check python send_csv_mail.py --help"
            sys.exit(-1)

    def open_excel_files(self, source, seg_type):
	os.chdir(self.csv_path)
	excel_file_name = '%s_%s_ranking_%s_avail.csv'%(source, seg_type, str(datetime.datetime.now().date()))
	oupf = open(excel_file_name, 'ab+')
	todays_excel_file  = csv.writer(oupf)
	return (todays_excel_file, excel_file_name)

    def get_compressed_file(self):
	os.chdir(self.csv_path)
	gz_file = 'ct_search_ranking_%s.tar.gz'%str(datetime.datetime.now().date())
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
	    '''
	    ccing = ['lakshmi.b@cleartrip.com', 'srinivas.v@cleartrip.com',
			'cleartrip@headrun.com','hareesh.r@cleartrip.com',
			'pallav.singhvi@cleartrip.com', 'chetan.sharma@cleartrip.com',
			'adhvaith.h@cleartrip.com', 'deepak.sharma@cleartrip.com',
			'ashwin.d@cleartrip.com', 'ankit.dutt@cleartrip.com'
		     ]
	    '''
	    ccing = []
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Price Benchmarking Report On %s'%(str(datetime.datetime.now().date()))
            mas = '<h2>ONE-WAY Domestic and International Reports</h2>'
	    
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
		rank, segment_type, segments, trip_type, flight_id, created_at, modified_at = record
	    key = '%s%s'%(segments.strip(), flight_id.strip())
	    try: date = arrival_datetime.date()
	    except: date = depature_datetime.date()
	    dict_.update({key.lower():[airline, segments, trip_type, flight_id, rank, price, date, segment_type]})
	return dict_

    def get_cvs_file(self, ct_dict, mmt_dict, excel_file):
	#excel_file, file_name = self.open_excel_files(source)
	#headers = ["Airline", "Segments", "Trip Type", "Segment Type", "Date", "Flight Number", "CT Rank", "CT Price", "MMT Rank", "MMT Price"]
	#excel_file.writerow(headers)
        for key, ct_lst in ct_dict.iteritems():
	    mmt_lst = mmt_dict.get(key.lower(), ['']*7)
	    airline_name = '<>'.join(list(set(ct_lst[0].split('<>'))))
	    vals = (airline_name, ct_lst[1], ct_lst[2], ct_lst[7], ct_lst[6], ct_lst[3], ct_lst[4], ct_lst[5], mmt_lst[4], mmt_lst[5]) 
	    excel_file.writerow(vals)
        #return file_name

    def main(self):
        self.check_options()
	ct, other = self.source.split(',')
	csv_lst = []
	seg_list = ['Domestic', 'International']
	#seg_list = ['International']
	conn, cursor = self.create_cursor(self.ip, 'CLEARTRIP_MAP')
	for seg in seg_list:
	    if not self.ensure_db_exists(self.ip, 'CLEARTRIP_MAP'):
		    print 'Enter valid DB and Ip'
		    pass
	    ct_dict = self.get_db_data(cursor, ct, seg)
	    mmt_dict = self.get_db_data(cursor, other, seg)
	    if ct_dict:
		excel_file, file_name = self.open_excel_files('%s-%s'%(ct, other), seg.lower())
                excel_file.writerow(self.headers)
	        self.get_cvs_file(ct_dict, mmt_dict, excel_file)
	        csv_lst.append(file_name)
	gz_file = self.get_compressed_file()
        self.send_mails([gz_file])
	self.move_compressed_file()
 	
if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--source-name', default='', help = 'sourcename')
    (options, args) = parser.parse_args()
    CTrankOrder(options)
