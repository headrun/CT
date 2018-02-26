import scrapy
from scrapy.selector import Selector
from scrapy_splash import SplashRequest

class RehlatSpider(scrapy.Spider):
    name = "rehlat_browse"
    start_urls = ["https://www.rehlat.com/en/cheap-flights/airfare/delhi-to-mumbai/del-bom/oneway/"]
	
    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse,
                endpoint='render.html',
                args={'wait': 5},
            )

    def parse(self, response):
	sel = Selector(response)
	import pdb;pdb.set_trace()
