CRAWL_TABLE_CREATE_QUERY = """
    CREATE TABLE `#CRAWL-TABLE#` (
      `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
      `dx` int(4) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
      `crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
      `from_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
      `to_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
      `trip_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
      `start_date` datetime NOT NULL,
      `return_date` datetime NOT NULL,
      `crawl_status` int(3) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
      `meta_data` text COLLATE utf8_unicode_ci,
      `created_at` datetime NOT NULL,
      `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`sk`, `start_date`, `from_location`, `to_location`),
      KEY `sk` (`sk`),
      KEY `type` (`crawl_type`),
      KEY `type_time` (`crawl_type`,`modified_at`)
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE utf8_unicode_ci;
"""

#crawl_table_insert_query

# Crawl table related Querires
CRAWL_TABLE_SELECT_QUERY = 'SELECT sk, from_location, to_location, start_date, dx, return_date FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND trip_type="%s" ORDER BY crawl_type DESC LIMIT 100;'

CRAWL_TABLE_SELECT_QUERY_LIMIT = 'SELECT sk, from_location, to_location, start_date, dx, return_date FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND trip_type="%s" ORDER BY crawl_type DESC LIMIT %s;'

UPDATE_QUERY = 'UPDATE %s SET crawl_status=9, modified_at=NOW() WHERE crawl_type="%s" AND crawl_status=0 AND sk = "%s" AND trip_type="%s";'

UPDATE_WITH_9_STATUS = 'UPDATE %s SET crawl_status=%s, modified_at=NOW() WHERE crawl_status=9 AND crawl_type="%s" AND sk="%s" AND trip_type="%s";'

