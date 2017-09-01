import csv
import MySQLdb
from handle_utils import * 

class Littlecsv(object):
    def __init__(self):
        self.foodqry = 'select id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_image, place_url, reference_url from Food'
        self.food_header_params = ['article_id', 'city', 'article_name', 'posted_by', 'state', 'article_description', 'place_name', 'category', 'sub_category', 'working_hours', 'delivery_availablity', 'price', 'price_notes', 'contact_number', 'email', 'fb_link', 'web_link', 'twitter_link', 'instagram_link', 'nearest_railway_station', 'nearest_metro', 'location', 'street', 'address', 'place_images', 'place_url', 'reference_url']
        self.file_name_food = 'lbb_food_info.csv'
        outfile_food = open(self.file_name_food, 'ab+')
        self.excel_file_food  = csv.writer(outfile_food)
        
        self.lifestyleqry = 'select id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_image, place_url, reference_url from Lifestyle'
        self.lifestyle_header_params = ['article_id', 'city', 'article_name', 'posted_by', 'state', 'article_description', 'place_name', 'category', 'sub_category', 'working_hours', 'delivery_availablity', 'price', 'price_notes', 'contact_number', 'email', 'fb_link', 'web_link', 'twitter_link', 'instagram_link', 'nearest_railway_station', 'nearest_metro', 'location', 'street', 'address', 'place_images', 'place_url', 'reference_url']
        self.file_name_lifestyle = 'lbb_lifestyle_info.csv'
        outfile_lifestyle = open(self.file_name_lifestyle, 'ab+')
        self.excel_file_lifestyle  = csv.writer(outfile_lifestyle)

        self.shoppingqry = 'select id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_image, place_url, reference_url from Shopping'
        self.shopping_header_params = ['article_id', 'city', 'article_name', 'posted_by', 'state', 'article_description', 'place_name', 'category', 'sub_category', 'working_hours', 'delivery_availablity', 'price', 'price_notes', 'contact_number', 'email', 'fb_link', 'web_link', 'twitter_link', 'instagram_link', 'nearest_railway_station', 'nearest_metro', 'location', 'street', 'address', 'place_images', 'place_url', 'reference_url']
        self.file_name_shopping = 'lbb_shopping_info.csv'
        outfile_shopping = open(self.file_name_shopping, 'ab+')
        self.excel_file_shopping  = csv.writer(outfile_shopping)

        self.activityqry = 'select id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_image, place_url, reference_url from Activity'
        self.activity_header_params = ['article_id', 'city', 'article_name', 'posted_by', 'state', 'article_description', 'place_name', 'category', 'sub_category', 'working_hours', 'delivery_availablity', 'price', 'price_notes', 'contact_number', 'email', 'fb_link', 'web_link', 'twitter_link', 'instagram_link', 'nearest_railway_station', 'nearest_metro', 'location', 'street', 'address', 'place_images', 'place_url', 'reference_url']
        self.file_name_activity = 'lbb_activity_info.csv'
        outfile_activity = open(self.file_name_activity, 'ab+')
        self.excel_file_activity  = csv.writer(outfile_activity)
        
        self.cultureqry = 'select id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_image, place_url, reference_url from Culture'
        self.culture_header_params = ['article_id', 'city', 'article_name', 'posted_by', 'state', 'article_description', 'place_name', 'category', 'sub_category', 'working_hours', 'delivery_availablity', 'price', 'price_notes', 'contact_number', 'email', 'fb_link', 'web_link', 'twitter_link', 'instagram_link', 'nearest_railway_station', 'nearest_metro', 'location', 'street', 'address', 'place_images', 'place_url', 'reference_url']
        self.file_name_culture = 'lbb_culture_info.csv'
        outfile_culture = open(self.file_name_culture, 'ab+')
        self.excel_file_culture  = csv.writer(outfile_culture)
        
        self.travelqry = 'select id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_image, place_url, reference_url from Travel'
        self.travel_header_params = ['article_id', 'city', 'article_name', 'posted_by', 'state', 'article_description', 'place_name', 'category', 'sub_category', 'working_hours', 'delivery_availablity', 'price', 'price_notes', 'contact_number', 'email', 'fb_link', 'web_link', 'twitter_link', 'instagram_link', 'nearest_railway_station', 'nearest_metro', 'location', 'street', 'address', 'place_images', 'place_url', 'reference_url']
        self.file_name_travel = 'lbb_travel_info.csv'
        outfile_travel = open(self.file_name_travel, 'ab+')
        self.excel_file_travel  = csv.writer(outfile_travel)
        
        self.fitnessqry = 'select id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_image, place_url, reference_url from Fitness'
        self.fitness_header_params = ['article_id', 'city', 'article_name', 'posted_by', 'state', 'article_description', 'place_name', 'category', 'sub_category', 'working_hours', 'delivery_availablity', 'price', 'price_notes', 'contact_number', 'email', 'fb_link', 'web_link', 'twitter_link', 'instagram_link', 'nearest_railway_station', 'nearest_metro', 'location', 'street', 'address', 'place_images', 'place_url', 'reference_url']
        self.file_name_fitness = 'lbb_fitness_info.csv'
        outfile_fitness = open(self.file_name_fitness, 'ab+')
        self.excel_file_fitness  = csv.writer(outfile_fitness)


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
        con2_,cur2_ = self.create_cursor('LBB', 'root','', 'localhost')
        cur2_.execute(self.foodqry)
        records = cur2_.fetchall()
        for index, record in enumerate(records):
            article_id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_images, place_url, reference_url = record
	    values = [article_id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_images, place_url, reference_url]
            values =  [normalize(i) for i in values]
            if index == 0:
                self.excel_file_food.writerow(self.food_header_params)
            self.excel_file_food.writerow(values)

        cur2_.execute(self.lifestyleqry) 
        records = cur2_.fetchall()
        for index, record in enumerate(records):
            article_id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_images, place_url, reference_url = record
            values = [article_id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_images, place_url, reference_url]
            values =  [normalize(i) for i in values]
            if index == 0:
                self.excel_file_lifestyle.writerow(self.lifestyle_header_params)
            self.excel_file_lifestyle.writerow(values)

        cur2_.execute(self.shoppingqry)
        records = cur2_.fetchall()
        for index, record in enumerate(records):
            article_id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_images, place_url, reference_url = record
            values = [article_id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_images, place_url, reference_url]
            values =  [normalize(i) for i in values]
            if index == 0:
                self.excel_file_shopping.writerow(self.shopping_header_params)
            self.excel_file_shopping.writerow(values)

        cur2_.execute(self.activityqry)
        records = cur2_.fetchall()
        for index, record in enumerate(records):
            article_id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_images, place_url, reference_url  = record
            values = [article_id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_images, place_url, reference_url]
            values =  [normalize(i) for i in values]
            if index == 0:
                self.excel_file_activity.writerow(self.activity_header_params)
            self.excel_file_activity.writerow(values)

        cur2_.execute(self.cultureqry)
        records = cur2_.fetchall()
        for index, record in enumerate(records):
            article_id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_images, place_url, reference_url = record
            values = [article_id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_images, place_url, reference_url]
            values =  [normalize(i) for i in values]
            if index == 0:
                self.excel_file_culture.writerow(self.culture_header_params)
            self.excel_file_culture.writerow(values)

        cur2_.execute(self.travelqry)
        records = cur2_.fetchall()
        for index, record in enumerate(records):
            article_id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_images, place_url, reference_url = record
            values = [article_id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_images, place_url, reference_url]
            values =  [normalize(i) for i in values]
            if index == 0:
                self.excel_file_travel.writerow(self.travel_header_params)
            self.excel_file_travel.writerow(values)

        cur2_.execute(self.fitnessqry)
        records = cur2_.fetchall()
        for index, record in enumerate(records):
            article_id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_images, place_url, reference_url = record
            values = [article_id, city, article_name, posted_by, state, article_description, place_name, category, sub_category, working_hours, delivery_availablity, price, price_notes, contact_number, email, fb_link, web_link, twitter_link, instagram_link, nearest_railway_station, nearest_metro, location, street, address, place_images, place_url, reference_url]
            values =  [normalize(i) for i in values]
            if index == 0:
                self.excel_file_fitness.writerow(self.fitness_header_params)
            self.excel_file_fitness.writerow(values)


        self.close_sql_connection(con2_, cur2_)


if __name__ == '__main__':
    Littlecsv().main()

