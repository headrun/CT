import os
import sys
import MySQLdb
import time
import datetime
import re
import logging
import asyncore
from scripts.crawl_table_queries import *
from itertools import chain


OUTPUT_DIR = os.path.join(os.getcwd(), 'OUTPUT')
CRAWL_OUT_PATH = os.path.join(OUTPUT_DIR, 'crawl_out')
PROCESSING_PATH = os.path.join(OUTPUT_DIR, 'processing')
PROCESSED_PATH = os.path.join(OUTPUT_DIR, 'processed')
PROD_DB_NAME =  PROD_META_DB ='IP_SCRAPER'


def get_current_ts_with_ms():
    dt = datetime.datetime.now().strftime("%Y%m%dT%H%M%S%f")
    return dt


def get_gobtrip_file(source):
    out_file = os.path.join(CRAWL_OUT_PATH, "%s_out_file_%s.queries" %(source, get_current_ts_with_ms()))
    out_put = open(out_file, 'a+')
    return out_put

def gob_crawlout_processing(source):
    os.chdir(CRAWL_OUT_PATH)
    cmd = 'mv %s  %s'%(source.name, PROCESSING_PATH)
    os.system(cmd)


def insert_crawlct_tables_data(cur,source,val):
    CRAWL_TABLE_QUERY='INSERT INTO %s_crawl'%source +'(sk, crawl_type, content_type,'
    CRAWL_TABLE_QUERY+='meta_data,aux_info,reference_url,created_at,modified_at)'\
                    'VALUES(%s, %s, %s, %s, %s, %s, NOW(), NOW())'
    CRAWL_TABLE_QUERY+= 'ON DUPLICATE KEY UPDATE sk=%s, crawl_type=%s, content_type=%s,'
    CRAWL_TABLE_QUERY+= 'meta_data=%s,aux_info=%s,reference_url=%s,created_at=Now(),modified_at=NOW()'
    if val:
        vals = (val['sk'], val['crawl_type'], val['content_type'], val['meta_data'],
		val['aux_info'],val['reference_url'], val['sk'], val['crawl_type'], val['content_type'], val['meta_data'],
		val['aux_info'],val['reference_url']
                )
        cur.execute(CRAWL_TABLE_QUERY,vals)


def terminal_ip_requests(cursor, source, crawl_type, content_type, limit):
    crawl_table_name = "%s" % (source)
    if limit:
        cursor.execute(IP_TABLE_SELECT_QUERY_LIMIT%(crawl_table_name, crawl_type, content_type, limit))
    else:
        cursor.execute(IP_TABLE_SELECT_QUERY%(crawl_table_name, crawl_type, content_type))
    rows = cursor.fetchall()
    sks_lst = []
    if rows:
        for row in rows:
            if row[0]:
                sks_lst.append(str(row[0]))
                cursor.execute(UPDATE_QUERY%(crawl_table_name, crawl_type, str(row[0]), content_type))
        return rows



def ct_crawlout_processing(source):
    os.chdir(CRAWL_OUT_PATH)
    cmd = 'mv %s  %s'%(source.name, PROCESSING_PATH)
    os.system(cmd)

def got_page(cursor, source, sk, status, crawl_type, content_type):
      crawl_table_name = "%s_crawl" % (source)
      cursor.execute(UPDATE_WITH_9_STATUS%(crawl_table_name, status, crawl_type, sk, content_type))

    
def create_ct_table_cusor():
    conns = MySQLdb.connect(host ='localhost', user ='root', db = PROD_META_DB, charset='utf8', use_unicode=True)
    curs = conns.cursor()
    return curs


def create_logger_obj(source):
    cur_dt = str(datetime.datetime.now().date())
    LOGS_DIR = os.path.join(os.path.dirname(os.getcwd()),'logs')
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
    value = re.sub("&nbsp;", "", value)
    return value

def normalize_clean(text):
    return clean(compact(xcode(text)))

def normalize(text):
    value =text.replace(",","").strip()
    return value
