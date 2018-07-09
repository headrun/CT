'''Flights GoAir Support functions'''
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.mime.multipart import MIMEMultipart
import datetime
import MySQLdb
import ast
import re
from collections import Counter
from ConfigParser import SafeConfigParser
_cfg = SafeConfigParser()
_cfg.read('/root/scrapers/flights/amend_airline_names.cfg')

class AirAsiaAmendUtils(object):

    def get_pcc_name(self):
        return 'airasia_' + self.booking_dict['details'][0].get('pcc','')

    def insert_error(self, pnr='', mesg='', err='', tolerance='', f_no='', a_price='', p_details='{}'):
        trip_id = self.booking_dict['trip_ref']
        trip_type = self.booking_dict['trip_type']
        print mesg, err
        return
        if not f_no:
            f_no = [self.ow_flight_nos, self.rt_flight_nos]
            f_no = '<>'.join(f_no)
        vals = (trip_id, 'AirAsia', pnr, f_no, origin, destination, trip_type, self.ct_price, a_price, mesg, tolerance, ow_date, rt_date, err, str(self.booking_dict), str(p_details), pnr, f_no, a_price, mesg,  err, str(self.booking_dict), str(p_details))
        try:
            self.cur.execute(self.insert_query, vals)
        except Exception as e:
            print "some insert error"
            self.log.debug('some insert error: %s' % e)
        self.conn.commit()


    def check_tolerance(self, ctprice, airasiaprice):
        tolerance_value, is_proceed = 0, 0
        total_fare = float(airasiaprice.replace(',', ''))
        if total_fare != 0:
            tolerance_value = total_fare - float(ctprice.replace(',', ''))
            if tolerance_value >= float(self.booking_dict.get('tolerance_amount', '5000')):#2000:
                is_proceed = 0  #movie it to off line
            else: is_proceed = 1
        else:
            tolerance_value, is_proceed = 0, 0
        print tolerance_value, is_proceed
        return (tolerance_value, is_proceed)

    def get_flight_fares(self, nodes, fares_dict={}):
        for node in nodes:
            fares_ = {}
            flight_text = ''.join(node.xpath('.//div[@class="scheduleFlightNumber"]//span[@class="hotspot"]/@onmouseover').extract())
            if not flight_text:
                flight_text = ''.join(node.xpath('.//div[@class="scheduleFlightNumber"]//div[@class="hotspot"]/@onmouseover').extract())
            if flight_text:
                flt_ids = re.findall('<b>(.*?)</b>', flight_text)
                if flt_ids: flt_id = '<>'.join(flt_ids).replace(' ', '').strip()
                else: flt_id = ''
            else: flt_id = ''
            for i in range(2, 6):
                fare_cls = ''.join(node.xpath('./..//th[%s]//div[contains(@class, "fontNormal")]//text()'%i).extract()).replace(' ', '').strip()
                fare_id = ''.join(node.xpath('.//td[%s]//div[@id="fareRadio"]//input/@id'%i).extract())
                fare_name = ''.join(node.xpath('.//td[%s]//div[@id="fareRadio"]//input/@name'%i).extract())
                fare_vlue = ''.join(node.xpath('.//td[%s]//div[@id="fareRadio"]//input/@value'%i).extract())
                price = '<>'.join(node.xpath('.//td[%s]//div[@class="price"]//div[@id="originalLowestFare"]//text()'%i).extract())
                if fare_id:
                    fares_.update({fare_cls:(fare_id, fare_name, fare_vlue, price)})
            if flt_id:
                fares_dict.update({flt_id:fares_})
        return fares_dict

    def get_fin_fares_dict(self, flight_fares, ct_flights):
        '''
        returing the requested flight details
        '''
        aa_keys = flight_fares.keys()
        fin_fare_dict, flight_no = {}, ''
        for key in aa_keys:
            key_actual = '<>'.join(set(key.split('<>')))
            flt_status_key, rank = False, 0
            ctflights = '<>'.join(ct_flights).replace(' ', '').replace('-', '').strip()
            if ctflights.lower() == str(key_actual.lower()):
                flt_status_key = True
                rank = rank + 1
                fin_fare_dict = flight_fares.get(key, {})
                flight_no = key
                break
            else:
                flt_status_key = False
        print fin_fare_dict, flight_no
        return (fin_fare_dict, flight_no)

    def find_oneway_details(self):
        day, year_mon, orig, dest, status = '', '', '', '', 1
        try:
            details = self.booking_dict['details'][0]['amend_segment_details']
            dep_date = details[0]['departure_date']
            orig = details[0]['segment_src']
            if len(details) == 2:
                dest = details[1]['segment_dest']
            elif len(details) == 1:
                dest = details[0]['segment_dest']
            dep_date = datetime.datetime.strptime(dep_date, '%d-%b-%y').strftime('%d-%m-%Y')
            day, year_mon = dep_date.split('-')[0], '-'.join(dep_date.split('-')[:0:-1])
            self.booking_dict['onewayflightid'] = filter(None, [j['flight_no'] if j['flight_no'] else '' for j in filter(None, [i if i['seq_no']=='1' else '' for i in details])])
            self.booking_dict['onewayclass'] = self.booking_dict['cabin_class']#filter(None, [j['class'] if j['class'] else '' for j in filter(None, [i if i['seq_no']=='1' else '' for i in details])])[0]

        except Exception as e:
            self.log.debug(e)
            status = 0
        return day, year_mon,  dest, orig, status

    def find_rt_details(self):
        day1, year_mon1, dest1, org1, day2, year_mon2, dest2, org2 = [''] * 8
        status = 1
        try:
            details = self.booking_dict['details'][0]['amend_segment_details']
            ow_details = filter(None, [i if i['seq_no']=='1' else '' for i in details])
            rt_details = filter(None, [i if i['seq_no']=='2' else '' for i in details])
            dep_date1 = ow_details[0]['departure_date']
            dep_date2 = rt_details[0]['departure_date']
            org1 = ow_details[0]['segment_src']
            org2 = rt_details[0]['segment_src']
            dest1 = ow_details[0]['segment_dest']
            if len(ow_details) == 2:
                dest1 = ow_details[1]['segment_dest']
            dest2 = rt_details[0]['segment_dest']
            if len(rt_details)==2:
                dest2 = rt_details[1]['segment_dest']
            dep_date1 = datetime.datetime.strptime(dep_date1, '%d-%b-%y').strftime('%d-%m-%Y')
            dep_date2 = datetime.datetime.strptime(dep_date2, '%d-%b-%y').strftime('%d-%m-%Y')
            day1, year_mon1 = dep_date1.split('-')[0], '-'.join(dep_date1.split('-')[:0:-1])
            day2, year_mon2 = dep_date2.split('-')[0], '-'.join(dep_date2.split('-')[:0:-1])
            self.booking_dict['onewayflightid'] = filter(None, [j['flight_no'] if j['flight_no'] else '' for j in filter(None, [i if i['seq_no']=='1' else '' for i in details])])
            self.booking_dict['onewayclass'] = self.booking_dict['cabin_class']#filter(None, [j['class'] if j['class'] else '' for j in filter(None, [i if i['seq_no']=='1' else '' for i in details])])[0]
            self.booking_dict['returnflightid'] = filter(None, [j['flight_no'] if j['flight_no'] else '' for j in filter(None, [i if i['seq_no']=='2' else '' for i in details])])
            self.booking_dict['returnclass'] = self.booking_dict['cabin_class']#filter(None, [j['class'] if j['class'] else '' for j in filter(None, [i if i['seq_no']=='2' else '' for i in details])])[0]
        except Exception as e:
            self.log.debug(e)
            status = 0
        return day1, year_mon1, dest1, org1, day2, year_mon2, dest2, org2, status

