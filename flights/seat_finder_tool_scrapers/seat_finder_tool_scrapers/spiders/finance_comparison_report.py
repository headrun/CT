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
from datetime import timedelta

class SendMail_FinanceCalledReport:
    
    def main(self):
	recievers_list = ['sathwick.katta@cleartrip.com']
        sender, receivers  = 'ctmonitoring17@gmail.com', ','.join(recievers_list)
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'No Show: Finance-Agent_Called Comparison Report on %s'%(str(datetime.datetime.now().date()))
        mas= '<table border="1">'
        mas+='<tr><th>Booking No</th><th>PNR</th><th>Airline</th><th>PCC</th><th>Ticket No</th><th>Agent</th><th>Agent Calling Status</th><th>Agent Actioned Date</th><th>Finance Amount</th><th>Agent Amount</th>'

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

	db_records = "select sk,pnr, airline,pcc, ticket_number, agent, agent_calling_status, agent_action_date, finance_amount, agent_amount from discrepancy where created_at between '%s' and '%s'"%(yesterdays_time_to_check,todays_time_to_check)
  	cursor.execute(db_records)
	rows =cursor.fetchall()
	for row in rows:
		booking_no, pnr, airline,pcc, ticket_number, agent, agent_calling_status, agent_action_date, finance_amount, agent_amount = row
		mas+='<tr><td><center>%s</center></td><td><center>%s</center></td><td><center>%s</center></td><td><center>%s</center></td><td><center>%s</center></td><td><center>%s</center></td><td><center>%s</center></td><td><center>%s</center></td><td><center>%s</center></td><td><center>%s</center></td>' % (booking_no, pnr, airline,pcc, ticket_number, agent, agent_calling_status, agent_action_date, finance_amount, agent_amount)
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
	SendMail_FinanceCalledReport().main()
