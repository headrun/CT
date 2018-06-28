import MySQLdb
import json
from auto_input import *
import sys
import csv
sys.path.insert(0, '../')
from blacklist_properties import total_blacklist_properties, duplicates_mmt_ct_list

class HotelsUnique(object):
        def __init__(self):
                user = 'root' # your username
                passwd = DB_PASSWORD # your password
                host = 'localhost' # your host
                db = PROD_META_DB # database where your table is stored
                self.con = MySQLdb.connect(user=user, host=host, db=db, passwd=DB_PASSWORD)
                self.cursor = self.con.cursor()
		for hotels in ['Cleartrip_hotels',  'Goibibotrip_hotels', 'Makemytrip_hotels', 'Tripadvisor_hotels', 'Booking_hotels']:
			self.cursor.execute("delete from %s" % hotels)
		self.mmt_ct_ids_list_check = []
		with open('../spiders/SampleCITY.json') as json_data:
		    self.dsample = json.load(json_data)
		    for d_city_name, d_hotel_id in self.dsample.iteritems():
			for d_hotel_ids, d_hotel_details in d_hotel_id.iteritems():
			    ct_mmt_id = d_hotel_details[2]
			    self.mmt_ct_ids_list_check.append(ct_mmt_id)
		self.check_mmt_listb = []
		with open('../spiders/csv_file/Bookingdotcom_mapping_file.csv') as bcsvfile:
		    all_linesb = csv.reader(bcsvfile, delimiter=',')
		    all_linesb = [icsv for icsv in all_linesb]
		    for hotel_id_, b_h_url_, ct_h_id_, ta_h_id_, hotel_name_, ta_url_, b_h_name_, city_name_ in all_linesb[1:]:
			self.check_mmt_listb.append(ct_h_id_)



        def __del__(self):
		self.cursor.close()

        def clean(self, text):
		text = text.strip()
		return text

        def main(self):
		ta_urls_data, ta_urls_data1, ta_urls_data2, ta_urls_data3, ta_urls_data4 = {}, {}, {}, {}, {}
                with open('../spiders/City_H_IDNS.json') as fp:
                	d = json.load(fp)
			for city_name,h_ids in d.iteritems():
				for h_id,hotel_name in h_ids.iteritems():
					if h_id not in total_blacklist_properties:
						ta_urls_data.update({self.clean(h_id): [self.clean(city_name), self.clean(hotel_name)]})
		for key, value in ta_urls_data.iteritems():
			city_name, hotel_name = value 
			try:self.cursor.execute('INSERT INTO Cleartrip_hotels(hotel_id, city_name, hotel_name, created_on) values ("%s", "%s", "%s", now())' % (self.clean(key), self.clean(city_name), self.clean(hotel_name)))
			except:
				print h_id
		print len(ta_urls_data.keys()), 'cleartrip'
		with open('../spiders/GoiboCity_codes.json') as fg:
			dg = json.load(fg)
			for city_name,hotel_details in dg.iteritems():
				for hotel_id,hotel_data in hotel_details.iteritems():
					hotel_name=hotel_data[0]
					hotel_cgoi_id = hotel_data[-1]
					if (hotel_cgoi_id not in total_blacklist_properties) and (hotel_cgoi_id not in self.mmt_ct_ids_list_check):
						ta_urls_data1.update({self.clean(hotel_id) : [self.clean(city_name), self.clean(hotel_name)]})
		for key1, value1 in ta_urls_data1.iteritems():
			city_name, hotel_name = value1
			try:self.cursor.execute('INSERT INTO Goibibotrip_hotels(hotel_id, city_name, hotel_name, created_on) values ("%s", "%s", "%s", now())' % (self.clean(key1), self.clean(city_name), self.clean(hotel_name)))
			except:
				print h_id
		print len(ta_urls_data1.keys()), 'goibibo'
		with open('../spiders/SampleCITY.json') as fm:
			dm = json.load(fm)
			for city_name,hotel_id in dm.iteritems():
				for hotel_ids, hotel_details in hotel_id.iteritems():
					hotel_name =hotel_details[0]
					hotel_cmmt_id = hotel_details[-1]
					if (hotel_cmmt_id not in total_blacklist_properties) and (hotel_cmmt_id not in duplicates_mmt_ct_list) and (hotel_cmmt_id not in self.check_mmt_listb):
						ta_urls_data2.update({self.clean(hotel_ids) : [self.clean(city_name), self.clean(hotel_name)]})

		for key2, value2 in ta_urls_data2.iteritems():
			city_name, hotel_name = value2
			try:self.cursor.execute('INSERT INTO Makemytrip_hotels(hotel_id, city_name, hotel_name, created_on) values ("%s", "%s", "%s", now())' % (self.clean(key2), self.clean(city_name), self.clean(hotel_name)))
			except:
				print h_id

		print len(ta_urls_data2.keys()), 'makemytrip '
		with open('TAD_URLS.json') as fta:
			dta = json.load(fta)
			for hotel_id, hotel_details in dta.iteritems():
				city_name, ctid, ta_url, hotel_name = hotel_details
				if ctid not in total_blacklist_properties:
					ta_urls_data3.update({self.clean(hotel_id) : [self.clean(city_name), self.clean(hotel_name)]})

		for key3, value3 in ta_urls_data3.iteritems():
			city_name, hotel_name = value3
			try:self.cursor.execute('INSERT INTO Tripadvisor_hotels(hotel_id, city_name, hotel_name, created_on) values ("%s", "%s", "%s", now())' % (self.clean(key3), self.clean(city_name), self.clean(hotel_name)))
			except: 
				print h_id
		print len(ta_urls_data3.keys()), 'tripadvisor'

        	with open('../spiders/csv_file/Bookingdotcom_mapping_file.csv') as bcsvfile:
	            	all_linesb = csv.reader(bcsvfile, delimiter=',')
		        all_linesb = [icsv for icsv in all_linesb]
			for hotel_id, b_h_url, ct_h_id, ta_h_id, hotel_name, ta_url, b_h_name, city_name in all_linesb[1:]:
				if ct_h_id not in total_blacklist_properties:
					ta_urls_data4.update({self.clean(hotel_id) : [self.clean(city_name), self.clean(hotel_name)]})

                for key4, value4 in ta_urls_data4.iteritems():
                        city_name, hotel_name = value4
                        try:self.cursor.execute('INSERT INTO Booking_hotels(hotel_id, city_name, hotel_name, created_on) values ("%s", "%s", "%s", now())' % (self.clean(key4), self.clean(city_name), self.clean(hotel_name)))
                        except: 
                                print h_id
                print len(ta_urls_data4.keys()), 'Booking'


			
if __name__ == '__main__':
        HotelsUnique().main()

