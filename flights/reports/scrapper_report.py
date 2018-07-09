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

class ScrapperReports(object):
        
    def __init__(self, options):
	self.source = options.source_name
        self.ip     = 'localhost'
	self.csv_path = '/root/aravind/reports'
	self.csv_mv_path = '/root/aravind/reports/processed'
        self.scrapper_report_query = "select sk, status_message, error_message ,pnr, flight_number , %s_price , cleartrip_price , tolerance_amount, triptype from %s_booking_report where date(created_at)= subdate(curdate(), 1)"
	self.html_report_query = 'select count(*), triptype, error_message , status_message   from %s_booking_report where date(created_at ) =subdate( curdate(),1) group by error_message, status_message, triptype;'
	self.headers = ['Airline', 'Trip ID', 'Status message', 'Error message' , 'PNR', 'Flight number' , 'Airline price' , 'Cleartrip price', 'Tolerance amount', 'Queue']
	self.main()

    def check_options(self):
        if not self.source or not self.ip:
            print "Souce cant be empty. For more check python scrapper_report.py --help"
            sys.exit(-1)

    def open_excel_files(self, source):
        os.chdir(self.csv_path)
        excel_file_name = '%s_scrapper_report_%s.csv'%(source, str((datetime.datetime.today() - timedelta(days=1)).date()))
        oupf = open(excel_file_name, 'ab+')
        todays_excel_file  = csv.writer(oupf)
        return (todays_excel_file, excel_file_name, oupf)

    def get_compressed_file(self):
        os.chdir(self.csv_path)
        gz_file = 'scrappers_report_%s.tar.gz'%str(datetime.datetime.now().date())
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


    def get_html_report_table(self, cursor, source, html_text):
	data = cursor.execute(self.html_report_query % source)
        data = cursor.fetchall()
	coupon_list, offline_list, adhoc_list = [], [], []
        for row in data:
            count, trip_type, error, status_msg = row
	    count = int(count)
	    if error.startswith('Case'):
		error = error[:53]
	    if trip_type:
		    trip, queue, pcc = trip_type.split('_')[0], trip_type.split('_')[1], '_'.join(trip_type.split('_')[2:])
        	    if 'coupon' in queue:
                	coupon_list.append((count, error, status_msg, pcc, trip))
	            else:
        	        offline_list.append((count, error, status_msg, pcc, trip))
	    else:
		    adhoc_list.append((count, error, status_msg, trip_type, trip_type ))
	html_text += "<center><h2>%s Inline HTML Summary</h2></center>" % source.title()
	queue_dict = {0: 'Coupon', 1 : 'Offline', 2: 'Adhoc(not captured queue info as it failed)'}
	for index, data_list in enumerate([coupon_list, offline_list, adhoc_list]):
		html_text += "<h4>Queue %s</h4>" % queue_dict[index]
		if not data_list: continue
		html_text += '<table border="1" width="700px">'
		html_text += '<tr><th>Count</th><th>Error message</th><th>Status</th><th>PCC</th><th>Trip</th>'
		for i in data_list:
		    html_text += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'%i
		html_text += '</table>\n'
        return html_text


    def send_mails(self, file_lst, html_table):
    	os.chdir(self.csv_path)
        if file_lst:
            recievers_list = ["mahesh.ghewade@cleartrip.com", "ticketing.teamleads@cleartrip.com", "dhruvi.kothari@cleartrip.com", "rohit.makar@cleartrip.com", "lcc.finance@cleartrip.com", "ilayaraja.k@cleartrip.com", "sheba.antao@cleartrip.com", "snehal.k@cleartrip.com", "hareesh.r@cleartrip.com"]
	    #recievers_list = ['aravind.r@cleartrip.com', 'prasad.k@cleartrip.com']
            sender, receivers  = 'ctmonitoring17@gmail.com', ','.join(recievers_list)
            ccing = ['aravind.r@cleartrip.com', "prasad.k@cleartrip.com", 'rakesh.g@cleartrip.com', 'jivan@cleartrip.com', 'subramanya.sharma@cleartrip.com', 'satish.desai@cleartrip.com', 'sudhir.mantena@cleartrip.com', 'ff.bdops@cleartrip.com', 'pallavi.khandekar@cleartrip.com']
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Airlines Scrapper Report On %s'%(str(datetime.datetime.now().date()))
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
        cursor.execute(self.scrapper_report_query%(source, source))
        records = cursor.fetchall()
        dict_ = {}; dict_ = collections.OrderedDict(dict_)
    	for record in records:
            sk, status_message, error_message ,pnr, flight_number , indigo_price , cleartrip_price , tolerance_amount, triptype = record
	    if source == 'airasia' and flight_number:
		flight_number = ', '.join(ast.literal_eval(flight_number))
	    if indigo_price:
		    indigo_price = indigo_price.strip('INR').replace(',', '')
	    if not tolerance_amount:
		try:
			tolerance_amount = float(indigo_price) - float(cleartrip_price)
		except:
			tolerance_amount  = 0
	    if source == 'airasia' and not pnr and not error_message:
		error_message = 'Payment failed whereas payment is successful'
            dict_.update({sk :[status_message, error_message ,pnr, flight_number , indigo_price , cleartrip_price , tolerance_amount, triptype]})
        return dict_

    def get_cvs_file(self, ct_dict, source, excel_file):
        for key, ct_lst in ct_dict.iteritems():
            try: vals = (source, key, ct_lst[0], ct_lst[1], ct_lst[2], ct_lst[3], ct_lst[4], ct_lst[5], ct_lst[6], ct_lst[7]) 
            except: vals = (source, key, ct_lst[0], ct_lst[1], ct_lst[2], ct_lst[3], ct_lst[4], ct_lst[5], ct_lst[6])
            excel_file.writerow(vals)
        #return file_name

    def main(self):
        self.check_options()
        sources = self.source.split(',')
        csv_lst = []
        conn, cursor = self.create_cursor(self.ip, 'TICKETBOOKINGDB')
        if not self.ensure_db_exists(self.ip, 'TICKETBOOKINGDB'):
			print 'Enter valid DB'
			pass
	html_table = '<html>'
        for source in sources:
            _dict = self.get_db_data(cursor, source)
            if not _dict: continue
            excel_file, file_name, oupf = self.open_excel_files(source)
            excel_file.writerow(self.headers)
            self.get_cvs_file(_dict, source, excel_file)
	    oupf.close()
            csv_lst.append(file_name)
	    html_table = self.get_html_report_table(cursor, source, html_table)
	html_table += '</html>\n'
        self.send_mails(csv_lst, html_table)
        self.move_csv_file()
	
if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--source-name', default='', help = 'sourcename')
    (options, args) = parser.parse_args()
    ScrapperReports(options)
