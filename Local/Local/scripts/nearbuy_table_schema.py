import MySQLdb

conn = MySQLdb.connect(host="localhost",user="root",passwd="")
cursor = conn.cursor()
try:
    dbname = cursor.execute('CREATE DATABASE NEARBUY')
except:
    pass
cursor.close()

eatout_info  = """ CREATE TABLE `Eatout` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `place_category` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `description` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `addresses` text COLLATE utf8_unicode_ci,
  `how_to_use_offer` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `cancelletion_policy` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `things_to_remember` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `rating` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `rating_type` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `image_urls` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

spas_info  = """ CREATE TABLE `Spa` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `place_category` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `description` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `addresses` text COLLATE utf8_unicode_ci,
  `how_to_use_offer` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `cancelletion_policy` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `things_to_remember` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `rating` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `rating_type` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `image_urls` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

theatre_info  = """ CREATE TABLE `Theatre` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `place_category` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `description` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `addresses` text COLLATE utf8_unicode_ci,
  `how_to_use_offer` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `cancelletion_policy` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `things_to_remember` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `rating` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `rating_type` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `image_urls` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

activity_info  = """ CREATE TABLE `Activity` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `place_category` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `description` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `addresses` text COLLATE utf8_unicode_ci,
  `how_to_use_offer` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `cancelletion_policy` text COLLATE utf8_unicode_ci,
  `things_to_remember` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `rating` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `rating_type` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `image_urls` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

salon_info = """ CREATE TABLE `Salon` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `place_category` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `description` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `addresses` text COLLATE utf8_unicode_ci,
  `how_to_use_offer` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `cancelletion_policy` text COLLATE utf8_unicode_ci,
  `things_to_remember` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `rating` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `rating_type` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `image_urls` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

health_info = """ CREATE TABLE `Health` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `place_category` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `description` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `addresses` text COLLATE utf8_unicode_ci,
  `how_to_use_offer` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `cancelletion_policy` text COLLATE utf8_unicode_ci,
  `things_to_remember` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `rating` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `rating_type` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `image_urls` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

hotel_info = """ CREATE TABLE `Hotel` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `place_category` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `description` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `addresses` text COLLATE utf8_unicode_ci,
  `how_to_use_offer` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `cancelletion_policy` text COLLATE utf8_unicode_ci,
  `things_to_remember` text COLLATE utf8_unicode_ci,
  `rating` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `rating_type` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `terms_conditions` text COLLATE utf8_unicode_ci,
  `image_urls` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

shopping_info = """ CREATE TABLE `Shopping` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `place_category` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `description` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `addresses` text COLLATE utf8_unicode_ci,
  `how_to_use_offer` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `cancelletion_policy` text COLLATE utf8_unicode_ci,
  `things_to_remember` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `rating` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `rating_type` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `terms_conditions` text COLLATE utf8_unicode_ci,
  `image_urls` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """


hobbie_info = """ CREATE TABLE `Hobbie` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `place_category` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `description` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `addresses` text COLLATE utf8_unicode_ci,
  `how_to_use_offer` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `cancelletion_policy` text COLLATE utf8_unicode_ci,
  `things_to_remember` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `rating` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `rating_type` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `image_urls` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

homeauto_info = """ CREATE TABLE `Homeauto` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `place_category` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `description` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `addresses` text COLLATE utf8_unicode_ci,
  `how_to_use_offer` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `cancelletion_policy` text COLLATE utf8_unicode_ci,
  `things_to_remember` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `rating` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `rating_type` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `image_urls` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

offer_info = """ CREATE TABLE `Offer` (
  `program_id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `price_original` text COLLATE utf8_unicode_ci,
  `price_discounted` text COLLATE utf8_unicode_ci,
  `price_notes` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `offer_title` text COLLATE utf8_unicode_ci,
  `offer_description` text COLLATE utf8_unicode_ci,
  `offer_inclusions` text COLLATE utf8_unicode_ci,
  `offer_validity` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  `offer_validity_details` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

con = MySQLdb.connect(db   =  'NEARBUY',
                      user              = 'root',
                      passwd            = '',
                      charset           = "utf8",
                      host              = 'localhost',
                      use_unicode       = True)
cur = con.cursor()

try:
    cur.execute(offer_info)
    cur.execute(eatout_info)
    cur.execute(spas_info)
    cur.execute(theatre_info)
    cur.execute(activity_info)
    cur.execute(salon_info)
    cur.execute(health_info)
    cur.execute(hotel_info)
    cur.execute(shopping_info)
    cur.execute(hobbie_info)
    cur.execute(homeauto_info)

except:
    pass

cur.close()

