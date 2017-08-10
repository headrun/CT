import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ast import literal_eval
from email.mime.base import MIMEBase
from datetime import datetime
from email import encoders
import smtplib,ssl
import MySQLdb
import optparse
import datetime
import json
import csv
import sys
import os

class SendCSVmail(object):
        
    def __init__(self, options):
	self.source = options.source_name
        self.ip     = 'localhost'
	self.csv_path = '/root/headrun/CTmonitoring/CTmonitoring/scripts/csv_processing'
	self.csv_mv_path = '/root/headrun/CTmonitoring/CTmonitoring/scripts/csv_file'
        self.data_query = "select sk, flight_id, providers, airline, dx, no_of_passengers, departure_time, arrival_time, from_location, to_location, return_airline, return_flight_id, return_departure_time from RTAvailability where date(modified_at) = curdate()-1"
	self.header_params = ["Flight number", "Airline", "Origin", "Destination", "Departure date", "Return Departure date", "Retuen Flight number", "Dx", "No.of Passengers", "Price b/w CT and OTA", "Cleartrip-Price" ,"Cleartrip-Rank", "Sastiticket-Price", "Sastiticket-Rank", "Easemytrip-Price", "Easemytrip-Rank", "Cheapticket-Price", "Cheapticket-Rank", "in.via-Price", "in.via-Rank", "ezeego1-Price", "ezeego1-Rank", "in.musafir-Price", "in.musafir-Rank", "Smartfares-Price", "Smartfares-Rank", "in.airtickets-Price", "in.airtickets-Rank",  "Travelgenio-Price", "Travelgenio-Rank", "Traveasy-Price", "Traveasy-Rank", "Jetairways-Price", "Jetairways-Rank", "Kiwi-Price", "Kiwi-Rank", "Mytrip-Price", "Mytrip-Rank"]

	self.main()

    def check_options(self):
        if not self.source or not self.ip:
            print "Souce, Db and Ip cant be empty. For more check python send_csv_mail.py --help"
            sys.exit(-1)

    def open_excel_files(self, source):
	os.chdir(self.csv_path)
	excel_file_name = 'cleartrip_monitoring_%s_avail_%s.csv'%(str(datetime.datetime.now().date()), source)
	oupf = open(excel_file_name, 'ab+')
	todays_excel_file  = csv.writer(oupf)
	return (todays_excel_file, excel_file_name)

    def get_compressed_file(self):
	os.chdir(self.csv_path)
	gz_file = 'cleartrip_monitoring_roundtrip_avail_%s.tar.gz'%str(datetime.datetime.now().date())
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
            recievers_list = ['sudhir.mantena@cleartrip.com']
	    #recievers_list = ["prasadk@notemonk.com"]
            sender, receivers  = 'prasadk@notemonk.com', ','.join(recievers_list)
	    
	    ccing = ['aravind@headrun.com', 'raja@headrun.com',
			'cleartrip@headrun.com','hareesh.r@cleartrip.com',
			'pallav.singhvi@cleartrip.com', 'chetan.sharma@cleartrip.com',
			'adhvaith.h@cleartrip.com', 'deepak.sharma@cleartrip.com',
			'ashwin.d@cleartrip.com'
		     ]
	    
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Cleartrip - Monitoring Availability On %s'%(str(datetime.datetime.now().date()))
            mas = '<h2>Cleartrip - Monitoring Availability on Round Trip</h2>'
	    
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

    def get_cvs_file(self, records, source):
	excel_file, file_name = self.open_excel_files(source)
	fin_recs = []
        for rec in records:
	    pro_lst = []
	    sk, flight_id, providers, airline, dx, no_of_passengers, \
		departure_time, arrival_time, from_location, to_location, \
			return_airline, return_flight_id, return_departure_time = rec
	    ct_price, ct_rank, least_price, price_diff = ['']*4
	    pd_dict= {
                        "sastiticket":{}, "easemytrip":{}, "cheapticket":{}, "via":{},
                        "ezeego1":{}, "musafir":{}, "smartfares":{}, "airtickets":{},
                        "travelgenio":{}, "traveasy":{}, "cleartrip":{}, "jetairways":{},
                        "mytrip":{}, "kiwi":{}, "budgetair":{}, "bravofly":{},
			"ebookers":{}, "gotogate":{}, "tripair":{}, "flightnetwork":{},
			"kayak":{}, "yatra":{},
                }

	    if providers:
	        pro_ = json.loads(providers)
		pr_list, least_price = {}, ''
		#pro_ = literal_eval(pro_)
		keys = pro_.keys()
		for i in keys:
		    for prov in pd_dict.keys():
			price_ = pro_.get(i, {})
			if prov.replace(' ', '').lower().strip() in i.replace(' ', '').lower().strip():
			    pd_dict.update({prov:pro_.get(i, {})})
		            if 'cleartrip' in i.lower():
			        ct_price, ct_rank = price_.get('price', ''), price_.get('rank', '')
		        if int(price_.get('rank', 0)) == 1:
			    least_price = price_.get('price', '')
			pr_list.update({price_.get('rank', 0):price_.get('price', '')})
		if not least_price:
		    least_price = str(pr_list.get(2, '0')).replace(',', '').strip()
	    if ct_price and least_price:
	        price_diff = str(float(str(least_price).replace(',', '')) - float(str(ct_price).replace(',', '')))
	    if ct_rank == '': ct_rank = 'NA'
	    fin_recs.append((flight_id, airline, from_location, to_location, str(departure_time),
				str(return_departure_time), str(return_flight_id), dx, no_of_passengers,
				price_diff, pd_dict.get('cleartrip', {}).get('price', 'NA'), pd_dict.get('cleartrip', {}).get('rank', 'NA'),
				pd_dict.get('sastiticket', {}).get('price', ''), pd_dict.get('sastiticket', {}).get('rank', ''),
				pd_dict.get('easemytrip', {}).get('price', ''), pd_dict.get('easemytrip', {}).get('rank', ''),
				pd_dict.get('cheapticket', {}).get('price', ''),pd_dict.get('cheapticket', {}).get('rank', ''),
				pd_dict.get('via', {}).get('price', ''), pd_dict.get('via', {}).get('rank', ''),
				pd_dict.get('ezeego1', {}).get('price', ''), pd_dict.get('ezeego1', {}).get('rank', ''),
				pd_dict.get('musafir', {}).get('price', ''), pd_dict.get('musafir', {}).get('rank', ''),
				pd_dict.get('smartfares', {}).get('price', ''), pd_dict.get('smartfares', {}).get('rank', ''),
				pd_dict.get('airtickets', {}).get('price', ''),  pd_dict.get('airtickets', {}).get('rank', ''),
				pd_dict.get('travelgenio', {}).get('price', ''), pd_dict.get('travelgenio', {}).get('rank', ''),
				pd_dict.get('traveasy', {}).get('price', ''), pd_dict.get('traveasy', {}).get('rank', ''),
				pd_dict.get('jetairways', {}).get('price', ''), pd_dict.get('jetairways', {}).get('rank', ''),
				pd_dict.get('kiwi', {}).get('price', ''), pd_dict.get('kiwi', {}).get('rank', ''),
				pd_dict.get('mytrip', {}).get('price', ''), pd_dict.get('mytrip', {}).get('rank', ''),
				
				))
	for idx, vals in enumerate(fin_recs):
	    if idx == 0:
		excel_file.writerow(self.header_params)
	    excel_file.writerow(vals)
        return file_name
		

    def main(self):
        self.check_options()

	sources = self.source.split(',')
	csv_lst = []
	for source in sources:
	    db = '%s%s'%(source.upper(), 'DB')
	    if not self.ensure_db_exists(self.ip, db):
		print 'Enter valid DB and Ip'
		pass
            conn, cursor = self.create_cursor(self.ip, db)
	    cursor.execute(self.data_query)
	    records = cursor.fetchall()
	    if records:
	        file_name = self.get_cvs_file(records, source)
		csv_lst.append(file_name)
	gz_file = self.get_compressed_file()
        self.send_mails([gz_file])
	self.move_compressed_file()
 
		
if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--source-name', default='', help = 'sourcename')
    (options, args) = parser.parse_args()
    SendCSVmail(options)

