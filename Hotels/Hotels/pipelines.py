# -*- coding: utf- -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re
import json
import MySQLdb
import datetime
from Hotels.items import *

class HotelsPipeline(object):
    def process_item(self, item, spider):
         
         if isinstance(item, CTRIPItem):
             cleartrip_values = '#<>#'.join([
             str(item['city']), str(item['cthotelname']), str(item['cthotelid']),str(item['check_in']),str(item['dx']), str(item['los']),
             str(item['ctpax']),item.get('ctroomtype', ''),str(item['ctrate']),str(item['ctb2cdiff']), item.get('ctinclusions', ''),
             item.get('ctapprate', ''), item.get('mobilediff', ''),str(item['ctb2csplashedprice']), item.get('ctappsplashedprice',''),
             str(item['ctb2ctaxes']),item.get('ctapptaxes', ''),str(item['child']), item.get('ctcouponcode',''),
             item.get('ctcoupondescription',''),item.get('ctcoupondiscount',''),item.get('rmtc',''), str(item['check_out'])])
             
             spider.out_put_file.write('%s\n' % cleartrip_values)
             spider.out_put_file.flush()


         if isinstance(item, MMTRIPItem):

             makemytrip_values = '#<>#'.join([
             str(item['city']), item.get('mmthotelname',''), str(item['mmthotelid']),str(item['check_in']),str(item['dx']), str(item['los']),
             str(item['mmtpax']),item.get('mmtroomtype', ''),str(item['mmtrate']),str(item['mmtb2cdiff']), item.get('mmtinclusions', ''), 
             item.get('mmtapprate', ''), item.get('mobilediff', ''),str(item['mmtb2csplashedprice']), str(item['mmtappsplashedprice']),
             str(item['mmtb2ctaxes']),item.get('mmtapptaxes', ''),str(item['child']), item.get('mmtcouponcode',''), 
             item.get('mmtcoupondescription',''),item.get('mmtcoupondiscount',''),item.get('rmtc',''), str(item['check_out']),
             item.get('gstincluded',''), str(item.get('totalamtaftergst',''))])
             
             spider.out_put_file.write('%s\n' % makemytrip_values)
             spider.out_put_file.flush()

	
         if isinstance(item, GOBTRIPItem):

             gbtrip_values = '#<>#'.join([
             str(item['city']), item.get('gbthotelname',''), str(item['gbthotelid']),str(item['check_in']),str(item['dx']), str(item['los']),
             str(item['gbtpax']),item.get('gbtroomtype', ''),str(item['gbtrate']),str(item['gbtb2cdiff']), item.get('gbtinclusions', ''), 
             item.get('gbtapprate', ''), item.get('mobilediff', ''),str(item['gbtb2csplashedprice']), str(item['gbtappsplashedprice']),
             str(item['gbtb2ctaxes']),item.get('gbtapptaxes', ''),str(item['child']), item.get('gbtcouponcode',''), 
             item.get('gbtcoupondescription',''),item.get('gbtcoupondiscount',''),item.get('rmtc',''), str(item['check_out']),
             item.get('gstincluded',''), str(item.get('totalamtaftergst','')), str(item.get('aux_info','')), 
	     str(item.get('reference_url',''))])
             
             spider.out_put_file.write('%s\n' % gbtrip_values)
             spider.out_put_file.flush()


         return item
         
