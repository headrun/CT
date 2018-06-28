import MySQLdb
import csv
import os
import optparse
import re
from datetime import datetime, timedelta
from auto_input import *

class TRIVAGO(object):
	def __init__(self, options):
		user = 'root' # your username
		passwd = DB_PASSWORD # your password
		host = 'localhost' # your host
		db = PROD_META_DB # database where your table is stored
		self.con = MySQLdb.connect(user=user, host=host, db=db, passwd=DB_PASSWORD)
		self.cursor = self.con.cursor()
		self.fields = ["City" , "Cleartrip Hotel ID" , "Hotel Name" , "Trivago Hotel ID" , "Check in" , "LOS" , "Rank1" , "Rank2" , "Rank3" , "Rank4" , "Ct Price" , "Ct type" , "Expedia Price" , "Expedia type" , "Hotels.com Price" , "Hotels.com type" , "Booking.com Price" , "Booking.com type" , "Hotel.info Price" , "Hotel.info type" , "mmtPrice" , "mmtType" , "agodaPrice" , "agodaType" , "Amoma Price" , "Amoma type" , "HRS Price" , "HRS type" , "AvailableOTAs" , "PriceDiff" , "BeatenByBookingDotCom" , "BeatenByPrice" , "BeatenByPriceYesterday" , "BeatenByPriceDayBeforeYesterday" , "BeatenByPriceWeekBefore"]
                self.fields1 = ['city', 'Property Name', 'TA Hotel ID', 'Check In', 'Cleartrip Hotel Id', 'DX']
                self.fields2 = self.fields1 + ['Price difference', 'Cheapest OTA', 'Cleartrip Price', 'Cheapest OTA price']
		self.CSV_PATH = "/NFS/data/HOTELS_SCRAPED_DATA/TRIVAGO/"
		self.filename = "TRIVAGO.csv"
		self.filename1 = "TRIVAGO_Inventory.csv"
		self.filename2 = "TRIVAGO_PriceDiff.csv"
		self.cvs = ('Expedia', 'Hotels.com', 'Booking.com', 'Hotel.info', 'Makemytrip', 'Agoda', 'Amoma', 'HRS')
		self.main()
		
		
	def main(self):
		try:
			trivago_query = "select * from Trivago"
			self.cursor.execute(trivago_query)
			total_data = self.cursor.fetchall()
			dict_cities = {}
			if total_data:
				dict_cities = dict((sublist[0], sublist[1:]) for sublist in total_data)
			current_date = datetime.now().date()
			dx_5_date = str((current_date + timedelta(days=5)))
			dx_1_date = str((current_date + timedelta(days=1)))
			today_dx_dict = {dx_5_date:"5", dx_1_date:"1"}
			todays_date = str(current_date)
			yesterdays_date = str((current_date - timedelta(days=1)))
			day_before_yesterday = str((current_date - timedelta(days=2)))	
			week_before_date = str((current_date - timedelta(days=7)))
			dates_list = [yesterdays_date, day_before_yesterday, week_before_date]
    			mydir = os.path.join(self.CSV_PATH, datetime.now().strftime('%Y/%m/%d'))
    			os.makedirs(mydir)
			sql_data = [(key, value) for key,value in dict_cities.iteritems() if '_%s'%todays_date in key]
			with open(os.path.join(mydir, self.filename), 'w+') as csvfile:
				csvwriter = csv.writer(csvfile)
				csvwriter.writerow(self.fields)
				for sql_data1 in sql_data:
					here_sk = sql_data1[0]
					b1, b2, b3 = [0]*3
					if sql_data1[1][11]:
						for index, datli in enumerate(dates_list):
							to_check = self.get_results(datli, here_sk)
							data_dict = dict_cities.get(to_check, {})
							if data_dict:
								to_value = self.get_value(data_dict, sql_data1[1][11])
								if index == 0:
									b1 = to_value
								if index == 1:
									b2 = to_value
								if index == 3:
									b3 = to_value
					sql_data1_ = tuple(sql_data1[1][1:-6])+(b1, b2, b3)
					sql_data1_ = tuple(['NA' if x=='' else x for x in sql_data1_])
					csvwriter.writerow(sql_data1_)
			query_inventory = "select city, hotel_name, trivago_hotel_id, check_in, cleartrip_hotel_id from Trivago where (ct_price ='0' or ct_price ='-' or ct_price = '') and (date(created_on)='%s') and (available_otas >=4)" % str(current_date)
			self.cursor.execute(query_inventory)
			no_ct_data = self.cursor.fetchall()
                        if no_ct_data:
                                with open(os.path.join(mydir, self.filename1), 'w+') as csvfile1:
                                        csvwriter = csv.writer(csvfile1)
                                        csvwriter.writerow(self.fields1)
                                        for ncd in no_ct_data:
						ncd_data1 = tuple(ncd)+(today_dx_dict.get(str(ncd[3]), ''),)
                                                csvwriter.writerow(ncd_data1)
                        query_non = "select ct_price, expedia_price, hotelsdot_com_price, bookingdot_com_price, hotel_info_price, mmt_price, agoda_price, amoma_price, hrs_price, city, hotel_name, trivago_hotel_id, check_in, cleartrip_hotel_id from Trivago where (ct_price !='0' and ct_price !='-' and ct_price != '' and date(created_on)='%s') " % str(current_date)
                        self.cursor.execute(query_non)
                        pf_data = self.cursor.fetchall()
                        if query_non:
                                with open(os.path.join(mydir, self.filename2), 'w+') as csvfile2:
                                        csvwriter = csv.writer(csvfile2)
                                        csvwriter.writerow(self.fields2)
                                        for pfd in pf_data:
                                                total_ct = pfd[0]
                                                total_others = pfd[1:9]
                                                main_da = pfd[9:]
                                                both_comb = zip(self.cvs, total_others)
                                                filer_list = list(filter(lambda x:x[1]!='-'  and x[1]!='0' and x[1] != '', both_comb))
                                                if filer_list:
                                                        min_price = min(filer_list, key = lambda t: t[1])
                                                        if min_price:
								pricd_ = int(total_ct) - int(min_price[1])
                                                                if pricd_ > 3500:
                                                                        sql_pf_data = main_da + (today_dx_dict.get(str(main_da[3]), ''), pricd_, min_price[0], total_ct, min_price[1])
                                                                        csvwriter.writerow(sql_pf_data)


			self.cursor.close()
			self.con.close()
		except Exception, e:
    			print str(e)

	def get_value(self, data_dict, sql_data1):
		counter = 0
		cvs = filter(None, list(data_dict[11:-10])[::2])
		for cv in cvs:
			if int(sql_data1)> int(cv):
				counter += 1
		return counter

	def get_results(self, check_date, here_sk):
		to_check = re.sub('_(\d+-\d+-\d+)', '_%s'%check_date, here_sk)
		return to_check

if __name__ == '__main__':
        parser = optparse.OptionParser()
        parser.add_option('-s', '--set_up', default = '', help = 'set_up')
        (options, args) = parser.parse_args()
        TRIVAGO(options)
