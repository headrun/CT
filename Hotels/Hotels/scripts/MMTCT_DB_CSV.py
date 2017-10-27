import MySQLdb
import csv
import os
import datetime
import optparse

class MMTCTcsv(object):
	def __init__(self, options):
		user = 'root' # your username
		passwd = '' # your password
		host = 'localhost' # your host
		db = 'MMCTRP' # database where your table is stored
		self.con = MySQLdb.connect(user=user, host=host, db=db)
		self.cursor = self.con.cursor()
		self.fields = ['City', 'CT Hotel Name', 'MMT Hotel Name', 'CT HotelId', 'MMT HotelId', 'Check-in', 'DX', 'LOS', 'CT Pax', 'MMT RoomType', 'CT RoomType', 'MMT Rate', 
'CT Rate','B2C Diff', 'MMT Inclusions', 'CT Inclusions', 'MMT App Rate', 'CT App Rate', 'Mobile Diff', 'CT_B2C_Slashed Price', 'MMT_B2C_Slashed Price', 
'CT_APP_Slashed Price','MMT_APP_Slashed Price', 'CT B2C Taxes', 'MMT B2C Taxes', 'CT App Taxes', 'MMT App Taxes', 'RMTC', 'Created On', 'Child', 'MMT Coupon Code',
'Coupon Description','Coupon Discount Amount','MMTGST_Included']
		self.CSV_PATH = "/NFS/data/HOTELS_SCRAPED_DATA/MMT/"
		self.filename = "MMT.csv"
		self.db_names_query = ' from Makemytrip m,Cleartrip c where m.mmthotelname=c.ctthotelname and m.check_in=c.check_in and m.check_out=c.check_out and m.dx=c.dx'
		if options.set_up  == 'onetime':
			self.CSV_PATH = "/NFS/data/HOTELS_SCRAPED_DATA/MMT_ONE_TIME/"
			self.filename = "MMTonetime.csv"
			self.db_names_query = ' from Makemytriponetime m,Cleartriponetime c where m.mmthotelname=c.ctthotelname and m.check_in=c.check_in and m.check_out=c.check_out and m.dx=c.dx'
		self.main()
		
	def main(self):
		try:
    			query = 'SELECT m.city,m.mmthotelname,c.ctthotelname,c.ctthotelid,m.mmthotelid,m.check_in,m.dx,m.los,c.pax,m.mmtroomtype,c.cttroomtype,'
    			query+= 'm.mmtrate,c.cttrate, (CAST(m.b2cdiff as Decimal(6,1))  - CAST(c.b2cdiff as Decimal(6,1))) as b2cdiff, m.mmtinclusions,c.cttinclusions,m.mmtapprate,'
    			query+= 'c.cttapprate,m.mobilediff,c.ctt_b2c_splashed_price,m.mmt_b2c_splashed_price,c.ctt_app_splashed_price,m.mmt_app_splashed_price,'
    			query+= 'c.cttb2ctaxes,m.mmtb2ctaxes,c.ctt_apptaxes,m.mmt_apptaxes,c.rmtc,c.created_on,c.child,m.mmtcoupon_code,m.mmtcoupon_description,m.mmtcoupon_discount,m.mmtgst_included'
    			query+= self.db_names_query
    			query+= ' and m.los=c.los and m.pax = c.pax and c.city=m.city;'
   	 		self.cursor.execute(query)
    			mydir = os.path.join(self.CSV_PATH, datetime.datetime.now().strftime('%Y/%m/%d'))
    			os.makedirs(mydir)
			sql_data = self.cursor.fetchall()
			with open(os.path.join(mydir, self.filename), 'w+') as csvfile:
				csvwriter = csv.writer(csvfile)
				csvwriter.writerow(self.fields)
				for sql_data1 in sql_data:
					sql_data1=list(sql_data1)
					if (sql_data1[11]=="Sold Out") or (sql_data1[12]=='NR'):
						for n,i in enumerate(sql_data1):
							if n==13:
								sql_data1[n]="N/A"

					sql_data1=tuple(sql_data1)
					csvwriter.writerow(sql_data1)
			self.cursor.close()
			self.con.close()
		except Exception, e:
    			print str(e)

if __name__ == '__main__':
        parser = optparse.OptionParser()
        parser.add_option('-s', '--set_up', default = '', help = 'set_up')
        (options, args) = parser.parse_args()
        MMTCTcsv(options)
