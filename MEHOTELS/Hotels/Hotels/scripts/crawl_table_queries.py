MMT_CRAWL_TABLE_CREATE_QUERY ="""
    CREATE TABLE `#CRAWL-TABLE#` (

	`sk` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  	`url` text COLLATE utf8_unicode_ci,
  	`dx` int(3) NOT NULL,
  	`los` int(3) NOT NULL,
  	`pax` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  	`ccode` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  	`hotel_ids` bigint(20) NOT NULL,
  	`hotel_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  	`crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  	`content_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  	`start_date` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
  	`end_date` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
  	`crawl_status` int(3) NOT NULL DEFAULT '0',
  	`meta_data` text COLLATE utf8_unicode_ci,
  	`created_at` datetime NOT NULL,
  	`modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  	UNIQUE KEY `ccid` (`sk`),
  	KEY `sk` (`sk`),
  	KEY `type` (`crawl_type`),
  	KEY `type_time` (`crawl_type`,`modified_at`)
	) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci

"""

#MMt_table_Create_query


MMT_TABLE_CREATE_QUERY ="""
    CREATE TABLE `#MMT-TABLE#` (
        `city` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
        `mmthotelname` text COLLATE utf8_unicode_ci,
        `mmthotelid` BIGINT  COLLATE utf8_unicode_ci NOT NULL,
        `check_in` date COLLATE utf8_unicode_ci NOT NULL,
        `dx` int(3) COLLATE utf8_unicode_ci NOT NULL,
        `los` int (3) COLLATE utf8_unicode_ci NOT NULL,
        `pax` int(2) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
        `mmtroomtype` varchar(50) COLLATE utf8_unicode_ci,
        `mmtrate` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
        `b2cdiff` varchar(10)  COLLATE utf8_unicode_ci DEFAULT '0',
        `mmtinclusions` text COLLATE utf8_unicode_ci,
        `mmtapprate` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
        `mobilediff` varchar(10)  COLLATE utf8_unicode_ci DEFAULT '0' ,
        `mmt_b2c_splashed_price` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
        `mmt_app_splashed_price` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
        `mmtb2ctaxes` varchar(10)  COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
        `mmt_apptaxes` varchar(10)  COLLATE utf8_unicode_ci DEFAULT '0',
        `child`  int(3) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
        `mmtcoupon_code` varchar(40) COLLATE utf8_unicode_ci,
        `mmtcoupon_description` varchar(50) COLLATE utf8_unicode_ci,
        `mmtcoupon_discount` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
        `rmtc` varchar(25) COLLATE utf8_unicode_ci DEFAULT '0',
        `check_out` date COLLATE utf8_unicode_ci NOT NULL,
        `mmtgst_included` varchar(5) COLLATE utf8_unicode_ci,
        `mmttotalamt_aftergst` varchar(10) COLLATE utf8_unicode_ci,
	`cancellation_policy` text COLLATE utf8_unicode_ci,
        `ct_id` bigint(20) NOT NULL,
        `unique_sk` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
        `aux_info` text COLLATE utf8_unicode_ci,
        `created_on` datetime NOT NULL,
        `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        `last_seen` datetime NOT NULL,
        UNIQUE KEY `hotelid` (`city`,`mmthotelid`,`dx`,`los`,`pax`,`unique_sk`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci
"""

#Cleartrip_table_query




CT_TABLE_CREATE_QUERY ="""
    CREATE TABLE `#CT-TABLE#` (
        `city` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
        `ctthotelname` text COLLATE utf8_unicode_ci NOT NULL,
        `ctthotelid` BIGINT COLLATE utf8_unicode_ci NOT NULL,
        `check_in` date COLLATE utf8_unicode_ci NOT NULL,
        `dx` int(3) COLLATE utf8_unicode_ci NOT NULL,
        `los` int (3) COLLATE utf8_unicode_ci NOT NULL,
        `pax` int(2) COLLATE utf8_unicode_ci NOT NULL,
        `cttroomtype` varchar(50) COLLATE utf8_unicode_ci,
        `cttrate` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
        `b2cdiff` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
        `cttinclusions` text COLLATE utf8_unicode_ci DEFAULT '',
        `cttapprate` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
        `mobilediff` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
        `ctt_b2c_splashed_price` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
        `ctt_app_splashed_price` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
        `cttb2ctaxes` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
        `ctt_apptaxes` varchar(10)  COLLATE utf8_unicode_ci DEFAULT '0',
        `child`  int(3) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
        `cttcoupon_code` varchar(50) COLLATE utf8_unicode_ci DEFAULT '',
        `cttcoupon_description` varchar(30) COLLATE utf8_unicode_ci DEFAULT '',
        `cttcoupon_discount`  varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
        `rmtc` varchar(25) COLLATE utf8_unicode_ci DEFAULT '',
        `check_out` date COLLATE utf8_unicode_ci NOT NULL,
        `ctsell_price` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
        `ctchmm_discount` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
        `cancellation_policy` text COLLATE utf8_unicode_ci,
	`unique_sk` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
        `aux_info` text COLLATE utf8_unicode_ci,
        `created_on` datetime NOT NULL,
        `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        `last_seen` datetime NOT NULL,
        UNIQUE KEY `hotelid` (`city`,`ctthotelid`,`dx`,`los`,`pax`,`unique_sk`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE utf8_unicode_ci;
"""


#Crawl_table_ClearTrip_query




CLEAR_CRAWL_TABLE_CREATE_QUERY ="""
    CREATE TABLE `#CRAWL-TABLE#` (
	`sk` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  	`url` text COLLATE utf8_unicode_ci,
  	`dx` int(3) NOT NULL,
  	`los` int(3) NOT NULL,
  	`pax` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  	`h_name` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  	`h_id` bigint(20) NOT NULL,
  	`crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  	`content_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  	`start_date` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
  	`end_date` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
  	`crawl_status` int(3) NOT NULL DEFAULT '0',
  	`meta_data` text COLLATE utf8_unicode_ci,
  	`created_at` datetime NOT NULL,
  	`modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  	UNIQUE KEY `clearid` (`sk`),
  	KEY `sk` (`sk`),
  	KEY `type` (`crawl_type`),
  	KEY `type_time` (`crawl_type`,`modified_at`)
	) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci

"""
#GOIBIBO_table Querys

GB_CRAWL_TABLE_CREATE_QUERY ="""
    CREATE TABLE `#CRAWL-TABLE#` (

        `sk` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
        `url` text COLLATE utf8_unicode_ci,
        `dx` int(3) NOT NULL,
        `los` int(3) NOT NULL,
        `pax` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
        `ccode` varchar(25) COLLATE utf8_unicode_ci NOT NULL,
        `hotel_ids` bigint(20) NOT NULL,
        `hotel_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
        `crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
        `content_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
        `start_date` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
        `end_date` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
        `crawl_status` int(3) NOT NULL DEFAULT '0',
        `meta_data` text COLLATE utf8_unicode_ci,
	`aux_info` text COLLATE utf8_unicode_ci,
	`reference_url` text COLLATE utf8_unicode_ci,
        `created_at` datetime NOT NULL,
        `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY `ccid` (`sk`),
        KEY `sk` (`sk`),
        KEY `type` (`crawl_type`),
        KEY `type_time` (`crawl_type`,`modified_at`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci

"""




GB_TABLE_CREATE_QUERY ="""
    CREATE TABLE `#GOB-TABLE#` (
        `city` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
        `gbthotelname` text COLLATE utf8_unicode_ci,
        `gbthotelid` BIGINT  COLLATE utf8_unicode_ci NOT NULL,
        `check_in` date COLLATE utf8_unicode_ci NOT NULL,
        `dx` int(3) COLLATE utf8_unicode_ci NOT NULL,
        `los` int (3) COLLATE utf8_unicode_ci NOT NULL,
        `pax` int(2) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
        `gbtroomtype` varchar(100) COLLATE utf8_unicode_ci,
        `gbtrate` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
        `b2cdiff` varchar(10)  COLLATE utf8_unicode_ci DEFAULT '0',
        `gbtinclusions` text COLLATE utf8_unicode_ci,
        `gbtapprate` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
        `mobilediff` varchar(10)  COLLATE utf8_unicode_ci DEFAULT '0' ,
        `gbt_b2c_splashed_price` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
        `gbt_app_splashed_price` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
        `gbtb2ctaxes` varchar(10)  COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
        `gbt_apptaxes` varchar(10)  COLLATE utf8_unicode_ci DEFAULT '0',
        `child`  int(3) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
        `gbtcoupon_code` varchar(40) COLLATE utf8_unicode_ci,
        `gbtcoupon_description` varchar(50) COLLATE utf8_unicode_ci,
        `gbtcoupon_discount` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
        `rmtc` varchar(25) COLLATE utf8_unicode_ci DEFAULT '0',
        `check_out` date COLLATE utf8_unicode_ci NOT NULL,
        `gbtgst_included` varchar(5) COLLATE utf8_unicode_ci,
        `gbttotalamt_aftergst` varchar(10) COLLATE utf8_unicode_ci,
	`cancellation_policy` text COLLATE utf8_unicode_ci,
	`ct_id` bigint(20) NOT NULL,
	`unique_sk` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
	`aux_info` text COLLATE utf8_unicode_ci,
	`reference_url` text COLLATE utf8_unicode_ci,
	`created_on` datetime NOT NULL,
	`modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	`last_seen` datetime NOT NULL,
	UNIQUE KEY `gbhotelid` (`city`,`gbthotelid`,`dx`,`los`,`pax`,`unique_sk`)
	) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci

"""

BOOKING_TABLE_CREATE_QUERY = """
CREATE TABLE `Booking` (
  `pax` int(2) NOT NULL DEFAULT '0',
  `child` int(3) NOT NULL DEFAULT '0',
  `dx` int(3) NOT NULL,
  `los` int(3) NOT NULL,
  `check_in` date NOT NULL,
  `check_out` date NOT NULL,
  `city` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `hotelname` text COLLATE utf8_unicode_ci,
  `hotelid` bigint(20) NOT NULL,
  `room_type` text COLLATE utf8_unicode_ci,
  `rmtc` text COLLATE utf8_unicode_ci,
  `rate_plan` text COLLATE utf8_unicode_ci,
  `final_rate_plan` text COLLATE utf8_unicode_ci,
  `inclusions` text COLLATE utf8_unicode_ci,
  `cancellation_policy` text COLLATE utf8_unicode_ci,
  `splashed_price` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
  `actual_price` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
  `gst_amt` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
  `ct_id` bigint(20) NOT NULL,
  `unique_sk` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `aux_info` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_on` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  UNIQUE KEY `gbhotelid` (`city`,`hotelid`,`dx`,`los`,`pax`,`unique_sk`,`child`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci

"""

TA_CRAWL_TABLE_CREATE_QUERY ="""
	CREATE TABLE `#CRAWL-TABLE#` (
	`sk` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
	`url` text COLLATE utf8_unicode_ci,
	`dx` int(3) NOT NULL,
	`los` int(3) NOT NULL,
	`pax` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
	`ccode` varchar(25) COLLATE utf8_unicode_ci NOT NULL,
	`hotel_ids` bigint(20) NOT NULL,
	`hotel_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
	`crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
	`content_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
	`start_date` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
	`end_date` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
	`crawl_status` int(3) NOT NULL DEFAULT '0',
	`crawl_ref_status` int(3) NOT NULL DEFAULT '0',
	`meta_data` text COLLATE utf8_unicode_ci,
	`aux_info` text COLLATE utf8_unicode_ci,
	`reference_url` text COLLATE utf8_unicode_ci,
	`created_at` datetime NOT NULL,
	`modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	UNIQUE KEY `ccid` (`sk`),
	KEY `sk` (`sk`),
	KEY `type` (`crawl_type`),
	KEY `type_time` (`crawl_type`,`modified_at`)
	) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci
	"""

TRIPM_TABLE_CREATE_QUERY = """
CREATE TABLE `#TA-TABLE#` (
  `sk` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `city_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `property_name` text COLLATE utf8_unicode_ci,
  `TA_hotel_id` text COLLATE utf8_unicode_ci,
  `checkin` date NOT NULL,
  `DX` int(4) NOT NULL,
  `Pax` int(4) NOT NULL,
  `Ranking_Agoda` int(10) NOT NULL,
  `Ranking_BookingCom` int(10) NOT NULL,
  `Ranking_ClearTrip` int(10) NOT NULL,
  `Ranking_Expedia` int(10) NOT NULL,
  `Ranking_Goibibo` int(10) NOT NULL,
  `Ranking_HotelsCom2` int(10) NOT NULL,
  `Ranking_MakeMyTrip` int(10) NOT NULL,
  `Ranking_Yatra` int(10) NOT NULL,
  `Ranking_TG` int(10) NOT NULL,
  `Price_Agoda` text COLLATE utf8_unicode_ci,
  `Price_BookingCom` text COLLATE utf8_unicode_ci,
  `Price_ClearTrip` text COLLATE utf8_unicode_ci,
  `Price_Expedia` text COLLATE utf8_unicode_ci,
  `Price_Goibibo` text COLLATE utf8_unicode_ci,
  `Price_HotelsCom2` text COLLATE utf8_unicode_ci,
  `Price_MakeMyTrip` text COLLATE utf8_unicode_ci,
  `Price_Yatra` text COLLATE utf8_unicode_ci,
  `Price_TG` text COLLATE utf8_unicode_ci,
  `Tax_Agoda` text COLLATE utf8_unicode_ci,
  `Tax_BookingCom` text COLLATE utf8_unicode_ci,
  `Tax_ClearTrip` text COLLATE utf8_unicode_ci,
  `Tax_Expedia` text COLLATE utf8_unicode_ci,
  `Tax_Goibibo` text COLLATE utf8_unicode_ci,
  `Tax_HotelsCom2` text COLLATE utf8_unicode_ci,
  `Tax_MakeMyTrip` text COLLATE utf8_unicode_ci,
  `Tax_Yatra` text COLLATE utf8_unicode_ci,
  `Tax_TG` text COLLATE utf8_unicode_ci,
  `Total_Agoda` text COLLATE utf8_unicode_ci,
  `Total_BookingCom` text COLLATE utf8_unicode_ci,
  `Total_ClearTrip` text COLLATE utf8_unicode_ci,
  `Total_Expedia` text COLLATE utf8_unicode_ci,
  `Total_Goibibo` text COLLATE utf8_unicode_ci,
  `Total_HotelsCom2` text COLLATE utf8_unicode_ci,
  `Total_MakeMyTrip` text COLLATE utf8_unicode_ci,
  `Total_Yatra` text COLLATE utf8_unicode_ci,
  `Total_TG` text COLLATE utf8_unicode_ci,
  `Cheaper_Agoda` text COLLATE utf8_unicode_ci,
  `Cheaper_BookingCom` text COLLATE utf8_unicode_ci,
  `Cheaper_ClearTrip` text COLLATE utf8_unicode_ci,
  `Cheaper_Expedia` text COLLATE utf8_unicode_ci,
  `Cheaper_Goibibo` text COLLATE utf8_unicode_ci,
  `Cheaper_HotelsCom2` text COLLATE utf8_unicode_ci,
  `Cheaper_MakeMyTrip` text COLLATE utf8_unicode_ci,
  `Cheaper_Yatra` text COLLATE utf8_unicode_ci,
  `Cheaper_TG` text COLLATE utf8_unicode_ci,
  `Status_Agoda` text COLLATE utf8_unicode_ci,
  `Status_BookingCom` text COLLATE utf8_unicode_ci,
  `Status_ClearTrip` text COLLATE utf8_unicode_ci,
  `Status_Expedia` text COLLATE utf8_unicode_ci,
  `Status_Goibibo` text COLLATE utf8_unicode_ci,
  `Status_HotelsCom2` text COLLATE utf8_unicode_ci,
  `Status_MakeMyTrip` text COLLATE utf8_unicode_ci,
  `Status_Yatra` text COLLATE utf8_unicode_ci,
  `Status_TG` text COLLATE utf8_unicode_ci,
  `Ranking_Stayzilla` int(10) NOT NULL,
  `Price_Stayzilla` text COLLATE utf8_unicode_ci,
  `Tax_Stayzilla` text COLLATE utf8_unicode_ci,
  `Total_Stayzilla` text COLLATE utf8_unicode_ci,
  `Cheaper_Stayzilla` text COLLATE utf8_unicode_ci,
  `Status_Stayzilla` text COLLATE utf8_unicode_ci,
  `Time` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_on` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  UNIQUE KEY `hotelid` (`sk`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci
"""

TRIPMCITY_TABLE_CREATE_QUERY = """
CREATE TABLE `#TA-TABLE#cityrank` (
  `sk` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `city_rank` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `created_on` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  UNIQUE KEY `hotelid` (`sk`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci

"""


CTCONTENT_TABLE_CREATE_QUERY = """
        CREATE TABLE `#CONTENT-TABLE#`(
         `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
          `hotel_id` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
          `hotel_name` text COLLATE utf8_unicode_ci,
          `address` text COLLATE utf8_unicode_ci,
          `city` text COLLATE utf8_unicode_ci,
          `locality_latitude` text COLLATE utf8_unicode_ci,
          `locality_longitude` text COLLATE utf8_unicode_ci,
          `star_rating` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
          `description` text COLLATE utf8_unicode_ci,
          `amenities` text COLLATE utf8_unicode_ci,
          `aux_info` text COLLATE utf8_unicode_ci,
          `reference_url` text COLLATE utf8_unicode_ci,
          `html_hotel_url` text COLLATE utf8_unicode_ci,
          `main_listing_url` text COLLATE utf8_unicode_ci,
          `navigation_url` text COLLATE utf8_unicode_ci,
          `created_on` datetime NOT NULL,
          `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          `last_seen` datetime NOT NULL,
          UNIQUE KEY `hotelid` (`sk`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci
"""

TRIPMIN_TABLE_CREATE_QUERY = """
CREATE TABLE `#TA-TABLE#Inventory` (
  `sk` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `city_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `property_name` text COLLATE utf8_unicode_ci,
  `TA_hotel_id` text COLLATE utf8_unicode_ci,
  `CT_hotel_id` text COLLATE utf8_unicode_ci,
  `checkin` date NOT NULL,
  `DX` int(4) NOT NULL,
  `Pax` int(4) NOT NULL,
  `ct_price` text COLLATE utf8_unicode_ci,
  `cheapest_ota_price` text COLLATE utf8_unicode_ci,
  `cheapest_ota_name` text COLLATE utf8_unicode_ci,
  `ct_room_name` text COLLATE utf8_unicode_ci,
  `cheapest_ota_room_name` text COLLATE utf8_unicode_ci,
  `status` text COLLATE utf8_unicode_ci,
  `which_case` text COLLATE utf8_unicode_ci,
  `Ranking_ClearTrip` text COLLATE utf8_unicode_ci,
  `Time` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `from_ta_url` text COLLATE utf8_unicode_ci,
  `main_url` text COLLATE utf8_unicode_ci,
  `created_on` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  UNIQUE KEY `hotelid` (`sk`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci
"""

#crawl_table_insert_query


# crawl_table_Select_query


CLEAR_TABLE_SELECT_QUERY = 'SELECT sk, url, dx, los, pax, start_date, end_date,h_name,h_id FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT 100;'

CLEAR_TABLE_SELECT_QUERY_LIMIT = 'SELECT sk, url, dx, los, pax, start_date, end_date,h_name,h_id FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT %s;'

CONTENT_CLEAR_TABLE_SELECT_QUERY = 'SELECT sk, url, h_name, meta_data FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT 100;'

CONTENT_CLEAR_TABLE_SELECT_QUERY_LIMIT = 'SELECT sk, url, h_name, meta_data FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT %s;'


CRAWL_TABLE_SELECT_QUERY = 'SELECT sk, url, dx, los, pax, start_date, end_date,ccode,hotel_ids,hotel_name, meta_data FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT 100;'



CRAWL_TABLE_SELECT_QUERY_LIMIT = 'SELECT sk, url, dx, los, pax, start_date, end_date,ccode,hotel_ids,hotel_name, meta_data FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT %s;'




GB_TABLE_SELECT_QUERY = 'SELECT sk, url, dx, los, pax, start_date, end_date, ccode, hotel_ids, hotel_name, meta_data FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT 100;'

GB_TABLE_SELECT_QUERY_LIMIT = 'SELECT sk, url, dx, los, pax, start_date, end_date, ccode, hotel_ids, hotel_name, meta_data FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT %s;'

UPDATE_QUERY = 'UPDATE %s SET crawl_status=9, modified_at=NOW() WHERE crawl_type="%s" AND crawl_status=0 AND sk = "%s" AND content_type="%s";'

UPDATE_WITH_9_STATUS = 'UPDATE %s SET crawl_status=%s, modified_at=NOW() WHERE crawl_status=9 AND crawl_type="%s" AND sk="%s" AND content_type="%s";'

TA_UPDATE_QUERY = 'UPDATE %s SET crawl_status=9, modified_at=NOW() WHERE crawl_type="%s" AND (crawl_status=0 or crawl_status=8) AND sk = "%s" AND content_type="%s";'

TA_TABLE_SELECT_QUERY = 'SELECT sk, url, dx, los, pax, start_date, end_date, ccode, hotel_ids, hotel_name, aux_info FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" AND dx="%s" ORDER BY crawl_type DESC LIMIT 100;'

TA_TABLE_SELECT_QUERY_LIMIT = 'SELECT sk, url, dx, los, pax, start_date, end_date, ccode, hotel_ids, hotel_name, aux_info FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" AND dx="%s" ORDER BY crawl_type DESC LIMIT %s;'

TA_TABLE_SELECT_AQUERY_LIMIT = 'SELECT sk, url, dx, los, pax, start_date, end_date, ccode, hotel_ids, hotel_name, aux_info FROM %s WHERE crawl_type="%s" AND crawl_status=8 AND content_type="%s" AND dx="%s" ORDER BY crawl_type DESC LIMIT %s;'

TAH_TABLE_SELECT_AQUERY_LIMIT = 'SELECT DISTINCT hotel_ids, reference_url FROM %s WHERE crawl_type="%s" AND crawl_ref_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT %s;'

TAH_UPDATE_QUERY = 'UPDATE %s SET crawl_ref_status=9, modified_at=NOW() WHERE crawl_type="%s" AND crawl_ref_status=0 AND hotel_ids = "%s" AND content_type="%s";'

TAH_TABLE_SELECT_QUERY = 'SELECT sk, reference_url FROM %s WHERE crawl_type="%s" AND crawl_ref_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT 100;'

TG_TABLE_SELECT_QUERY_LIMIT = 'select sk, dx, los, city_name, city_id, latitude, longitude, crawl_type, content_type, start_date, end_date, crawl_status, reference_url FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY meta_data+0 ASC LIMIT %s;'

TG_TABLE_SELECT_QUERY = 'select sk, dx, los, city_name, city_id, latitude, longitude, crawl_type, content_type, start_date, end_date, crawl_status, reference_url FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY meta_data+0 ASC LIMIT 100;'
CRAWL_TABLE_SELECT_QUERY_LIMIT_STATIC = 'SELECT sk, url, dx, los, pax, start_date, end_date,ccode,hotel_ids,hotel_name, meta_data FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT %s;'
CRAWL_TABLE_SELECT_QUERY_STATIC = 'SELECT sk, url, dx, los, pax, start_date, end_date,ccode,hotel_ids,hotel_name, meta_data FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT 100;'
TA_TABLE_SELECT_QUERY_WDX = 'SELECT sk, url, dx, los, pax, start_date, end_date, ccode, hotel_ids, hotel_name, aux_info FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT 100;'

TA_TABLE_SELECT_QUERY_LIMIT_WDX = 'SELECT sk, url, dx, los, pax, start_date, end_date, ccode, hotel_ids, hotel_name, aux_info FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT %s;'

TA_TABLE_SELECT_AQUERY_LIMIT_WDX = 'SELECT sk, url, dx, los, pax, start_date, end_date, ccode, hotel_ids, hotel_name, aux_info FROM %s WHERE crawl_type="%s" AND crawl_status=8 AND content_type="%s" ORDER BY crawl_type DESC LIMIT %s;'

