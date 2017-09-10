import MySQLdb

conn = MySQLdb.connect(host="localhost",user="root",passwd="")
cursor = conn.cursor()
try:
    dbname = cursor.execute('CREATE DATABASE LITTLE')
except:
    pass
cursor.close()

thingstodo_info = """ CREATE TABLE `ThingsToDo` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `deal_sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `image_url` text COLLATE utf8_unicode_ci,
  `terms_conditions` text COLLATE utf8_unicode_ci,
  `contact_numbers` varchar(250) COLLATE utf8_unicode_ci DEFAULT '',
  `description` text COLLATE utf8_unicode_ci,
  `zipcode` int(6) DEFAULT '0',
  `latitude` float(6,3) DEFAULT '0.000',
  `longitude` float(6,3) DEFAULT '0.000',
  `state` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `city` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(100) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `address` text COLLATE utf8_unicode_ci,
  `no_of_ratings` int(11) DEFAULT '0',
  `no_of_reviews` int(11) DEFAULT '0',
  `item_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `price` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL,
  `offer` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL,
  `discount` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL,
  `available_weeks` text COLLATE utf8_unicode_ci,
  `available_timings` varchar(512) COLLATE utf8_unicode_ci DEFAULT NULL,
  `deal_terms_conditions` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`sk`,`deal_sk`),
  KEY `deal_sk` (`sk`,`deal_sk`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

food_drinks_info  = """ CREATE TABLE `Food_Drinks` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `deal_sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `image_url` text COLLATE utf8_unicode_ci,
  `terms_conditions` text COLLATE utf8_unicode_ci,
  `contact_numbers` varchar(250) COLLATE utf8_unicode_ci DEFAULT '',
  `description` text COLLATE utf8_unicode_ci,
  `zipcode` int(6) DEFAULT '0',
  `latitude` float(6,3) DEFAULT '0.000',
  `longitude` float(6,3) DEFAULT '0.000',
  `state` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `city` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(100) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `address` text COLLATE utf8_unicode_ci,
  `no_of_ratings` int(11) DEFAULT '0',
  `no_of_reviews` int(11) DEFAULT '0',
  `item_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `price` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL,
  `offer` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL,
  `discount` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL,
  `available_weeks` text COLLATE utf8_unicode_ci,
  `available_timings` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `delivery_status` text COLLATE utf8_unicode_ci,
  `deal_terms_conditions` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`sk`,`deal_sk`),
  KEY `deal_sk` (`sk`,`deal_sk`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci"""

spas_salons_info  = """ CREATE TABLE `Spas_Salons` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `deal_sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `image_url` text COLLATE utf8_unicode_ci,
  `terms_conditions` text COLLATE utf8_unicode_ci,
  `contact_numbers` varchar(250) COLLATE utf8_unicode_ci DEFAULT '',
  `description` text COLLATE utf8_unicode_ci,
  `zipcode` int(6) DEFAULT '0',
  `latitude` float(6,3) DEFAULT '0.000',
  `longitude` float(6,3) DEFAULT '0.000',
  `state` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `city` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `location` varchar(100) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `address` text COLLATE utf8_unicode_ci,
  `no_of_ratings` int(11) DEFAULT '0',
  `no_of_reviews` int(11) DEFAULT '0',
  `item_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `price` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL,
  `offer` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL,
  `discount` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL,
  `available_weeks` text COLLATE utf8_unicode_ci,
  `available_timings` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `deal_terms_conditions` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`sk`,`deal_sk`),
  KEY `deal_sk` (`sk`,`deal_sk`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci"""


con = MySQLdb.connect(db   =  'LITTLE',
                      user              = 'root',
                      passwd            = '',
                      charset           = "utf8",
                      host              = 'localhost',
                      use_unicode       = True)
cur = con.cursor()

cur.execute(thingstodo_info)
cur.execute(food_drinks_info)
cur.execute(spas_salons_info)


cur.close()
