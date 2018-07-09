-- MySQL dump 10.13  Distrib 5.5.59, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: TICKETBOOKINGDB
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
-- Table structure for table `airasia_booking_report`
--

DROP TABLE IF EXISTS `airasia_booking_report`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `airasia_booking_report` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `airline` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `auto_pnr` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `pnr` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `flight_number` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `from_location` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `to_location` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `ticket` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `triptype` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `cleartrip_price` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `airasia_price` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `status_message` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `tolerance_amount` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `oneway_date` text COLLATE utf8_unicode_ci,
  `return_date` text COLLATE utf8_unicode_ci,
  `error_message` text COLLATE utf8_unicode_ci,
  `paxdetails` text COLLATE utf8_unicode_ci,
  `price_details` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sk`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `goair_booking_report`
--

DROP TABLE IF EXISTS `goair_booking_report`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `goair_booking_report` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `airline` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `auto_pnr` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `pnr` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `flight_number` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `from_location` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `to_location` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `ticket` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `triptype` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `cleartrip_price` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `airline_price` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `status_message` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `tolerance_amount` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `oneway_date` text COLLATE utf8_unicode_ci,
  `return_date` text COLLATE utf8_unicode_ci,
  `error_message` text COLLATE utf8_unicode_ci,
  `paxdetails` text COLLATE utf8_unicode_ci,
  `price_details` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sk`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `indigo_booking_report`
--

DROP TABLE IF EXISTS `indigo_booking_report`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `indigo_booking_report` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `airline` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `auto_pnr` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `pnr` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `flight_number` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `from_location` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `to_location` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `ticket` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `triptype` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `cleartrip_price` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `indigo_price` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `status_message` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `tolerance_amount` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `oneway_date` datetime DEFAULT NULL,
  `return_date` datetime DEFAULT NULL,
  `error_message` text COLLATE utf8_unicode_ci,
  `paxdetails` text COLLATE utf8_unicode_ci,
  `price_details` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sk`),
  UNIQUE KEY `flight_number` (`flight_number`,`sk`)
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

-- Dump completed on 2018-04-09 15:51:35
