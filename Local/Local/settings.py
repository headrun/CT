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
USER_AGENT = "Mozilla/5.0 (Linux; Veveobot; + http://corporate.veveo.net/contact/) AppleWebKit/535.21 (KHTML, like Gecko) Chrome/19.0.1042.0"
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0

ROBOTSTXT_OBEY = 1
DOWNLOAD_TIMEOUT = 360
DOWNLOAD_DELAY = 0.25
RANDOMIZE_DOWNLOAD_DELAY = True


LOG_FILE = None
LOG_LEVEL = 'INFO'

SCRIPT_LOG_FILE = 'Local.log'

TELNETCONSOLE_ENABLED = False
WEBSERVICE_ENABLED = False

CONCURRENT_SPIDERS = 200


RANDOM_SCHEDULING = True

USER_AGENT_LIST = ["Mozilla/5.0 (Linux; Veveobot; + http://corporate.veveo.net/contact/) AppleWebKit/535.21 (KHTML, like Gecko) Chrome/19.0.1042.0"]

RETRY_HTTP_CODES = [503, 502]
DOWNLOADER_MIDDLEWARES = {
        'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'Local (+http://www.yourdomain.com)'
