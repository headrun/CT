import csv
import codecs
import shutil
import os
from pathos.multiprocessing import ProcessingPool as Pool
import random
import sys
import MySQLdb


reload(sys)
sys.setdefaultencoding('utf-8')
IPS_LIST = '/root/scrapers/flights/new_ips.list'

class GoAirCheck:
    def csv_process(self):
	conn = MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'root', db = 'SEATFINDERDB', charset="utf8", use_unicode=True)
        cur = conn.cursor()
        csv_list = []
        command_to_run_list = []
        current_path = os.getcwd()
        path_to_move = current_path+ '/'+'GOAIR_CSV/processed_complete'
        path_to_check = current_path +'/'+'GOAIR_CSV/processed'
        files_in_path = os.listdir(path_to_check)
        file_=''
        if len(files_in_path)==1:
            file_ = path_to_check + '/'+files_in_path[0]
            print "processing csv"
        elif len(files_in_path)==0:
            print "no files in yet_to_process directory to process"
            return
        else:
            print "multiple files in the yet_to_process directory. Unable to process"
            return
        ###Processing CSV###
        with codecs.open(file_,'r',encoding='utf-8', errors='ignore') as csvfile:
            plots=csv.reader(csvfile,delimiter=',')
            ticket_number_check=list()
            for row in plots:
                booking_no, transaction_date, airline_pnr, gds_pnr, supplier, airline, departure_date, return_date, ticket_no, journey_type, total_booking_amount, air_booking_type, source_type, agent_pcc, pax_first_name, pax_last_name, sector, remarks, status = row
                if 'booking_no' in row and "total_booking_amount" in row:
                    continue
                else:
                    if airline=="GoAir" and gds_pnr=='':
                        if ticket_no not in ticket_number_check:
				ticket_number_check.append(ticket_no)
				seat_finder_query = 'select * from seat_finder where pnr="%s"'%airline_pnr
				cur.execute(seat_finder_query)
                		rows = cur.fetchall()
                		if len(rows)>=1:
					continue
				else:
					csv_list.append(row)
					print airline_pnr

	
	'''			   
        ###Processed path Check###
        if not os.path.exists(path_to_move):
		os.makedirs(path_to_move)
        else:
            pass

        ###MOVING processed csv to Processed path###
        shutil.move(file_,path_to_move)
	'''
        ###processing csv data###
        self.csv_list = [list(item) for item in set(tuple(row) for row in csv_list)]
	print len(csv_list), len(self.csv_list)
        print "Total No of Records:%s"%str(len(self.csv_list))
        for line in self.csv_list:
            booking_no, transaction_date, airline_pnr, gds_pnr, supplier, airline, departure_date, return_date, ticket_no, journey_type, total_booking_amount, air_booking_type, source_type, agent_pcc, pax_first_name, pax_last_name, sector, remarks, status = line
            if airline_pnr=='':
                airline_pnr=ticket_no
            details_dict = {'booking_no':booking_no, 'transaction_date':transaction_date,'airline_pnr':airline_pnr,'gds_pnr':gds_pnr,'supplier':supplier,'airline':airline,'departure_date':departure_date,'return_date':return_date,'ticket_no':ticket_no,'journey_type':journey_type,'total_booking_amount':total_booking_amount,'air_booking_type':air_booking_type,'source_type':source_type,'agent_pcc':agent_pcc,'pax_first_name':pax_first_name,'pax_last_name':pax_last_name,'sector':sector,'remarks':remarks,'status':status}
            command_to_run_list.append(details_dict)
        return command_to_run_list


    def run_command(self,details_dict):
	proxy = random.choice(list(open(IPS_LIST)))
	ip_ = proxy.split('-ip-')[-1].split(':')[0]
	ip = "http://lum-customer-cleartripin-zone-static-ip-%s:ip2hzveqnkoh@zproxy.lum-superproxy.io:22225"%(ip_)
	os.system('scrapy crawl goair_seatfinder_browse -ajsons="%s" --set HTTP_PROXY="%s"'%(details_dict,ip))

    def main(self):
        p = Pool(5)
        command_to_run_list= self.csv_process()
        if command_to_run_list:
            p.map(self.run_command, command_to_run_list)
	    print "Total no of records in csv missing in DB:%s"%str(len(self.csv_list))
            print "Total No of Records:%s"%str(len(command_to_run_list))
if __name__=="__main__":
    GoAirCheck().main()
