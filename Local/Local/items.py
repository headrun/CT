# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class LocalItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class ActivityItem(Item):
    sk                          = Field()
    title                       = Field()
    city                        = Field()
    reference_url               = Field()
    itinerary                   = Field()
    aux_info                    = Field()

class StayItem(Item):
    sk                          = Field()
    title                       = Field()
    city                        = Field()
    reference_url               = Field()
    aux_info                    = Field()

class RentalItem(Item):
    sk                          = Field()
    title                       = Field()
    city                        = Field()
    reference_url               = Field()
    aux_info                    = Field()

class RichMedia(Item):
    sk                          = Field()
    program_sk                  = Field()
    program_type                = Field()
    media_type                  = Field()
    dimensions                  = Field()
    image_url                   = Field()
    reference_url               = Field()
    aux_info                    = Field()

class CommonItem(Item):
    program_sk                  = Field()
    program_type                = Field()
    city                        = Field()
    location                    = Field()
    overview                    = Field()
    no_of_days_nights           = Field()
    stay                        = Field()
    meal                        = Field()
    activity                    = Field()
    other_inclusions            = Field()
    things_to_carry             = Field()
    advisory                    = Field()
    tour_type                   = Field()
    reference_url               = Field()
    cancellation_policy         = Field()
    refund_policy               = Field()
    confirmation_policy         = Field()

class PriceItem(Item):
    program_sk                  = Field()
    program_type                = Field()
    price                       = Field()
    price_discounted            = Field()
    cashback                    = Field()
    specail_offer               = Field()

class ReviewItem(Item):
    program_sk                  = Field()
    program_type                = Field()
    review_count                = Field()
    review_url                  = Field()

class RatingItem(Item):
    program_sk                  = Field()
    program_type                = Field()
    rating                      = Field()
    rating_type                 = Field()
    rating_reason               = Field()
