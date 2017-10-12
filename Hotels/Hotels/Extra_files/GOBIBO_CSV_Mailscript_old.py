import os
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import MySQLdb
import datetime
import json

class Sendmail(object):
    
    def __init__(self):
	try:

		self.CSV_PATH="/NFS/data/HOTELS_SCRAPED_DATA/GOIBIBO/"
		self.mydir = os.path.join(self.CSV_PATH, datetime.datetime.now().strftime('%Y/%m/%d'))
		os.listdir(self.mydir)
		for csvfile in os.listdir(self.mydir):
		    if csvfile.endswith('.csv'):
			self.size=os.stat(os.path.join(self.mydir, csvfile))
		self.size.st_size

	except Exception,e:
		print str(e)


    
    
    def send_mails(self):
        
        recievers_list = ['surendra@headrun.com','sowjanya@headrun.com']
        sender, receivers  = 'kattababu@gmail.com', ','.join(recievers_list)
        msg = MIMEMultipart('alternative')
        if self.size.st_size <= 455:
            msg['Subject'] = 'GOIBOBO CSV Sheet Availability'
            mas = '<h2> GOIBIBO CSV SHEET is not loaded data:</h2>'
            mas+= '<h2> Please check the logs files once.</h2>' 
            msg['From'] = sender
            msg['To'] = receivers
            tem = MIMEText(''.join(mas), 'html')
            msg.attach(tem)

        else:
            msg['Subject'] = 'GOIBIBO CSV Sheet  Availability'
            mas = '<h2> GOIBIBO CSV SHEET loaded data successfully. </h2>'
            msg['From'] = sender
            msg['To'] = receivers
            tem = MIMEText(''.join(mas), 'html')
            msg.attach(tem)

        s = smtplib.SMTP('smtp.gmail.com:587')
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(sender, 'Mohanrao@542')
        s.sendmail(sender, (recievers_list), msg.as_string())
        s.quit()


    def main(self):
        self.send_mails()


if __name__ == '__main__':
            Sendmail().main()
