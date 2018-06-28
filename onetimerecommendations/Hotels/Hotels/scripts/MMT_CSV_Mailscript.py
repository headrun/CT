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

class Sendmail(object):
	
    
    def __init__(self):
	try:

		self.CSV_PATH="/NFS/data/HOTELS_SCRAPED_DATA/MMT/"
		self.mydir = os.path.join(self.CSV_PATH, datetime.datetime.now().strftime('%Y/%m/%d'))
		os.listdir(self.mydir)
		self.suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
		for csvfile in os.listdir(self.mydir):
		    if csvfile.endswith('.csv'):
			self.csvfile=csvfile
			self.size=os.stat(os.path.join(self.mydir, self.csvfile))
		self.size.st_size

	except Exception,e:
		print str(e)


    
    
    def send_mails(self):
        
        recievers_list = ['chlskiranmayi@gmail.com']
        sender, receivers  = 'chlskiranmayi@gmail.com', ','.join(recievers_list)
        msg = MIMEMultipart('alternative')
	mbfile= self.humansize(self.size.st_size)
        if self.size.st_size <= 455:
	    istatus = "Incompleted"
            msg['Subject'] = 'MMT CSV Sheet Availability on %s'%(str(datetime.datetime.now().date()))
            mas = '<h2> MMT CSV SHEET is not uploaded successfully:</h2>'
            mas+= '<h2> Please check the logs files once.</h2>' 
	    mas+= '<table border="1">'
	    mas+='<tr><th>File Loction</th><th>CSV File Name </th><th>File Size in Bytes</th><th>Status</th><th>File Size In MB</th>'
	    mas+='<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>' % (self.mydir,self.csvfile,self.size.st_size,istatus,mbfile)
	    mas+='</table>\n'
	    msg['From'] = sender
            msg['To'] = receivers
            tem = MIMEText(''.join(mas), 'html')
            msg.attach(tem)

        else:
	    cstatus='Completed'
            msg['Subject'] = 'MMT CSV Sheet  Availability on %s'%(str(datetime.datetime.now().date()))
            mas = '<h2> MMT CSV SHEET uploaded successfully. </h2>'
	    mas+= '<table border="1">'
	    mas+='<tr><th>File Loction</th><th>CSV File Name </th><th>File Size in Bytes</th><th>Status</th><th>File Size In MB</th>'
	    mas+='<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>' % (self.mydir,self.csvfile,self.size.st_size,cstatus,mbfile)
	    mas+='</table>\n'
            msg['From'] = sender
            msg['To'] = receivers
            tem = MIMEText(''.join(mas), 'html')
            msg.attach(tem)

        s = smtplib.SMTP('smtp.gmail.com:587')
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(sender, 'Dotoday1!')
	total_mail=(recievers_list)
        s.sendmail(sender, (total_mail), msg.as_string())
        s.quit()

    def humansize(self, nbytes):
    	i = 0
    	while nbytes >= 1024 and i < len(self.suffixes)-1:
        	nbytes /= 1024.
        	i += 1
    		f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    	return '%s %s' % (f, self.suffixes[i])

    def main(self):
        self.send_mails()
    



if __name__ == '__main__':
            Sendmail().main()
