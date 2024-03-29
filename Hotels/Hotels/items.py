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

class TRIPADVISORItem(Item):
    sk=Field()
    city_name=Field()
    property_name=Field()
    TA_hotel_id=Field()
    checkin=Field()
    DX=Field()
    Pax=Field()
    Ranking_Agoda=Field()
    Ranking_BookingCom=Field()
    Ranking_ClearTrip=Field()
    Ranking_Expedia=Field()
    Ranking_Goibibo=Field()
    Ranking_HotelsCom2=Field()
    Ranking_MakeMyTrip=Field()
    Ranking_Yatra=Field()
    Ranking_TG=Field()
    Price_Agoda=Field()
    Price_BookingCom=Field()
    Price_ClearTrip=Field()
    Price_Expedia=Field()
    Price_Goibibo=Field()
    Price_HotelsCom2=Field()
    Price_MakeMyTrip=Field()
    Price_Yatra=Field()
    Price_TG=Field()
    Tax_Agoda=Field()
    Tax_BookingCom=Field()
    Tax_ClearTrip=Field()
    Tax_Expedia=Field()
    Tax_Goibibo=Field()
    Tax_HotelsCom2=Field()
    Tax_MakeMyTrip=Field()
    Tax_Yatra=Field()
    Tax_TG=Field()
    Total_Agoda=Field()
    Total_BookingCom=Field()
    Total_ClearTrip=Field()
    Total_Expedia=Field()
    Total_Goibibo=Field()
    Total_HotelsCom2=Field()
    Total_MakeMyTrip=Field()
    Total_Yatra=Field()
    Total_TG=Field()
    Cheaper_Agoda=Field()
    Cheaper_BookingCom=Field()
    Cheaper_ClearTrip=Field()
    Cheaper_Expedia=Field()
    Cheaper_Goibibo=Field()
    Cheaper_HotelsCom2=Field()
    Cheaper_MakeMyTrip=Field()
    Cheaper_Yatra=Field()
    Cheaper_TG=Field()
    Status_Agoda=Field()
    Status_BookingCom=Field()
    Status_ClearTrip=Field()
    Status_Expedia=Field()
    Status_Goibibo=Field()
    Status_HotelsCom2=Field()
    Status_MakeMyTrip=Field()
    Status_Yatra=Field()
    Status_TG=Field()
    Ranking_Stayzilla=Field()
    Price_Stayzilla=Field()
    Tax_Stayzilla=Field()
    Total_Stayzilla=Field()
    Cheaper_Stayzilla=Field()
    Status_Stayzilla=Field()
    Time=Field()
    reference_url=Field()
class TRIPADVISORcityrankItem(Item):
    sk=Field()
    city_rank=Field()

