import scrapy
import  MySQLdb
import json
con = MySQLdb.connect(db   = 'urlqueue_dev', \
    host = 'localhost', charset="utf8", use_unicode=True, \
    user = 'root', passwd ='root')
cur = con.cursor()
insert_query = 'insert into tripadvisor_crawl(sk,crawl_status,url, meta_data, created_at, modified_at)values(%s,%s, %s, %s, now(), now()) on duplicate key update modified_at = now()'
class TripAdvisorBrowse(scrapy.Spider):
        name = "tripadvisor_browse"
        with open('TAD_URLS.json', 'r') as f: rows = f.readlines()
        for row in rows:
	    json_data = json.loads(row)
	    locations_list = json_data.keys()
	    for locationid in locations_list:
		crawl_status = 0
		sk = locationid
		url = json_data[locationid][2]
		values = (sk,crawl_status,url,'')
		cur.execute(insert_query,values)

