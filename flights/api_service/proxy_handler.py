import random

def http_proxy_ip():
	port = 'zproxy.lum-superproxy.io:22225'
	http = '%s'%random.choice(list(open('/root/scrapers/flights/luminati_ips.list'))).strip()
	http_ip = http.replace(port, '').strip(':')
	http_url = 'http://%s@%s'%(http_ip, port)
        return http_url

def exclusive_proxy_ip():
        port = 'zproxy.lum-superproxy.io:22225'
        http = '%s'%random.choice(list(open('/root/scrapers/flights/api_service/exclusiv_luminati_ips.list'))).strip()
        http_ip = http.replace(port, '').strip(':')
        http_url = 'http://%s@%s'%(http_ip, port)
        return http_url
