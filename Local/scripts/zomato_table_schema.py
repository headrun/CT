import MySQLdb

conn = MySQLdb.connect(host="localhost",user="root",passwd="")
cursor = conn.cursor()
try:
    dbname = cursor.execute('CREATE DATABASE ZOMATO')
except:
    cursor.close()

Restaraunt_info = """CREATE TABLE `Restaraunt` (
    `sk` varchar(230) COLLATE utf8_unicode_ci NOT NULL,
    `title` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
    `city` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
    `cusiness` mediumtext COLLATE utf8_unicode_ci NOT NULL,
    `restaraunt_type` mediumtext COLLATE utf8_unicode_ci NOT NULL,
    `contact_number` mediumtext COLLATE utf8_unicode_ci NOT NULL,
    `no_of_ratings` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL,
    `no_of_reviews` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL,
    `votes` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL,
    `latitude` float DEFAULT '0',
    `longitude` float DEFAULT '0',
    `discount_date` text COLLATE utf8_unicode_ci,
    `discount_text` text COLLATE utf8_unicode_ci,
    `address` text COLLATE utf8_unicode_ci,
    `opening_hours` text COLLATE utf8_unicode_ci,
    `highlights` text COLLATE utf8_unicode_ci,
    `category` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
    `price` varchar(200) COLLATE utf8_unicode_ci DEFAULT NULL,
    `reference_url` text COLLATE utf8_unicode_ci,
    `created_at` datetime NOT NULL,
    `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `last_seen` datetime NOT NULL,
    PRIMARY KEY (`sk`)
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci """

con = MySQLdb.connect(db   =  'ZOMATO',
                      user              = 'root',
                      passwd            = '',
                      charset           = "utf8",
                      host              = 'localhost',
                      use_unicode       = True)
cur = con.cursor()
try:
    cur.execute(Restaraunt_info)

except:
    cur.close()

