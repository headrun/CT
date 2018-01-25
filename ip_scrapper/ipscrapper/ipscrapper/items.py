# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.item import Item, Field


class IpscrapperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass
class IpItem(Item):
    ip = Field()
    continent = Field()
    country = Field()
    capital = Field()
    city_location = Field()
    isp = Field()
    is_csvrun = Field()
    aux_info = Field()
    reference_url = Field()
