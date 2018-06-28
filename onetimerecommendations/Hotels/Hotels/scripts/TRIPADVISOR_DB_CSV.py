import MySQLdb
import csv
import os
import datetime
import optparse
import json
from auto_input import *


class TRIPADVISOR(object):
    def __init__(self, options):
        with open('TAD_URLS.json') as json_data1:
            self.ct_id = json.load(json_data1)
        self.market_name_dict = {}
        with open('../spiders/csv_file/market_names.csv') as csv_mar:
            self.all_lines = csv.reader(csv_mar, delimiter=',')
            self.all_lines = [icsv for icsv in self.all_lines]
            for alll in self.all_lines:
                if 'Market Name' not in alll[1]:
                    self.market_name_dict.update({alll[0]: alll[1]})
        user = 'root'  # your username
        passwd = DB_PASSWORD  # your password
        host = 'localhost'  # your host
        db = PROD_META_DB  # database where your table is stored
        self.con = MySQLdb.connect(
            user=user, host=host, db=db, passwd=DB_PASSWORD)
        self.cursor = self.con.cursor()
        self.fields = ['City', 'Property Name', 'TA Hotel ID', 'Check In', 'DX', 'Pax', 'Ranking-Agoda', 'Ranking-BookingCom', 'Ranking-ClearTrip', 'Ranking-Expedia', 'Ranking-Goibibo', 'Ranking-HotelsCom2', 'Ranking-MakeMyTrip', 'Ranking-Yatra', 'Ranking-TG', 'Price-Agoda', 'Price-BookingCom', 'Price-ClearTrip', 'Price-Expedia', 'Price-Goibibo', 'Price-HotelsCom2', 'Price-MakeMyTrip', 'Price-Yatra', 'Price-TG', 'Tax-Agoda', 'Tax-BookingCom', 'Tax-ClearTrip', 'Tax-Expedia', 'Tax-Goibibo', 'Tax-HotelsCom2', 'Tax-MakeMyTrip', 'Tax-Yatra', 'Tax-TG', 'Total-Agoda', 'Total-BookingCom', 'Total-ClearTrip',
                       'Total-Expedia', 'Total-Goibibo', 'Total-HotelsCom2', 'Total-MakeMyTrip', 'Total-Yatra', 'Total-TG', 'Cheaper-Agoda', 'Cheaper-BookingCom', 'Cheaper-ClearTrip', 'Cheaper-Expedia', 'Cheaper-Goibibo', 'Cheaper-HotelsCom2', 'Cheaper-MakeMyTrip', 'Cheaper-Yatra', 'Cheaper-TG', 'Status-Agoda', 'Status-BookingCom', 'Status-ClearTrip', 'Status-Expedia', 'Status-Goibibo', 'Status-HotelsCom2', 'Status-MakeMyTrip', 'Status-Yatra', 'Status-TG', 'Ranking-Stayzilla', 'Price-Stayzilla', 'Tax-Stayzilla', 'Total-Stayzilla', 'Cheaper-Stayzilla', 'Status-Stayzilla', 'Time', 'city_rank', 'CT Hotel ID']
        self.fields1 = ['city', 'Property Name', 'TA Hotel ID',
                        'Check In', 'DX', 'Cleartrip Hotel Id']
        self.fields2 = self.fields1 + \
            ['Price difference', 'Cheapest OTA',
                'Cleartrip Price', 'Cheapest OTA price']
        self.fields3 = ['city', 'Property Name', 'TA Hotel ID', 'Check In', 'DX', 'Adult count', 'Los', 'No of Rooms',
                        'Cleartrip Hotel Id', 'CT price', 'CT Room name', 'Cheapest OTA name', 'Cheapest OTA price', 'Vendor name', 'Vendor price', 'Vendor Room name', "Average of 3 cheapest OTA's", 'Market Name']
	self.name_g = 'Tripadvisor'
        self.CSV_PATH = "/NFS/data/HOTELS_SCRAPED_DATA/TRIPADVISOR/"
	if options.set_up:
		self.CSV_PATH = "/NFS/data/HOTELS_SCRAPED_DATA/TRIPADVISORAPC/"
		self.name_g = 'TripadvisorAPC'
        self.filename = "TRIPADVISOR.csv"
        self.filename1 = "TRIPADVISOR_Inventory.csv"
        self.filename2 = "TRIPADVISOR_PriceDiff.csv"
        self.cvs = ('Total_Agoda', 'Total_BookingCom', 'Total_Expedia', 'Total_Goibibo',
                    'Total_HotelsCom2', 'Total_MakeMyTrip', 'Total_Yatra', 'Total_TG', 'Total_Stayzilla')
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
            query = 'select * from %s' % self.name_g
            self.cursor.execute(query)
            mydir = os.path.join(
                self.CSV_PATH, datetime.datetime.now().strftime('%Y/%m/%d'))
            os.makedirs(mydir)
            sql_data = self.cursor.fetchall()
            with open(os.path.join(mydir, self.filename), 'w+') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(self.fields)
                for sql_data1 in sql_data:
                    four_el = tuple(sql_data1[1:-4])
                    sql_data1 = four_el + \
                        (dict_cities.get(sql_data1[3], ''),
                         self.ct_id.get(four_el[2], ['', 'NA'])[1])
                    csvwriter.writerow(sql_data1)
	    query_inventory =  "select city_name, property_name, TA_hotel_id, checkin, DX, Pax, sk, sk, CT_hotel_id, ct_price, ct_room_name,from_ta_url, which_case, cheapest_ota_name, cheapest_ota_price, cheapest_ota_room_name, Time from {}Inventory where status not like '%failed%' and Ranking_ClearTrip != 0 ".format(self.name_g)
            self.cursor.execute(query_inventory)
            no_ct_data = self.cursor.fetchall()
            if no_ct_data:
                for marknme in self.market_name_dict.values():
                    with open(os.path.join(mydir, "%s%s" % (marknme.replace(' ', '_'), '.csv')), 'w+') as csvfile:
                        csvwriter = csv.writer(csvfile)
                        csvwriter.writerow(self.fields3)
                        for mninventory in no_ct_data:
                            records_ = list(mninventory)
                            records_[6] = records_[6].split('_')[2]
                            records_[7] = records_[7].split('_')[-1]
                            records_[11] = records_[11].replace('Intl', '').lower()
                            records_[13] = records_[13].replace('Intl', '').lower()
			    if records_[13] == 'na':
				records_[13] = 'NA'
                            records_.append(
                                self.market_name_dict.get(records_[8], ''))
                            if records_[-1] == marknme:
                                csvwriter.writerow(records_)
            query_non = "select Total_ClearTrip, Total_Agoda, Total_BookingCom, Total_Expedia, Total_Goibibo, Total_HotelsCom2, Total_MakeMyTrip, Total_Yatra, Total_TG, Total_Stayzilla, city_name, property_name, TA_hotel_id, checkin, DX from %s where Total_ClearTrip!='-'" % self.name_g
            self.cursor.execute(query_non)
            pf_data = self.cursor.fetchall()
            if query_non:
                with open(os.path.join(mydir, self.filename2), 'w+') as csvfile2:
                    csvwriter = csv.writer(csvfile2)
                    csvwriter.writerow(self.fields2)
                    for pfd in pf_data:
                        total_ct = pfd[0]
                        total_others = pfd[1:10]
                        main_da = pfd[10:]
                        both_comb = zip(self.cvs, total_others)
                        filer_list = list(
                            filter(lambda x: x[1] != '-' and x[1] != '0', both_comb))
                        if filer_list:
                            min_price = min(filer_list, key=lambda t: t[1])
                            if min_price:
                                pricd_ = int(total_ct) - int(min_price[1])
                                if pricd_ > 3500:
                                    sql_pf_data = main_da + (self.ct_id.get(main_da[2], ['', 'NA'])[
                                                             1], pricd_, min_price[0].replace('Total_', ''), total_ct, min_price[1])
                                    csvwriter.writerow(sql_pf_data)
            self.cursor.close()
            self.con.close()
        except Exception, e:
            print str(e)


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-s', '--set_up', default='', help='set_up')
    (options, args) = parser.parse_args()
    TRIPADVISOR(options)
