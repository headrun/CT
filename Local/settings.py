# -*- coding: utf-8 -*-

# Scrapy settings for Local project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'Local'
BOT_VERSION = '2.0'

SPIDER_MODULES = ['Local.spiders']
NEWSPIDER_MODULE = 'Local.spiders'
ROBOTSTXT_OBEY = 1
LOG_LEVEL = 'INFO'
USER_AGENT = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/50.0.2661.102 Chrome/50.0.2661.102 Safari/537.36"

DOWNLOAD_TIMEOUT = 360
DOWNLOAD_DELAY = 0.5 
RANDOMIZE_DOWNLOAD_DELAY = True

HTTPCACHE_ENABLED = False

LOG_FILE = None
LOG_LEVEL = 'INFO'

SCRIPT_LOG_FILE = 'Local.log'
TELNETCONSOLE_ENABLED = False
WEBSERVICE_ENABLED = False

DEFAULT_CRAWLER_PRIORITY = 5

MIN_URLS_TO_GET = 10

CONCURRENT_SPIDERS = 200
RANDOM_SCHEDULING = True

NO_ITEMS_TO_PROCESS = 100
NO_URLS_TO_PROCESS = 10000
NO_DUMPSTORE_ITEMS_TO_PROCESS = 10000

COUNTER_PREFIX  = "services.intervod.stats"

RETRY_TIMES = 10
RETRY_HTTP_CODES = [500, 503, 504, 400, 403, 404, 408]

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}

EXTENSIONS = {
  'scrapy.extensions.telnet.TelnetConsole': None
}

PROXIES_LIST = [i.strip() for i in list(open('/root/Local/Local/proxy1.list'))]

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'Local (+http://www.yourdomain.com)'

