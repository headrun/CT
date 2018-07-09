'''Indigo split cancellation helper functions'''
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

class IndigoSCancel(object):

	def journey_check(self, journey_details):
		all_segments = self.cancellation_dict['details'][0]['all_segment_details']
		journey_check = True
		journ_details = filter(None, [i.xpath('.//td') for i in journey_details])
		for index, i in enumerate(journ_details):
			travel_date = datetime.datetime.strptime(''.join(i[0].xpath('./text()').extract()), '%d %b %y').strftime('%d-%b-%y')
			flight_no = ''.join(i[1].xpath('./text()').extract())
			flight_no = ' '.join(re.findall('(6E).*\s(\d+)', flight_no)[0])
			departure_time = ''.join(i[6].xpath('./text()').extract())
			arrival_time = ''.join(i[-1].xpath('./text()').extract())
			#Compare with self.cancellation_dict of original all_segment_details.
			#Cancelled_segment_details and all_segment_details will  be equal always.
			site_travel_datetime = travel_date + ' ' + departure_time
			json_segments_datetime = all_segments[index]['departure_date'] + ' '+ all_segments[index]['departure_time']
			if not (datetime.datetime.strptime(site_travel_datetime, '%d-%b-%y %H:%M') >= datetime.datetime.strptime(json_segments_datetime, '%d-%b-%y %H:%M') - timedelta(hours = 1) and datetime.datetime.strptime(json_segments_datetime, '%d-%b-%y %H:%M')>= datetime.datetime.strptime(site_travel_datetime, '%d-%b-%y %H:%M') - timedelta(hours = 2)):
				self.log.debug('flight delayed more than expected or preponed less than expected %s %s' % (departure_time, arrival_time))
				#% (all_segments[index]['departure_date'], travel_date))
                                self.journey_mismatch = 'travel datetime mismatch %s %s' % (arrival_time, departure_time)
                                journey_check = True
                                break
			'''if not all_segments[index]['flight_no'] == flight_no:
				self.log.debug('flight no mismatch %s %s' % (all_segments[index]['flight_no'], flight_no))
				self.journey_mismatch = 'flight no mismatch'
				journey_check = True
				break'''
			self.log.debug('%sth index of all segments matched' % index)
			journey_check = False
		return journey_check

	def get_pcc_name(self):
		return 'indigo_' + self.cancellation_dict['details'][0].get('pcc','').upper()

	def findall_splits(self, contents):
		hdnpax_values = ''
		passengers, hdnpax = [], []
		for i in contents:
			data = i.xpath('./td/text()').extract()
			if not data: continue
			passengers.append(data)
		self.log.debug(passengers)
		persons_to_be_cancelled = self.cancellation_dict['details'][0]['cancelled_pax_details']
		for i in passengers:
			num, fname, lname = i[:3]
			name_actual = '%s %s' % (fname, lname)
			self.log.debug(name_actual)
			for j in persons_to_be_cancelled:
				name_pax = ' '.join(j[1:])
				if name_pax.upper() == name_actual.upper():
					hdnpax.append(str(num))
					break
		if hdnpax:
			hdnpax_values = ','.join(hdnpax)

		print hdnpax_values
		self.log.debug(hdnpax_values)
		return hdnpax_values

	def insert_into_table(self, mesg='', err='', cancel_amount=0, pricing_details={}):
		trip_ref = self.cancellation_dict.get('trip_ref')#'%s_%s' % (self.cancellation_dict.get('trip_ref'), main_index)
		flight_ids = [i.get('flight_no') for i in self.cancellation_dict.get('details')[0].get('all_segment_details', '')]
		vals = (trip_ref, 'indigo', self.cancellation_dict.get('details')[0].get('pnr', ''),\
				self.new_pnr,
				self.cancellation_dict.get('details')[0].get('pcc', ''),\
				str(flight_ids), err, mesg, cancel_amount, str(pricing_details), str(self.cancellation_dict), '', err, str(pricing_details),\
				str(self.cancellation_dict), cancel_amount, mesg, self.new_pnr)
		try:
			self.cur.execute(self.insert_query, vals)
		except Exception as e:
			print 'some insert error'
                        self.log.debug('Some insert error %s\n%s\n%s' % (e, self.insert_query, vals))
                        self.conn.commit()
