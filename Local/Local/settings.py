# -*- coding: utf-8 -*-

# Scrapy settings for Local project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'Local'

SPIDER_MODULES = ['Local.spiders']
NEWSPIDER_MODULE = 'Local.spiders'
ROBOTSTXT_OBEY = 1
LOG_LEVEL = 'INFO'
USER_AGENT = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/50.0.2661.102 Chrome/50.0.2661.102 Safari/537.36"
RETRY_HTTP_CODES = [503, 502]
DOWNLOADER_MIDDLEWARES = {
        'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'Local (+http://www.yourdomain.com)'
