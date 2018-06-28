import MySQLdb
import datetime
import json
from configobj import ConfigObj
from auto_input import *

class Trivagoscript(object):

	def ensure_crawlta_table(self, cur, source):
		crawl_table = '%s_crawl'%(source)
		SHOW_QUERY = 'SHOW TABLES LIKE "%s_%%";' %(source)
		cur.execute(SHOW_QUERY)
		try:cur.execute(self.TA_CRAWL_TABLE_CREATE_QUERY.replace('#CRAWL-TABLE#', crawl_table))
		except Exception, e: print str(e)

	def drop_crawlta_table(self, cur,source):
		dropcrawl_table ='%s_crawl'%(source)
		DROP_QUERY ='TRUNCATE TABLE %s;' %(dropcrawl_table)
		try: cur.execute(DROP_QUERY)
		except Exception, e: print str(e)

        def drop_ta_table(self, cur, source, dat_it):
		db_name = PROD_META_DB
                yesterday = str(dat_it-datetime.timedelta(days=1))
                day_before = str(dat_it-datetime.timedelta(days=2))
                week_before = str(dat_it-datetime.timedelta(days=7))
                pat = '%'+yesterday+'%'
                pat1 = '%'+day_before+'%'
                pat2 = '%'+week_before+'%'
                #DROP_QUERY1 = 'DELETE FROM %s.%s where sk not like "%s" and sk not like "%s" and sk not like "%s"' %(db_name, source, pat, pat1, pat2)
		DROP_QUERY1 = 'DELETE FROM %s.%s where date(created_on) < "%s"' % (db_name, source, week_before)
                try:cur.execute(DROP_QUERY1)
                except Exception, e: print str(e)

	def insert_crawlta_tables_data(self, cur,source,val):
		CRAWL_TABLE_QUERY='INSERT INTO %s_crawl'%source +'(sk,' 
		CRAWL_TABLE_QUERY += 'dx, los,'\
		'city_name, city_id, latitude, longitude, crawl_type, content_type, start_date, end_date, crawl_status, meta_data,'\
		'reference_url,created_at,modified_at)'\
	    'VALUES(%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())'\
                'ON DUPLICATE KEY UPDATE sk=%s, dx=%s, los=%s, city_name=%s, city_id=%s, latitude=%s, longitude=%s, crawl_type=%s, content_type=%s, start_date=%s, end_date=%s, crawl_status=%s, meta_data=%s,reference_url=%s,'
                CRAWL_TABLE_QUERY+='created_at=NOW(), modified_at=NOW()'

		if val:
			vals = (MySQLdb.escape_string(val['sk']),  val['dx'], val['los'], MySQLdb.escape_string(val['city_name'].encode('utf8')),
			val['city_id'], val['latitude'],val['longitude'], val['crawl_type'], val['content_type'], val['start_date'], val['end_date'], val['crawl_status'],
			val['meta_data'], val['reference_url'],
			MySQLdb.escape_string(val['sk']), val['dx'], val['los'], MySQLdb.escape_string(val['city_name'].encode('utf8')),
			val['city_id'], val['latitude'],val['longitude'], val['crawl_type'], val['content_type'], val['start_date'], val['end_date'], val['crawl_status'],
			val['meta_data'], val['reference_url'],)

			try:	cur.execute(CRAWL_TABLE_QUERY,vals)
			except: pass


        def __del__(self):
                self.cursor.close()

	def __init__(self):
		user = 'root'
		passwd = DB_PASSWORD
		host = 'localhost'
		db = PROD_DB_NAME
		self.name = 'Trivago'
		self.con = MySQLdb.connect(user=user, host=host, db=db, passwd=DB_PASSWORD)
		self.cursor = self.con.cursor()
		self.TA_CRAWL_TABLE_CREATE_QUERY ="""
                CREATE TABLE `#CRAWL-TABLE#` (
                `sk` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
                `dx` int(3) NOT NULL,
                `los` int(3) NOT NULL,
		`city_name` text COLLATE utf8_unicode_ci,
		`city_id`  varchar(30) COLLATE utf8_unicode_ci NOT NULL,
 		`latitude` varchar(40) COLLATE utf8_unicode_ci NOT NULL,
		`longitude` varchar(40) COLLATE utf8_unicode_ci NOT NULL,
                `crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
                `content_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
                `start_date` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
                `end_date` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
                `crawl_status` int(3) NOT NULL DEFAULT '0',
                `meta_data` text COLLATE utf8_unicode_ci,
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
		dx = date_.strftime('%Y-%m-%d')
		los_date = date_ + datetime.timedelta(days=int(los))
		los = los_date.strftime('%Y-%m-%d')
		return (dx, los)


	def main(self):
		dat_it = datetime.datetime.now().date()
		self.ensure_crawlta_table(self.cursor, self.name)
		self.drop_crawlta_table(self.cursor, self.name)
		self.drop_ta_table(self.cursor, self.name, dat_it)
		dict_ = {}
		dat_ti = str(dat_it)
		with open('TG_CITIES43.json') as json_data1:
			self.ta_data = json.load(json_data1)
			for city_id, city_details in self.ta_data.iteritems():
				latitude, longitude, city_name = city_details
				config = ConfigObj('Trivago43.cfg')
				sectionall = config.sections
				for sectionbyone in sectionall:
					sections_ = config[sectionbyone]
			                DX_num = sections_['Dx']
                			LOS_num = sections_['LoS']
                			dxs, loss = self.Strp_times(DX_num, LOS_num)
					for offset in range(0, 500, 25):
						sk = "_".join([city_name, str(DX_num),str(LOS_num),city_id, str(offset), dat_ti])
						ref_urls = "%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s" % ("https://www.trivago.in/?iPathId=", city_id, "&bDispMoreFilter=false&aDateRange%5Barr%5D=", dxs,"&aDateRange%5Bdep%5D=", loss, "&aCategoryRange=0%2C1%2C2%2C3%2C4%2C5&iRoomType=7&sOrderBy=relevance%20desc&aPartner=&aOverallLiking=1%2C2%2C3%2C4%2C5&iOffset=", str(offset), "&iLimit=25&iIncludeAll=0&bTopDealsOnly=false&iViewType=0&aPriceRange%5Bto%5D=0&aPriceRange%5Bfrom%5D=0&aPathList=", city_id, "&aGeoCode%5Blng%5D=", longitude,"&aGeoCode%5Blat%5D=", latitude,"&bIsSeoPage=false&aHotelTestClassifier=&bSharedRooms=false&bIsSitemap=false&rp=&cpt=", city_id,"03&iFilterTab=0&")
						dict_.update({'sk':sk, 'dx': str(DX_num),'los': str(LOS_num), "city_name": str(city_name), "city_id":str(city_id), "latitude":str(latitude), "longitude":str(longitude), 'crawl_type': 'keepup', 'content_type': 'hotels', 'start_date': dxs, 'end_date': loss, 'crawl_status': '0', 'meta_data': str(offset), 'reference_url':ref_urls})
						self.insert_crawlta_tables_data(self.cursor, self.name, dict_)

if __name__ == '__main__':
	Trivagoscript().main()

