-- MySQL dump 10.13  Distrib 5.5.60, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: IP_SCRAPER
-- ------------------------------------------------------
-- Server version	5.5.60-0ubuntu0.14.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `IP_SCRAPER`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `IP_SCRAPER` /*!40100 DEFAULT CHARACTER SET latin1 */;

USE `IP_SCRAPER`;

--
-- Table structure for table `ip_crawl`
--

DROP TABLE IF EXISTS `ip_crawl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ip_crawl` (
  `sk` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `crawl_status` int(3) NOT NULL DEFAULT '0',
  `crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `content_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `meta_data` text COLLATE utf8_unicode_ci,
  `aux_info` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `ccid` (`sk`),
  KEY `sk` (`sk`),
  KEY `type` (`crawl_type`),
  KEY `type_time` (`crawl_type`,`modified_at`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ipmeta`
--

DROP TABLE IF EXISTS `ipmeta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ipmeta` (
  `ip` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `continent` text COLLATE utf8_unicode_ci,
  `country` text COLLATE utf8_unicode_ci,
  `capital` text COLLATE utf8_unicode_ci,
  `city_location` text COLLATE utf8_unicode_ci,
  `isp` text COLLATE utf8_unicode_ci,
  `is_csvrun` text COLLATE utf8_unicode_ci,
  `aux_info` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `ip` (`ip`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Current Database: `m_MMCTRP`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `m_MMCTRP` /*!40100 DEFAULT CHARACTER SET latin1 */;

USE `m_MMCTRP`;

--
-- Table structure for table `Booking`
--

DROP TABLE IF EXISTS `Booking`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
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
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Cleartrip`
--

DROP TABLE IF EXISTS `Cleartrip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Cleartrip` (
  `city` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `ctthotelname` text COLLATE utf8_unicode_ci NOT NULL,
  `ctthotelid` bigint(20) NOT NULL,
  `check_in` date NOT NULL,
  `dx` int(3) NOT NULL,
  `los` int(3) NOT NULL,
  `pax` int(2) NOT NULL,
  `cttroomtype` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `cttrate` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `b2cdiff` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `cttinclusions` text COLLATE utf8_unicode_ci,
  `cttapprate` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `mobilediff` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `ctt_b2c_splashed_price` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
  `ctt_app_splashed_price` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `cttb2ctaxes` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
  `ctt_apptaxes` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `child` int(3) NOT NULL DEFAULT '0',
  `cttcoupon_code` varchar(50) COLLATE utf8_unicode_ci DEFAULT '',
  `cttcoupon_description` varchar(30) COLLATE utf8_unicode_ci DEFAULT '',
  `cttcoupon_discount` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `rmtc` varchar(25) COLLATE utf8_unicode_ci DEFAULT '',
  `check_out` date NOT NULL,
  `ctsell_price` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
  `ctchmm_discount` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
  `cancellation_policy` text COLLATE utf8_unicode_ci,
  `unique_sk` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `aux_info` text COLLATE utf8_unicode_ci,
  `created_on` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  UNIQUE KEY `hotelid` (`city`,`ctthotelid`,`dx`,`los`,`pax`,`unique_sk`,`child`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Cleartrip_hotels`
--

DROP TABLE IF EXISTS `Cleartrip_hotels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Cleartrip_hotels` (
  `hotel_id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `city_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `hotel_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `created_on` datetime NOT NULL,
  UNIQUE KEY `hotelid` (`hotel_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Cleartriponetime`
--

DROP TABLE IF EXISTS `Cleartriponetime`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Cleartriponetime` (
  `city` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `ctthotelname` text COLLATE utf8_unicode_ci NOT NULL,
  `ctthotelid` bigint(20) NOT NULL,
  `check_in` date NOT NULL,
  `dx` int(3) NOT NULL,
  `los` int(3) NOT NULL,
  `pax` int(2) NOT NULL,
  `cttroomtype` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `cttrate` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `b2cdiff` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `cttinclusions` text COLLATE utf8_unicode_ci,
  `cttapprate` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `mobilediff` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `ctt_b2c_splashed_price` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
  `ctt_app_splashed_price` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `cttb2ctaxes` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
  `ctt_apptaxes` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `child` int(3) NOT NULL DEFAULT '0',
  `cttcoupon_code` varchar(50) COLLATE utf8_unicode_ci DEFAULT '',
  `cttcoupon_description` varchar(30) COLLATE utf8_unicode_ci DEFAULT '',
  `cttcoupon_discount` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `rmtc` varchar(25) COLLATE utf8_unicode_ci DEFAULT '',
  `check_out` date NOT NULL,
  `created_on` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  UNIQUE KEY `hotelid` (`city`,`ctthotelid`,`dx`,`los`,`pax`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Goibibotrip`
--

DROP TABLE IF EXISTS `Goibibotrip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Goibibotrip` (
  `city` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `gbthotelname` text COLLATE utf8_unicode_ci,
  `gbthotelid` bigint(20) NOT NULL,
  `check_in` date NOT NULL,
  `dx` int(3) NOT NULL,
  `los` int(3) NOT NULL,
  `pax` int(2) NOT NULL DEFAULT '0',
  `gbtroomtype` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `gbtrate` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `b2cdiff` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `gbtinclusions` text COLLATE utf8_unicode_ci,
  `gbtapprate` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `mobilediff` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `gbt_b2c_splashed_price` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
  `gbt_app_splashed_price` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
  `gbtb2ctaxes` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
  `gbt_apptaxes` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `child` int(3) NOT NULL DEFAULT '0',
  `gbtcoupon_code` varchar(40) COLLATE utf8_unicode_ci DEFAULT NULL,
  `gbtcoupon_description` text COLLATE utf8_unicode_ci,
  `gbtcoupon_discount` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `rmtc` varchar(25) COLLATE utf8_unicode_ci DEFAULT '0',
  `check_out` date NOT NULL,
  `gbtgst_included` varchar(5) COLLATE utf8_unicode_ci DEFAULT NULL,
  `gbttotalamt_aftergst` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `cancellation_policy` text COLLATE utf8_unicode_ci,
  `ct_id` bigint(20) NOT NULL,
  `unique_sk` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `aux_info` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_on` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  UNIQUE KEY `gbhotelid` (`city`,`gbthotelid`,`dx`,`los`,`pax`,`unique_sk`,`child`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Goibibotrip_hotels`
--

DROP TABLE IF EXISTS `Goibibotrip_hotels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Goibibotrip_hotels` (
  `hotel_id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `city_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `hotel_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `created_on` datetime NOT NULL,
  UNIQUE KEY `hotelid` (`hotel_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Makemytrip`
--

DROP TABLE IF EXISTS `Makemytrip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Makemytrip` (
  `city` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `mmthotelname` text COLLATE utf8_unicode_ci,
  `mmthotelid` bigint(20) NOT NULL,
  `check_in` date NOT NULL,
  `dx` int(3) NOT NULL,
  `los` int(3) NOT NULL,
  `pax` int(2) NOT NULL DEFAULT '0',
  `mmtroomtype` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `mmtrate` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `b2cdiff` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `mmtinclusions` text COLLATE utf8_unicode_ci,
  `mmtapprate` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `mobilediff` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `mmt_b2c_splashed_price` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
  `mmt_app_splashed_price` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
  `mmtb2ctaxes` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '0',
  `mmt_apptaxes` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `child` int(3) NOT NULL DEFAULT '0',
  `mmtcoupon_code` varchar(40) COLLATE utf8_unicode_ci DEFAULT NULL,
  `mmtcoupon_description` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `mmtcoupon_discount` varchar(10) COLLATE utf8_unicode_ci DEFAULT '0',
  `rmtc` varchar(25) COLLATE utf8_unicode_ci DEFAULT '0',
  `check_out` date NOT NULL,
  `mmtgst_included` varchar(5) COLLATE utf8_unicode_ci DEFAULT NULL,
  `mmttotalamt_aftergst` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `cancellation_policy` text COLLATE utf8_unicode_ci,
  `ct_id` bigint(20) NOT NULL,
  `unique_sk` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `aux_info` text COLLATE utf8_unicode_ci,
  `created_on` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  UNIQUE KEY `hotelid` (`city`,`mmthotelid`,`dx`,`los`,`pax`,`unique_sk`,`child`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Makemytrip_hotels`
--

DROP TABLE IF EXISTS `Makemytrip_hotels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Makemytrip_hotels` (
  `hotel_id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `city_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `hotel_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `created_on` datetime NOT NULL,
  UNIQUE KEY `hotelid` (`hotel_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Tripadvisor`
--

DROP TABLE IF EXISTS `Tripadvisor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Tripadvisor` (
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
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Tripadvisor_hotels`
--

DROP TABLE IF EXISTS `Tripadvisor_hotels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Tripadvisor_hotels` (
  `hotel_id` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `city_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `hotel_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `created_on` datetime NOT NULL,
  UNIQUE KEY `hotelid` (`hotel_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Tripadvisorcityrank`
--

DROP TABLE IF EXISTS `Tripadvisorcityrank`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Tripadvisorcityrank` (
  `sk` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `city_rank` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `created_on` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  UNIQUE KEY `hotelid` (`sk`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Trivago`
--

DROP TABLE IF EXISTS `Trivago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Trivago` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `crawl_table_sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `city` text COLLATE utf8_unicode_ci,
  `cleartrip_hotel_id` text COLLATE utf8_unicode_ci,
  `hotel_name` text COLLATE utf8_unicode_ci,
  `trivago_hotel_id` text COLLATE utf8_unicode_ci,
  `check_in` date NOT NULL,
  `los` int(4) NOT NULL,
  `rank1` text COLLATE utf8_unicode_ci,
  `rank2` text COLLATE utf8_unicode_ci,
  `rank3` text COLLATE utf8_unicode_ci,
  `rank4` text COLLATE utf8_unicode_ci,
  `ct_price` text COLLATE utf8_unicode_ci,
  `ct_type` text COLLATE utf8_unicode_ci,
  `expedia_price` text COLLATE utf8_unicode_ci,
  `expedia_type` text COLLATE utf8_unicode_ci,
  `hotelsdot_com_price` text COLLATE utf8_unicode_ci,
  `hotelsdot_com_type` text COLLATE utf8_unicode_ci,
  `bookingdot_com_price` text COLLATE utf8_unicode_ci,
  `bookingdot_com_type` text COLLATE utf8_unicode_ci,
  `hotel_info_price` text COLLATE utf8_unicode_ci,
  `hotel_info_type` text COLLATE utf8_unicode_ci,
  `mmt_price` text COLLATE utf8_unicode_ci,
  `mmt_type` text COLLATE utf8_unicode_ci,
  `agoda_price` text COLLATE utf8_unicode_ci,
  `agoda_type` text COLLATE utf8_unicode_ci,
  `amoma_price` text COLLATE utf8_unicode_ci,
  `amoma_type` text COLLATE utf8_unicode_ci,
  `hrs_price` text COLLATE utf8_unicode_ci,
  `hrs_type` text COLLATE utf8_unicode_ci,
  `available_otas` text COLLATE utf8_unicode_ci,
  `price_difference` text COLLATE utf8_unicode_ci,
  `beaten_by_booking_com` text COLLATE utf8_unicode_ci,
  `beaten_by_price` text COLLATE utf8_unicode_ci,
  `aux_info` text COLLATE utf8_unicode_ci,
  `check_out` date NOT NULL,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_on` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_seen` datetime NOT NULL,
  UNIQUE KEY `hotelid` (`sk`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Current Database: `m_urlqueue_dev`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `m_urlqueue_dev` /*!40100 DEFAULT CHARACTER SET latin1 */;

USE `m_urlqueue_dev`;

--
-- Table structure for table `Booking_crawl`
--

DROP TABLE IF EXISTS `Booking_crawl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Booking_crawl` (
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
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Cleartrip_crawl`
--

DROP TABLE IF EXISTS `Cleartrip_crawl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Cleartrip_crawl` (
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
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Goibibotrip_crawl`
--

DROP TABLE IF EXISTS `Goibibotrip_crawl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Goibibotrip_crawl` (
  `sk` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `url` text COLLATE utf8_unicode_ci,
  `dx` int(3) NOT NULL,
  `los` int(3) NOT NULL,
  `pax` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
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
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Makemytrip_crawl`
--

DROP TABLE IF EXISTS `Makemytrip_crawl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Makemytrip_crawl` (
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
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Tripadvisor_crawl`
--

DROP TABLE IF EXISTS `Tripadvisor_crawl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Tripadvisor_crawl` (
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
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Trivago_crawl`
--

DROP TABLE IF EXISTS `Trivago_crawl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Trivago_crawl` (
  `sk` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `dx` int(3) NOT NULL,
  `los` int(3) NOT NULL,
  `city_name` text COLLATE utf8_unicode_ci,
  `city_id` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `latitude` varchar(40) COLLATE utf8_unicode_ci NOT NULL,
  `longitude` varchar(40) COLLATE utf8_unicode_ci NOT NULL,
  `crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `content_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `start_date` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
  `end_date` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
  `crawl_status` int(3) NOT NULL DEFAULT '0',
  `meta_data` text COLLATE utf8_unicode_ci,
  `reference_url` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `ccid` (`sk`),
  KEY `sk` (`sk`),
  KEY `type` (`crawl_type`),
  KEY `type_time` (`crawl_type`,`modified_at`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `kayak_crawl`
--

DROP TABLE IF EXISTS `kayak_crawl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `kayak_crawl` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `dx` int(4) NOT NULL DEFAULT '0',
  `crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `from_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `to_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `trip_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `start_date` datetime NOT NULL,
  `return_date` datetime NOT NULL,
  `crawl_status` int(3) NOT NULL DEFAULT '0',
  `meta_data` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sk`,`start_date`,`from_location`,`to_location`),
  KEY `sk` (`sk`),
  KEY `type` (`crawl_type`),
  KEY `type_time` (`crawl_type`,`modified_at`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `skyscanner_crawl`
--

DROP TABLE IF EXISTS `skyscanner_crawl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `skyscanner_crawl` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `dx` int(4) NOT NULL DEFAULT '0',
  `crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `from_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `to_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `trip_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `start_date` datetime NOT NULL,
  `return_date` datetime NOT NULL,
  `crawl_status` int(3) NOT NULL DEFAULT '0',
  `meta_data` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sk`,`start_date`,`from_location`,`to_location`),
  KEY `sk` (`sk`),
  KEY `type` (`crawl_type`),
  KEY `type_time` (`crawl_type`,`modified_at`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `skyscannerae_crawl`
--

DROP TABLE IF EXISTS `skyscannerae_crawl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `skyscannerae_crawl` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `dx` int(4) NOT NULL DEFAULT '0',
  `crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `from_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `to_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `trip_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `start_date` datetime NOT NULL,
  `return_date` datetime NOT NULL,
  `crawl_status` int(3) NOT NULL DEFAULT '0',
  `meta_data` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sk`,`start_date`,`from_location`,`to_location`),
  KEY `sk` (`sk`),
  KEY `type` (`crawl_type`),
  KEY `type_time` (`crawl_type`,`modified_at`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `skyscannerrt_crawl`
--

DROP TABLE IF EXISTS `skyscannerrt_crawl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `skyscannerrt_crawl` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `dx` int(4) NOT NULL DEFAULT '0',
  `crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `from_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `to_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `trip_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `start_date` datetime NOT NULL,
  `return_date` datetime NOT NULL,
  `crawl_status` int(3) NOT NULL DEFAULT '0',
  `meta_data` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sk`,`start_date`,`from_location`,`to_location`),
  KEY `sk` (`sk`),
  KEY `type` (`crawl_type`),
  KEY `type_time` (`crawl_type`,`modified_at`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `wego_crawl`
--

DROP TABLE IF EXISTS `wego_crawl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wego_crawl` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `dx` int(4) NOT NULL DEFAULT '0',
  `crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `from_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `to_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `trip_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `start_date` datetime NOT NULL,
  `return_date` datetime NOT NULL,
  `crawl_status` int(3) NOT NULL DEFAULT '0',
  `meta_data` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sk`,`start_date`,`from_location`,`to_location`),
  KEY `sk` (`sk`),
  KEY `type` (`crawl_type`),
  KEY `type_time` (`crawl_type`,`modified_at`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `wegoae_crawl`
--

DROP TABLE IF EXISTS `wegoae_crawl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wegoae_crawl` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `dx` int(4) NOT NULL DEFAULT '0',
  `crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `from_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `to_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `trip_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `start_date` datetime NOT NULL,
  `return_date` datetime NOT NULL,
  `crawl_status` int(3) NOT NULL DEFAULT '0',
  `meta_data` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sk`,`start_date`,`from_location`,`to_location`),
  KEY `sk` (`sk`),
  KEY `type` (`crawl_type`),
  KEY `type_time` (`crawl_type`,`modified_at`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `wegosa_crawl`
--

DROP TABLE IF EXISTS `wegosa_crawl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wegosa_crawl` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `dx` int(4) NOT NULL DEFAULT '0',
  `crawl_type` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `from_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `to_location` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `trip_type` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `start_date` datetime NOT NULL,
  `return_date` datetime NOT NULL,
  `crawl_status` int(3) NOT NULL DEFAULT '0',
  `meta_data` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sk`,`start_date`,`from_location`,`to_location`),
  KEY `sk` (`sk`),
  KEY `type` (`crawl_type`),
  KEY `type_time` (`crawl_type`,`modified_at`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2018-04-26 11:37:48
