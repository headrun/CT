import MySQLdb
import datetime
import json
from configobj import ConfigObj

class Tripadvisorscript(object):

	def ensure_crawlta_table(self, cur, source):
		crawl_table = '%s_crawl'%(source)
		SHOW_QUERY = 'SHOW TABLES LIKE "%s_%%";' %(source)
		cur.execute(SHOW_QUERY)
		try:cur.execute(self.TA_CRAWL_TABLE_CREATE_QUERY.replace('#CRAWL-TABLE#', crawl_table))
		except Exception, e: print str(e)

	def drop_crawlta_table(self, cur,source):
		dropcrawl_table ='%s_crawl'%(source)
		DROP_QUERY ='TRUNCATE TABLE %s;' %(dropcrawl_table)
		try:cur.execute(DROP_QUERY)
		except Exception, e: print str(e)

        def drop_ta_table(self, cur, source):
		db_name = 'MMCTRP'
                DROP_QUERY ='TRUNCATE TABLE %s.%s;' %(db_name, source)
                try:cur.execute(DROP_QUERY)
                except Exception, e: print str(e)
                DROP_QUERY1 ='TRUNCATE TABLE %s.%scityrank' %(db_name, source)
                try:cur.execute(DROP_QUERY1)
                except Exception, e: print str(e)



	def insert_crawlta_tables_data(self, cur,source,val):
		CRAWL_TABLE_QUERY='INSERT INTO %s_crawl'%source +'(sk, url, crawl_type, start_date,'
		CRAWL_TABLE_QUERY+='end_date,crawl_status,crawl_ref_status,content_type,dx,los,pax,ccode,hotel_ids,hotel_name,meta_data,aux_info,'
		CRAWL_TABLE_QUERY+='reference_url,created_at,modified_at)'\
	    'VALUES(%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())'
		CRAWL_TABLE_QUERY+= 'ON DUPLICATE KEY UPDATE sk=%s,url=%s,crawl_type=%s,start_date=%s,end_date=%s,crawl_status=%s,crawl_ref_status=%s, content_type=%s,'
		CRAWL_TABLE_QUERY+='dx=%s,los=%s,pax=%s,ccode=%s,hotel_ids=%s,hotel_name=%s,meta_data=%s,aux_info=%s,reference_url=%s,'
		CRAWL_TABLE_QUERY+='created_at=NOW(), modified_at=NOW()'
		if val:
			vals = (val['sk'], val['url'], val['crawl_type'], val['start_date'], val['end_date'],
			val['crawl_status'], val['crawl_ref_status'],val['content_type'], val['dx'], val['los'], val['pax'], val['ccode'], val['hotel_ids'],
			val['hotel_name'].encode('utf8'), val['meta_data'], val['aux_info'], val['reference_url'],
			val['sk'], val['url'], val['crawl_type'], val['start_date'], val['end_date'],
			val['crawl_status'], val['crawl_ref_status'],val['content_type'], val['dx'], val['los'], val['pax'], val['ccode'], val['hotel_ids'],
			val['hotel_name'], val['meta_data'], val['aux_info'], val['reference_url'],)

			try:	cur.execute(CRAWL_TABLE_QUERY,vals)
			except: pass


        def __del__(self):
                self.cursor.close()

	def __init__(self):
		user = 'root'
		passwd = ''
		host = 'localhost'
		db = 'urlqueue_dev'
		self.name = 'Tripadvisor'
		self.con = MySQLdb.connect(user=user, host=host, db=db)
		self.cursor = self.con.cursor()
		self.TA_CRAWL_TABLE_CREATE_QUERY ="""
                CREATE TABLE `#CRAWL-TABLE#` (
                `sk` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
                `url` text COLLATE utf8_unicode_ci,
                `dx` int(3) NOT NULL,
                `los` int(3) NOT NULL,
                `pax` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
                `ccode` varchar(25) COLLATE utf8_unicode_ci NOT NULL,
                `hotel_ids` bigint(20) NOT NULL,
                `hotel_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
                `crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
                `content_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
                `start_date` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
                `end_date` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
                `crawl_status` int(3) NOT NULL DEFAULT '0',
		`crawl_ref_status` int(3) NOT NULL DEFAULT '0',
                `meta_data` text COLLATE utf8_unicode_ci,
                `aux_info` text COLLATE utf8_unicode_ci,
                `reference_url` text COLLATE utf8_unicode_ci,
                `created_at` datetime NOT NULL,
                `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY `ccid` (`sk`),
                KEY `sk` (`sk`),
                KEY `type` (`crawl_type`),
                KEY `type_time` (`crawl_type`,`modified_at`)
                ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci
                """
	def Strp_times(self, dx, los):
		date_ = datetime.datetime.now() + datetime.timedelta(days=int(dx))
		dx = date_.strftime('%Y_%m_%d')
		los_date = date_ + datetime.timedelta(days=int(los))
		los = los_date.strftime('%Y_%m_%d')
		return (dx, los)


	def main(self):
		self.ensure_crawlta_table(self.cursor, self.name)
		self.drop_crawlta_table(self.cursor, self.name)
		self.drop_ta_table(self.cursor, self.name)
		dict_ = {}
		with open('TAD_URLS.json') as json_data1:
			self.ta_data = json.load(json_data1)
			for hotel_id, hotel_details in self.ta_data.iteritems():
				city_name, ctid, ta_url, hotel_name = hotel_details
				config = ConfigObj('TripAdvisor.cfg')
				sectionall = config.sections
				for sectionbyone in sectionall:
					sections_ = config[sectionbyone]
			                DX_num = sections_['Dx']
                			LOS_num = sections_['LoS']
                			PAX_val = ''.join(sections_['Pax'])
                			dxs, loss = self.Strp_times(DX_num, LOS_num)
					sk = "_".join([city_name, str(DX_num),str(LOS_num),str(PAX_val), hotel_id])
					aux_conf = {}
					aux_conf.update({"city_name":city_name})
					dict_.update({'sk': sk,'start_date': dxs,'dx': str(DX_num),'los': str(LOS_num),'pax': str(PAX_val), 'url': ta_url, 'crawl_type': 'keepup', 'crawl_status': '0', 'crawl_ref_status':'0','content_type': 'hotels', 'end_date': loss, 'ccode': ctid, 'hotel_ids': hotel_id,'hotel_name': hotel_name, 'meta_data': '','aux_info':json.dumps(aux_conf), 'reference_url': ta_url})
                        		self.insert_crawlta_tables_data(self.cursor, self.name, dict_)

if __name__ == '__main__':
	Tripadvisorscript().main()

