import MySQLdb
import csv
import os
import datetime
import optparse
from auto_input import *

class GBCTcsv(object):
        def __init__(self, options):
                user = 'root' # your username
                passwd = DB_PASSWORD # your password
                host = 'localhost' # your host
                db = PROD_META_DB # database where your table is stored
                self.con = MySQLdb.connect(user=user, host=host, db=db, passwd=DB_PASSWORD)
                self.cursor = self.con.cursor()
		self.fields = ['City', 'CT Hotel Name', 'GO Hotel Name', 'CT HotelId', 'GO HotelId', 'Check-in', 'DX', 'LOS', 'CT Pax', 'GO RoomType', 'CT RoomType', 'GO Rate', 'CT Rate','B2C Diff', 'GO Inclusions', 'CT Inclusions', 'GO App Rate', 'CT App Rate', 'Mobile Diff', 'Offer', 'Created On', 
'GOIB GST Included', 'GO Coupon code', 'GO Coupon Description' , 'GO Coupon Discount Amount', 'Go Cancellation policy', 'CT Cancellation policy', 'CT Sell price', 'CT CHMM discount']

		self.CSV_PATH="/NFS/data/HOTELS_SCRAPED_DATA/GOIBIBO/"
		self.filename = "GOIBIBO.csv"
		self.main()

	def main(self):
		try:
                        final_ct_as_dict, final_goi_as_dict = {}, {}
                        query_goi = 'select ct_id, check_in, los, pax, check_out, city, gbthotelname, gbthotelid, check_in, dx, los, pax, gbtroomtype, gbtrate, CAST(b2cdiff as Decimal(6,1)), gbtinclusions, gbtapprate, mobilediff, gbtcoupon_discount, created_on, gbtgst_included, gbtcoupon_code, gbtcoupon_description, gbtcoupon_discount, cancellation_policy from Goibibotrip'
                        self.cursor.execute(query_goi)
                        sql_data_goi = self.cursor.fetchall()
                        query_ct = 'select ctthotelid, check_in, los, pax, check_out, city, ctthotelid, ctthotelname, ctthotelid, check_in, dx, los, pax, cttroomtype, cttrate, CAST(b2cdiff as Decimal(6,1)) , cttinclusions, cttapprate, cancellation_policy, ctsell_price, ctchmm_discount from Cleartrip'
                        self.cursor.execute(query_ct)
                        sql_data_ct = self.cursor.fetchall()
                        if sql_data_goi and sql_data_ct:
                                for sdmmt in sql_data_goi:
                                        key = '<>'.join([str(ki) for ki in sdmmt[0:5]])
                                        if key not in final_goi_as_dict.keys():
                                                final_goi_as_dict[key] = []
                                        final_goi_as_dict[key].append(sdmmt[5:])
                                for sdct in sql_data_ct:
                                        keyc = '<>'.join([str(ki) for ki in sdct[0:5]])
                                        if keyc not in final_ct_as_dict.keys():
                                                final_ct_as_dict[keyc] = []
                                        final_ct_as_dict[keyc].append(sdct[5:])
                                print len(final_ct_as_dict.keys()), 'ct_len'
                                print len(final_goi_as_dict.keys()), 'goi_len'
				mydir = os.path.join(self.CSV_PATH, datetime.datetime.now().strftime('%Y/%m/%d'))
				os.makedirs(mydir)
				sql_data = self.cursor.fetchall()
				with open(os.path.join(mydir, self.filename), 'w+') as csvfile:
					csvwriter = csv.writer(csvfile)
					csvwriter.writerow(self.fields)
                                        for ct_key, goi_info in final_goi_as_dict.iteritems():
                                                ct_info = final_ct_as_dict.get(ct_key, {})
                                                if goi_info and ct_info:
                                                        if len(goi_info) > len(ct_info):
                                                                difference_length = len(goi_info) - len(ct_info)
                                                                for ra in range(difference_length):
                                                                        ct_info.append(tuple(['']*len(ct_info[0])))
                                                        if len(ct_info) > len(goi_info):
                                                                difference_length = len(ct_info) - len(goi_info)
                                                                for rc in range(difference_length):
                                                                        goi_info.append(tuple(['']*len(goi_info[0])))
                                                        for mc, cc in zip(goi_info, ct_info):
								if mc and cc:
									gcity, ggbthotelname, ggbthotelid, gcheck_in, gdx, glos, gpax, ggbtroomtype, ggbtrate, gb2cdiff, ggbtinclusions, ggbtapprate, gmobilediff, ggbtcoupon_discount, gcreated_on, ggbtgst_included, ggbtcoupon_code, ggbtcoupon_description, ggbtcoupon_discount, gcancellation_policy = mc
									ccity, cctthotelid, cctthotelname, cctthotelid, ccheck_in, cdx, clos, cpax, ccttroomtype, ccttrate, cb2cdiff, ccttinclusions, ccttapprate, ccancellation_policy, cctsell_price, cctchmm_discount = cc
									if (ccttroomtype == 'Sold Out') or (ggbtrate == 'NR'):
										fb2cdiff = ''
									try:
										fb2cdiff = gb2cdiff-cb2cdiff
									except: 
										fb2cdiff = ''
									if 'sold out' in ccttrate.lower() or 'sold out' in ggbtrate.lower():
										fb2cdiff = 'N/A'
									if not gcity:
										gcity = ccity
										gdx = cdx
										glos = clos
										gcheck_in = ccheck_in
									if not cpax:
										cpax = gpax
									values = [gcity, cctthotelname, ggbthotelname, cctthotelid, ggbthotelid, gcheck_in, gdx, glos, cpax, ggbtroomtype, ccttroomtype, ggbtrate, ccttrate, fb2cdiff, ggbtinclusions, ccttinclusions, ggbtapprate, ccttapprate, gmobilediff, ggbtcoupon_discount, gcreated_on, ggbtgst_included, ggbtcoupon_code, ggbtcoupon_description, ggbtcoupon_discount, gcancellation_policy, ccancellation_policy, cctsell_price, cctchmm_discount]
									sql_data1=tuple(values)
									csvwriter.writerow(sql_data1)
		    	self.cursor.close()
		    	self.con.close()
		except Exception, e:
			print str(e)

if __name__ == '__main__':
        parser = optparse.OptionParser()
        parser.add_option('-s', '--set_up', default = '', help = 'set_up')
        (options, args) = parser.parse_args()
        GBCTcsv(options)

