from scrapy.xlib.pydispatch import dispatcher
import scrapy
from scrapy.selector import Selector
from scrapy.http import Request
from scrapy.http import FormRequest
from Hotels.items import *
import os
import json
import datetime
import time
import urllib
from Hotels.utils import *
import re
import MySQLdb
import collections
import csv
import logging
from scrapy import log
from scrapy import signals


def create_crawl_table_cursor():
    conn = MySQLdb.connect(host='localhost', user='root', db=PROD_DB_NAME, charset='utf8', use_unicode=True, passwd=DB_PASSWORD)
    cur = conn.cursor()
    return cur



class TripAdvisorcityrank(scrapy.Spider):
    name = 'tripadvisorcityrank_terminal'
    #handle_httpstatus_list = [400,404,500,503,301,302]

    def __init__(self, *args, **kwargs):
        super(TripAdvisorcityrank, self).__init__(*args, **kwargs)
	self.name = 'Tripadvisorcityrank'
	self.cursor = create_crawl_table_cusor()
        self.log = create_logger_obj(self.name)
        self.crawl_type = kwargs.get('crawl_type','keepup')
        self.content_type = kwargs.get('content_type','hotels')
        self.limit = kwargs.get('limit',1000)
	self.out_put_file =get_gobtrip_file(self.name)
	dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self,spider):
	self.cursor.close()
        gob_crawlout_processing(self.out_put_file)

    def start_requests(self):
	rows = terminal_advisor_hotels(self.cursor, 'Tripadvisor', self.crawl_type, self.content_type, self.limit)
	if rows:
		for row_ in rows:
			sk , ref_url = row_
			yield Request(ref_url, callback=self.parse_next, dont_filter=True, meta = {"sk":sk})
    def parse_next(self, response):
	sel = Selector(response)
	sk = response.meta.get('sk', '')
	city_rank = ''.join(sel.xpath('//span[@class="header_popularity popIndexValidation"]//b[@class="rank"]/text()').extract()).replace('#', '')
	total_dict = TRIPADVISORcityrankItem()
	total_dict.update({"sk":sk, "city_rank":city_rank})
	self.cursor.execute("update Tripadvisor_crawl set crawl_ref_status=1 where hotel_ids='%s'" % sk)
	yield total_dict
