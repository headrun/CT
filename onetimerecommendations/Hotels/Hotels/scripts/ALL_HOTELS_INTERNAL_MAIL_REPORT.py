import os
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import MySQLdb
import datetime
import json
import math
from os.path import getsize

class SendmailGONewIn(object):


    def __init__(self):
        try:
	
		self.CSV_PATH = "/NFS/data/HOTELS_SCRAPED_DATA/"
		self.Hotels_list = ['MMT', 'GOIBIBO', 'MMTGOICOMMON' ,'TRIPADVISOR', 'TRIVAGO', 'BOOKING']
                self.suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
                self.all_files = []
		for ho in self.Hotels_list:
			new_path = os.path.join(self.CSV_PATH, ho)
			mydir = os.path.join(new_path, datetime.datetime.now().strftime('%Y/%m/%d'))
			os.listdir(mydir)
			for csvfile in os.listdir(mydir):
			    if csvfile.endswith('.csv'):
				self.all_files.append((csvfile, (os.stat(os.path.join(mydir, csvfile)).st_size), mydir))
                        #self.csvfile=csvfile
                        #self.size=os.stat(os.path.join(self.mydir, self.csvfile))

                #self.size.st_size

        except Exception,e:
                print str(e)

    def send_mails(self):
        recievers_list = ['cleartrip@headrun.com']
        sender, receivers  = 'chlskiranmayi@gmail.com', ','.join(recievers_list)
        msg = MIMEMultipart('alternative')
        ccing = ['lakshmi.c@cleartrip.com']
        istatus = "Completed"
        msg['Subject'] = 'Hotels CSV Sheets Availability on %s'%(str(datetime.datetime.now().date()))
        mas = '<h2> CSV SHEET Details</h2>'
        mas+= '<table border="1">'
        mas+='<tr><th>File Loction</th><th>CSV File Name </th><th>File Size in Bytes</th><th>Status</th><th>File Size In MB</th>'
        for all_file in self.all_files:
                mbfile= self.humansize(all_file[1])   
                if all_file[1] <= 455:
                    istatus = "Incompleted"
                mas+='<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>' % (all_file[2],all_file[0], all_file[1], istatus, mbfile)
        mas+='</table>\n'
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

    def humansize(self, nbytes):
	f = ''
        i = 0
        while nbytes >= 1024 and i < len(self.suffixes)-1:
                nbytes /= 1024.
                i += 1
                f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
        return '%s %s' % (f, self.suffixes[i])

    def main(self):
        self.send_mails()

if __name__ == '__main__':
            SendmailGONewIn().main()
