import MySQLdb

conn = MySQLdb.connect(host="localhost",user="root",passwd="")
cursor = conn.cursor()
try:
    dbname = cursor.execute('CREATE DATABASE THRILLOPHILIA')
except:
    pass
cursor.close()

activity_info = """ CREATE TABLE `Activity` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `activity_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `itinerary` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `overview` text COLLATE utf8_unicode_ci,
  `no_of_days_nights` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `stay` text COLLATE utf8_unicode_ci,
  `meal` text COLLATE utf8_unicode_ci,
  `activities_available` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `other_inclusions` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `things_to_carry` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `advisory` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `tour_type` text COLLATE utf8_unicode_ci,
  `cancellation_policy` text COLLATE utf8_unicode_ci,
  `refund_policy` text COLLATE utf8_unicode_ci,
  `confirmation_policy` text COLLATE utf8_unicode_ci,
  `price` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `cashback` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `special_offer` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `rating` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `image_urls` text COLLATE utf8_unicode_ci,
  `review_url` text COLLATE utf8_unicode_ci,
  `reviews_count` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """


stays_info = """ CREATE TABLE `Stay` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `stay_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `itinerary` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `overview` text COLLATE utf8_unicode_ci,
  `no_of_days_nights` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `stay` text COLLATE utf8_unicode_ci,
  `meal` text COLLATE utf8_unicode_ci,
  `activities_available` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `other_inclusions` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `things_to_carry` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `advisory` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `tour_type` text COLLATE utf8_unicode_ci,
  `cancellation_policy` text COLLATE utf8_unicode_ci,
  `refund_policy` text COLLATE utf8_unicode_ci,
  `confirmation_policy` text COLLATE utf8_unicode_ci,
  `price` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `cashback` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `special_offer` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `rating` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `image_urls` text COLLATE utf8_unicode_ci,
  `review_url` text COLLATE utf8_unicode_ci,
  `reviews_count` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """


rental_info = """ CREATE TABLE `Rentals` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `rental_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `itinerary` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `overview` text COLLATE utf8_unicode_ci,
  `no_of_days_nights` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `other_inclusions` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `things_to_carry` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `advisory` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `tour_type` text COLLATE utf8_unicode_ci,
  `cancellation_policy` text COLLATE utf8_unicode_ci,
  `refund_policy` text COLLATE utf8_unicode_ci,
  `confirmation_policy` text COLLATE utf8_unicode_ci,
  `price` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `cashback` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `special_offer` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `rating` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `image_urls` text COLLATE utf8_unicode_ci,
  `review_url` text COLLATE utf8_unicode_ci,
  `reviews_count` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

con = MySQLdb.connect(db   =  'THRILLOPHILIA',
                      user              = 'root',
                      passwd            = '',
                      charset           = "utf8",
                      host              = 'localhost',
                      use_unicode       = True)
cur = con.cursor()

try:
    cur.execute(stays_info)
    cur.execute(activity_info)
    cur.execute(rental_info)

except:
    pass

cur.close()

