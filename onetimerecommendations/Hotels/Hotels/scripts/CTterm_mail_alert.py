import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from auto_input import *
import MySQLdb
import datetime
import json

class Sendmail(object):
    
    def __init__(self):
        self.con = MySQLdb.connect(db    = PROD_META_DB,
                                    user              = "root",
                                    passwd            = DB_PASSWORD,
                                    charset           = "utf8",
                                    host              = "localhost",
                                    use_unicode       = True)
        self.cur = self.con.cursor()
        query = "select count(ctthotelid) from Cleartrip where created_on between concat(curdate(),' 00:30:00') and concat(curdate(), ' 01:50:00');"
        self.cur.execute(query)
        self.ua_list = self.cur.fetchall()

    
    
    def send_mails(self):
        
        recievers_list = ['chlskiranmayi@gmail.com']
        sender, receivers  = 'chlskiranmayi@gmail.com', ','.join(recievers_list)
        msg = MIMEMultipart('alternative')
        if self.ua_list[0][0]==0:
            msg['Subject'] = 'Cleartrip Terminal Availability on %s'%(str(datetime.datetime.now().date()))
            mas = '<h2>Cleartrip - Source table data fails to load :</h2>'
            mas+= '<h2> Please check the logs files once.</h2>' 
            msg['From'] = sender
            msg['To'] = receivers
            tem = MIMEText(''.join(mas), 'html')
            msg.attach(tem)

        else:
            msg['Subject'] = 'Cleartrip  Terminal Availability on %s'%(str(datetime.datetime.now().date()))
            mas = '<h2>Cleartrip -Source table  data is loading successfully. </h2>'
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


    def main(self):
        self.send_mails()


if __name__ == '__main__':
            Sendmail().main()
