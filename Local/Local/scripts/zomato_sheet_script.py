import re
import csv
import MySQLdb
import datetime
from handle_utils import *

class Zomatocsv(object):

    def __init__(self):
        self.selectqry = 'select sk,title,city,cusiness,restaraunt_type,contact_number,ratings,reviews,votes,latitude,longitude,discount_date,discount_text,address,opening_hours,highlights,category,price,reference_url from Restaraunt'
        self.header_params = ['sk','title','city','cusiness','restaraunt_type','contact_number','ratings','reviews','votes','latitude','longitude','discount_date','discount_text','address','opening_hours','highlights','category','price','reference_url']
        self.excel_file_name = 'zomato.csv'
        oupf = open(self.excel_file_name, 'ab+')
        self.todays_excel_file  = csv.writer(oupf)
        #self.applications_url = 'https://www.zomato.com'

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
        con2_,cur2_ = self.create_cursor('ZOMATO', 'root', '', 'localhost')
        cur2_.execute(self.selectqry)
        records = cur2_.fetchmany(5000)
        for index, rec in enumerate(records):
            sk,title,city,cusiness,restaraunt_type,contact_number,ratings,reviews,votes,latitude,longitude,discount_date,discount_text,address,opening_hours,highlights,category,price,reference_url = rec
            values = [sk,title,city,cusiness,restaraunt_type,contact_number,ratings,reviews,votes,latitude,longitude,discount_date,discount_text,address,opening_hours,highlights,category,price,reference_url]
            values = [str(i) if isinstance(i, float) else i for i in values]
            values =  [normalize(i) for i in values]
            if index == 0:
                self.todays_excel_file.writerow(self.header_params)
            self.todays_excel_file.writerow(values)         
        self.close_sql_connection(con2_, cur2_)
if __name__ == '__main__':
    Zomatocsv().main()

