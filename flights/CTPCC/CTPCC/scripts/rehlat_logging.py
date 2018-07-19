import os
import csv
import traceback
import logging
import datetime
import logging.handlers


class RHLOG(object):
    def __init__(self):
        self.MAIN_PATH = '/nfs/data/FLIGHTS_SCRAPED_DATA/REHLAT/'
        self.CSV_PATH = os.path.join(
        self.MAIN_PATH, datetime.datetime.now().strftime('%Y/%m/%d'))
        self.init_logger("logging.log")
        self.filename = 'rehlat_oneway.csv'

    def init_logger(self, filename, level=''):
        if not os.path.isdir(self.CSV_PATH):
            os.mkdir(self.CSV_PATH)
        file_name = os.path.join(self.CSV_PATH, filename)
        self.log = logging.getLogger(file_name)
        handler = logging.handlers.RotatingFileHandler(
            file_name, maxBytes=524288000, backupCount=5)
        self.log.addHandler(handler)
        self.log.setLevel(logging.DEBUG)

    def main(self):
        try:
            with open(os.path.join(self.CSV_PATH, self.filename)) as file_obj:
                reader = csv.reader(file_obj, delimiter=',')
                for index, line in enumerate(reader):
                    if index == 0:
                        fin_line = ['Sector', 'Date', 'Stops', 'FlightKey', 'ctBaseFare', 'ctTaxes', 'ctDiscount', 'ctTotalPriceSlashed', 'ctTotalPrice', 'ctClass', 'ctResponseTime', 'ctPosition', 'rhlBasefare', 'rhlTaxes', 'rhlTotalPrice', 'rhlClass', 'rhlResponseTime', 'rhlPosition', 'CompetitorSector', 'rhlCabinBag', 'rhlCheckInBag', 'ctMarkup']
                        #fin_line = ['Sector', 'Date', 'Stops', 'FlightKey', 'Price', 'Class', 'Trip', 'Pax count']
                    else:
                        #flt_id, airline, sector, dep_time, dx, stops, pax, trip_type, price = line
                        flt_id,airline,sector,dep_time,dx,stops,no_of_passengers,trip_type,rhlTotalprice = line
                        dep_time = datetime.datetime.strptime(line[3], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y-%H-%M-%S')
                        sectors = sector.split('-')
                        sector = '%s-%s'%(sectors[0], sectors[-1])
                        flt_id = flt_id.replace('-', '_').replace('<>', '_')
                        cabin_class = 'Economy'
                        #fin_line = [sector, dep_time, stops, flt_id, price, cabin_class, trip_type, pax]
                        fin_line = [sector, dep_time, stops, flt_id,'-','-','-','-','-','-','-','-','-','-',rhlTotalprice,cabin_class,'-','-','-','-','-','-','-']
                    self.log.info(':'.join(fin_line))
            print 'sucess'
        except:
            print 'fail'


if __name__ == '__main__':
    RHLOG().main()
