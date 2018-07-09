from ast import literal_eval
from collections import OrderedDict
from ConfigParser import SafeConfigParser
import copy
import datetime
from datetime import timedelta
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import MySQLdb
import re
import requests
import smtplib
import ssl
import time
import md5

class GoAirCancelUtils(object):

    def insert_into_table(self, mesg, err):
        trip_ref = self.cancel_dict.get('trip_ref')#'%s_%s' % (self.cancellation_dict.get('trip_ref'), main_index)
        flight_ids = [i.get('flight_no') for i in self.cancel_dict.get('details')[0].get('all_segment_details', '')]
        pricing_details = self.cancel_dict.get('pricing_details', {})
        cancel_amount = ''
        vals = (trip_ref, 'Goair', self.cancel_dict.get('details')[0].get('pnr', ''),\
               self.new_pnr,
               self.cancel_dict.get('details')[0].get('pcc', ''),\
               str(flight_ids), err, mesg, cancel_amount, str(pricing_details), str(self.cancel_dict), '', err, str(pricing_details),\
               str(self.cancel_dict), cancel_amount, mesg, self.new_pnr)
        try:
            self.cur.execute(self.insert_query, vals)
        except:
            print 'some insert error'
            self.conn.commit()

    def get_pcc_name(self):
        if not self.cancel_dict:
            error = 'Empty Request'
            return ('', {'error':error})
        try:
            self.cancel_dict = eval(self.cancel_dict)
        except:
            error = 'Wrong input format'
            return ('', {'error':error})
        pcc_name = 'GOAIR_' + self.cancel_dict['details'][0].get('pcc','').upper()
        cancellation_type = self.cancel_dict['details'][0].get('cancellation_type', '').get('type', '')
        self.cancel_dict['pcc_name'] = pcc_name
        self.cancel_dict['cancel_type'] = cancellation_type
        return (pcc_name)

    def split_pax_value(self, split_pax_dict):
        hq_pax_names = [' '.join(i[1:]).lower().replace(' ', '').strip() for i in self.cancel_dict['details'][0]['cancelled_pax_details']]
        vals_list = [split_pax_dict[i] for i in hq_pax_names]
        #cnl_pax = [i for i in split_pax_dict.keys() if i not in vals_list]
        return vals_list

    def check_dup_pax(self):
        pax_names = [''.join(i[1:]) for i in self.cancel_dict['details'][0]['all_pax_details']]
        if len(set(pax_names)) != len(pax_names):
            dupe_pax = True
        else:
            dupe_pax = False
        return dupe_pax

    def check_segments(self, outbound_date, ow_flight_details):
        site_details = self.cancel_dict.get('site_details', {})
        seg_src, seg_dest, dep_date = ['']*3
        ow_all_segs = []
        for i in self.cancel_dict['details'][0].get('all_segment_details', []):
            ow_check = i.get('seq_no', '')
            if ow_check == 1 or ow_check == '1':
                ow_all_segs.append(i)
        for idx, seg in enumerate(ow_all_segs):
            segment_src = seg.get('segment_src', '')
            segment_dest = seg.get('segment_dest', '')
            departure_date = seg.get('departure_date', '')
            departure_time = seg.get('departure_time', '')
            if idx == 0:
                seg_src = segment_src
                dep_date = '%s %s'%(departure_date, departure_time)
            seg_dest = segment_dest
        site_origin = site_details.get('site_origin')
        site_dest = site_details.get('site_dest', '')
        if site_origin != seg_src or seg_dest != site_dest:
            seg_check = True
        else:
            seg_check = False
        if ow_flight_details:
            try: ow_dept_time = ow_flight_details[1]
            except:
                ow_dept_time = ''
                error = "flight depart tine not found"
        else:
            ow_dept_time = ''
            error = "flight depart tine not found"
        site_travel_datetime = "%s %s"%(outbound_date, ow_dept_time)
        json_segments_datetime = dep_date#all_segments[0]['departure_date'] + ' '+ all_segments[0]['departure_time']
        if not (datetime.datetime.strptime(site_travel_datetime, '%d %b %Y %H:%M') >= datetime.datetime.strptime(json_segments_datetime, '%d-%b-%y %H:%M') - timedelta(hours = 2) and datetime.datetime.strptime(json_segments_datetime, '%d-%b-%y %H:%M')>= datetime.datetime.strptime(site_travel_datetime, '%d %b %Y %H:%M') - timedelta(hours = 1)):
                self.log.debug('flight delayed more than expected or preponed less than expected')
                #% (all_segments[index]['departure_date'], travel_date))
                journey_check = True #'travel datetime mismatch'
        else:
                journey_check = False
        return (seg_check, journey_check)

    def check_flight_ids(self, site_flight_ids):
        flight_check = False
        #hq_flight_nos = [i[0]['flight_no'] for i in [i.values()[0]['segments'] for i in cancel_dict['all_segments']]]
        hq_flight_nos = []
        for seg in self.cancel_dict['details'][0].get('all_segment_details', []):
            flight_id = seg.get('flight_no', '')
            hq_flight_nos.append(flight_id)
        for index, i in enumerate(site_flight_ids):
            if i.replace(' ', '') != hq_flight_nos[index].replace(' ', ''):
                print "flight numbers mismatch"
                flight_check = True
                break
        return flight_check

    def check_pax_details(self, site_pass_names):
        passengers_check, counter = False, 0
        hq_pass_names = [' '.join(i[1:]).title().strip() for i in self.cancel_dict['details'][0]['all_pax_details']]
        pass_names = [i.split(' ', 1)[1].title() for i in site_pass_names]
        allhq_names = len(hq_pass_names)
        if len(pass_names) != len(set(hq_pass_names)):
            duplicate_pax = True
        else:
            duplicate_pax = False
        for i in hq_pass_names:
            for j in pass_names:
                if i.title() == j.title():
                    counter += 1
                    break
        if counter != allhq_names:
            passengers_check = True
        return (passengers_check, duplicate_pax)
