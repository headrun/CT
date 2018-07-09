import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ast import literal_eval
from email.mime.base import MIMEBase
from datetime import datetime, timedelta
from email import encoders
import smtplib,ssl
import collections
import MySQLdb
import ast
import optparse
import datetime
import json
import time
import csv
import sys
import os

class CancellationScrapperReports(object):
        
    def __init__(self, options):
	self.source = options.source_name
        self.ip     = 'localhost'
	self.csv_path = '/root/aravind/reports'
	self.csv_mv_path = '/root/aravind/reports/processed'
        self.scrapper_report_query = "select * from %ssplit_cancellation_report where date(created_at)= subdate(curdate(), 1)"
	self.html_report_query = 'select count(*), error_message, status  from indigosplit_cancellation_report where date(modified_at)= subdate(curdate(), 1) group by error_message, status;'
        #self.scrapper_report_query = "select * from %s_cancellation_report where date(created_at)= curdate()"
	self.headers = ['Airline', 'Trip ID', 'PNR', 'Split PNR', 'Flight number', 'Status message', 'Error message']
	self.main()

    def check_options(self):
        if not self.source or not self.ip:
            print "Souce cant be empty. For more check python scrapper_report.py --help"
            sys.exit(-1)

    def open_excel_files(self, source):
        os.chdir(self.csv_path)
        excel_file_name = '%ssplit_cancellation_scrapper_report_%s.csv'%(source, str((datetime.datetime.today() - timedelta(days=1)).date()))
        oupf = open(excel_file_name, 'ab+')
        todays_excel_file  = csv.writer(oupf)
        return (todays_excel_file, excel_file_name, oupf)

    def get_compressed_file(self):
        os.chdir(self.csv_path)
        gz_file = 'splitcancellation_scrappers_report_%s.tar.gz'%str(datetime.datetime.now().date())
        gz_cmd = 'tar -czf %s *' %gz_file
        os.system(gz_cmd)
        return gz_file

    def move_csv_file(self):
        os.chdir(self.csv_path)
        mc_cmd = 'mv *.csv %s'%self.csv_mv_path
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

    def send_mails(self, file_lst, html_table):
    	os.chdir(self.csv_path)
        if file_lst:
	    #recievers_list = ['Ivy.pinto@cleartrip.com', 'Dhruvi.kothari@cleartrip.com', 'Tauseef.farooqui@cleartrip.com']
	    recievers_list = ['Ivy.pinto@cleartrip.com', 'Dhruvi.kothari@cleartrip.com', 'Tauseef.farooqui@cleartrip.com', 'samir.nayak@cleartrip.com', "snehal.k@cleartrip.com", "hareesh.r@cleartrip.com"]
	    #recievers_list = ['aravind@headrun.com', 'prasadk@notemonk.com']
            sender, receivers  = 'ctmonitoring17@gmail.com', ','.join(recievers_list)
            #ccing = ["cleartrip@headrun.com"]
	    ccing = ['aravind.r@cleartrip.com', "prasad.k@cleartrip.com", 'rakesh.g@cleartrip.com',  'jivan@cleartrip.com', 'subramanya.sharma@cleartrip.com', 'satish.desai@cleartrip.com', 'sudhir.mantena@cleartrip.com', 'ff.bdops@cleartrip.com', 'pallavi.khandekar@cleartrip.com', 'hareesh.r@cleartrip.com']
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Airlines SplitCancellation Scrapper Report On %s'%(str(datetime.datetime.now().date()))
            mas = html_table
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
            s.login(sender, 'ctmonitoring@123')
            s.sendmail(sender, (recievers_list + ccing), msg.as_string())
            s.quit()

    def get_db_data(self, cursor, source):
        cursor.execute(self.scrapper_report_query%(source))
        records = cursor.fetchall()
        dict_ = {}; dict_ = collections.OrderedDict(dict_)
    	for record in records:
		sk, airline, pnr, new_pnr, \
                pcc, flight_id, error_mesg, status, \
                                 cancel_amount, pricing_details, request_input, \
                                        aux_info, created_at, modified_at = record
            	if not flight_id:
                	flight_id = ''
                dict_.update({sk :[airline, pnr, new_pnr,  sk, flight_id, status, error_mesg]})
        return dict_

    def get_cvs_file(self, ct_dict, source, excel_file):
        for key, ct_lst in ct_dict.iteritems():
            vals = (source, ct_lst[3], ct_lst[1], ct_lst[2], ct_lst[4], ct_lst[5], ct_lst[6])
            excel_file.writerow(vals)
        #return file_name

    def get_html_report_table(self, cursor):
        data = cursor.execute(self.html_report_query)
        data = cursor.fetchall()
        data_list = []
        for row in data:
            count, error, status_msg = row
            data_list.append((count, error, status_msg))
        html_text = "<html>"
        html_text += "<h4>Indigo Inline HTML Summary</h4>"
        html_text += '<table border="1">'
        html_text += '<tr><th>Count(*)</th><th>Error Message</th><th>Cancellation Status</th>'
        for i in data_list:
            html_text += '<tr><td>%s</td><td>%s</td><td>%s</td></tr>'%i
        html_text += '</table>\n<h2>PFA</h2></html>'
        return html_text

    def main(self):
        self.check_options()
        sources = self.source.split(',')
        csv_lst = []
        conn, cursor = self.create_cursor(self.ip, 'SPLITCANCELLATIONDB')
        if not self.ensure_db_exists(self.ip, 'SPLITCANCELLATIONDB'):
			print 'Enter valid DB'
			pass
        for source in sources:
            _dict = self.get_db_data(cursor, source)
            if not _dict: continue
            excel_file, file_name, oupf = self.open_excel_files(source)
            excel_file.writerow(self.headers)
            self.get_cvs_file(_dict, source, excel_file)
	    oupf.close()
            csv_lst.append(file_name)
    	gz_file = self.get_compressed_file()
	html_table = self.get_html_report_table(cursor)
        self.send_mails(csv_lst, html_table)
        self.move_csv_file()
	
if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--source-name', default='', help = 'sourcename')
    (options, args) = parser.parse_args()
    CancellationScrapperReports(options)
