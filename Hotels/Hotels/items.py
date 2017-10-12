# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html


from scrapy.item import Item, Field

import scrapy


class MmtctItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass



class MMTRIPItem(Item):
    city =  Field()
    mmthotelname= Field()
    mmthotelid = Field()
    check_in = Field()
    dx = Field()
    los = Field()
    mmtpax = Field()
    mmtroomtype = Field()
    mmtrate = Field()
    mmtb2cdiff = Field()
    mmtinclusions = Field()
    mmtapprate = Field()
    mobilediff = Field()
    mmtb2csplashedprice = Field()
    mmtappsplashedprice = Field()
    mmtb2ctaxes = Field()
    mmtapptaxes = Field()
    child = Field()
    mmtcouponcode = Field()
    mmtcoupondescription = Field()
    mmtcoupondiscount  = Field()
    rmtc = Field()
    check_out = Field()
    gstincluded=Field()
    totalamtaftergst = Field()


class CTRIPItem(Item):
    city =  Field()
    cthotelname= Field()
    cthotelid = Field()
    check_in = Field()
    dx = Field()
    los = Field()
    ctpax = Field()
    ctroomtype = Field()
    ctrate = Field()
    ctb2cdiff = Field()
    ctinclusions = Field()
    ctapprate = Field()
    mobilediff = Field()
    ctb2csplashedprice = Field()
    ctappsplashedprice = Field()
    ctb2ctaxes = Field()
    ctapptaxes = Field()
    child = Field()
    ctcouponcode = Field()
    ctcoupondescription = Field()
    ctcoupondiscount  = Field()
    rmtc = Field()
    check_out = Field()


class GOBTRIPItem(Item):
    city =  Field()
    gbthotelname= Field()
    gbthotelid = Field()
    check_in = Field()
    dx = Field()
    los = Field()
    gbtpax = Field()
    gbtroomtype = Field()
    gbtrate = Field()
    gbtb2cdiff = Field()
    gbtinclusions = Field()
    gbtapprate = Field()
    mobilediff = Field()
    gbtb2csplashedprice = Field()
    gbtappsplashedprice = Field()
    gbtb2ctaxes = Field()
    gbtapptaxes = Field()
    child = Field()
    gbtcouponcode = Field()
    gbtcoupondescription = Field()
    gbtcoupondiscount  = Field()
    rmtc = Field()
    check_out = Field()
    gstincluded=Field()
    totalamtaftergst = Field()
    aux_info=Field()
    reference_url=Field()
