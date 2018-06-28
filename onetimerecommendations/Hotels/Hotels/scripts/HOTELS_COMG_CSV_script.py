import os
import csv
import MySQLdb
import json
import datetime
from auto_input import *

class COMG(object):
    def __init__(self):
	try:
                user = 'root' # your username
                passwd = DB_PASSWORD # your password
                host = 'localhost' # your host
                db = PROD_META_DB # database where your table is stored
                self.con = MySQLdb.connect(user=user, host=host, db=db, passwd=DB_PASSWORD)
                self.cursor = self.con.cursor()
		self.CSV_PATH  = "/NFS/data/HOTELS_SCRAPED_DATA/MMTGOICOMMON/"
		self.final_fields = ['City', 'CT Hotel Name', 'MMT/GO Hotel Name', 'CT HotelId', 'MMT HotelId', 'GO HotelId', 'Check-in', 'DX', 'LOS', 'Pax', 'MMT RoomType', 'CT RoomType', 'GO RoomType', 'MMT Rate', 'CT Rate', 'GO Rate', 'GO B2C Diff', 'MMT B2C Diff', 'MMT Inclusions', 'GO Inclusions', 'CT Inclusions', 'MMT App Rate', 'CT App Rate', 'GO App Rate', 'MMT Mobile Diff', 'GO Mobile Diff', 'CT_B2C_Slashed Price', 'MMT_B2C_Slashed Price', 'CT_APP_Slashed Price', 'MMT_APP_Slashed Price', 'CT B2C Taxes', 'MMT B2C Taxes', 'CT App Taxes', 'MMT App Taxes', 'RMTC', 'MMT Created On', 'Go Created On', 'Child', 'GO Coupon code', 'MMT Coupon Code', 'GO Coupon Description', 'MMT Coupon Description', 'GO Coupon Discount Amount', 'MMT Coupon Discount Amount', 'MMTGST_Included', 'GOIB GST Included', 'Offer', 'CT Sell price', 'CT CHMM discount']
		self.filename = "MMTGOICOMMON.csv"

	except Exception,e:
		print str(e)

    def __del__(self):
		self.cursor.close()
		self.con.close()

    def main(self):
		query = 'SELECT g.city,g.gbthotelname,c.ctthotelname,c.ctthotelid,g.gbthotelid,g.check_in,g.dx,g.los,c.pax,g.gbtroomtype,c.cttroomtype,'
		query+= 'g.gbtrate,c.cttrate,(CAST(g.b2cdiff as Decimal(6,1)) - CAST(c.b2cdiff as Decimal(6,1))) as b2cdiff,'
		query+= 'g.gbtinclusions,c.cttinclusions,g.gbtapprate,c.cttapprate,g.mobilediff,g.gbtcoupon_discount,g.created_on,g.gbtgst_included, g.gbtcoupon_code, g.gbtcoupon_description, g.gbtcoupon_discount, c.ctsell_price, c.ctchmm_discount'
		query+= ' from Goibibotrip g,Cleartrip c where g.gbthotelname=c.ctthotelname and g.check_in=c.check_in and g.check_out=c.check_out'
		query+= ' and g.dx=c.dx and g.los=c.los and g.pax=c.pax and c.city=g.city;'
		self.cursor.execute(query)
		go_data = self.cursor.fetchall()
		query1 = 'SELECT m.city,m.mmthotelname,c.ctthotelname,c.ctthotelid,m.mmthotelid,m.check_in,m.dx,m.los,c.pax,m.mmtroomtype,c.cttroomtype,'
                query1+= 'm.mmtrate,c.cttrate, (CAST(m.b2cdiff as Decimal(6,1))  - CAST(c.b2cdiff as Decimal(6,1))) as b2cdiff, m.mmtinclusions,c.cttinclusions,m.mmtapprate,'
                query1+= 'c.cttapprate,m.mobilediff,c.ctt_b2c_splashed_price,m.mmt_b2c_splashed_price,c.ctt_app_splashed_price,m.mmt_app_splashed_price,'
                query1+= 'c.cttb2ctaxes,m.mmtb2ctaxes,c.ctt_apptaxes,m.mmt_apptaxes,c.rmtc,c.created_on,c.child,m.mmtcoupon_code,m.mmtcoupon_description,m.mmtcoupon_discount,m.mmtgst_included'
                query1+= ' from Makemytrip m,Cleartrip c where m.mmthotelname=c.ctthotelname and m.check_in=c.check_in and m.check_out=c.check_out and m.dx=c.dx'
                query1+= ' and m.los=c.los and m.pax = c.pax and c.city=m.city;'
		self.cursor.execute(query1)
		ma_data = self.cursor.fetchall()
		ma_data_dict = {}
		for ma_dat in ma_data:
			if ma_dat:
				ma_dat = list(ma_dat)
				key = '<>'.join(ma_dat[0:2]+ [str(val1) for val1 in ma_dat[5:9]])
				ma_data_dict.update({key:ma_dat})

		mydir = os.path.join(self.CSV_PATH, datetime.datetime.now().strftime('%Y/%m/%d'))
		os.makedirs(mydir)
		with open(os.path.join(mydir, self.filename), 'w+') as csvfile:
			csvwriter = csv.writer(csvfile)
			csvwriter.writerow(self.final_fields)
			for go_dat in go_data:
				if go_dat:
					go_dat = list(go_dat)
					key = '<>'.join(go_dat[0:2]+ [str(val1) for val1 in go_dat[5:9]])
					if key in ma_data_dict.keys():
						ma_values = ma_data_dict[key]
						ma_values = self.get_correct(ma_values)
						go_values = self.get_correct(go_dat[:-2])
						go_values = go_values[4:5]+go_values[9:10]+go_values[11:12]+go_values[13:15]+go_values[16:17]+go_values[18:]
						final_values = self.get_correct_order(ma_values, go_values)
						final_values = final_values + go_dat[-2:]
						csvwriter.writerow(final_values)
    def get_correct_order(self, ma_values, go_values):
	ma_values.insert(5, go_values[0])
	ma_values.insert(12, go_values[1])
	ma_values.insert(15, go_values[2])
	ma_values.insert(16, go_values[3])
	ma_values.insert(19, go_values[4])
	ma_values.insert(23, go_values[5])
	ma_values.insert(25, go_values[6])
	ma_values.insert(36, go_values[8])
	ma_values.insert(42, go_values[9])
	ma_values.insert(38, go_values[10])
	ma_values.insert(40, go_values[11])
	ma_values.insert(42, go_values[12])
	ma_values.insert(46, go_values[7])
	return ma_values
    
					
    def get_correct(self, go_values):
		if (go_values[11]=="Sold Out") or (go_values[12]=='NR'):
			for n,i in enumerate(go_values):
				if n==13:
					go_values[n]="N/A"
		return go_values

if __name__ == '__main__':
            COMG().main()
