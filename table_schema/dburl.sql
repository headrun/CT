-- MySQL dump 10.13  Distrib 5.5.59, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: urlqueue_dev
-- ------------------------------------------------------
-- Server version	5.5.59-0ubuntu0.14.04.1

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

-- Dump completed on 2018-04-17 12:05:41
