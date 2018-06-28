import MySQLdb
import json
from itertools import chain
from auto_input import *

class Hotelsgather(object):
        def __init__(self):
                user = 'root' # your username
                passwd = DB_PASSWORD # your password
                host = 'localhost' # your host
                db = PROD_META_DB # database where your table is stored
                self.con = MySQLdb.connect(user=user, host=host, db=db, passwd=DB_PASSWORD)
                self.cursor = self.con.cursor()

        def __del__(self):
		self.cursor.close()

        def main(self):
		gob_list, cle_list, make_list, trp_list, book_list = [], [], [], [], []
		new_gob_list, new_cle_list, new_make_list, new_trp_list, new_book_list = [], [], [], [], []
		dup_gob_list, dup_cle_list, dup_make_list, dup_trp_list, dup_book_list =[], [], [], [], []
	        go_in_make, go_in_trp, go_in_book, make_in_gob, make_in_trp, make_in_book, trp_in_gob, trp_in_make, trp_in_book = [], [], [], [], [], [], [], [], []
        	go_in_both, make_in_both, trp_in_both, book_in_both = [], [], [], []
		book_in_make, book_in_trp, book_in_gob = [], [], []

		for hote_ in [('gob', 'Goibibotrip'), ('cle', 'Cleartrip'), ('make', 'Makemytrip'), ('trp', 'Tripadvisor'), ('book', 'Booking')]:
			self.cursor.execute("select hotel_id, hotel_name, city_name from %s_hotels" % hote_[1])
			goibibo_list = self.cursor.fetchall()
			new_goibibo_list = list(chain.from_iterable(goibibo_list))[1:]
			cntf = map(lambda x:(x[1:]), goibibo_list)
			for cnt in cntf:
				cntf_ =  '<>'.join(list(cnt))
				if hote_[0] == 'gob':
					gob_list.append(cntf_.lower())
				elif hote_[0] == "cle":
					cle_list.append(cntf_.lower())
				elif hote_[0] == "make":
					make_list.append(cntf_.lower())
				elif hote_[0] == "trp":
					trp_list.append(cntf_.lower())
				else:
				     	book_list.append(cntf_.lower())
		for go_ in gob_list:
			if (go_ not in make_list) and (go_ not in trp_list) and (go_ not in book_list):
				new_gob_list.append(go_)
			else:
				dup_gob_list.append(go_)
			if (go_ in make_list):
				go_in_make.append(go_)
			if (go_ in trp_list):
				go_in_trp.append(go_)
			if (go_ in book_list):
				go_in_book.append(go_)
			if (go_ in make_list) and (go_ in trp_list) and (go_ in book_list):
				go_in_both.append(go_)

		for make_ in make_list:
			if (make_ not in gob_list) and (make_ not in trp_list) and (make_ not in book_list):
				new_make_list.append(make_)
			else:
				dup_make_list.append(make_)
			if (make_ in gob_list):
				make_in_gob.append(make_)
			if (make_ in trp_list):
				make_in_trp.append(make_)
			if (make_ in book_list):
				make_in_book.append(make_)
			if (make_ in gob_list) and (make_ in trp_list) and (make_ in book_list):
				make_in_both.append(make_)


		for trp_ in trp_list:
			if (trp_ not in make_list) and (trp_ not in gob_list) and (trp_ not in book_list):
				new_trp_list.append(trp_)
			else:
				dup_trp_list.append(trp_)
			if (trp_ in make_list):
				trp_in_make.append(trp_)
			if (trp_ in gob_list):
				trp_in_gob.append(trp_)
			if (trp_ in book_list):
				trp_in_book.append(trp_)
			if (trp_ in make_list) and (trp_ in gob_list) and (trp_ in book_list):
				trp_in_both.append(trp_)

                for boo_ in book_list:
                        if (boo_ not in make_list) and (boo_ not in gob_list) and (boo_ not in trp_list):
                                new_book_list.append(boo_)
                        else:
                                dup_book_list.append(boo_)
                        if (boo_ in make_list):
                                book_in_make.append(boo_)
                        if (boo_ in gob_list):
                                book_in_gob.append(boo_)
                        if (boo_ in trp_list):
                                book_in_trp.append(boo_)
                        if (boo_ in make_list) and (boo_ in gob_list) and (boo_ in trp_list):
                                book_in_both.append(boo_)


		lst1 = [ "Total Goibibo input hotels: %s" % len(gob_list), "Total number of unique Goibibo hotels : %s"% len(new_gob_list), "Total number of Goibibo hotels in Makemytrip, Tripadvisor and Booking : %s" % len(go_in_both), "Number of goibibo hotels in makemytrip : %s" % len(go_in_make), "Number of goibibo hotels in tripadvisor : %s" % len(go_in_trp), "Total number of duplicates in goibibo : %s" % len(dup_gob_list), "Number of goibibo hotels in Booking : %s" % len(go_in_book)]
		lst2 = ["Total Makemytrip input hotels: %s"% len(make_list), "Total number of unique Makemytrip hotels : %s"% len(new_make_list), "Total number of Makemytrip hotels in Goibibo, Tripadvisor and Booking : %s"% len(make_in_both), "Number of makemytrip hotels in goibibo : %s"% len(make_in_gob), "Number of makemytrip hotels in tripadvisor : %s"% len(make_in_trp), "Total number of duplicates in makemytrip : %s"% len(dup_make_list), "Number of makemytrip hotels in Booking : %s" % len(make_in_book)]
		lst3 = ["Total Tripadvisor input hotels : %s"% len(trp_list),  "Total number of unique Tripadvisor hotels : %s"% len(new_trp_list), "Total number of Tripadvisor hotels in Goibibo, Makemytrip and Booking : %s"% len(trp_in_both), "Number of tripadvisor hotels in goibibo : %s"% len(trp_in_gob), "Number of tripadvisor hotels in makemytrip : %s"% len(trp_in_make),  "Total number of duplicates in tripadvisor : %s"% len(dup_trp_list), "Number of tripadvisor hotels in Booking : %s" % len(trp_in_book)]
                lst4 = ["Total Booking input hotels : %s"% len(book_list),  "Total number of unique Booking hotels : %s"% len(new_book_list), "Total number of Booking hotels in Goibibo, Makemytrip and Tripadvisor : %s"% len(book_in_both), "Number of Booking hotels in goibibo : %s"% len(book_in_gob), "Number of Booking hotels in makemytrip : %s"% len(book_in_make),  "Total number of duplicates in Booking : %s"% len(dup_book_list), "Number of Booking hotels in Tripadvisor : %s" % len(book_in_trp)]
		return lst1, lst2, lst3, lst4

if __name__ == '__main__':
        list_of = Hotelsgather().main()
