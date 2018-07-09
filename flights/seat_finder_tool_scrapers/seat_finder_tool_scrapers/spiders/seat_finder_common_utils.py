'''Flights Indigo Support functions'''
import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.mime.multipart import MIMEMultipart
import datetime
import ast
from ConfigParser import SafeConfigParser
_cfg = SafeConfigParser()
_cfg.read('../../../seat_finder_names.cfg')

class CommonUtils(object):
	def send_mail(self, sub, error_msg=''):
		receivers_list = ast.literal_eval(_cfg.get('nocsv_common', 'receivers_list'))
		sender, receivers = 'ctmonitoring17@gmail.com', ','.join(receivers_list)
		ccing = ['sathwick.katta@cleartrip.com']
		msg = MIMEMultipart('alternative')
		msg['Subject'] = 'NoShow/SeatFinder CSV Downloader on %s: %s found'%(str(datetime.datetime.now().date()),sub)
		mas = '<p>%s</p>' % error_msg
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
		s.sendmail(sender, (receivers_list + ccing), msg.as_string())
