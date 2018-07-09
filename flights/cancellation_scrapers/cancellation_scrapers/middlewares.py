# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.conf import settings
import logging

class ProxyMiddleware(object):
   def process_request(self, request, spider):
       request.meta['proxy'] = settings.get('HTTP_PROXY')
       #request.meta['proxy'] = settings.get('HTTPS_PROXY')
       #print "Proxy from middlewares", request.meta['proxy']
       logging.warning('Proxy from middlewares %s' % request.meta['proxy'])

from scrapy.downloadermiddlewares.retry import RetryMiddleware
import time
class CustomRetryMiddleware(RetryMiddleware):

    def process_response(self, request, response, spider):
        url = response.url
	
        if 'airasia.com/AgentHome' in response.url and not request.meta.get('content'):
            check_login_button = response.xpath('//p[@class="loginButton"]/a/@id').extract()
            retry_xpath = response.xpath('//a[@id="MyBookings"]/@href').extract()
            if not retry_xpath and not check_login_button:
		time.sleep(50)
                return self._retry(request, 'Retry for mybookings', spider) or response
        elif 'airasia.com/ChangeItinerary' in response.url:
            if response.status not in [200, 302]:
		time.sleep(10)
                return self._retry(request, 'meta', spider) or response
        elif 'airasia.com/FlightCancel' in response.url:
            check_status = response.xpath('//div[@id="cancelContent"]//text()').extract()
            if not check_status:
		time.sleep(10)
                return self._retry(request, 'meta', spider) or response
	elif 'airasia.com/s/customcontactsupport' in response.url:
	    time.sleep(10)
	    return self._retry(request, 'meta', spider) or response
        return response
