import MySQLdb

conn = MySQLdb.connect(host="localhost",user="root",passwd="")
cursor = conn.cursor()
try:
    dbname = cursor.execute('CREATE DATABASE VIATOR')
except:
    pass
cursor.close()

thingstodo_info = """ CREATE TABLE `Things_To_Do` (
  `sk` varchar(230) COLLATE utf8_unicode_ci NOT NULL,
  `tour_code` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `travel_code` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `image_url` text COLLATE utf8_unicode_ci,
  `description` text COLLATE utf8_unicode_ci,
  `no_of_ratings` int(15) DEFAULT '0',
  `expectations` text COLLATE utf8_unicode_ci,
  `no_of_reviews` int(15) DEFAULT '0',
  `city` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(100) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `duration` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `highlights` text COLLATE utf8_unicode_ci,
  `departure_time` text COLLATE utf8_unicode_ci,
  `category` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `departure_point` text COLLATE utf8_unicode_ci,
  `price` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL,
  `about_travel` text COLLATE utf8_unicode_ci,
  `travel_description` text COLLATE utf8_unicode_ci,
  `return_details` text COLLATE utf8_unicode_ci,
  `cancellation_policy` text COLLATE utf8_unicode_ci,
  `inclusions` text COLLATE utf8_unicode_ci,
  `exclusions` text COLLATE utf8_unicode_ci,
  `additional_info` text COLLATE utf8_unicode_ci,
  `local_operatorinfo` text COLLATE utf8_unicode_ci,
  `voucher_info` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`sk`,`travel_code`),
  KEY `travel_code` (`sk`,`travel_code`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

con = MySQLdb.connect(db   =  'VIATOR',
                      user              = 'root',
                      passwd            = '',
                      charset           = "utf8",
                      host              = 'localhost',
                      use_unicode       = True)
cur = con.cursor()

cur.execute(thingstodo_info)




cur.close()
