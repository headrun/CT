'''Helper functions'''
import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.mime.multipart import MIMEMultipart
import datetime
import ast
from ConfigParser import SafeConfigParser
_cfg = SafeConfigParser()

class Helpers(object):
	
	def send_mail(self, sub='', error_msg='', config='', airline='', receiver=''):
	    _cfg.read('/root/scrapers/flights/%s_airline_names.cfg' % config)
            recievers_list = []
            if 'Login' in sub:
                recievers_list = ast.literal_eval(_cfg.get('%s' % receiver, 'login_recievers_list'))
                import way2sms
                obj = way2sms.sms('9442843049', 'bhava')
                phones = ast.literal_eval(_cfg.get('%s' % receiver, 'phones'))
                for i in phones:
                    sent = obj.send(i, 'Unable to login to %s %s, Please check' % (airline, config))
                    if sent:
                        print 'Sent sms successfully'
            recievers_list = ast.literal_eval(_cfg.get('%s' % receiver, 'recievers_list'))
            sender, receivers = 'ctmonitoring17@gmail.com', ','.join(recievers_list)
            ccing = []
            msg = MIMEMultipart('alternative')
            msg['Subject'] = '%s %s PROD : %s On %s'%(airline, config, sub, str(datetime.datetime.now().date()))
            mas = '<p>%s</p>' % error_msg
            msg['From'] = sender
            msg['To'] = receivers
            msg['Cc'] = ','.join(ccing)
            tem = MIMEText(''.join(mas), 'html')
            msg.attach(tem)
            s =  smtplib.SMTP('smtp.gmail.com:587')
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(sender, 'ctmonitoring@123')
            s.sendmail(sender, (recievers_list + ccing), msg.as_string())
            s.quit()		

if __name__ == '__main__':
	Helpers().send_mail(receiver='indigo_common', config='splitcancel')

