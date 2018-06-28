import os
import csv
import traceback
import logging
import datetime
import logging.handlers

class TALOG(object):
    def __init__(self):
	self.MAIN_PATH = '/NFS/data/HOTELS_SCRAPED_DATA/TRIPADVISOR/'
	self.CSV_PATH = os.path.join(self.MAIN_PATH, datetime.datetime.now().strftime('%Y/%m/%d'))
        self.init_logger("logging.log")
	self.filename = 'TRIPADVISOR.csv'

    def init_logger(self, filename, level=''):
        if not os.path.isdir(self.CSV_PATH):
            os.mkdir(self.CSV_PATH)
        file_name   = os.path.join(self.CSV_PATH, filename)
        self.log    = logging.getLogger(file_name)
        handler     = logging.handlers.RotatingFileHandler(file_name, maxBytes=524288000, backupCount=5)
        self.log.addHandler(handler)
        self.log.setLevel(logging.DEBUG)

    def main(self):
	try:
		with open(os.path.join(self.CSV_PATH, self.filename)) as file_obj:
			reader = csv.reader(file_obj, delimiter=',')
			for index, line in enumerate(reader):
				line.insert(2, line[-1])
				del line[-1]
				line[-1], line[-2] = line[-2], line[-1]
				if index !=0:
					try:
						line[-1] = str((datetime.datetime.strptime(line[-1], "%Y-%m-%d %H:%M:%S")).strftime('%d/%m/%Y-%H-%M-%S'))
					except: line[-1] = ''
                                        try:
                                                line[4] = str((datetime.datetime.strptime(line[4], "%Y-%m-%d")).strftime('%m-%d-%Y'))
                                        except: line[4] = ''

				if ':' in line:
					line = line.replace(':', ' ')
				self.log.info(':'.join(line))
		print 'sucess'
	except:
		print 'fail'

if __name__ == '__main__':
	TALOG().main()
