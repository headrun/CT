import csv
import MySQLdb
from scripts.handle_utils import *

class Thrillophiliacsv(object):
    def __init__(self):
        self.rental_qry = 'select city, id, name, rental_url, location, price, no_of_days_nights, image_urls, overview, rating, other_inclusions, things_to_carry, advisory, tour_type, cancellation_policy, refund_policy, confirmation_policy, reviews_count, review_url, special_offer, cashback from Rentals'
        self.header_params_rental = ['city', 'rental_id', 'rental_name', 'rental_url', 'location', 'price', 'no_of_days_nights', 'rental_images', 'overview', 'rating', 'other_inclusions', 'things_to_carry', 'advisory', 'tour_type', 'cancellation_policy', 'refund_policy', 'confirmation_policy', 'reviews_count', 'review_url', 'special_offer', 'cashback']
        
        self.activity_qry = 'select city, id, name, activity_url, location, price, no_of_days_nights, image_urls, overview, rating, itinerary, meal, activities_available, other_inclusions, things_to_carry, advisory, tour_type, cancellation_policy, refund_policy, confirmation_policy, reviews_count, review_url, special_offer, cashback from Activity'
        self.header_params_activity = ['city', 'activity_id', 'activity_name', 'activity_url', 'location', 'price', 'no_of_days_nights', 'activity_images', 'overview', 'rating', 'itinerary', 'meal','activities_available', 'other_inclusions', 'things_to_carry', 'advisory', 'tour_type', 'cancellation_policy', 'refund_policy', 'confirmation_policy', 'reviews_count', 'review_url', 'special_offer', 'cashback']
        
        self.stay_qry = 'select city, id, name, stay_url, location, price, no_of_days_nights, image_urls, overview, rating, itinerary, meal, activities_available, other_inclusions, things_to_carry, advisory, tour_type, cancellation_policy, refund_policy, confirmation_policy, reviews_count, review_url, special_offer, cashback from Stay'
        self.header_params_stay = ['city', 'stay_id', 'stay_name', 'stay_url', 'location', 'price', 'no_of_days_nights', 'stay_images', 'overview', 'rating', 'itinerary', 'meal', 'activitis_available', 'other_inclusions', 'things_to_carry', 'advisory', 'tour_type', 'cancellation_policy', 'refund_policy', 'confirmation_policy', 'reviews_count', 'review_url', 'special_offer', 'cashback']
        
        self.file_name_rental = ('thrilophilia_rental_information.csv')
        outfile_rental = open(self.file_name_rental, 'ab+')
        self.excel_file_rental  = csv.writer(outfile_rental)

        self.file_name_activity = ('thrilophilia_activity_information.csv')
        outfile_activity = open(self.file_name_activity,'ab+')
        self.excel_file_activity = csv.writer(outfile_activity)

        self.file_name_stay = ('thrilophilia_stay_information.csv')
        outfile_stay =  open(self.file_name_stay, 'ab+')
        self.excel_file_stay = csv.writer(outfile_stay)

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
        con2_,cur2_ = self.create_cursor('THRILLOPHILIA', 'root', '', 'localhost')
        cur2_.execute(self.rental_qry)
        records = cur2_.fetchmany(6000)
        for index, record in enumerate(records):
            city, rental_id, rental_name, rental_url, location, price, no_of_days_nights, rental_images, overview, rating, other_inclusions, things_to_carry, advisory, tour_type, cancellation_policy, refund_policy, confirmation_policy, reviews_count, review_url, special_offer, cashback = record
            values = [city, rental_id, rental_name, rental_url, location, price, no_of_days_nights, rental_images, overview, rating, other_inclusions, things_to_carry, advisory, tour_type, cancellation_policy, refund_policy, confirmation_policy, reviews_count, review_url, special_offer, cashback]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_rental.writerow(self.header_params_rental)
            self.excel_file_rental.writerow(values)

        cur2_.execute(self.activity_qry)
        records = cur2_.fetchmany(6000)
        for index, record in enumerate(records):
            city, activity_id, activity_name, activity_url, location, price, no_of_days_nights, activity_images, overview, rating, itinerary, meal, activities_available, other_inclusions, things_to_carry, advisory, tour_type, cancellation_policy, refund_policy, confirmation_policy, reviews_count, review_url, special_offer, cashback = record
            values = [city, activity_id, activity_name, activity_url, location, price, no_of_days_nights, activity_images, overview, rating, itinerary, meal, activities_available, other_inclusions, things_to_carry, advisory, tour_type, cancellation_policy, refund_policy, confirmation_policy, reviews_count, review_url, special_offer, cashback]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_activity.writerow(self.header_params_activity)
            self.excel_file_activity.writerow(values)
        
        cur2_.execute(self.stay_qry)
        records = cur2_.fetchmany(6000)
        for index, record in enumerate(records):
            city, stay_id, stay_name, stay_url, location, price, no_of_days_nights, stay_images, overview, rating, itinerary, meal, activities_available, other_inclusions, things_to_carry, advisory, tour_type, cancellation_policy, refund_policy, confirmation_policy, reviews_count, review_url, special_offer, cashback = record
            values = [city, stay_id, stay_name, stay_url, location, price, no_of_days_nights, stay_images, overview, rating, itinerary, meal, activities_available, other_inclusions, things_to_carry, advisory, tour_type, cancellation_policy, refund_policy, confirmation_policy, reviews_count, review_url, special_offer, cashback]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_stay.writerow(self.header_params_stay)
            self.excel_file_stay.writerow(values)


        self.close_sql_connection(con2_, cur2_)
        

if __name__ == '__main__':
    Thrillophiliacsv().main()
