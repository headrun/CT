import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import MySQLdb
import datetime
import json

class Sendmail(object):
        
        def __init__(self):
                self.con = MySQLdb.connect(db    =  "WEGODB",
                      user                      = "root",
                      passwd            = '',
                      charset           = "utf8",
                      host              = "localhost",
                      use_unicode       = True)
                self.cur = self.con.cursor()
                query = "select sk, providers, aux_info, airline, departure_time, arrival_time, from_location, to_location from Availability  where is_available = 0 and date(modified_at)=curdate()"
                self.cur.execute(query)
                self.ua_list = self.cur.fetchall()

        def send_mails(self):
            if self.ua_list:
                recievers_list = ['prasadk@headrun.net']
                sender, receivers  = 'prasadk@notemonk.com', ','.join(recievers_list)
                msg = MIMEMultipart('alternative')
                msg['Subject'] = 'Wego Cleartrip Availability'
                mas = '<h2>Cleartrip - Wego Not available :</h2>' 
                mas += '<table border="1">'
                mas += '<tr><th>S.No</th><th>Airline</th><th>From</th><th>To</th><th>Departure Time</th><th>Arrival Time</th><th>Providers with Price(P), rank (R)</th>'
                _r = 1
                for i in self.ua_list:
                    json_data = json.loads(i[2])
                    ava_js_data = json.loads(json_data.get('avail_data','{}')).get('outbound_segments', [])
                    providers = []
                    provd  = json.loads(i[1])
                    for ke, va in provd.iteritems():
                        list_all = []
                        name = ke.split('_')[0]
                        price = provd[ke].get('price', '')
                        ranks = provd[ke].get('rank', '')
                        if name:
                            list_all.append("%s: " % name)
                            if price:
                                list_all.append('%s(P)' % price)
                            if ranks:
                                list_all.append('%s(R)' % ranks)
                            providers.append(', '.join(list_all).replace(': ,', ':'))
                    mas += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>' % (_r, i[3], i[6], i[7], i[4], i[5], '<>'.join(providers))
                            
                    _r += 1
                mas += '</table>\n'
                msg['From'] = sender
                msg['To'] = receivers
                tem = MIMEText(''.join(mas), 'html')
                msg.attach(tem)
                s = smtplib.SMTP('smtp.gmail.com:587')
                s.ehlo()
                s.starttls()
                s.ehlo()
                s.login(sender, 'amma@nanna')
                s.sendmail(sender, (recievers_list), msg.as_string())
                s.quit()

        def main(self):
            self.send_mails()
if __name__ == '__main__':
        Sendmail().main()
