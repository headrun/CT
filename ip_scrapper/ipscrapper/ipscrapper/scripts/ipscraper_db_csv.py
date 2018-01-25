import MySQLdb
import csv
import os
import datetime
import optparse
import json

class Ctcontent(object):
	def __init__(self, options):
		user = 'root' # your username
		passwd = '' # your password
		host = 'localhost' # your host
		db = 'IP_SCRAPER' # database where your table is stored
		self.con = MySQLdb.connect(user=user, host=host, db=db)
		self.cursor = self.con.cursor()
		self.fields = ["Ip", "Continent", "Country", "Capital", "City Location", "ISP"]
		#self.CSV_PATH = "/NFS/data/HOTELS_SCRAPED_DATA/CTCONTENT/"
		self.CSV_PATH = "/home/lakshmic/ip_scrapper/ipscrapper/ipscrapper/scripts"
		self.filename = "IPCONTENT.csv"
		self.data_date = str(datetime.datetime.now().date())
		self.update_yes = 'update ipmeta set is_csvrun="yes" where ip = "%s"'
		self.main()
		
	def main(self):
		try:
			query = "select * from ipmeta where is_csvrun='no'"
			self.cursor.execute(query)
			sql_data = self.cursor.fetchall()
			mydir = os.path.join(self.CSV_PATH, datetime.datetime.now().strftime('%Y/%m/%d'))
			os.makedirs(mydir)
			with open(os.path.join(mydir, self.filename), 'w+') as csvfile:
				csvwriter = csv.writer(csvfile)
				csvwriter.writerow(self.fields)
				for dat in sql_data:
					data_i = dat[:-5]
					csvwriter.writerow(data_i)
					self.cursor.execute(self.update_yes % data_i[0])
			self.cursor.close()
			self.con.close()
		except Exception, e:
    			print str(e)

if __name__ == '__main__':
        parser = optparse.OptionParser()
        parser.add_option('-s', '--set_up', default = '', help = 'set_up')
        (options, args) = parser.parse_args()
        Ctcontent(options)
