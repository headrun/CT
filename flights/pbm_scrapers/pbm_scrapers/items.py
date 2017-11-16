# -*- coding: utf-6 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.item import Item, Field

class PbmScrapersItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class OnewayItem(Item):
    sk                       	= Field()
    price                    	= Field()
    airline                  	= Field()
    depature_datetime        	= Field()
    arrival_datetime         	= Field()
    rank              	    	= Field()
    segment_type		= Field()
    segment                	= Field()
    trip_type               	= Field()
    flight_id                 	= Field()
    aux_info                    = Field()

class ReturnItem(Item):
    sk                          = Field()
    price                       = Field()
    airline                     = Field()
    depature_datetime           = Field()
    arrival_datetime            = Field()
    rank                        = Field()
    segment_type                = Field()
    segment                     = Field()
    trip_type                   = Field()
    flight_id                   = Field()
    return_flight_id		= Field()
    return_price		= Field()
    aux_info                    = Field()
