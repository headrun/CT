import MySQLdb
import datetime
import json
import optparse
from configobj import ConfigObj
from auto_input import *
import sys
sys.path.insert(0, '../')
from blacklist_properties import total_blacklist_properties
from scripts.crawl_table_queries import *
from utils import *

class Tripadvisorscript(object):

        def __del__(self):
                self.cursor.close()

	def __init__(self, options):
		user = 'root'
		passwd = DB_PASSWORD
		host = 'localhost'
		db = PROD_DB_NAME
                self.name = 'Tripadvisor'
                self.config_file = 'TripAdvisor.cfg'
                if options.set_up:
                        self.name = 'TripadvisorAPC'
                        self.config_file = 'TripAdvisorAPC.cfg'
		self.con = MySQLdb.connect(user=user, host=host, db=db, passwd=DB_PASSWORD)
		self.cursor = self.con.cursor()
		self.cursor1 = create_mmt_table_cusor()
		ensure_ta_table(self.cursor1,self.name)
		drop_ta_table(self.cursor1,self.name)
		self.main()

	def Strp_times(self, dx, los):
		date_ = datetime.datetime.now() + datetime.timedelta(days=int(dx))
		dx = date_.strftime('%Y_%m_%d')
		los_date = date_ + datetime.timedelta(days=int(los))
		los = los_date.strftime('%Y_%m_%d')
		return (dx, los)

	def main(self):
		ensure_crawlta_table(self.cursor, self.name)
		drop_crawlta_table(self.cursor, self.name)
		dict_ = {}
		with open('TAD_URLS.json') as json_data1:
			ta_data = json.load(json_data1)
			for hotel_id, hotel_details in ta_data.iteritems():
				city_name, ctid, ta_url, hotel_name = hotel_details
				if ctid not in total_blacklist_properties:
					config = ConfigObj(self.config_file)
					sectionall = config.sections
					for sectionbyone in sectionall:
						sections_ = config[sectionbyone]
						DX_num = sections_['Dx']
						LOS_num = sections_['LoS']
						PAX_val = ''.join(sections_['Pax'])
						Room_cnt = ''.join(sections_['Rooms'])
						dxs, loss = self.Strp_times(DX_num, LOS_num)
						sk = "_".join([city_name, str(DX_num),str(LOS_num),str(PAX_val), hotel_id, Room_cnt])
						aux_conf = {}
						aux_conf.update({"city_name":city_name})
						dict_.update({'sk': sk,'start_date': dxs,'dx': str(DX_num),'los': str(LOS_num),'pax': str(PAX_val), 'url': ta_url, 'crawl_type': 'keepup', 'crawl_status': '0', 'crawl_ref_status':'0','content_type': 'hotels', 'end_date': loss, 'ccode': ctid, 'hotel_ids': hotel_id,'hotel_name': hotel_name, 'meta_data': '','aux_info':json.dumps(aux_conf), 'reference_url': ta_url})
						insert_crawlta_tables_data(self.cursor, self.name, dict_)

if __name__ == '__main__':
	parser = optparse.OptionParser()
	parser.add_option('-s', '--set_up', default='', help='set_up')
	(options, args) = parser.parse_args()
	Tripadvisorscript(options)
