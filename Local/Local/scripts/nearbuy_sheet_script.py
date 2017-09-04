import csv
import MySQLdb
from handle_utils import *

class Nearbuycsv(object):
    def __init__(self):
        self.spa_qry = "select id, city, name, place_category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, image_urls, reference_url from Spa"
        self.offer_qry = "select offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details,  price_original, price_discounted, price_notes from Offer where program_id= '%s'" 
        self.header_params_spa = ['spa_id', 'city', 'spa_name', 'category', 'location', 'addresses', 'how_to_use_offer', 'cancelletion_policy', 'things_to_remember', 'rating', 'rating_type', 'spa_images', 'reference_url', 'offer_title', 'offer_description', 'offer_inclusions', 'offer_validity', 'offer_validity_details','price_original', 'price_discounted', 'price_notes']
        
        self.eatout_qry = "select id, city, name, place_category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, image_urls, reference_url from Eatout"
        self.header_params_eatout = ['restaurant_id', 'city', 'restaurant_name', 'category', 'location', 'addresses', 'how_to_use_offer', 'cancelletion_policy', 'things_to_remember', 'rating', 'rating_type', 'restaurant_images', 'reference_url', 'offer_title', 'offer_description', 'offer_inclusions', 'offer_validity', 'offer_validity_details','price_original', 'price_discounted', 'price_notes']

        self.activity_qry = "select id, city, name, place_category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, image_urls, reference_url from Activity"
        self.header_params_activity = ['activity_id', 'city', 'activity_name', 'category', 'location', 'addresses', 'how_to_use_offer', 'cancelletion_policy', 'things_to_remember', 'rating', 'rating_type', 'activity_images', 'reference_url', 'offer_title', 'offer_description', 'offer_inclusions', 'offer_validity', 'offer_validity_details','price_original', 'price_discounted', 'price_notes']

        self.health_qry = "select id, city, name, place_category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, image_urls, reference_url from Health"
        self.header_params_health = ['hospital_id', 'city', 'hospital_name', 'category', 'location', 'addresses', 'how_to_use_offer', 'cancelletion_policy', 'things_to_remember', 'rating', 'rating_type', 'hospital_images', 'reference_url', 'offer_title', 'offer_description', 'offer_inclusions', 'offer_validity', 'offer_validity_details', 'price_original', 'price_discounted', 'price_notes']

        self.hobbie_qry = "select id, city, name, place_category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, image_urls, reference_url from Hobbie"
        self.header_params_hobbie = ['place_id', 'city', 'place_name', 'category', 'location', 'addresses', 'how_to_use_offer', 'cancelletion_policy', 'things_to_remember', 'rating', 'rating_type', 'place_images', 'reference_url', 'offer_title', 'offer_description', 'offer_inclusions', 'offer_validity', 'offer_validity_details', 'price_original', 'price_discounted', 'price_notes']
        
        self.homeauto_qry = "select id, city, name, place_category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, image_urls, reference_url from Homeauto"
        self.header_params_homeauto = ['place_id', 'city', 'place_name', 'category', 'location', 'addresses', 'how_to_use_offer', 'cancelletion_policy', 'things_to_remember', 'rating', 'rating_type', 'place_images', 'reference_url', 'offer_title', 'offer_description', 'offer_inclusions', 'offer_validity', 'offer_validity_details', 'price_original', 'price_discounted', 'price_notes']

        self.hotel_qry = "select id, city, name, place_category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, image_urls, reference_url from Hotel"
        self.header_params_hotel = ['hotel_id', 'city', 'hotel_name', 'category', 'location', 'addresses', 'how_to_use_offer', 'cancelletion_policy', 'things_to_remember', 'rating', 'rating_type', 'hotel_images', 'reference_url', 'offer_title', 'offer_description', 'offer_inclusions', 'offer_validity', 'offer_validity_details', 'price_original', 'price_discounted', 'price_notes']

        self.salon_qry = "select id, city, name, place_category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, image_urls, reference_url from Salon"
        self.header_params_salon = ['place_id', 'city', 'place_name', 'category', 'location', 'addresses', 'how_to_use_offer', 'cancelletion_policy', 'things_to_remember', 'rating', 'rating_type', 'place_images', 'reference_url', 'offer_title', 'offer_description', 'offer_inclusions', 'offer_validity', 'offer_validity_details', 'price_original', 'price_discounted', 'price_notes']

        self.shopping_qry = "select id, city, name, place_category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, terms_conditions, image_urls, reference_url from Shopping"
        self.header_params_shopping = ['place_id', 'city', 'place_name', 'category', 'location', 'addresses', 'how_to_use_offer', 'cancelletion_policy', 'things_to_remember', 'rating', 'rating_type', 'terms_conditions', 'place_images', 'reference_url', 'offer_title', 'offer_description', 'offer_inclusions', 'offer_validity', 'offer_validity_details', 'price_original', 'price_discounted', 'price_notes']

        self.theatre_qry = "select id, city, name, place_category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, image_urls, reference_url from Theatre"
        self.header_params_theatre = ['place_id', 'city', 'place_name', 'category', 'location', 'addresses', 'how_to_use_offer', 'cancelletion_policy', 'things_to_remember', 'rating', 'rating_type', 'place_images', 'reference_url', 'offer_title', 'offer_description', 'offer_inclusions', 'offer_validity', 'offer_validity_details', 'price_original', 'price_discounted', 'price_notes']

        self.file_name_spa = ('nearbuy_spa_info.csv')
        outfile_spa = open(self.file_name_spa, 'ab+')
        self.excel_file_spa = csv.writer(outfile_spa)

        self.file_name_eatout = ('nearbuy_eatout_info.csv')
        outfile_eatout = open(self.file_name_eatout, 'ab+')
        self.excel_file_eatout = csv.writer(outfile_eatout)

        self.file_name_activity = ('nearbuy_activity_info.csv')
        outfile_activity = open(self.file_name_activity, 'ab+')
        self.excel_file_activity =  csv.writer(outfile_activity)

        self.file_name_health = ('nearbuy_health_info.csv')
        outfile_health = open(self.file_name_health, 'ab+')
        self.excel_file_health = csv.writer(outfile_health)

        self.file_name_hobbie = ('nearbuy_hobbie_info.csv')
        outfile_hobbie =  open(self.file_name_hobbie, 'ab+')
        self.excel_file_hobbie = csv.writer(outfile_hobbie)

        self.file_name_homeauto = ('nearbuy_homeauto_info.csv')
        outfile_homeauto = open(self.file_name_homeauto, 'ab+')
        self.excel_file_homeauto = csv.writer(outfile_homeauto)

        self.file_name_hotel = ('nearbuy_hotel_info.csv')
        outfile_hotel = open(self.file_name_hotel, 'ab+')
        self.excel_file_hotel = csv.writer(outfile_hotel)

        self.file_name_salon = ('nearbuy_salon_info.csv')
        outfile_salon = open(self.file_name_salon, 'ab+')
        self.excel_file_salon = csv.writer(outfile_salon)

        self.file_name_shopping = ('nearbuy_shopping_info.csv')
        outfile_shopping = open(self.file_name_shopping, 'ab+')
        self.excel_file_shopping = csv.writer(outfile_shopping)

        self.file_name_theatre = ('nearbuy_theatre_info.csv')
        outfile_theatre = open(self.file_name_theatre, 'ab+')
        self.excel_file_theatre = csv.writer(outfile_theatre)

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
        con2_,cur2_ = self.create_cursor('NEARBUY', 'root', '', 'localhost')
        cur2_.execute(self.spa_qry)
        spa_values = cur2_.fetchall()
        for value in spa_values:
            id_ = value[0]
            cur2_.execute(self.offer_qry % id_)
            rows = cur2_.fetchall()
            spa_id, city, spa_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, spa_images, reference_url = value 
            spa_values = [spa_id, city, spa_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type,spa_images,reference_url]   
            for _row in rows:
                offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes = _row

                offer_values = [offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes]
                values = spa_values + offer_values
                for index in enumerate(values):
                    values =  [normalize(i) for i in values]
                    if index == 0:
                        self.excel_file_spa.writerow(self.header_params_spa)
                self.excel_file_spa.writerow(values)

        cur2_.execute(self.eatout_qry)
        eatout_values = cur2_.fetchall()
        for value in eatout_values:
            id_ = value[0]
            cur2_.execute(self.offer_qry % id_)
            rows = cur2_.fetchall()
            restaurant_id, city, restaurant_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, restaurant_images, reference_url = value
            eatout_values = [restaurant_id, city, restaurant_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, restaurant_images, reference_url]
            for _row in rows:
                offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes = _row
                offer_values = [offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes]
                values = eatout_values + offer_values
                for index, rec in enumerate(values):
                    values =  [normalize(i) for i in values]
                if index == 0:
                    self.excel_file_eatout.writerow(self.header_params_eatout)
                self.excel_file_eatout.writerow(values)

        cur2_.execute(self.activity_qry)
        activity_values = cur2_.fetchall()
        for value in activity_values:
            id_ = value[0]
            cur2_.execute(self.offer_qry % id_)
            rows = cur2_.fetchall()
            activity_id, city, activity_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, activity_images, reference_url = value
            activity_values = [activity_id, city, activity_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, activity_images, reference_url]
            for _row in rows:
                offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes = _row
                offer_values = [offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes]
                values = activity_values + offer_values
                for index, rec in enumerate(values):
                    values =  [normalize(i) for i in values]
                if index == 0:
                    self.excel_file_activity.writerow(self.header_params_activity)
                self.excel_file_activity.writerow(values)

        cur2_.execute(self.health_qry)
        health_values = cur2_.fetchall()
        for value in health_values:
            id_ = value[0]
            cur2_.execute(self.offer_qry % id_)
            rows = cur2_.fetchall()
            hospital_id, city, hospital_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, hospital_images, reference_url = value
            health_values = [hospital_id, city, hospital_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, hospital_images, reference_url]
            for _row in rows:
                offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes = _row
                offer_values = [offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes]
                values = health_values + offer_values
                for index, rec in enumerate(values):
                    values =  [normalize(i) for i in values]
                if index == 0:
                    self.excel_file_health.writerow(self.header_params_health)
                self.excel_file_health.writerow(values)

        cur2_.execute(self.hobbie_qry)
        hobbie_values = cur2_.fetchall()
        for value in hobbie_values:
            id_ = value[0]
            cur2_.execute(self.offer_qry % id_)
            rows = cur2_.fetchall()
            place_id, city, place_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, place_images, reference_url = value
            hobbie_values = [place_id, city, place_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, place_images, reference_url]
            for _row in rows:
                offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes = _row
                offer_values = [offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes]
                values = hobbie_values + offer_values
                for index, rec in enumerate(values):
                    values =  [normalize(i) for i in values]
                if index == 0:
                    self.excel_file_hobbie.writerow(self.header_params_hobbie)
                self.excel_file_hobbie.writerow(values)
        
        cur2_.execute(self.homeauto_qry)
        homeauto_values = cur2_.fetchall()
        for value in homeauto_values:
            id_ = value[0]
            cur2_.execute(self.offer_qry % id_)
            rows = cur2_.fetchall()
            place_id, city, place_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, place_images, reference_url = value
            homeauto_values = [place_id, city, place_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, place_images, reference_url]
            for _row in rows:
                offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes = _row
                offer_values = [offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes]
                values = homeauto_values + offer_values
                for index, rec in enumerate(values):
                    values =  [normalize(i) for i in values]
                if index == 0:
                    self.excel_file_homeauto.writerow(self.header_params_homeauto)
                self.excel_file_homeauto.writerow(values)

        cur2_.execute(self.hotel_qry)
        hotel_values = cur2_.fetchall()
        for value in hotel_values:
            id_ = value[0]
            cur2_.execute(self.offer_qry % id_)
            rows = cur2_.fetchall()
            hotel_id, city, hotel_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, hotel_images, reference_url = value
            hotel_values = [hotel_id, city, hotel_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, hotel_images, reference_url]
            for _row in rows:
                offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes = _row
                offer_values = [offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes]
                values = hotel_values + offer_values
                for index, rec in enumerate(values):
                    values =  [normalize(i) for i in values]
                if index == 0:
                    self.excel_file_hotel.writerow(self.header_params_hotel)
                self.excel_file_hotel.writerow(values)

        cur2_.execute(self.salon_qry)
        salon_values = cur2_.fetchall()
        for value in salon_values:
            id_ = value[0]
            cur2_.execute(self.offer_qry % id_)
            rows = cur2_.fetchall()
            place_id, city, place_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, place_images,reference_url = value
            salon_values = [place_id, city, place_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, place_images, reference_url]
            for _row in rows:
                offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes = _row
                offer_values = [offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes]
                values = salon_values + offer_values
                for index, rec in enumerate(values):
                     values =  [normalize(i) for i in values]
                if index == 0:
                    self.excel_file_salon.writerow(self.header_params_salon)
                self.excel_file_salon.writerow(values)

        cur2_.execute(self.shopping_qry)
        shopping_values =  cur2_.fetchall()
        for value in shopping_values:
            id_ = value[0]
            cur2_.execute(self.offer_qry % id_)
            rows = cur2_.fetchall()
            place_id, city, place_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, terms_conditions, place_images, reference_url = value
            shopping_values = [place_id, city, place_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, terms_conditions, place_images, reference_url]
            for _row in rows:
                offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes = _row
                offer_values = [offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes]
                values = shopping_values + offer_values
                for index, rec in enumerate(values):
                    values =  [normalize(i) for i in values]
                if index == 0:
                    self.excel_file_shopping.writerow(self.header_params_shopping)
                self.excel_file_shopping.writerow(values)

        cur2_.execute(self.theatre_qry)
        theatre_values = cur2_.fetchall()
        for value in theatre_values:
            id_ = value[0]
            cur2_.execute(self.offer_qry % id_)
            rows = cur2_.fetchall()
            place_id, city, place_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, place_images, reference_url = value
            theatre_values = [place_id, city, place_name, category, location, addresses, how_to_use_offer, cancelletion_policy, things_to_remember, rating, rating_type, place_images, reference_url]
            for _row in rows:
                offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes = _row
                offer_values = [offer_title, offer_description, offer_inclusions, offer_validity, offer_validity_details, price_original, price_discounted, price_notes]
                values = theatre_values + offer_values
                for index, rec in enumerate(values):
                    values =  [normalize(i) for i in values]
                if index == 0:
                    self.excel_file_theatre.writerow(self.header_params_theatre)
                self.excel_file_theatre.writerow(values)

        self.close_sql_connection(con2_, cur2_)

if __name__ == '__main__':
    Nearbuycsv().main()
