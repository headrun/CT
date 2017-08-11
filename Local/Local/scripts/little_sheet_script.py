import csv
import MySQLdb
from handle_utils import *

class Littleappcsv(object):
    def __init__(self):
        self.food_drinks_qry = 'select sk, deal_sk, name, image_url, terms_conditions, contact_numbers, description, zipcode, latitude, longitude, state, city, location, address, no_of_ratings, no_of_reviews, item_name, price, offer, discount, available_weeks, available_timings,delivery_status, deal_terms_conditions, reference_url from  Food_Drinks'
        self.header_params_food_drinks = ['sk', 'deal_sk', 'name', 'image_url', 'terms_conditions', 'contact_numbers', 'description', 'zipcode', 'latitude', 'longitude', 'state', 'city', 'location', 'address', 'no_of_ratings', 'no_of_reviews', 'item_name', 'price', 'offer', 'discount', 'available_weeks', 'available_timings', 'delivery_status', 'deal_terms_conditions', 'reference_url']
        
        self.thingstodo_qry = 'select sk, deal_sk, name, image_url, terms_conditions, contact_numbers, description, zipcode, latitude, longitude, state, city, location, address, no_of_ratings, no_of_reviews, item_name, price, offer, discount, available_weeks, available_timings, deal_terms_conditions, reference_url from ThingsToDo'
        self.header_params_thingstodo = ['sk', 'deal_sk', 'name', 'image_url', 'terms_conditions', 'contact_numbers', 'description', 'zipcode', 'latitude', 'longitude', 'state', 'city', 'location', 'address', 'no_of_ratings', 'no_of_reviews', 'item_name', 'price', 'offer', 'discount', 'available_weeks', 'available_timings', 'deal_terms_conditions', 'reference_url']
        
        self.spas_salons_qry = 'select sk, deal_sk, name, image_url, terms_conditions, contact_numbers, description, zipcode, latitude, longitude, state, city, location, address, no_of_ratings, no_of_reviews, item_name, price, offer, discount, available_weeks, available_timings, deal_terms_conditions, reference_url from Spas_Salons'
        self.header_params_spas_salons = ['sk', 'deal_sk', 'name', 'image_url', 'terms_conditions', 'contact_numbers', 'description', 'zipcode', 'latitude', 'longitude', 'state', 'city', 'location', 'address', 'no_of_ratings', 'no_of_reviews', 'item_name', 'price', 'offer', 'discount', 'available_weeks', 'available_timings', 'deal_terms_conditions', 'reference_url']

       
        self.file_name_food_drinks = ('littleapp_food_drinks_information.csv')
        outfile_food_drinks = open(self.file_name_food_drinks, 'ab+')
        self.excel_file_food_drinks  = csv.writer(outfile_food_drinks)

        self.file_name_thingstodo = ('littleapp_thingstodo_information.csv')
        outfile_thingstodo = open(self.file_name_thingstodo,'ab+')
        self.excel_file_thingstodo = csv.writer(outfile_thingstodo)

        self.file_name_spas_salons = ('littleapp_spas_salons_information.csv')
        outfile_spas_salons =  open(self.file_name_spas_salons, 'ab+')
        self.excel_file_spas_salons = csv.writer(outfile_spas_salons)

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
        con2_,cur2_ = self.create_cursor('LITTLE', 'root', '', 'localhost')
        cur2_.execute(self.food_drinks_qry)
        records = cur2_.fetchmany(6000)
        for index, record in enumerate(records):
            sk, deal_sk, name, image_url, terms_conditions, contact_numbers, description, zipcode, latitude, longitude, state, city, location, address, no_of_ratings, no_of_reviews, item_name, price, offer, discount, available_weeks, available_timings,delivery_status, deal_terms_conditions, reference_url = record
            values = [sk, deal_sk, name, image_url, terms_conditions, contact_numbers, description, zipcode, latitude, longitude, state, city, location, address, no_of_ratings, no_of_reviews, item_name, price, offer, discount, available_weeks, available_timings,delivery_status, deal_terms_conditions, reference_url]
            values = [str(i) if isinstance(i, float) else i for i in values]          
            values = [str(i) if isinstance(i, long) else i for i in values]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_food_drinks.writerow(self.header_params_food_drinks)
            self.excel_file_food_drinks.writerow(values)

        cur2_.execute(self.thingstodo_qry)
        records = cur2_.fetchmany(6000)
        for index, record in enumerate(records):
            sk, deal_sk, name, image_url, terms_conditions, contact_numbers, description, zipcode, latitude, longitude, state, city, location, address, no_of_ratings, no_of_reviews, item_name, price, offer, discount, available_weeks, available_timings, deal_terms_conditions, reference_url= record
            values = [sk, deal_sk, name, image_url, terms_conditions, contact_numbers, description, zipcode, latitude, longitude, state, city, location, address, no_of_ratings, no_of_reviews, item_name, price, offer, discount, available_weeks, available_timings, deal_terms_conditions, reference_url]
            values = [str(i) if isinstance(i, float) else i for i in values]
            values = [str(i) if isinstance(i, long) else i for i in values]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_thingstodo.writerow(self.header_params_thingstodo)
            self.excel_file_thingstodo.writerow(values)
        
        cur2_.execute(self.spas_salons_qry)
        records = cur2_.fetchmany(6000)
        for index, record in enumerate(records):
            sk, deal_sk, name, image_url, terms_conditions, contact_numbers, description, zipcode, latitude, longitude, state, city, location, address, no_of_ratings, no_of_reviews, item_name, price, offer, discount, available_weeks, available_timings, deal_terms_conditions, reference_url = record
            values =[sk, deal_sk, name, image_url, terms_conditions, contact_numbers, description, zipcode, latitude, longitude, state, city, location, address, no_of_ratings, no_of_reviews, item_name, price, offer, discount, available_weeks, available_timings, deal_terms_conditions, reference_url]
            values = [str(i) if isinstance(i, float) else i for i in values]
            values = [str(i) if isinstance(i, long) else i for i in values]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_spas_salons.writerow(self.header_params_spas_salons)
            self.excel_file_spas_salons.writerow(values)


        self.close_sql_connection(con2_, cur2_)
        

if __name__ == '__main__':
    Littleappcsv().main()
