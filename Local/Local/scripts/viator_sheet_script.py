import csv
import MySQLdb
from handle_utils import *

class Viatorcsv(object):
    def __init__(self):
        self.things_to_do_qry = 'select sk,tour_code,travel_code,name,image_url,description, no_of_ratings,expectations,no_of_reviews,city,location,duration,highlights,departure_time,category,departure_point,price,about_travel,travel_description,return_details,cancellation_policy,inclusions,exclusions,additional_info,local_operatorinfo,voucher_info from Things_To_Do'
        self.header_params_things_to_do = ['sk', 'tour_code' ,'travel_code' , 'name' ,'image_url' ,'description' ,'no_of_ratings' ,'expectations' ,'no_of_reviews' ,'city' ,'location' ,'duration' ,'highlights' ,'departure_time', 'category' ,'departure_point' ,'price' ,'about_travel' ,'travel_description' ,'return_details' ,'cancellation_policy' ,'inclusions' ,'exclusions' ,'additional_info' ,'local_operatorinfo' ,'voucher_info']
        

       
        self.file_name_things_to_do = ('viator_things_to_do_information2.csv')
        outfile_things_to_do = open(self.file_name_things_to_do, 'ab+')
        self.excel_file_things_to_do  = csv.writer(outfile_things_to_do)


    def close_sql_connection(self, conn, cursor):
        if cursor: cursor.close()
        if conn: conn.close()

    def create_cursor(self, db_, user_, pswd_, host_):
        try:
            con = MySQLdb.connect(db   = db_,
                  passwd                    = pswd_,
                  user                      = user_,
                  charset                   = "utf8",
                  host                      = host_,
                  use_unicode               = True)
            cur = con.cursor()
            return con, cur

        except:
            pass

    def main(self):
        con2_,cur2_ = self.create_cursor('VIATOR', 'root', '', 'localhost')
        cur2_.execute(self.things_to_do_qry)
        records = cur2_.fetchmany(6000)
        for index, record in enumerate(records):
            sk, tour_code, travel_code, name, image_url, description, no_of_ratings, expectations, no_of_reviews, city, location, duration, highlights, departure_time, category, departure_point, price, about_travel, travel_description, return_details, cancellation_policy, inclusions, exclusions, additional_info, local_operatorinfo, voucher_info = record
            values = [sk, tour_code, travel_code, name, image_url, description, no_of_ratings, expectations, no_of_reviews, city, location, duration,highlights, departure_time, category, departure_point, price, about_travel, travel_description, return_details, cancellation_policy, inclusions, exclusions, additional_info, local_operatorinfo, voucher_info]
            values = [str(i) if isinstance(i, float) else i for i in values]          
            values = [str(i) if isinstance(i, long) else i for i in values]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_things_to_do.writerow(self.header_params_things_to_do)
            self.excel_file_things_to_do.writerow(values)


        self.close_sql_connection(con2_, cur2_)
        

if __name__ == '__main__':
    Viatorcsv().main()
