import MySQLdb

conn = MySQLdb.connect(host="localhost",user="root",passwd="")
cursor = conn.cursor()
try:
    dbname = cursor.execute('CREATE DATABASE TIMEOUT')
except:
    pass
cursor.close()

city_guide_info = """ CREATE TABLE `City_Guide` (
  `sk` varchar(170) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(150) COLLATE utf8_unicode_ci NOT NULL,
  `image_url` text COLLATE utf8_unicode_ci,
  `contact_numbers` varchar(250) COLLATE utf8_unicode_ci DEFAULT '',
  `price` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8_unicode_ci,
  `latitude` float DEFAULT '0',
  `longitude` float DEFAULT '0',
  `city` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `address` text COLLATE utf8_unicode_ci,
  `Website_name` text COLLATE utf8_unicode_ci,
  `no_of_likes` int(15) DEFAULT '0',
  `no_of_checkins` int(15) DEFAULT '0',
  `available_timings` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`sk`,`name`),
  KEY `name` (`sk`,`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

food_drinks_info  = """ CREATE TABLE `Food_Drinks` (
  `sk` varchar(170) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(150) COLLATE utf8_unicode_ci NOT NULL,
  `image_url` text COLLATE utf8_unicode_ci,
  `contact_numbers` varchar(250) COLLATE utf8_unicode_ci DEFAULT '',
  `price` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8_unicode_ci,
  `latitude` float DEFAULT '0',
  `longitude` float DEFAULT '0',
  `city` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `address` text COLLATE utf8_unicode_ci,
  `Website_name` text COLLATE utf8_unicode_ci,
  `no_of_likes` int(15) DEFAULT '0',
  `no_of_checkins` int(15) DEFAULT '0',
  `available_timings` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`sk`,`name`),
  KEY `name` (`sk`,`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

movie_theatres_info  = """ CREATE TABLE `Movie_Theatres` (
  `sk` varchar(170) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(150) COLLATE utf8_unicode_ci NOT NULL,
  `image_url` text COLLATE utf8_unicode_ci,
  `contact_numbers` varchar(250) COLLATE utf8_unicode_ci DEFAULT '',
  `price` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8_unicode_ci,
  `latitude` float DEFAULT '0',
  `longitude` float DEFAULT '0',
  `city` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `address` text COLLATE utf8_unicode_ci,
  `Website_name` text COLLATE utf8_unicode_ci,
  `no_of_likes` int(15) DEFAULT '0',
  `no_of_checkins` int(15) DEFAULT '0',
  `available_timings` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`sk`,`name`),
  KEY `name` (`sk`,`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

music_nightlife_info  = """ CREATE TABLE `Music_Nightlife` (
  `sk` varchar(170) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(150) COLLATE utf8_unicode_ci NOT NULL,
  `image_url` text COLLATE utf8_unicode_ci,
  `contact_numbers` varchar(250) COLLATE utf8_unicode_ci DEFAULT '',
  `price` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8_unicode_ci,
  `latitude` float DEFAULT '0',
  `longitude` float DEFAULT '0',
  `city` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `address` text COLLATE utf8_unicode_ci,
  `Website_name` text COLLATE utf8_unicode_ci,
  `no_of_likes` int(15) DEFAULT '0',
  `no_of_checkins` int(15) DEFAULT '0',
  `available_timings` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`sk`,`name`),
  KEY `name` (`sk`,`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

shopping_style_info  = """ CREATE TABLE `Shopping_Style` (
  `sk` varchar(170) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(150) COLLATE utf8_unicode_ci NOT NULL,
  `image_url` text COLLATE utf8_unicode_ci,
  `contact_numbers` varchar(250) COLLATE utf8_unicode_ci DEFAULT '',
  `price` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8_unicode_ci,
  `latitude` float DEFAULT '0',
  `longitude` float DEFAULT '0',
  `city` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `address` text COLLATE utf8_unicode_ci,
  `Website_name` text COLLATE utf8_unicode_ci,
  `no_of_likes` int(15) DEFAULT '0',
  `no_of_checkins` int(15) DEFAULT '0',
  `available_timings` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`sk`,`name`),
  KEY `name` (`sk`,`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """


theatre_arts_info = """ CREATE TABLE `Theatre_Arts` (
  `sk` varchar(170) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(150) COLLATE utf8_unicode_ci NOT NULL,
  `image_url` text COLLATE utf8_unicode_ci,
  `contact_numbers` varchar(250) COLLATE utf8_unicode_ci DEFAULT '',
  `price` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8_unicode_ci,
  `latitude` float DEFAULT '0',
  `longitude` float DEFAULT '0',
  `city` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `address` text COLLATE utf8_unicode_ci,
  `Website_name` text COLLATE utf8_unicode_ci,
  `no_of_likes` int(15) DEFAULT '0',
  `no_of_checkins` int(15) DEFAULT '0',
  `available_timings` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`sk`,`name`),
  KEY `name` (`sk`,`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci"""

things_to_do = """ CREATE TABLE `Things_To_Do` (
  `sk` varchar(170) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(150) COLLATE utf8_unicode_ci NOT NULL,
  `image_url` text COLLATE utf8_unicode_ci,
  `contact_numbers` varchar(250) COLLATE utf8_unicode_ci DEFAULT '',
  `price` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8_unicode_ci,
  `latitude` float DEFAULT '0',
  `longitude` float DEFAULT '0',
  `city` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `address` text COLLATE utf8_unicode_ci,
  `Website_name` text COLLATE utf8_unicode_ci,
  `no_of_likes` int(15) DEFAULT '0',
  `no_of_checkins` int(15) DEFAULT '0',
  `available_timings` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`sk`,`name`),
  KEY `name` (`sk`,`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """


con = MySQLdb.connect(db   =  'TIMEOUT',
                      user              = 'root',
                      passwd            = '',
                      charset           = "utf8",
                      host              = 'localhost',
                      use_unicode       = True)
cur = con.cursor()
try:
    cur.execute(city_guide_info)
    cur.execute(food_drinks_info)
    cur.execute(movie_theatres_info)
    cur.execute(music_nightlife_info)
    cur.execute(shopping_style_info)
    cur.execute(theatre_arts_info)
    cur.execute(things_to_do)

except:
    cur.close()
