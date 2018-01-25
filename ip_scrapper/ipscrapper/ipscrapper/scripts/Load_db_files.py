import os
import sys
import re
import optparse
import json
from glob import glob
import traceback
import MySQLdb
import datetime
import logging, logging.handlers


PAR_DIR = os.path.abspath(os.pardir)
OUTPUT_DIR = os.path.join(PAR_DIR, 'spiders/OUTPUT')
PROCESSING_QUERY_FILES_PATH = os.path.join(OUTPUT_DIR, 'processing')
PROCESSED_QUERY_FILES_PATH = os.path.join(OUTPUT_DIR, 'processed')
UNPROCESSED_QUERY_FILES_PATH = os.path.join(OUTPUT_DIR, 'un-processed')
LOGS_DIR = os.path.join(os.getcwd(), 'logs')


def init_logger(filename, level=''):
    if not os.path.isdir(LOGS_DIR):
        os.mkdir(LOGS_DIR)
    file_name = os.path.join(LOGS_DIR, filename)
    log = logging.getLogger(file_name)
    handler = logging.handlers.RotatingFileHandler(file_name, maxBytes=524288000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s.%(msecs)d: %(filename)s: %(lineno)d: %(funcName)s: %(levelname)s: %(message)s', "%Y%m%dT%H%M%S")
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    return log
log = init_logger('load_queries_to_db.log')



def get_source_and_content_type(query_file):
    query_file = os.path.basename(query_file)
    source = query_file.split('_', 1)[0]
    content_type = query_file.split('_')[-2]
    db_name = 'IP_SCRAPER'
    table = source
    log.info("Query File: %s - Source: %s - Content Type: %s - Table Name: %s", query_file, source, content_type, table)
    return db_name, table



def load_meta_data_files(queries_file, _setup):
    _host = 'localhost'
    query_files = [queries_file] if queries_file else glob("%s/*.queries" % (PROCESSING_QUERY_FILES_PATH))
    for query_file in query_files:
        db_name, table = get_source_and_content_type(query_file)
        cmd = 'mysql -uroot ' +'-h'+ _host + ' -A ' + db_name + ' --local-infile=1 -e "%s"' 
        query =  "LOAD DATA LOCAL INFILE '%s' INTO TABLE %s CHARACTER SET utf8 FIELDS TERMINATED BY '#<>#'" % (query_file, table)
        query += "SET created_at=NOW(), modified_at=NOW();"
        try:
            log.info("Loading Started for: %s - Load Query: %s", query_file, cmd % query)
            os.system(cmd % query)
            log.info("Loading Completed For: %s", query_file)
        except:
            #log.error("Error Occured while loading %s data into %s table", ott_avail_file, table_name)
            log.error("Error: %s", traceback.format_exc())
            move_file(query_file, dest=UNPROCESSED_QUERY_FILES_PATH)
            continue
        move_file(query_file)


def move_file(source, dest=PROCESSED_QUERY_FILES_PATH):
    cmd = "mv %s %s" % (source, dest)
    os.system(cmd)
    log.info("Moved File From %s", cmd)


def main(options):
    load_meta_data_files(options.queries_file, options.setup)



if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-q', '--queries-file', default=None, help='Query File Name' )
    parser.add_option('-s', '--setup', default='localhost', help='Setup - localhost')
    (options, args) = parser.parse_args()
    main(options)


