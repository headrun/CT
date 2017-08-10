# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class CtmonitoringPipeline(object):
    #def process_item(self, item, spider):
        #return item

    def write_item_into_avail_file(self, item, spider, content_type):
        source = self.get_source(spider)

        if SOURCES_LIST.has_key(source):
            SOURCES_LIST[source](item, spider.get_avail_file(), spider.get_json_file())

    def process_item(self, item, spider):
        if isinstance(item, AvailabilityItem):
            best_seller_values = '#<>#'.join([
                item['sk'],item['date'], item.get('crawl_type', ''), item['is_available'], item['airline'], item['departure_time'],
                item['arrival_time'], item['from_location'], item['to_location'],
                MySQLdb.escape_string(item.get('providers', '')),
                MySQLdb.escape_string(item.get('aux_info', '')),
                item.get('reference_url', '')
            ])
            spider.get_availability_file().write('%s\n' %best_seller_values)
            spider.get_availability_file().flush()

            self.write_item_into_avail_file(item, spider, 'availability')

        return item

