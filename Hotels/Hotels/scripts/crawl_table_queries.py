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
        `created_on` datetime NOT NULL,
        `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        `last_seen` datetime NOT NULL,
        UNIQUE KEY `hotelid` (`city`,`mmthotelid`,`dx`,`los`,`pax`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE utf8_unicode_ci;
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
        `created_on` datetime NOT NULL,
        `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        `last_seen` datetime NOT NULL,
        UNIQUE KEY `hotelid` (`city`,`ctthotelid`,`dx`,`los`,`pax`)
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
	`aux_info` text COLLATE utf8_unicode_ci,
	`reference_url` text COLLATE utf8_unicode_ci,
        `created_on` datetime NOT NULL,
        `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        `last_seen` datetime NOT NULL,
        UNIQUE KEY `gbhotelid` (`city`,`gbthotelid`,`dx`,`los`,`pax`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE utf8_unicode_ci;
"""









#crawl_table_insert_query


# crawl_table_Select_query


CLEAR_TABLE_SELECT_QUERY = 'SELECT sk, url, dx, los, pax, start_date, end_date,h_name,h_id FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT 100;'

CLEAR_TABLE_SELECT_QUERY_LIMIT = 'SELECT sk, url, dx, los, pax, start_date, end_date,h_name,h_id FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT %s;'


CRAWL_TABLE_SELECT_QUERY = 'SELECT sk, url, dx, los, pax, start_date, end_date,ccode,hotel_ids,hotel_name FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT 100;'



CRAWL_TABLE_SELECT_QUERY_LIMIT = 'SELECT sk, url, dx, los, pax, start_date, end_date,ccode,hotel_ids,hotel_name FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT %s;'




GB_TABLE_SELECT_QUERY = 'SELECT sk, url, dx, los, pax, start_date, end_date, ccode, hotel_ids, hotel_name FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT 100;'

GB_TABLE_SELECT_QUERY_LIMIT = 'SELECT sk, url, dx, los, pax, start_date, end_date, ccode, hotel_ids, hotel_name FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT %s;'



UPDATE_QUERY = 'UPDATE %s SET crawl_status=9, modified_at=NOW() WHERE crawl_type="%s" AND crawl_status=0 AND sk = "%s" AND content_type="%s";'




UPDATE_WITH_9_STATUS = 'UPDATE %s SET crawl_status=%s, modified_at=NOW() WHERE crawl_status=9 AND crawl_type="%s" AND sk="%s" AND content_type="%s";'
