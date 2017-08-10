# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.item import Item, Field

class CtmonitoringItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class AvailabilityItem(Item):
    sk                          = Field()
    date                        = Field()
    crawl_type			= Field()
    is_available                = Field()
    airline                     = Field()
    departure_time              = Field()
    arrival_time                = Field()
    from_location               = Field()
    to_location                 = Field()
    providers                   = Field()
    aux_info                    = Field()
    reference_url               = Field()

