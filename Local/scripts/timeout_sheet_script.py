import csv
import MySQLdb
from handle_utils import *

class Timeoutcsv(object):
    def __init__(self):
        self.food_drinks_qry = 'select sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins, available_timings from Food_Drinks'
        self.header_params_food_drinks = ['sk', 'name', 'image_url', 'contact_numbers','price', 'description', 'latitude', 'longitude', 'city', 'address', 'Website_name', 'no_of_likes', 'no_of_checkins', 'available_timings']
      
        self.theatre_arts_qry = 'select sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name,no_of_likes, no_of_checkins, available_timings from Theatre_Arts'
        self.header_params_theatre_arts = ['sk', 'name', 'image_url', 'contact_numbers','price', 'description', 'latitude', 'longitude', 'city', 'address', 'Website_name', 'no_of_likes', 'no_of_checkins', 'available_timings']

        self.music_nightlife_qry = 'select sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins, available_timings from Music_Nightlife'
        self.header_params_music_nightlife = ['sk', 'name', 'image_url', 'contact_numbers','price', 'description', 'latitude', 'longitude', 'city', 'address', 'Website_name', 'no_of_likes', 'no_of_checkins', 'available_timings']

        self.city_guide_qry = 'select sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins, available_timings from City_Guide'
        self.header_params_city_guide = ['sk', 'name', 'image_url', 'contact_numbers','price', 'description', 'latitude', 'longitude', 'city', 'address', 'Website_name', 'no_of_likes', 'no_of_checkins', 'available_timings']

        self.shopping_style_qry = 'select sk, name, image_url, contact_numbers, price,description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins, available_timings from Shopping_Style'
        self.header_params_shopping_style = ['sk', 'name', 'image_url', 'contact_numbers','price', 'description', 'latitude', 'longitude', 'city', 'address', 'Website_name', 'no_of_likes', 'no_of_checkins', 'available_timings']

        self.movie_theatres_qry = 'select sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins,  available_timings from Movie_Theatres'
        self.header_params_movie_theatres = ['sk', 'name', 'image_url', 'contact_numbers','price', 'description', 'latitude', 'longitude', 'city', 'address', 'Website_name', 'no_of_likes', 'no_of_checkins', 'available_timings']

        self.things_to_do_qry = 'select sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name,no_of_likes, no_of_checkins,  available_timings from Things_To_Do'
        self.header_params_things_to_do = ['sk', 'name', 'image_url', 'contact_numbers', 'price','description', 'latitude', 'longitude', 'city', 'address', 'Website_name', 'no_of_likes', 'no_of_checkins', 'available_timings']


        self.file_name_food_drinks = ('timeout_food_drinks_information2.csv')
        outfile_food_drinks = open(self.file_name_food_drinks, 'ab+')
        self.excel_file_food_drinks  = csv.writer(outfile_food_drinks)

        self.file_name_theatre_arts = ('timeout_theatre_arts_information2.csv')
        outfile_theatre_arts = open(self.file_name_theatre_arts,'ab+')
        self.excel_file_theatre_arts = csv.writer(outfile_theatre_arts)

        self.file_name_music_nightlife = ('timeout_music_nightlife_information2.csv')
        outfile_music_nightlife =  open(self.file_name_music_nightlife, 'ab+')
        self.excel_file_music_nightlife = csv.writer(outfile_music_nightlife)

        self.file_name_city_guide = ('timeout_city_guide_information2.csv')
        outfile_city_guide = open(self.file_name_city_guide, 'ab+')
        self.excel_file_city_guide  = csv.writer(outfile_city_guide)

        self.file_name_shopping_style = ('timeout_shopping_style_information2.csv')
        outfile_shopping_style = open(self.file_name_shopping_style, 'ab+')
        self.excel_file_shopping_style = csv.writer(outfile_shopping_style)

        self.file_name_movie_theatres = ('timeout_movie_theatres_information2.csv')
        outfile_movie_theatres = open(self.file_name_movie_theatres, 'ab+')
        self.excel_file_movie_theatres = csv.writer(outfile_movie_theatres)

        self.file_name_things_to_do = ('timeout_things_to_do_information2.csv')
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
        con2_,cur2_ = self.create_cursor('TIMEOUT', 'root', '', 'localhost')
        cur2_.execute(self.food_drinks_qry)
        records = cur2_.fetchmany(6000)
        for index, record in enumerate(records):
            sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins,available_timings = record
            values = [sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins, available_timings]
            values = [str(i) if isinstance(i, float) else i for i in values]          
            values = [str(i) if isinstance(i, long) else i for i in values]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_food_drinks.writerow(self.header_params_food_drinks)
            self.excel_file_food_drinks.writerow(values)

        cur2_.execute(self.theatre_arts_qry)
        records = cur2_.fetchmany(6000)
        for index, record in enumerate(records):
            sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins,available_timings = record
            values = [sk, name, image_url, contact_numbers, price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins, available_timings]
            values = [str(i) if isinstance(i, float) else i for i in values]
            values = [str(i) if isinstance(i, long) else i for i in values]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_theatre_arts.writerow(self.header_params_theatre_arts)
            self.excel_file_theatre_arts.writerow(values)
        
        cur2_.execute(self.music_nightlife_qry)
        records = cur2_.fetchmany(6000)
        for index, record in enumerate(records):
            sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins,available_timings = record
            values = [sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins, available_timings]
            values = [str(i) if isinstance(i, float) else i for i in values]
            values = [str(i) if isinstance(i, long) else i for i in values]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_music_nightlife.writerow(self.header_params_music_nightlife)
            self.excel_file_music_nightlife.writerow(values)

        cur2_.execute(self.city_guide_qry)
        records = cur2_.fetchmany(6000)
        for index, record in enumerate(records):
            sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins,available_timings = record
            values = [sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins, available_timings]
            values = [str(i) if isinstance(i, float) else i for i in values]
            values = [str(i) if isinstance(i, long) else i for i in values]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_city_guide.writerow(self.header_params_city_guide)
            self.excel_file_city_guide.writerow(values)


        cur2_.execute(self.shopping_style_qry)
        records = cur2_.fetchmany(6000)
        for index, record in enumerate(records):
            sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins,available_timings = record
            values = [sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins, available_timings]
            values = [str(i) if isinstance(i, float) else i for i in values]
            values = [str(i) if isinstance(i, long) else i for i in values]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_shopping_style.writerow(self.header_params_shopping_style)
            self.excel_file_shopping_style.writerow(values)

        cur2_.execute(self.movie_theatres_qry)
        records = cur2_.fetchmany(6000)
        for index, record in enumerate(records):
            sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins,available_timings = record
            values = [sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins, available_timings]
            values = [str(i) if isinstance(i, float) else i for i in values]
            values = [str(i) if isinstance(i, long) else i for i in values]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_movie_theatres.writerow(self.header_params_movie_theatres)
            self.excel_file_movie_theatres.writerow(values)
 
        cur2_.execute(self.things_to_do_qry)
        records = cur2_.fetchmany(25000)
        for index, record in enumerate(records):
            sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins,available_timings = record
            values = [sk, name, image_url, contact_numbers,price, description, latitude, longitude, city, address, Website_name, no_of_likes, no_of_checkins, available_timings]
            values = [str(i) if isinstance(i, float) else i for i in values]
            values = [str(i) if isinstance(i, long) else i for i in values]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_things_to_do.writerow(self.header_params_things_to_do)
            self.excel_file_things_to_do.writerow(values)

        self.close_sql_connection(con2_, cur2_)
        

if __name__ == '__main__':
    Timeoutcsv().main()
