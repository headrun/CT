import MySQLdb
import csv
import os
import datetime
import optparse
import json
from auto_input import *


class MMTCTcsv(object):
    def __init__(self, options):
        user = 'root'  # your username
        passwd = DB_PASSWORD  # your password
        host = 'localhost'  # your host
        db = PROD_META_DB  # database where your table is stored
        self.con = MySQLdb.connect(
            user=user, host=host, db=db, passwd=DB_PASSWORD)
        self.cursor = self.con.cursor()
        self.hotel_goi_list = []
        with open('../spiders/GoiboCity_codes.json') as fg:
            dg = json.load(fg)
            for city_name, hotel_details in dg.iteritems():
                for hotel_id, hotel_data in hotel_details.iteritems():
                    hotel_name = hotel_data[0]
                    hotel_cgoi_id = hotel_data[-1]
                    self.hotel_goi_list.append(str(hotel_cgoi_id))
        self.fields = ['City', 'CT Hotel Name', 'MMT Hotel Name', 'CT HotelId', 'MMT HotelId', 'Check-in', 'DX', 'LOS', 'CT Pax', 'MMT RoomType', 'CT RoomType', 'MMT Rate',
                       'CT Rate', 'B2C Diff', 'MMT Inclusions', 'CT Inclusions', 'MMT App Rate', 'CT App Rate', 'Mobile Diff', 'CT_B2C_Slashed Price', 'MMT_B2C_Slashed Price',
                       'CT_APP_Slashed Price', 'MMT_APP_Slashed Price', 'CT B2C Taxes', 'MMT B2C Taxes', 'CT App Taxes', 'MMT App Taxes', 'RMTC', 'Created On', 'Child', 'MMT Coupon Code',
                       'Coupon Description', 'Coupon Discount Amount', 'MMTGST_Included', 'MMT Cancellation policy', 'CT Cancellation policy', 'CT Sell price', 'CT CHMM discount', 'No of recommendations']
        #self.CSV_PATH = "/NFS/data/HOTELS_SCRAPED_DATA/MMT/"
        self.CSV_PATH = '/root/hotels_dev/inventory/scrapers/Hotels/Hotels/scripts/2018'
        self.filename = "MMT.csv"
        self.main()

    def main(self):
        try:
            final_ct_as_dict, final_mmt_as_dict = {}, {}
            query_mmt = 'select ct_id, check_in, los, pax, check_out, city, mmthotelname, mmthotelid, check_in, dx, los, pax, mmtroomtype, mmtrate, CAST(b2cdiff as Decimal(6,1)), mmtinclusions, mmtapprate, mobilediff, mmt_b2c_splashed_price, mmt_app_splashed_price, mmtb2ctaxes, mmt_apptaxes, mmtcoupon_code, mmtcoupon_description, mmtcoupon_discount, mmtgst_included, cancellation_policy, aux_info from Makemytrip'
            self.cursor.execute(query_mmt)
            sql_data_mmt = self.cursor.fetchall()
            query_ct = 'select ctthotelid, check_in, los, pax, check_out, city, ctthotelid, ctthotelname, ctthotelid, check_in, dx, los, pax, cttroomtype, cttrate, CAST(b2cdiff as Decimal(6,1)) , cttinclusions, cttapprate, ctt_b2c_splashed_price, ctt_app_splashed_price, cttb2ctaxes, ctt_apptaxes, rmtc, created_on, child, cancellation_policy, ctsell_price, ctchmm_discount from Cleartrip'
            self.cursor.execute(query_ct)
            sql_data_ct = self.cursor.fetchall()
            if sql_data_mmt and sql_data_ct:
                for sdmmt in sql_data_mmt:
                    key = '<>'.join([str(ki) for ki in sdmmt[0:5]])
                    if key not in final_mmt_as_dict.keys():
                        final_mmt_as_dict[key] = []
                    final_mmt_as_dict[key].append(sdmmt[5:])
                for sdct in sql_data_ct:
                    keyc = '<>'.join([str(ki) for ki in sdct[0:5]])
                    if keyc not in final_ct_as_dict.keys():
                        final_ct_as_dict[keyc] = []
                    final_ct_as_dict[keyc].append(sdct[5:])
                print len(final_ct_as_dict.keys()), 'ct_len'
                print len(final_mmt_as_dict.keys()), 'mmt_len'
                mydir = os.path.join(
                    self.CSV_PATH, datetime.datetime.now().strftime('%Y/%m/%d'))
                os.makedirs(mydir)
                with open(os.path.join(mydir, self.filename), 'w+') as csvfile:
                    csvwriter = csv.writer(csvfile)
                    csvwriter.writerow(self.fields)
                    for ct_key, mmt_info in final_mmt_as_dict.iteritems():
                        ct_info = final_ct_as_dict.get(ct_key, {})
                        if mmt_info and ct_info:
                            if len(mmt_info) > len(ct_info):
                                difference_length = len(
                                    mmt_info) - len(ct_info)
                                for ra in range(difference_length):
                                    ct_info.append(tuple(['']*len(ct_info[0])))
                            if len(ct_info) > len(mmt_info):
                                difference_length = len(
                                    ct_info) - len(mmt_info)
                                for rc in range(difference_length):
                                    mmt_info.append(
                                        tuple(['']*len(mmt_info[0])))
                            for mc, cc in zip(mmt_info, ct_info):
                                if mc and cc:
                                    mcity, mmmthotelname, mmmthotelid, mcheck_in, mdx, mlos, mpax, mmmtroomtype, mmmtrate, mb2cdiff, mmmtinclusions, mmmtapprate, mmobilediff, mmmt_b2c_splashed_price, mmmt_app_splashed_price, mmmtb2ctaxes, mmmt_apptaxes, mmmtcoupon_code, mmmtcoupon_description, mmmtcoupon_discount, mmmtgst_included, mcancellation_policy, maux_info = mc
                                    if maux_info == 1 or maux_info == '1':
                                        maux_info = ''
                                    ccity, cctthotelid, cctthotelname, cctthotelid, ccheck_in, cdx, clos, cpax, ccttroomtype, ccttrate, cb2cdiff, ccttinclusions, ccttapprate, cctt_b2c_splashed_price, cctt_app_splashed_price, ccttb2ctaxes, cctt_apptaxes, crmtc, ccreated_on, cchild, ccancellation_policy, cctsell_price, cctchmm_discount = cc
                                    if (ccttroomtype == 'Sold Out') or (mmmtrate == 'NR'):
                                        ccttrate = 'N/A'
                                    fb2cdiff = ''
                                    try:
                                        fb2cdiff = mb2cdiff-cb2cdiff
                                    except:
                                        fb2cdiff = ''
                                    if 'sold out' in ccttrate.lower() or 'sold out' in mmmtrate.lower():
                                        fb2cdiff = 'N/A'
                                    if not mcity:
                                        mcity = ccity
                                        mdx = cdx
                                        mlos = clos
                                        mcheck_in = ccheck_in
                                    if not cpax:
                                        cpax = mpax
                                    values = [mcity, cctthotelname, mmmthotelname, cctthotelid, mmmthotelid, mcheck_in, mdx, mlos, cpax, mmmtroomtype, ccttroomtype, mmmtrate, ccttrate, fb2cdiff, mmmtinclusions, ccttinclusions, mmmtapprate, ccttapprate, mmobilediff, cctt_b2c_splashed_price, mmmt_b2c_splashed_price,
                                              cctt_app_splashed_price, mmmt_app_splashed_price, ccttb2ctaxes, mmmtb2ctaxes, cctt_apptaxes, mmmt_apptaxes, crmtc, ccreated_on, cchild, mmmtcoupon_code, mmmtcoupon_description, mmmtcoupon_discount, mmmtgst_included, mcancellation_policy, ccancellation_policy, cctsell_price, cctchmm_discount, maux_info]
                                    sql_data11 = tuple(values)
                                    csvwriter.writerow(sql_data11)

            self.cursor.close()
            self.con.close()
        except Exception, e:
            print str(e)


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-s', '--set_up', default='', help='set_up')
    (options, args) = parser.parse_args()
    MMTCTcsv(options)
