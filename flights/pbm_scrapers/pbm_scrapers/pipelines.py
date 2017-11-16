# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from utils import *

class PbmScrapersPipeline(object):
    def process_item(self, item, spider):
	if isinstance(item, OnewayItem):
            movie_values = '#<>#'.join([
                item['sk'],
		item,get('price', ''),
		item.get('airline', ''),
		item.get('depature_datetime', ''),
                item.get('arrival_datetime', ''),
		str(item.get('rank', '')),
		item.get('segment_type', ''),
		item.get('segments', ''),
                item.get('trip_type', ''),
		item.get('flight_id', ''), 
		MySQLdb.escape_string(item.get('aux_info', ''))
            ])
            spider.get_movie_file().write('%s\n' % movie_values)
            spider.get_movie_file().flush()

            self.write_item_into_avail_file(item, spider, 'movie')
        return item

    
