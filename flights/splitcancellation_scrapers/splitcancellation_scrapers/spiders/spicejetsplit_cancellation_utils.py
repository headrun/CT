'''Spicejet cancellation helper functions'''
import smtplib
import json
import re
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.mime.multipart import MIMEMultipart
import datetime
from datetime import timedelta
import ast
from collections import Counter
from ConfigParser import SafeConfigParser
_cfg = SafeConfigParser()
_cfg.read('/root/scrapers/flights/splitcancel_airline_names.cfg')
findsplits_pattern = re.compile('M\w+.\s(\w+.*)\s[(].*[)]')


class SGCancel(object):

	def journey_check(self, journey_details):
		journ_details = [journey_details[x:x+6] for x in range(0, len(journey_details), 6)]
		all_segments = self.cancellation_dict['details'][0]['all_segment_details']
		journey_check = True
		for index, i in enumerate(journ_details):
			travel_date = datetime.datetime.strptime(i[0], '%a %d %b, %Y').strftime('%d-%b-%y')
			flight_no = i[1].replace(u'\xa0\r\n', '')
			flight_no = ' '.join(re.findall('(SG).*\s(\d+)', flight_no)[0])
			departure_time = i[-2]
			arrival_time = i[-1]
			#Compare with self.cancellation_dict of original all_segment_details.
			#Cancelled_segment_details and all_segment_details will  be equal always.
			site_travel_datetime = travel_date + ' ' + departure_time
			site_travel_datetime = datetime.datetime.strptime(site_travel_datetime,'%d-%b-%y %I:%M %p').strftime('%d-%b-%y %H:%M')
                        json_segments_datetime = all_segments[index]['departure_date'] + ' '+ all_segments[index]['departure_time']
                        if not (datetime.datetime.strptime(site_travel_datetime, '%d-%b-%y %H:%M') >= datetime.datetime.strptime(json_segments_datetime, '%d-%b-%y %H:%M') - timedelta(hours = 1) and datetime.datetime.strptime(json_segments_datetime, '%d-%b-%y %H:%M')>= datetime.datetime.strptime(site_travel_datetime, '%d-%b-%y %H:%M') - timedelta(hours = 2)):
                                self.log.debug('flight delayed more than expected or preponed less than expected')
                                #% (all_segments[index]['departure_date'], travel_date))
                                self.journey_mismatch = 'travel datetime mismatch'
                                journey_check = True
                                break

			'''if not all_segments[index]['flight_no'] == flight_no:
				self.log.debug('flight no mismatch  %s %s' % (all_segments[index]['flight_no'], flight_no))
				journey_check = True
				break'''

			self.log.debug('%sth index of all segments matched' % index)
			journey_check = False

		return journey_check

	def get_pcc_name(self):
		return 'spicejet_' + self.cancellation_dict['details'][0].get('pcc','').replace('spicejet_', '')

	def findall_splits(self, contents):
		url_to_send = ''
		contents = [contents[x:x+2] for x in range(0, len(contents), 2)]
		passengers = []
		persons_to_be_cancelled = self.cancellation_dict['details'][0]['cancelled_pax_details']
		#[['Mr', 'Monideep', 'Roychowdhury'],...]
		#[u'MR. Monideep Roychowdhury (ADULT,Male)', u'109855786', u'MS. Moumita Majumder (ADULT,Female)', u'109855787']
		for i in contents:
			name, num = i
			name_actual = findsplits_pattern.match(name).group(1)
			if not name_actual:
				self.log.debug("regex issue while parsing name from site")
				return
			for j in persons_to_be_cancelled:
				name_pax = ' '.join(j[1:])
				if name_pax.upper() == name_actual.upper():
					passengers.append(num)
					break
		if passengers:
			split_values = '&'.join(['passenger%s=%s' %  i for i in enumerate(passengers)])
			url_to_send = 'https://book.spicejet.com/AjaxInfo-resource.aspx?MethodName=splitpassengerlist&' + split_values
		self.log.debug('%s %s' % (passengers, url_to_send))
		return url_to_send

	def insert_into_table(self, mesg, err, cancel_amount=0, pricing_details={}):
		trip_ref = self.cancellation_dict.get('trip_ref')#'%s_%s' % (self.cancellation_dict.get('trip_ref'), main_index)
		flight_ids = str([i.get('flight_no') for i in self.cancellation_dict.get('details')[0].get('all_segment_details', '')])
		vals = (trip_ref, 'spicejet', self.cancellation_dict.get('details')[0].get('pnr', ''),\
				self.new_pnr,
				self.cancellation_dict.get('details')[0].get('pcc', ''),\
				flight_ids, err, mesg, cancel_amount, str(pricing_details), str(self.cancellation_dict), '', err, str(pricing_details),\
				str(self.cancellation_dict), cancel_amount, mesg, self.new_pnr)
		try:
			self.cur.execute(self.insert_query, vals)
		except Exception as e:
			self.log.debug('some insert error %s' % e)
	        self.conn.commit()





