import MySQLdb
import csv
import os
import datetime
import optparse
import json
import sys
reload(sys)
sys.setdefaultencoding('UTF8')
from auto_input import *


class Ctcontent(object):
    def __init__(self, options):
        user = 'root'  # your username
        passwd = DB_PASSWORD  # your password
        host = 'localhost'  # your host
        db = PROD_META_DB  # database where your table is stored
        self.con = MySQLdb.connect(user=user, host=host, db=db, passwd=DB_PASSWORD, charset='utf8')
        self.cursor = self.con.cursor()
        inputs_list = ['Cleartrip', 'Booking', 'Expedia', 'Tajawal']
        if options.set_up:
            if options.set_up not in inputs_list:
                print 'need to specify soruce name properly and must be any one in this%s' % ','.join(
                    inputs_list)
                sys.exit(-1)
            self.fields = ['HOTEL NAME', 'HOTEL ID', 'HOTEL ADDRESS', 'HOTEL LATITUDE',
                           'HOTEL LONGITUDE', 'CITY', 'HOTEL STAR RATING', 'HOTEL DETAILS', 'AMENITIES', 'HOTEL URL']
            self.CSV_PATH = os.getcwd()
            self.filename = "%sCONTENT.csv" % options.set_up
            self.data_date = str(datetime.datetime.now().date())
            self.main()
        else:
            print 'give the input for this script'

    def main(self):
        try:
            query = "select hotel_name, hotel_id, address, locality_latitude, locality_longitude, city, star_rating, description, amenities, html_hotel_url  from %scontentscore" % options.set_up
            self.cursor.execute(query)
            sql_data = self.cursor.fetchall()
            mydir = os.path.join(
                self.CSV_PATH, datetime.datetime.now().strftime('%Y/%m/%d'))
            os.makedirs(mydir)
            with open(os.path.join(mydir, self.filename), 'w+') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(self.fields)
                for dat in sql_data:
                    csvwriter.writerow(dat)
            self.cursor.close()
            self.con.close()
        except Exception, e:
            print str(e)


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-s', '--set_up', default='', help='set_up')
    (options, args) = parser.parse_args()
    Ctcontent(options)
