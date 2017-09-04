import csv
import MySQLdb
from handle_utils import *

class Explaracsv(object):
    def __init__(self):
        self.entertainment_qry = 'select id, city, name, location, address, dates, timings, image_urls, details, organizer, price, reference_url, webpage from Entertainment'
        self.adventure_qry = 'select id, city, name, location, address, dates, timings, image_urls, details, organizer, price, reference_url, webpage from Adventure'
        self.alumni_qry = 'select id, city, name, location, address, dates, timings, image_urls, details, organizer, price, reference_url, webpage from Alumni'
        self.biztech_qry = 'select id, city, name, location, address, dates, timings, image_urls, details, organizer, price, reference_url, webpage from BizTech'
        self.food_qry = 'select id, city, name, location, address, dates, timings, image_urls, details, organizer, price, reference_url, webpage from Food'
        self.interest_qry = 'select id, city, name, location, address, dates, timings, image_urls, details, organizer, price, reference_url, webpage from Interest'
        self.sports_qry = 'select id, city, name, location, address, dates, timings, image_urls, details, organizer, price, reference_url, webpage from Sports'
        self.headers = ['event_id', 'city', 'event_name', 'location', 'address', 'dates', 'timings', 'images', 'details', 'organizer', 'price', 'reference_url', 'webpage']
        self.file_name_entertainment = 'explara_entertainment_info.csv'
        outfile_entertainment = open(self.file_name_entertainment, 'ab+')
        self.excel_file_entertainment = csv.writer(outfile_entertainment)

        self.file_name_adventure = 'explara_adventure_info.csv'
        outfile_adventure = open(self.file_name_adventure, 'ab+')
        self.excel_file_adventure = csv.writer(outfile_adventure)

        self.file_name_alumni = 'explara_alumni_info.csv'
        outfile_alumni = open(self.file_name_alumni, 'ab+')
        self.excel_file_alumni = csv.writer(outfile_alumni)

        self.file_name_biztech = 'explara_biztech_info.csv'
        outfile_biztech = open(self.file_name_biztech, 'ab+')
        self.excel_file_biztech = csv.writer(outfile_biztech)

        self.file_name_food = 'explara_food_info.csv'
        outfile_food = open(self.file_name_food, 'ab+')
        self.excel_file_food = csv.writer(outfile_food)

        self.file_name_interest = 'explara_interest_info.csv'
        outfile_interest = open(self.file_name_interest, 'ab+')
        self.excel_file_interest = csv.writer(outfile_interest)

        self.file_name_sports = 'explara_sports_info.csv'
        outfile_sports = open(self.file_name_sports, 'ab+')
        self.excel_file_sports = csv.writer(outfile_sports)

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
        con2_,cur2_ = self.create_cursor('EXPLARA', 'root', '', 'localhost')
        cur2_.execute(self.entertainment_qry)
        records = cur2_.fetchall()
        for index, record in enumerate(records):
            event_id, city, event_name, location, address, dates, timings, images, details, organizer, price, reference_url, webpage = record
            values = [event_id, city, event_name, location, address, dates, timings, images, details, organizer, price, reference_url, webpage]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_entertainment.writerow(self.headers)
            self.excel_file_entertainment.writerow(values)

        cur2_.execute(self.adventure_qry)
        records = cur2_.fetchall()
        for index, record in enumerate(records):
            event_id, city, event_name, location, address, dates, timings, images, details, organizer, price, reference_url, webpage = record
            values = [event_id, city, event_name, location, address, dates, timings, images, details, organizer, price, reference_url, webpage]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_adventure.writerow(self.headers)
            self.excel_file_adventure.writerow(values)

        cur2_.execute(self.alumni_qry)
        records = cur2_.fetchall()
        for index, record in enumerate(records):
            event_id, city, event_name, location, address, dates, timings, images, details, organizer, price, reference_url, webpage = record
            values = [event_id, city, event_name, location, address, dates, timings, images, details, organizer, price, reference_url, webpage]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_alumni.writerow(self.headers)
            self.excel_file_alumni.writerow(values)

        cur2_.execute(self.biztech_qry)
        records = cur2_.fetchall()
        for index, record in enumerate(records):
            event_id, city, event_name, location, address, dates, timings, images, details, organizer, price, reference_url, webpage = record
            values = [event_id, city, event_name, location, address, dates, timings, images, details, organizer, price, reference_url, webpage]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_biztech.writerow(self.headers)
            self.excel_file_biztech.writerow(values)

        cur2_.execute(self.food_qry)
        records = cur2_.fetchall()
        for index, record in enumerate(records):
            event_id, city, event_name, location, address, dates, timings, images, details, organizer, price, reference_url, webpage = record
            values = [event_id, city, event_name, location, address, dates, timings, images, details, organizer, price, reference_url, webpage]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_food.writerow(self.headers)
            self.excel_file_food.writerow(values)

        cur2_.execute(self.interest_qry)
        records = cur2_.fetchall()
        for index, record in enumerate(records):
            event_id, city, event_name, location, address, dates, timings, images, details, organizer, price, reference_url, webpage = record
            values = [event_id, city, event_name, location, address, dates, timings, images, details, organizer, price, reference_url, webpage]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_interest.writerow(self.headers)
            self.excel_file_interest.writerow(values)

        cur2_.execute(self.sports_qry)
        records = cur2_.fetchall()
        for index, record in enumerate(records):
            event_id, city, event_name, location, address, dates, timings, images, details, organizer, price, reference_url, webpage = record
            values = [event_id, city, event_name, location, address, dates, timings, images, details, organizer, price, reference_url, webpage]
            values = [normalize(i) for i in values]
            if index == 0:
                self.excel_file_sports.writerow(self.headers)
            self.excel_file_sports.writerow(values)

        self.close_sql_connection(con2_, cur2_)

if __name__ == '__main__':
    Explaracsv().main()
