# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re
import json
import MySQLdb
import datetime
from ipscrapper.items import *

class IpscrapperPipeline(object):
    def process_item(self, item, spider):
	if isinstance(item, IpItem):
		ip_values = '#<>#'.join([
		str(item['ip']), str(item.get('continent', '')), str(item.get('country', '')), str(item.get('capital', '')), str(item.get('city_location', '')), str(item.get('isp', '')), str(item.get('is_csvrun', '')),str(item.get('aux_info', '')), str(item.get('reference_url', ''))
		])
		spider.out_put_file.write('%s\n' % ip_values)
        	spider.out_put_file.flush()

        return item
