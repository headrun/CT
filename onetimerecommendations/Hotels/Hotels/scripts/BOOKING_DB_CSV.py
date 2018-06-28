import MySQLdb
import csv
import os
import json
import datetime
import optparse
from auto_input import *


class BookingCTcsv(object):
    def __init__(self, options):
        self.check_list, self.another_check_list = [], []
        user = 'root'  # your username
        passwd = DB_PASSWORD  # your password
        host = 'localhost'  # your host
        db = PROD_META_DB  # database where your table is stored
        self.con = MySQLdb.connect(
            user=user, host=host, db=db, passwd=DB_PASSWORD)
        self.cursor = self.con.cursor()
        self.fields = ['City', 'CT Hotel Name', 'Booking Hotel Name', 'CT HotelId', 'Booking HotelId', 'Check-in', 'DX', 'LOS', 'CT Pax', 'Booking RoomType', 'CT RoomType', 'Booking Rate', 'CT Rate', 'B2C Diff', 'Booking Inclusions',
                       'CT Inclusions', 'CT_B2C_Slashed Price', 'Booking_B2C_Slashed Price', 'RMTC', 'GST Amount', 'Created On', 'Child', 'Booking Cancellation policy', 'CT Cancellation policy', 'CT Sell price', 'CT CHMM discount', 'No of recommendations']
        #self.CSV_PATH = "/NFS/data/HOTELS_SCRAPED_DATA/BOOKING/"
        self.CSV_PATH = os.getcwd()
        self.filename = "BOOKING.csv"
        with open('../spiders/SampleCITY.json') as json_mmt:
            self.d_mmt = json.load(json_mmt)
            for city_name, hotel_id in self.d_mmt.iteritems():
                for hotel_ids, hotel_details in hotel_id.iteritems():
                    ct_mmt_id = hotel_details[2]
                    self.another_check_list.append(ct_mmt_id)
        with open('../spiders/GoiboCity_codes.json') as json_goi:
            self.d_goi = json.load(json_goi)
            for city_name, hotel_details in self.d_goi.iteritems():
                for hotel_id, hotel_data in hotel_details.iteritems():
                    ct_goi_id = hotel_data[2]
                    if ct_goi_id not in self.another_check_list:
                        self.check_list.append(ct_goi_id)
        self.check_list = [str(ch) for ch in self.check_list]
        self.main()

    def main(self):
        try:
            final_ct_as_dict, final_mmt_as_dict = {}, {}
            query_mmt = 'select child, ct_id, check_in, los, pax, check_out, ct_id, check_in, los, pax, check_out, city, actual_price, CAST(actual_price as Decimal(6,1)), hotelname, hotelid, final_rate_plan, inclusions, splashed_price, rmtc, cancellation_policy, dx, gst_amt, aux_info from Booking'
            self.cursor.execute(query_mmt)
            sql_data_mmt = self.cursor.fetchall()
            query_ct = 'select child, ctthotelid, check_in, los, pax, check_out, city, ctthotelid, ctthotelname, ctthotelid, check_in, dx, los, pax, cttroomtype, cttrate, CAST(b2cdiff as Decimal(6,1)) , cttinclusions, cttapprate, ctt_b2c_splashed_price, ctt_app_splashed_price, cttb2ctaxes, ctt_apptaxes, rmtc, created_on, child, cancellation_policy, ctsell_price, ctchmm_discount from Cleartrip'
            self.cursor.execute(query_ct)
            sql_data_ct = self.cursor.fetchall()
            if sql_data_mmt and sql_data_ct:
                for sdmmt in sql_data_mmt:
                    key = '<>'.join([str(ki) for ki in sdmmt[0:6]])
                    if key not in final_mmt_as_dict.keys():
                        final_mmt_as_dict[key] = []
                    final_mmt_as_dict[key].append(sdmmt[6:])
                for sdct in sql_data_ct:
                    keyc = '<>'.join([str(ki) for ki in sdct[0:6]])
                    if keyc not in final_ct_as_dict.keys():
                        final_ct_as_dict[keyc] = []
                    final_ct_as_dict[keyc].append(sdct[6:])
                print len(final_ct_as_dict.keys()), 'ct_len'
                print len(final_mmt_as_dict.keys()), 'booking_len'
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
                                bct_id, bcheck_in, blos, bpax, bcheck_out, bcity, bactual_price, bb2cdiff, bhotelname, bhotelid, bfinal_rate_plan, binclusions, bsplashed_price, brmtc, bcancellation_policy, bdx, bgst_amt, baux_info = mc
                                ccity, cctthotelid, cctthotelname, cctthotelid, ccheck_in, cdx, clos, cpax, ccttroomtype, ccttrate, cb2cdiff, ccttinclusions, ccttapprate, cctt_b2c_splashed_price, cctt_app_splashed_price, ccttb2ctaxes, cctt_apptaxes, crmtc, ccreated_on, cchild, ccancellation_policy, cctsell_price, cctchmm_discount = cc
                                fb2cdiff = ''
                                try:
                                    fb2cdiff = bb2cdiff-cb2cdiff
                                except:
                                    fb2cdiff = ''
                                if not bcity:
                                    bcity = ccity
                                    bdx = cdx
                                    blos = clos
                                    bcheck_in = ccheck_in
                                if not cpax:
                                    cpax = bpax
                                if mc and cc and (str(cctthotelid) not in self.check_list):
                                    values = [bcity, cctthotelname, bhotelname, cctthotelid, bhotelid, bcheck_in, bdx, blos, cpax, bfinal_rate_plan, ccttroomtype, bactual_price, ccttrate, fb2cdiff, binclusions,
                                              ccttinclusions, cctt_b2c_splashed_price, bsplashed_price, crmtc, bgst_amt, ccreated_on, cchild, bcancellation_policy, ccancellation_policy, cctsell_price, cctchmm_discount, baux_info]
                                    sql_data1 = tuple(values)
                                    csvwriter.writerow(sql_data1)

            self.cursor.close()
            self.con.close()
        except Exception, e:
            print str(e)


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-s', '--set_up', default='', help='set_up')
    (options, args) = parser.parse_args()
    BookingCTcsv(options)
