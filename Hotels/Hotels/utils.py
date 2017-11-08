import os
import sys
import MySQLdb
import time
import datetime
import re
import logging
import asyncore
from scripts.crawl_table_queries import *



CRAWL_OUT_PATH = '/root/hotels/HOTELS/Hotels/Hotels/spiders/OUTPUT/crawl_out'
PROCESSING_PATH = "/root/hotels/HOTELS/Hotels/Hotels/spiders/OUTPUT/processing"
PROCESSED_PATH = "/root/hotels/HOTELS/Hotels/Hotels/spiders/OUTPUT/processed"


def get_current_ts_with_ms():
    dt = datetime.datetime.now().strftime("%Y%m%dT%H%M%S%f")
    return dt


def get_mmtrip_file(source):
    out_file = os.path.join(CRAWL_OUT_PATH, "%s_out_file_%s.queries" %(source, get_current_ts_with_ms()))
    out_put = open(out_file, 'a+')
    return out_put



def mmt_crawlout_processing(source):
    os.chdir(CRAWL_OUT_PATH)
    cmd = 'mv %s  %s'%(source.name, PROCESSING_PATH)
    os.system(cmd)


def get_ctrip_file(source):
    out_file = os.path.join(CRAWL_OUT_PATH, "%s_out_file_%s.queries" %(source, get_current_ts_with_ms()))
    out_put = open(out_file, 'a+')
    return out_put




def ct_crawlout_processing(source):
    os.chdir(CRAWL_OUT_PATH)
    cmd = 'mv %s  %s'%(source.name, PROCESSING_PATH)
    os.system(cmd)


def get_gobtrip_file(source):
    out_file = os.path.join(CRAWL_OUT_PATH, "%s_out_file_%s.queries" %(source, get_current_ts_with_ms()))
    out_put = open(out_file, 'a+')
    return out_put




def gob_crawlout_processing(source):
    os.chdir(CRAWL_OUT_PATH)
    cmd = 'mv %s  %s'%(source.name, PROCESSING_PATH)
    os.system(cmd)



def get_compact_traceback(e=''):
    except_list = [asyncore.compact_traceback()]
    return "Error: %s Traceback: %s" % (str(e), str(except_list))


def create_crawl_table_cusor():
    conn = MySQLdb.connect(host ='localhost', user ='root', db = 'urlqueue_dev', charset='utf8', use_unicode=True)
    cur= conn.cursor()
    return cur


def drop_crawlmt_table(cur,source):
    dropcrawl_table ='%s_crawl'%(source)
    DROP_QUERY ='TRUNCATE TABLE %s;' %(dropcrawl_table)
    try:cur.execute(DROP_QUERY)
    except Exception, e: print str(e)



def ensure_crawlmt_table(cur, source):
    crawl_table = '%s_crawl'%(source)
    SHOW_QUERY = 'SHOW TABLES LIKE "%s_%%";' %(source)
    cur.execute(SHOW_QUERY)
    try:cur.execute(MMT_CRAWL_TABLE_CREATE_QUERY.replace('#CRAWL-TABLE#', crawl_table))
    except Exception, e: print str(e)



def insert_crawlmt_tables_data(cur,source,val):
    CRAWL_TABLE_QUERY='INSERT INTO %s_crawl'%source +'(sk, url, crawl_type, start_date,'
    CRAWL_TABLE_QUERY+='end_date,crawl_status,content_type,dx,los,pax,ccode,hotel_ids,hotel_name,meta_data,created_at,modified_at)'\
                    'VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())'
    CRAWL_TABLE_QUERY+= 'ON DUPLICATE KEY UPDATE sk=%s,url=%s,crawl_type=%s,start_date=%s,end_date=%s,crawl_status=%s,'
    CRAWL_TABLE_QUERY+= 'content_type=%s,dx=%s,los=%s,pax=%s,ccode=%s,hotel_ids=%s,hotel_name=%s,meta_data=%s,'
    CRAWL_TABLE_QUERY+= 'created_at=Now(),modified_at=NOW()'
    if val:
        vals = (val['sk'], val['url'], val['crawl_type'], val['start_date'], val['end_date'],
                val['crawl_status'], val['content_type'], val['dx'], val['los'], val['pax'], val['ccode'], val['hotel_ids'], 
                val['hotel_name'], val['meta_data'],val['sk'], val['url'], val['crawl_type'], val['start_date'], val['end_date'],
                val['crawl_status'], val['content_type'], val['dx'], val['los'], val['pax'], val['ccode'], val['hotel_ids'],
                val['hotel_name'], val['meta_data'],
                )

        cur.execute(CRAWL_TABLE_QUERY,vals)
                


def drop_crawlgb_table(cur,source):
    dropcrawl_table ='%s_crawl'%(source)
    DROP_QUERY ='TRUNCATE TABLE %s;' %(dropcrawl_table)
    try:cur.execute(DROP_QUERY)
    except Exception, e: print str(e)



def ensure_crawlgb_table(cur, source):
    crawl_table = '%s_crawl'%(source)
    SHOW_QUERY = 'SHOW TABLES LIKE "%s_%%";' %(source)
    cur.execute(SHOW_QUERY)
    try:cur.execute(GB_CRAWL_TABLE_CREATE_QUERY.replace('#CRAWL-TABLE#', crawl_table))
    except Exception, e: print str(e)



def insert_crawlgb_tables_data(cur,source,val):
    CRAWL_TABLE_QUERY='INSERT INTO %s_crawl'%source +'(sk, url, crawl_type, start_date,'
    CRAWL_TABLE_QUERY+='end_date,crawl_status,content_type,dx,los,pax,ccode,hotel_ids,hotel_name,meta_data,aux_info,'
    CRAWL_TABLE_QUERY+='reference_url,created_at,modified_at)'\
                    'VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())'
    CRAWL_TABLE_QUERY+= 'ON DUPLICATE KEY UPDATE sk=%s,url=%s,crawl_type=%s,start_date=%s,end_date=%s,crawl_status=%s,content_type=%s,'
    CRAWL_TABLE_QUERY+='dx=%s,los=%s,pax=%s,ccode=%s,hotel_ids=%s,hotel_name=%s,meta_data=%s,aux_info=%s,reference_url=%s,'
    CRAWL_TABLE_QUERY+='created_at=NOW(), modified_at=NOW()'
    if val:
        vals = (val['sk'], val['url'], val['crawl_type'], val['start_date'], val['end_date'],
                val['crawl_status'], val['content_type'], val['dx'], val['los'], val['pax'], val['ccode'], val['hotel_ids'],
                val['hotel_name'], val['meta_data'], val['aux_info'], val['reference_url'],
		val['sk'], val['url'], val['crawl_type'], val['start_date'], val['end_date'],
                val['crawl_status'], val['content_type'], val['dx'], val['los'], val['pax'], val['ccode'], val['hotel_ids'],
                val['hotel_name'], val['meta_data'], val['aux_info'], val['reference_url'],



                )

        cur.execute(CRAWL_TABLE_QUERY,vals)

def terminal_tripadvisor_requests(cursor, source, crawl_type, content_type, dx_val, limit):
    crawl_table_name = "%s_crawl" % (source)
    if limit:
        cursor.execute(TA_TABLE_SELECT_AQUERY_LIMIT%(crawl_table_name, crawl_type, content_type, dx_val, limit))
    else:
        cursor.execute(TA_TABLE_SELECT_QUERY%(crawl_table_name, crawl_type, content_type, dx_val))
    rows = cursor.fetchall()
    if not rows:
        if limit:
                cursor.execute(TA_TABLE_SELECT_QUERY_LIMIT%(crawl_table_name, crawl_type, content_type, dx_val, limit))
                rows = cursor.fetchall()
    sks_lst = []
    if rows:  
        for row in rows:
            if row[0]:
                sks_lst.append(str(row[0]))
                cursor.execute(TA_UPDATE_QUERY%(crawl_table_name, crawl_type, str(row[0]), content_type))
        return rows

def terminal_advisor_hotels(cursor, source, crawl_type, content_type, limit):
    crawl_table_name = "%s_crawl" % (source)
    if limit:
        cursor.execute(TAH_TABLE_SELECT_AQUERY_LIMIT%(crawl_table_name, crawl_type, content_type, limit))
    else:
        cursor.execute(TAH_TABLE_SELECT_QUERY%(crawl_table_name, crawl_type, content_type))
    rows = cursor.fetchall()
    sks_lst = []
    if rows:
        for row in rows:
            if row[0]:
                sks_lst.append(str(row[0]))
                cursor.execute(TAH_UPDATE_QUERY%(crawl_table_name, crawl_type, str(row[0]), content_type))
        return rows


def drop_gob_table(curs,source):
    dropcrawl_table ='%s' %(source)
    DROP_QUERY ='TRUNCATE TABLE %s;' %(dropcrawl_table)
    try:curs.execute(DROP_QUERY)
    except Exception, e: print str(e)



def ensure_gob_table(curs, source):
    gbt_table = '%s' %(source)
    SHOW_QUERY = 'SHOW TABLES LIKE "%s";' %(source)
    curs.execute(SHOW_QUERY)
    try:curs.execute(GB_TABLE_CREATE_QUERY.replace('#GOB-TABLE#', source))
    except: print "Table already exists"




def create_mmt_table_cusor():
    conns = MySQLdb.connect(host ='localhost', user ='root', db = 'MMCTRP', charset='utf8', use_unicode=True)
    curs = conns.cursor()
    return curs




def drop_mmt_table(curs,source):
    dropcrawl_table ='%s' %(source)
    DROP_QUERY ='TRUNCATE TABLE %s;' %(dropcrawl_table)
    try:curs.execute(DROP_QUERY)
    except Exception, e: print str(e)




def ensure_mmt_table(curs, source):
    mmt_table = '%s' %(source)
    SHOW_QUERY = 'SHOW TABLES LIKE "%s";' %(source)
    curs.execute(SHOW_QUERY)
    try:curs.execute(MMT_TABLE_CREATE_QUERY.replace('#MMT-TABLE#', source))
    except: print "Table already exists"



'''
def insert_mmt_tables_data(curs,source,val): 
    try:
        
        MMT_TABLE_QUERY = 'INSERT INTO %s'%source +'(city, mmthotelname, mmthotelid, check_in, mmtrate, b2cdiff, mmtinclusions,'
        MMT_TABLE_QUERY+='dx, los, pax, mmtroomtype, mmtapprate, mobilediff, rmtc, child, mmt_b2c_splashed_price, mmt_app_splashed_price,'\
                        'mmtb2ctaxes, mmt_apptaxes, mmtcoupon_code, mmtcoupon_discount, mmtcoupon_description,check_out, created_on)'\
                        'VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())'

        MMT_TABLE_QUERY+= 'ON DUPLICATE KEY UPDATE mmthotelid=%s'
        if val:
            vals=(val['city'], val['mmthotelname'], val['mmthotelid'], val['check_in'], val['mmtrate'], val['b2cdiff'], val['mmtinclusions'],
                  val['dx'], val['los'], val['pax'], val['mmtroomtype'], val['mmtapprate'], val['mobilediff'], val['rmtc'], val['child'],
                  val['mmt_b2c_splashed_price'], val['mmt_app_splashed_price'], val['mmtb2ctaxes'], val['mmt_apptaxes'], val['mmtcoupon_code'],
                  val['mmtcoupon_discount'], val['mmtcoupon_description'], val['check_out'], val['mmthotelid']
                  )

            curs.execute(MMT_TABLE_QUERY,vals)
    except Exception, e: print str(e)
	'''




def drop_crawlct_table(cur, source):
    dropcrawl_table ='%s_crawl'%(source)
    DROP_QUERY ='TRUNCATE TABLE %s;' %(dropcrawl_table)
    try:cur.execute(DROP_QUERY)
    except Exception, e: print str(e)


def ensure_crawlct_table(cur, source):
    crawl_table = '%s_crawl'%(source)
    SHOW_QUERY = 'SHOW TABLES LIKE "%s_%%";' %(source)
    cur.execute(SHOW_QUERY)
    try:cur.execute(CLEAR_CRAWL_TABLE_CREATE_QUERY.replace('#CRAWL-TABLE#', crawl_table))
    except: print "Table already exists"



        

def insert_crawlct_tables_data(cur,source,val):
    CRAWL_TABLE_QUERY='INSERT INTO %s_crawl'%source +'(sk, url, crawl_type, start_date,'
    CRAWL_TABLE_QUERY+='end_date,crawl_status,content_type,dx,los,pax,h_name,h_id,meta_data,created_at,modified_at)'\
                    'VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())'
    CRAWL_TABLE_QUERY+= 'ON DUPLICATE KEY UPDATE sk=%s, url=%s, crawl_type=%s,start_date=%s,end_date=%s,crawl_status=%s,'
    CRAWL_TABLE_QUERY+= 'content_type=%s,dx=%s,los=%s,pax=%s,h_name=%s,h_id=%s,meta_data=%s,created_at=Now(),modified_at=NOW()'
    if val:
        vals = (val['sk'], val['url'], val['crawl_type'], val['start_date'], val['end_date'],
                val['crawl_status'], val['content_type'], val['dx'], val['los'], val['pax'], val['h_name'], val['h_id'], val['meta_data'],
                val['sk'], val['url'], val['crawl_type'], val['start_date'], val['end_date'],
                val['crawl_status'], val['content_type'], val['dx'], val['los'], val['pax'], val['h_name'], val['h_id'], val['meta_data'],
                )

        cur.execute(CRAWL_TABLE_QUERY,vals)





def terminal_requests(cursor, source, crawl_type, content_type, limit):
    crawl_table_name = "%s_crawl" % (source)
    if limit:
        cursor.execute(CRAWL_TABLE_SELECT_QUERY_LIMIT%(crawl_table_name, crawl_type, content_type, limit))
    else:
        cursor.execute(CRAWL_TABLE_SELECT_QUERY%(crawl_table_name, crawl_type, content_type))
    rows = cursor.fetchall()
    sks_lst = []
    if rows:
        for row in rows:
            if row[0]:
                sks_lst.append(str(row[0]))
                cursor.execute(UPDATE_QUERY%(crawl_table_name, crawl_type, str(row[0]), content_type))
        return rows





def terminal_clear_requests(cursor, source, crawl_type, content_type, limit):
    crawl_table_name = "%s_crawl" % (source)
    if limit:
        cursor.execute(CLEAR_TABLE_SELECT_QUERY_LIMIT%(crawl_table_name, crawl_type, content_type, limit))
    else:
        cursor.execute(CLEAR_TABLE_SELECT_QUERY%(crawl_table_name, crawl_type, content_type))
    rows = cursor.fetchall()
    sks_lst = []
    if rows:
        for row in rows:
            if row[0]:
                sks_lst.append(str(row[0]))
                cursor.execute(UPDATE_QUERY%(crawl_table_name, crawl_type, str(row[0]), content_type))
        return rows


def terminal_goibibo_requests(cursor, source, crawl_type, content_type, limit):
    crawl_table_name = "%s_crawl" % (source)
    if limit:
        cursor.execute(GB_TABLE_SELECT_QUERY_LIMIT%(crawl_table_name, crawl_type, content_type, limit))
    else:
        cursor.execute(GB_TABLE_SELECT_QUERY%(crawl_table_name, crawl_type, content_type))
    rows = cursor.fetchall()
    sks_lst = []
    if rows:
        for row in rows:
            if row[0]:
                sks_lst.append(str(row[0]))
                cursor.execute(UPDATE_QUERY%(crawl_table_name, crawl_type, str(row[0]), content_type))
        return rows





def got_page(cursor, source, sk, status, crawl_type, content_type):
      crawl_table_name = "%s_crawl" % (source)
      cursor.execute(UPDATE_WITH_9_STATUS%(crawl_table_name, status, crawl_type, sk, content_type))


    
def create_ct_table_cusor():
    conns = MySQLdb.connect(host ='localhost', user ='root', db = 'MMCTRP', charset='utf8', use_unicode=True)
    curs = conns.cursor()
    return curs

def drop_ct_table(curs,source):
    dropcrawl_table ='%s' %(source)
    DROP_QUERY ='TRUNCATE TABLE %s;' %(dropcrawl_table)
    try:curs.execute(DROP_QUERY)
    except Exception, e: print str(e)

def ensure_ct_table(curs, source):
    mmt_table = '%s' %(source)
    SHOW_QUERY = 'SHOW TABLES LIKE "%s";' %(source)
    curs.execute(SHOW_QUERY)
    try:curs.execute(CT_TABLE_CREATE_QUERY.replace('#CT-TABLE#', source))
    except: print "Table already exists"

'''

def insert_ct_tables_data(curs,source,val): 
    try:
        
        CT_TABLE_QUERY = 'INSERT INTO %s'%source +'(city, ctthotelname, ctthotelid, check_in, cttrate, b2cdiff, cttinclusions,'
        CT_TABLE_QUERY+='dx, los, pax, cttroomtype, cttapprate, mobilediff, rmtc, child, ctt_b2c_splashed_price, ctt_app_splashed_price,'\
                        'cttb2ctaxes, ctt_apptaxes, cttcoupon_code, cttcoupon_discount, cttcoupon_description,check_out, created_on)'\
                        'VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())'

        CT_TABLE_QUERY+= 'ON DUPLICATE KEY UPDATE ctthotelid=%s'
        if val:
            vals=(val['city'], val['ctthotelname'], val['ctthotelid'], val['check_in'], val['cttrate'], val['b2cdiff'], val['cttinclusions'],
                  val['dx'], val['los'], val['pax'], val['cttroomtype'], val['cttapprate'], val['mobilediff'], val['rmtc'], val['child'],
                  val['ctt_b2c_splashed_price'], val['ctt_app_splashed_price'], val['cttb2ctaxes'], val['ctt_apptaxes'], val['cttcoupon_code'],
                  val['cttcoupon_discount'], val['cttcoupon_description'], val['check_out'], val['ctthotelid']
                  )

            curs.execute(CT_TABLE_QUERY,vals)
    except Exception, e: print str(e)
	'''






def create_logger_obj(source):
    cur_dt = str(datetime.datetime.now().date())
    LOGS_DIR = '/root/hotels/HOTELS/Hotels/Hotels/logs'
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

def normalize_clean(text):
    return clean(compact(xcode(text)))

def normalize(text):
    value =text.replace(",","").strip()
    return value
