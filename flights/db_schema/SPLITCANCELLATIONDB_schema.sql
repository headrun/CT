-- MySQL dump 10.13  Distrib 5.5.59, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: SPLITCANCELLATIONDB
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
-- Table structure for table `indigosplit_cancellation_report`
--

DROP TABLE IF EXISTS `indigosplit_cancellation_report`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `indigosplit_cancellation_report` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `airline` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `pnr` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `new_pnr` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `pcc` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `flight_number` text COLLATE utf8_unicode_ci,
  `error_message` text COLLATE utf8_unicode_ci,
  `status` text COLLATE utf8_unicode_ci,
  `cancel_amount` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `pricing_details` text COLLATE utf8_unicode_ci,
  `request_input` text COLLATE utf8_unicode_ci,
  `aux_info` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sk`,`pnr`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `spicejet_cancellation_report`
--

DROP TABLE IF EXISTS `spicejet_cancellation_report`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `spicejet_cancellation_report` (
  `sk` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `airline` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `pnr` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `new_pnr` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `pcc` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `flight_number` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `error_message` text COLLATE utf8_unicode_ci,
  `status` text COLLATE utf8_unicode_ci,
  `cancel_amount` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `pricing_details` text COLLATE utf8_unicode_ci,
  `request_input` text COLLATE utf8_unicode_ci,
  `aux_info` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sk`,`pnr`)
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

-- Dump completed on 2018-04-09 15:52:44
