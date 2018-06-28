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
             item.get('ctcoupondescription',''),item.get('ctcoupondiscount',''),item.get('rmtc',''), str(item['check_out']), str(item.get('ctsell_price', 'N/A')), str(item.get('ctchmm_discount', 'N/A')), str(item.get('cancellation_policy', '')), str(item.get('unique_sk', '')), str(item.get('aux_info', ''))])
             
             spider.out_put_file.write('%s\n' % cleartrip_values)
             spider.out_put_file.flush()


         if isinstance(item, MMTRIPItem):

             makemytrip_values = '#<>#'.join([
             str(item['city']), item.get('mmthotelname',''), str(item['mmthotelid']),str(item['check_in']),str(item['dx']), str(item['los']),
             str(item['mmtpax']),item.get('mmtroomtype', ''),str(item['mmtrate']),str(item['mmtb2cdiff']), item.get('mmtinclusions', ''), 
             item.get('mmtapprate', ''), item.get('mobilediff', ''),str(item['mmtb2csplashedprice']), str(item['mmtappsplashedprice']),
             str(item['mmtb2ctaxes']),item.get('mmtapptaxes', ''),str(item['child']), item.get('mmtcouponcode',''), 
             item.get('mmtcoupondescription',''),item.get('mmtcoupondiscount',''),item.get('rmtc',''), str(item['check_out']),
             item.get('gstincluded',''), str(item.get('totalamtaftergst','')), str(item.get('cancellation_policy','')), str(item.get('ct_id', '')), str(item.get('unique_sk', '')), str(item.get('aux_info',''))])
             
             spider.out_put_file.write('%s\n' % makemytrip_values)
             spider.out_put_file.flush()

	
         if isinstance(item, GOBTRIPItem):

             gbtrip_values = '#<>#'.join([
             str(item['city']), item.get('gbthotelname',''), str(item['gbthotelid']),str(item['check_in']),str(item['dx']), str(item['los']),
             str(item['gbtpax']),item.get('gbtroomtype', ''),str(item['gbtrate']),str(item['gbtb2cdiff']), item.get('gbtinclusions', ''), 
             item.get('gbtapprate', ''), item.get('mobilediff', ''),str(item['gbtb2csplashedprice']), str(item['gbtappsplashedprice']),
             str(item['gbtb2ctaxes']),item.get('gbtapptaxes', ''),str(item['child']), item.get('gbtcouponcode',''), 
             item.get('gbtcoupondescription',''),item.get('gbtcoupondiscount',''),item.get('rmtc',''), str(item['check_out']),
             item.get('gstincluded',''), str(item.get('totalamtaftergst','')), str(item.get('cancellation_policy','')), str(item.get('ct_id', '')), str(item.get('unique_sk', '')),  str(item.get('aux_info','')), 
	     str(item.get('reference_url',''))])
             
             spider.out_put_file.write('%s\n' % gbtrip_values)
             spider.out_put_file.flush()

         if isinstance(item, TRIPADVISORItem):
             tripad_values = '#<>#'.join([
                str(item['sk']), str(item.get('city_name', '')),  str(item.get('property_name', '')), str(item.get('TA_hotel_id', '')), str(item.get('checkin', '')), str(item.get('DX', '')), str(item.get('Pax', '')), str(item.get('Ranking_Agoda', '')), str(item.get('Ranking_BookingCom', '')), str(item.get('Ranking_ClearTrip', '')), str(item.get('Ranking_Expedia', '')), str(item.get('Ranking_Goibibo', '')), str(item.get('Ranking_HotelsCom2', '')), str(item.get('Ranking_MakeMyTrip', '')), str(item.get('Ranking_Yatra', '')), str(item.get('Ranking_TG', '')), str(item.get('Price_Agoda', '')), str(item.get('Price_BookingCom', '')), str(item.get('Price_ClearTrip', '')), str(item.get('Price_Expedia', '')), str(item.get('Price_Goibibo', '')), str(item.get('Price_HotelsCom2', '')), str(item.get('Price_MakeMyTrip', '')), str(item.get('Price_Yatra', '')), str(item.get('Price_TG', '')), str(item.get('Tax_Agoda', '')), str(item.get('Tax_BookingCom', '')), str(item.get('Tax_ClearTrip', '')), str(item.get('Tax_Expedia', '')), str(item.get('Tax_Goibibo', '')), str(item.get('Tax_HotelsCom2', '')), str(item.get('Tax_MakeMyTrip', '')), str(item.get('Tax_Yatra', '')), str(item.get('Tax_TG', '')), str(item.get('Total_Agoda', '')), str(item.get('Total_BookingCom', '')), str(item.get('Total_ClearTrip', '')), str(item.get('Total_Expedia', '')), str(item.get('Total_Goibibo', '')), str(item.get('Total_HotelsCom2', '')), str(item.get('Total_MakeMyTrip', '')), str(item.get('Total_Yatra', '')), str(item.get('Total_TG', '')), str(item.get('Cheaper_Agoda', '')), str(item.get('Cheaper_BookingCom', '')), str(item.get('Cheaper_ClearTrip', '')), str(item.get('Cheaper_Expedia', '')), str(item.get('Cheaper_Goibibo', '')), str(item.get('Cheaper_HotelsCom2', '')), str(item.get('Cheaper_MakeMyTrip', '')), str(item.get('Cheaper_Yatra', '')), str(item.get('Cheaper_TG', '')), str(item.get('Status_Agoda', '')), str(item.get('Status_BookingCom', '')), str(item.get('Status_ClearTrip', '')), str(item.get('Status_Expedia', '')), str(item.get('Status_Goibibo', '')), str(item.get('Status_HotelsCom2', '')), str(item.get('Status_MakeMyTrip', '')), str(item.get('Status_Yatra', '')), str(item.get('Status_TG', '')), str(item.get('Ranking_Stayzilla', '')), str(item.get('Price_Stayzilla', '')), str(item.get('Tax_Stayzilla', '')), str(item.get('Total_Stayzilla', '')), str(item.get('Cheaper_Stayzilla', '')), str(item.get('Status_Stayzilla', '')), str(item.get('Time', '')), str(item.get('reference_url', ''))
                ])
             spider.out_put_file.write('%s\n' % tripad_values)
             spider.out_put_file.flush()

         if isinstance(item, TRIPADVISORcityrankItem):
             tripci_value = '#<>#'.join([
                str(item['sk']), str(item.get('city_rank', ''))
                ])
             spider.out_put_file.write('%s\n' % tripci_value)
             spider.out_put_file.flush()

         if isinstance(item, TRIVAGOItem):
            trivago_value = '#<>#'.join([
                str(item['sk']), str(item.get('crawl_table_sk', '')), str(item.get('city', '')), str(item.get('cleartrip_hotel_id', '')), str(item.get('hotel_name', '')), str(item.get('trivago_hotel_id', '')), str(item.get('check_in', '')), str(item.get('los', '')), str(item.get('rank1', '')), str(item.get('rank2', '')), str(item.get('rank3', '')),str(item.get('rank4')), str(item.get('ct_price', '')), str(item.get('ct_type', '')), str(item.get('expedia_price', '')), str(item.get('expedia_type', '')),str(item.get('hotelsdot_com_price', '')), str(item.get('hotelsdot_com_type', '')), str(item.get('bookingdot_com_price', '')), str(item.get('bookingdot_com_type', '')), str(item.get('hotel_info_price', '')),str(item.get('hotel_info_type', '')), str(item.get('mmt_price', '')), str(item.get('mmt_type', '')), str(item.get('agoda_price', '')), str(item.get('agoda_type', '')),str(item.get('amoma_price', '')), str(item.get('amoma_type', '')), str(item.get('hrs_price', '')), str(item.get('hrs_type', '')), str(item.get('available_otas', '')),str(item.get('price_difference')), str(item.get('beaten_by_booking_com', '')), str(item.get('beaten_by_price', '')), str(item.get('aux_info', '')), str(item.get('check_out', '')), str(item.get('reference_url', ''))
                ])
            spider.out_put_file.write('%s\n' % trivago_value)
            spider.out_put_file.flush()

         if isinstance(item, BookingItem):
            booking_value = '#<>#'.join([
             str(item.get('pax', '')), str(item.get('child', '')), str(item.get('dx', '')), str(item.get('los', '')), str(item.get('check_in', '')), str(item.get('check_out', '')), str(item.get('city', '')), str(item.get('hotelname', '')), str(item.get('hotelid', '')), str(item.get('room_type', '')), str(item.get('rmtc', '')), str(item.get('rate_plan', '')), str(item.get('final_rate_plan', '')),  str(item.get('inclusions', '')), str(item.get('cancellation_policy', '')), str(item.get('splashed_price', '')), str(item.get('actual_price', '')), str(item.get('gst_amt', '')),str(item.get('ct_id', '')), str(item.get('unique_sk', '')), str(item.get('aux_info', '')), str(item.get('reference_url', ''))
                ]) 
            spider.out_put_file.write('%s\n' % booking_value)
            spider.out_put_file.flush()

         if isinstance(item, TripadvisorInventoryItem):
            tripin_value = '#<>#'.join([
                str(item['sk']), str(item.get('city_name', '')), str(item.get('property_name', '')), str(item.get('TA_hotel_id', '')), str(item.get('CT_hotel_id', '')), str(item.get('checkin', '')), str(item.get('DX', '')), str(item.get('Pax', '')), str(item.get('ct_price', '')), str(item.get('cheapest_ota_price', '')), str(item.get('cheapest_ota_name', '')), str(item.get('ct_room_name', '')), str(item.get('cheapest_ota_room_name', '')), str(item.get('status', '')), str(item.get('which_case', '')), str(item.get('Ranking_ClearTrip', '')), str(item.get('Time', '')), str(item.get('reference_url', '')), str(item.get('from_ta_url', '')), str(item.get('main_url', ''))
            ])
            spider.out_put_file1.write('%s\n' % tripin_value)
            spider.out_put_file1.flush()

         return item
         
