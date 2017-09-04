import MySQLdb

conn = MySQLdb.connect(host="localhost",user="root",passwd="")
cursor = conn.cursor()

try:
    dbname = cursor.execute('CREATE DATABASE EXPLARA')

except:
    cursor.close()

entertainment_info = """ CREATE TABLE `Entertainment` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` text COLLATE utf8_unicode_ci,
  `address` text COLLATE utf8_unicode_ci,
  `details` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `organizer` text COLLATE utf8_unicode_ci,
  `dates` text COLLATE utf8_unicode_ci,
  `timings` text COLLATE utf8_unicode_ci,
  `image_urls` text COLLATE utf8_unicode_ci,
  `price` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `webpage` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

alumni_campus_info = """ CREATE TABLE `Alumni` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` text COLLATE utf8_unicode_ci,
  `address` text COLLATE utf8_unicode_ci,
  `details` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `organizer` text COLLATE utf8_unicode_ci,
  `dates` text COLLATE utf8_unicode_ci,
  `timings` text COLLATE utf8_unicode_ci,
  `image_urls` text COLLATE utf8_unicode_ci,
  `price` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `webpage` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

adventure_outdoor_info = """ CREATE TABLE `Adventure` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` text COLLATE utf8_unicode_ci,
  `address` text COLLATE utf8_unicode_ci,
  `details` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `organizer` text COLLATE utf8_unicode_ci,
  `dates` text COLLATE utf8_unicode_ci,
  `timings` text COLLATE utf8_unicode_ci,
  `image_urls` text COLLATE utf8_unicode_ci,
  `price` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `webpage` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

biz_tech_info = """ CREATE TABLE `BizTech` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` text COLLATE utf8_unicode_ci,
  `address` text COLLATE utf8_unicode_ci,
  `details` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `organizer` text COLLATE utf8_unicode_ci,
  `dates` text COLLATE utf8_unicode_ci,
  `timings` text COLLATE utf8_unicode_ci,
  `image_urls` text COLLATE utf8_unicode_ci,
  `price` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `webpage` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

sports_fitness_info  = """ CREATE TABLE `Sports` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` text COLLATE utf8_unicode_ci,
  `address` text COLLATE utf8_unicode_ci,
  `details` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `organizer` text COLLATE utf8_unicode_ci,
  `dates` text COLLATE utf8_unicode_ci,
  `timings` text COLLATE utf8_unicode_ci,
  `image_urls` text COLLATE utf8_unicode_ci,
  `price` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `webpage` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

food_bevarages_info = """ CREATE TABLE `Food` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` text COLLATE utf8_unicode_ci,
  `address` text COLLATE utf8_unicode_ci,
  `details` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `organizer` text COLLATE utf8_unicode_ci,
  `dates` text COLLATE utf8_unicode_ci,
  `timings` text COLLATE utf8_unicode_ci,
  `image_urls` text COLLATE utf8_unicode_ci,
  `price` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `webpage` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

interests_info = """ CREATE TABLE `Interest` (
  `id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `name` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `city` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `location` text COLLATE utf8_unicode_ci,
  `address` text COLLATE utf8_unicode_ci,
  `details` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `organizer` text COLLATE utf8_unicode_ci,
  `dates` text COLLATE utf8_unicode_ci,
  `timings` text COLLATE utf8_unicode_ci,
  `image_urls` text COLLATE utf8_unicode_ci,
  `price` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `webpage` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

con = MySQLdb.connect(db   =  'EXPLARA',
                      user              = 'root',
                      passwd            = '',
                      charset           = "utf8",
                      host              = 'localhost',
                      use_unicode       = True)
cur = con.cursor()

try:
    cur.execute(entertainment_info)
    cur.execute(alumni_campus_info)
    cur.execute(adventure_outdoor_info)
    cur.execute(biz_tech_info)
    cur.execute(sports_fitness_info)
    cur.execute(food_bevarages_info)
    cur.execute(interests_info)

except:
    cur.close()

