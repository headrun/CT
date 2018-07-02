import collections
import MySQLdb
import optparse
import MySQLdb

class DeleteRecords(object):
	def __init__(self, options):
        	self.database = options.database_name
		
        	self.ip     = 'localhost'
        	self.main()
	def create_cursor(self, host, db):
		try:
		    conn = MySQLdb.connect(user='root',host='localhost', db=db, passwd='root')
		    conn.set_character_set('utf8')
		    cursor = conn.cursor()
		    cursor.execute('SET NAMES utf8;')
		    cursor.execute('SET CHARACTER SET utf8;')
		    cursor.execute('SET character_set_connection=utf8;')
		except:
		    import traceback; print traceback.format_exc()
		    sys.exit(-1)

		return conn, cursor
	def ensure_db_exists(self, ip, dbname):
	
		conn, cursor = self.create_cursor(ip, dbname)
		if dbname.isupper():
			stmt = "show databases like '%s';" % dbname
			cursor.execute(stmt)
			result = cursor.fetchone()
			if result:
				is_existing = True
			else:
				is_existing = False

			cursor.close()
			conn.close()
			return is_existing
	def main(self):
		conn, cursor = self.create_cursor(self.ip, self.database)
		table_names_query = "show tables"
		data = cursor.execute(table_names_query)
		table_names = cursor.fetchall()
		#currentdate = datetime.datetime.now()
		#specific_date = currentdate - 7
		if not self.ensure_db_exists(self.ip, self.database):
                    print 'Enter valid DB and Ip or dbname should be in capital letters'
                    pass
		if self.database.isupper():
			for tablename in table_names:
				delete_query = "delete  from %s where modified_at < DATE(NOW()) + INTERVAL -7 DAY" %(tablename)
				cursor.execute(delete_query)
				print "Records are deleted successfully"	
if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--database-name', default='', help = 'databasename')
    (options, args) = parser.parse_args()
    DeleteRecords(options)
		
