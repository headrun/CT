import os
import csv
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import MySQLdb
import datetime
import json
import math
import operator
from os.path import getsize
from collections import OrderedDict
from auto_input import *
from itertools import chain
from datetime import timedelta
from Hotels_gather import *

class SendmailallHotels(object):
    def __init__(self):
	try:
                user = 'root' # your username
                passwd = DB_PASSWORD # your password
                host = 'localhost' # your host
                db = PROD_META_DB # database where your table is stored
                self.con = MySQLdb.connect(user=user, host=host, db=db, passwd=DB_PASSWORD)
                self.cursor = self.con.cursor()
		self.CSV_PATH = "/NFS/data/HOTELS_SCRAPED_DATA/"
		self.PROD_PATH  = "http://summary.cleartrip.com/mis_reports/scrapper/"
		self.variable, self.variable1, self.variable2, self.variable3 = Hotelsgather().main()
		val1 = self.get_digit(self.variable1[0])
		val2 = self.get_digit(self.variable[0])
		val3 = self.get_digit(self.variable2[0]) 
		val4 = self.get_digit(self.variable3[0])
		self.hotel_dict = OrderedDict()
		self.hotel_dict = {'MMT':[['0', '1', '5', '15', '25', '45', '75'], '1', '2', val1, '0', 'Makemytrip', 'mmthotelid', 'MMT'], 
			'GOIBIBO':[['0', '1', '5', '15', '25', '45', '75'], '1', '2', val2, '0', 'Goibibotrip', 'gbthotelid', 'IBIBO'],
			 'TRIPADVISOR':[['1', '5', '15', '25'], '1', '2', val3, '0', 'Tripadvisor', 'TA_hotel_id', 'TA'],
			 "TRIVAGO":[['1', '5'], '2', '2', '0', '43', 'Trivago', 'trivago_hotel_id', 'Trivago'], "BOOKING":[['0', '1', '5', '15', '25', '45', '75'], '1', '2', val4, '0', 'Booking', 'hotelid', 'BOOKING']}
		self.suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
		self.h_map_c = {"MMT":4, "GOIBIBO":4, "TRIPADVISOR":2, "TRIVAGO":3, "BOOKING":4}
		self.query2 = "select count(distinct %s) from %s  where date(modified_at)=curdate()"
		self.query3_min = "select min(modified_at) from %s.%s_crawl"
		self.query3_max = "select max(modified_at) from %s.%s_crawl"

	except Exception,e:
		print str(e)

    def get_digit(self, to_di):
	vale = ''.join(re.findall(': (\d+)', to_di))
	return vale
	

    def __del__(self):
		self.cursor.close()
		self.con.close()

    def get_mapped_hotels_count(self, path, hotel_name):
        len_toa_li = 0
        try:
                total_lines = []
                h_filename = "%s.csv" % (hotel_name)
                with open(os.path.join(path, h_filename)) as file_obj:
                        reader = csv.reader(file_obj, delimiter=',')
                        for index, line in enumerate(reader):
                                if index != 0:
                                        total_lines.append(line[self.h_map_c[hotel_name]])
                len_toa_li = len(set(total_lines))

                print 'sucess'
        except: 
        	pass

        return len_toa_li



    def send_mails(self):
	try:
		recievers_list = ['lakshmi.c@cleartrip.com']
                ccing = ['raja@headrun.com', 'lakshmi.c@cleartrip.com',
                        'hareesh.r@cleartrip.com', 'shyam.sundar@cleartrip.com', 'diptendu.banerjee@cleartrip.com', 'ankit.r@cleartrip.com',
                        'kora.rohan@cleartrip.com', 'rajul.kukreja@cleartrip.com', 'rohit.v@cleartrip.com', 'anshul.virmani@cleartrip.com', 'rakesh.g@cleartrip.com', 'scrappers-engg@cleartrip.com'
                 ]
		sender, receivers  = 'chlskiranmayi@gmail.com', ','.join(recievers_list)
		msg = MIMEMultipart('alternative')
		msg['Subject'] = 'Hotels scraping Report on %s'%(str(datetime.datetime.now().date()))
		mas = '<h3> Details of scraping done: </h3>'
		mas += '<font face="Calibri" size="3" color = "black">'
		mas += '<table  border="1" cellpadding="0" cellspacing="0" >'
		mas+='<tr><th> Website </th><th> DX </th><th> LOS </th><th> PAX </th><th> Input Hotel count </th><th> Scraped Hotels Rate </th><th> Mapped Hotels Rate </th><th> CSV File Name </th><th>Status</th><th>File Size In MB</th><th> Total Runs Time</th><th> File Loction </th></tr>'
		for hotel_name, vendor_dta in self.hotel_dict.iteritems():
			dx, los, pax, input_hotel_count, input_city_count, table_name, hotel_id_name, prod_name = vendor_dta
			mydir = os.path.join(self.CSV_PATH, hotel_name, datetime.datetime.now().strftime('%Y/%m/%d'))
			mccount = self.get_mapped_hotels_count(mydir, hotel_name)
			hmydir = os.path.join(self.PROD_PATH, prod_name, datetime.datetime.now().strftime('%Y/%m/%d'))
			particular_files = []
			if os.path.exists(mydir):
				for csvfile in os.listdir(mydir):
					if (csvfile.endswith('.csv') and 'Inventory.csv'  not in csvfile and 'PriceDiff.csv' not in csvfile):
						if 'tripadvisor' in hotel_name.lower() and 'TRIPADVISOR' not in csvfile:
							continue
						st_sz =  (os.stat(os.path.join(mydir, csvfile)).st_size)
						mbfile= self.humansize(st_sz)
						particular_files.append((csvfile, st_sz, mbfile))
			else:
				particular_files.append(("NO FILE", '0', '0'))
			dx = ', '.join(dx)
			self.cursor.execute(self.query2 % (hotel_id_name, table_name))
			scrapped_hotels = self.cursor.fetchall()
			if scrapped_hotels:
				scrapped_hotels = scrapped_hotels[0][0]
			else:
				scrapped_hotels = 0
			self.cursor.execute(self.query3_min % (PROD_DB_NAME, table_name))
			scrapped_mintime = self.cursor.fetchall()
			self.cursor.execute(self.query3_max % (PROD_DB_NAME,table_name))
			scrapped_maxtime = self.cursor.fetchall()
			time_for_runs  = "00:00:00"
			if scrapped_mintime and scrapped_maxtime:
				the_time = (scrapped_maxtime[0][0]-scrapped_mintime[0][0]).seconds
				time_for_runs = str(timedelta(seconds=the_time))
			try:
				fil_ = ', '.join(map(operator.itemgetter(0), particular_files))
				mbfil_ = ', '.join(map(operator.itemgetter(2), particular_files))
				mas+='<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><a href="%s">Click Here</a></td></tr>' % (hotel_name, dx, los, pax, input_hotel_count, str(scrapped_hotels), str(mccount), fil_,'Ok', mbfil_, time_for_runs, hmydir)
			except:
				mas = ''
				mas = 'Error occured while fetching filename and size in the script. Please check once'
		mas+='</table>\n\n\n'
		mas += '\n<h4> Input considerations : </h4>'
		for out_va in [('Goibibo', self.variable), ('Makemytrip', self.variable1), ('Tripadvisor', self.variable2), ('Booking', self.variable3)]:
			mas += "<p align='justify'><b>For %s </b></p>" % out_va[0]
	                mas += '<table  border="1" cellpadding="0" cellspacing="0" >'
        	        mas += '<tr><th> Desc </th><th> Count </th></tr>'
			for var in out_va[1]:
				des, cou = var.split(":")
				mas+='<tr><td>%s</td><td>%s</td></tr>' % ( des, cou)
			mas+='</table>\n\n\n'
		
		msg['From'] = sender
		msg['To'] = receivers
		msg['Cc'] =",".join(ccing)
		tem = MIMEText(''.join(mas), 'html')
		msg.attach(tem)
		s = smtplib.SMTP('smtp.gmail.com:587')
		s.ehlo()
		s.starttls()
		s.ehlo()
		s.login(sender, 'Dotoday1!')
		total_mail=(recievers_list)+ ccing
		s.sendmail(sender, (total_mail), msg.as_string())
		s.quit()
	except:
		print 'script failed please check'
		pass
		

    def humansize(self, nbytes):
    	i,f = 0, ''
    	while nbytes >= 1024 and i < len(self.suffixes)-1:
        	nbytes /= 1024.
        	i += 1
    		f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    	return '%s %s' % (f, self.suffixes[i])

    def main(self):
        self.send_mails()
    
if __name__ == '__main__':
            SendmailallHotels().main()
