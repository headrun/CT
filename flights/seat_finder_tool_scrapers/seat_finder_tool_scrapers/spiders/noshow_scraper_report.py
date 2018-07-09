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

class SendMail_ScraperReport:
    
    def main(self):
	recievers_list = ['sathwick.katta@cleartrip.com']
        sender, receivers  = 'ctmonitoring17@gmail.com', ','.join(recievers_list)
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'No Show - Scraper Report on %s'%(str(datetime.datetime.now().date()))
        mas= '<table border="1">'
        mas+='<tr><th>Count</th><th>Error message</th><th>Airline</th><th>Status</th>'

	conn = MySQLdb.connect(user='root',host='localhost', db='SEATFINDERDB', passwd='root')
        conn.set_character_set('utf8')
        cursor = conn.cursor()
        cursor.execute('SET NAMES utf8;')
        cursor.execute('SET CHARACTER SET utf8;')
        cursor.execute('SET character_set_connection=utf8;')
	
	todays_date = datetime.date.today().strftime("%Y-%m-%d")
        yesterdays_date = (datetime.date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        todays_time_to_check = todays_date + ' '+ '16:30:00'
        yesterdays_time_to_check = yesterdays_date + ' '+ '17:30:00'

	#db_records = "select count(*), error_message,airline,status  from seat_finder where created_at between '2018-05-31 17:30:00' and '2018-06-01 16:00:00' group by error_message,airline,status;"
	db_records = "select count(*), error_message,airline,status  from seat_finder where created_at between '%s' and '%s' group by error_message,airline,status;"%(yesterdays_time_to_check,todays_time_to_check)
  	cursor.execute(db_records)
	rows =cursor.fetchall()
	for row in rows:
		self.count, self.error_message,self.airline, self.status = row
		mas+='<tr><td><center>%s</center></td><td><center>%s</center></td><td><center>%s</center></td><td><center>%s</center></td>' % (self.count,self.error_message,self.airline,self.status)
	mas+='</table>\n'
        msg['From'] = sender
        msg['To'] = receivers
        tem = MIMEText(''.join(mas), 'html')
        msg.attach(tem)
        s = smtplib.SMTP('smtp.gmail.com:587')
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(sender, 'ctmonitoring@123')
        total_mail=(recievers_list)
        s.sendmail(sender, (total_mail), msg.as_string())
        s.quit()

if __name__ == '__main__':
	SendMail_ScraperReport().main()
