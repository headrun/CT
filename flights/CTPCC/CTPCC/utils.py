import sys
import os
import re
import time
import asyncore
import MySQLdb
import datetime
import logging
from crawl_table_queries import *

OUTPUT_DIR = os.path.join(os.getcwd(), 'OUTPUT')
CRAWL_OUT_PATH = os.path.join(OUTPUT_DIR, 'crawl_out')
PROCESSING_PATH = os.path.join(OUTPUT_DIR, 'processing')
PROCESSED_PATH = os.path.join(OUTPUT_DIR, 'processed')

#CRAWL_OUT_PATH = '/root/headrun/CTmonitoring/CTmonitoring/spiders/OUTPUT/crawl_out'
#PROCESSING_PATH = "/root/headrun/CTmonitoring/CTmonitoring/spiders/OUTPUT/processing"
#PROCESSED_PATH = "/root/headrun/CTmonitoring/CTmonitoring/spiders/OUTPUT/processed"

def get_current_ts_with_ms():
    dt = datetime.datetime.now().strftime("%Y%m%dT%H%M%S%f")
    return dt

def get_compact_traceback(e=''):
    except_list = [asyncore.compact_traceback()]
    return "Error: %s Traceback: %s" % (str(e), str(except_list))

def get_output_file(source):
    out_file = os.path.join(CRAWL_OUT_PATH, "%s_out_file_%s.queries" %(source, get_current_ts_with_ms()))
    out_put = open(out_file, 'a+')
    return (out_put, out_file)

def move_crawlout_processing(source):
    os.chdir(CRAWL_OUT_PATH)
    cmd = 'mv %s  %s'%(source, PROCESSING_PATH)
    os.system(cmd)
    

def create_crawl_table_cursor():
    conn = MySQLdb.connect(host="localhost", user = "root", db = "urlqueue_dev", charset="utf8", use_unicode=True)
    cur = conn.cursor()
    return cur

def ensure_crawl_table(cursor, source):
    crawl_table_name = "%s_crawl" % (source)
    SHOW_QUERY = 'SHOW TABLES LIKE "%s_%%";' % (source)
    cursor.execute(SHOW_QUERY)
    try: cursor.execute(CRAWL_TABLE_CREATE_QUERY.replace('#CRAWL-TABLE#', crawl_table_name))
    except : print "crawl table already exists"

def insert_crawl_tables_data(cursor, source, val):
    CRAWL_TABLE_QUERY = 'INSERT INTO %s_crawl' % source + ' (sk, dx, crawl_type, from_location, to_location, start_date, '
    CRAWL_TABLE_QUERY += 'crawl_status, return_date, trip_type, meta_data, created_at, modified_at) \
			VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())'
    CRAWL_TABLE_QUERY += ' ON DUPLICATE KEY UPDATE sk=%s, from_location=%s, to_location=%s, start_date=%s, crawl_type=%s, crawl_status=%s, modified_at=NOW(), dx=%s'
    if val:
	vals = (val['sk'], val['dx'], val['crawl_type'], val['from'], val['to'], val['date'],
		val['crawl_status'], val['return_date'], val['trip_type'], '', val['sk'], val['from'], val['to'],
		val['date'], val['crawl_type'], val['crawl_status'],val['dx']
	)
	cursor.execute(CRAWL_TABLE_QUERY, vals)

def terminal_requests(cursor, source, crawl_type, trip_type, limit):
    crawl_table_name = "%s_crawl" % (source)
    if limit:
	cursor.execute(CRAWL_TABLE_SELECT_QUERY_LIMIT%(crawl_table_name, crawl_type, trip_type, limit))
    else:
        cursor.execute(CRAWL_TABLE_SELECT_QUERY%(crawl_table_name, crawl_type, trip_type))
    rows = cursor.fetchall()
    sks_lst = []
    if rows:
	for row in rows:
	    if row[0]:
	        sks_lst.append(str(row[0]))
	        cursor.execute(UPDATE_QUERY%(crawl_table_name, crawl_type, str(row[0]), trip_type))
    return rows

def got_page(cursor, source, sk, status, crawl_type, trip_type):
    crawl_table_name = "%s_crawl" % (source)
    cursor.execute(UPDATE_WITH_9_STATUS%(crawl_table_name, status, crawl_type, sk, trip_type))

def create_logger_obj(source):
    cur_dt = str(datetime.datetime.now().date())
    LOGS_DIR = '/root/headrun/CTmonitoring/CTmonitoring/logs'
    log_file_name = "spider_%s_%s.log" % (source, cur_dt)
    log = initialize_logger(os.path.join(LOGS_DIR, log_file_name))
    return log

def initialize_logger(file_name, log_level_list=[]):
    logger = logging.getLogger()
    try:
        add_logger_handler(logger, file_name, log_level_list)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        e = sys.exc_info()[2]
        time_str = time.strftime("%Y%m%dT%H%M%S", time.localtime())
        exception_str = "%s: %s: Exception: %s" % (time_str, sys.argv, get_compact_traceback(e))
        #print exception_str

    return logger


def add_logger_handler(logger, file_name, log_level_list=[]):
    success_cnt, handler = 3, None

    for i in xrange(success_cnt):
        try:
            handler = logging.FileHandler(file_name)
            break
        except (KeyboardInterrupt, SystemExit):
            raise
        except: pass

    if not handler: return

    formatter = logging.Formatter('%(asctime)s.%(msecs)d: %(filename)s: %(lineno)d: %(funcName)s: %(levelname)s: %(message)s', "%Y%m%d%H%M%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    set_logger_log_level(logger, log_level_list)

    if handler.stream:
        set_close_on_exec(handler.stream)

def textify(nodes, sep=' '):
    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]

    def _t(x):
        if isinstance(x, (str, unicode)):
            return [x]

        if hasattr(x, 'xmlNode'):
            if not x.xmlNode.get_type() == 'element':
                return [x.extract()]
        else:
            if isinstance(x.root, (str, unicode)):
                return [x.root]

        return (n.extract() for n in x.select('.//text()'))

    nodes = chain(*(_t(node) for node in nodes))
    nodes = (node.strip() for node in nodes if node.strip())

    return sep.join(nodes)

def xcode(text, encoding='utf8', mode='strict'):
    return text.encode(encoding, mode) if isinstance(text, unicode) else text


def compact(text, level=0):
    if text is None: return ''

    if level == 0:
        text = text.replace("\n", " ")
        text = text.replace("\r", " ")

    compacted = re.sub("\s\s(?m)", " ", text)
    if compacted != text:
        compacted = compact(compacted, level+1)

    return compacted.strip()

def clean(text):
    if not text: return text

    value = text
    value = re.sub("&amp;", "&", value)
    value = re.sub("&lt;", "<", value)
    value = re.sub("&gt;", ">", value)
    value = re.sub("&quot;", '"', value)
    value = re.sub("&apos;", "'", value)

    return value

def normalize(text):
    return clean(compact(xcode(text)))

