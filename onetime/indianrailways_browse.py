import os
import re
import json
import csv
import datetime
import requests
import time
import scrapy
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.http.cookies import CookieJar

class IndianRailways(scrapy.Spider):
    name = "indianrailways_browse"
    start_urls = ["https://enquiry.indianrail.gov.in/mntes"]

    def parse(self, response):
	headers = {
    'Origin': 'https://enquiry.indianrail.gov.in',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Referer': 'https://enquiry.indianrail.gov.in/mntes/q?opt=MainMenu&subOpt=trainSchedule&excpType=',
    'Connection': 'keep-alive',
	}
	data = [
	  ('trainNo', '12626'),
	  ('trainStartDate', '19-Apr-2018'),
	]
	url = "https://enquiry.indianrail.gov.in/mntes/q?opt=TrainServiceSchedule&subOpt=show&trainNo=12626"
	yield FormRequest(url, callback=self.parse_details, formdata=data, headers=headers)

    def parse_details(self, response):	
	sel = Selector(response)
	nodes = sel.xpath('//table/tbody/tr')
	for node in nodes:
		print '<>'.join(node.xpath('./td//text()').extract())
	
