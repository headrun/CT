import MySQLdb
import csv
import os
import datetime
import optparse

class TRIPADVISOR(object):
	def __init__(self, options):
		user = 'root' # your username
		passwd = '' # your password
		host = 'localhost' # your host
		db = 'MMCTRP' # database where your table is stored
		self.con = MySQLdb.connect(user=user, host=host, db=db)
		self.cursor = self.con.cursor()
		self.fields = ['city', 'Property Name', 'TA Hotel ID', 'Check In', 'DX', 'Pax', 'Ranking-Agoda', 'Ranking-BookingCom', 'Ranking-ClearTrip', 'Ranking-Expedia', 'Ranking-Goibibo', 'Ranking-HotelsCom2', 'Ranking-MakeMyTrip', 'Ranking-Yatra', 'Ranking-TG', 'Price-Agoda', 'Price-BookingCom', 'Price-ClearTrip', 'Price-Expedia', 'Price-Goibibo', 'Price-HotelsCom2', 'Price-MakeMyTrip', 'Price-Yatra', 'Price-TG', 'Tax-Agoda', 'Tax-BookingCom', 'Tax-ClearTrip', 'Tax-Expedia', 'Tax-Goibibo', 'Tax-HotelsCom2', 'Tax-MakeMyTrip', 'Tax-Yatra', 'Tax-TG', 'Total-Agoda', 'Total-BookingCom', 'Total-ClearTrip', 'Total-Expedia', 'Total-Goibibo', 'Total-HotelsCom2', 'Total-MakeMyTrip', 'Total-Yatra', 'Total-TG', 'Cheaper-Agoda', 'Cheaper-BookingCom', 'Cheaper-ClearTrip', 'Cheaper-Expedia', 'Cheaper-Goibibo', 'Cheaper-HotelsCom2', 'Cheaper-MakeMyTrip', 'Cheaper-Yatra', 'Cheaper-TG', 'Status-Agoda', 'Status-BookingCom', 'Status-ClearTrip', 'Status-Expedia', 'Status-Goibibo', 'Status-HotelsCom2', 'Status-MakeMyTrip', 'Status-Yatra', 'Status-TG', 'Ranking-Stayzilla', 'Price-Stayzilla', 'Tax-Stayzilla', 'Total-Stayzilla', 'Cheaper-Stayzilla', 'Status-Stayzilla', 'Time', 'city_rank'] 
		self.CSV_PATH = "/NFS/data/HOTELS_SCRAPED_DATA/TRIPADVISOR/"
		self.filename = "TRIPADVISOR.csv"
		self.data_date = str(datetime.datetime.now().date())
		self.main()
		
		
	def main(self):
		try:
			city_rank_query = "select sk, city_rank from Tripadvisorcityrank"
			self.cursor.execute(city_rank_query)
			city_rank_data = self.cursor.fetchall()
			dict_cities = {}
			if city_rank_data:
				dict_cities = dict(city_rank_data)
    			query = 'select * from Tripadvisor'
   	 		self.cursor.execute(query)
    			mydir = os.path.join(self.CSV_PATH, datetime.datetime.now().strftime('%Y/%m/%d'))
    			os.makedirs(mydir)
			sql_data = self.cursor.fetchall()
			with open(os.path.join(mydir, self.filename), 'w+') as csvfile:
				csvwriter = csv.writer(csvfile)
				csvwriter.writerow(self.fields)
				for sql_data1 in sql_data:
					sql_data1 = tuple(sql_data1[1:-4]) + (dict_cities.get(sql_data1[3], ''),)
					csvwriter.writerow(sql_data1)
			self.cursor.close()
			self.con.close()
		except Exception, e:
    			print str(e)

if __name__ == '__main__':
        parser = optparse.OptionParser()
        parser.add_option('-s', '--set_up', default = '', help = 'set_up')
        (options, args) = parser.parse_args()
        TRIPADVISOR(options)
