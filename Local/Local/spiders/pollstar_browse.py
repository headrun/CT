from handle_utils import *
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.http import Request, FormRequest
import re
import MySQLdb

artist_query = 'insert into Artist(id, title, avg_gross, genres, avg_tickets_sold, image, website, aux_info, reference_url, created_at, modified_at) values("%s", "%s", %d, "%s", %d, "%s", "%s", "%s", "%s", now(), now()) on duplicate key update modified_at=now(), id="%s"'

artist1_query = 'insert into Artist(id, title, reference_url, created_at, modified_at) values("%s", "%s", "%s", now(), now()) on duplicate key update modified_at=now(), id="%s"'

chart_query = 'insert into Charts(program_id, program_type, chart_type, chart_date, rank, avg_gross, avg_tickets_sold, avg_ticket_price, cities, reference_url, created_at, modified_at) values("%s", "%s", "%s", "%s", %d, %d, %d, %f, %d, "%s", now(), now()) on duplicate key update modified_at=now(), program_id="%s", chart_type="%s"'
class PollstarsBrowse(BaseSpider):

    name = "pollstar_browse"
    start_urls = ['https://www.pollstar.com/']
    handle_httpstatus_list = [404, 403]

    def parse(self, response):
        sel = Selector(response)
        login_url = 'https://www.pollstar.com/login?returnUrl=%2F'
        headers = {
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.8,fil;q=0.6',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'cache-control': 'max-age=0',
            'authority': 'www.pollstar.com',
            'referer': 'https://www.pollstar.com/login?returnUrl=%2Flogin%3FreturnUrl%3D%252F'
            }
        form_data = {'Email':'rosymaria.ramirez@tivo.com',
                    'Password':'Musicgroup18'}
        handle_httpstatus_list = [404, 403]
        yield FormRequest(login_url, self.list_parse, method='POST', formdata=form_data)


    def __init__(self, *args, **kwargs):
        super(PollstarsBrowse, self).__init__(*args, **kwargs)
        self.con = MySQLdb.connect(db='POLLSTARDB',
                                user = 'root',
                                charset="utf8",
                                host='localhost',
                                use_unicode=True)
        self.cur = self.con.cursor()
        #self.con = MySQLdb.connect(host="10.28.218.81", user="veveo", passwd="veveo123", db="POLLSTARDB")
        #self.cur = self.con.cursor()
        self.pattern1 = re.compile('ddDates = (\[.*\])')
        self.pattern2 = re.compile('value:(.*)')
        self.pattern3 = re.compile('\((.*)\)')

    def __del__(self):
        self.con.close()
        self.cur.close()

    def list_parse(self, response):
        sel = Selector(response)
        import pdb;pdb.set_trace()
        if 'concert' in response.url:
            import pdb;pdb.set_trace()
            dates_data = extract_data(sel, '//script[@type="text/javascript"][contains(text(), "value")]/text()')
            data = self.pattern1.findall(dates_data.replace('\n' , '').replace('\t', '').replace('\r', ''))
            data = ''.join(data).split('},')
            for v_date in data:
                ddate = ''.join(self.pattern2.findall(v_date)).replace("'", '').strip()
                if ddate:
                    link = "https://www.pollstar.com/concertpulsejson/?pageIndex=0&pageSize=100&concertPulseDateTime=%s"%ddate
                    date_info = datetime.datetime.strptime(ddate, '%m/%d/%Y').strftime('%Y-%m-%d')
                    yield Request(link, self.parse_next1, meta={'ddate':date_info, 'ref_url':response.url})
        elif 'new-tours' in response.url:
            ddates = extract_list_data(sel, '//select/option/@value')
            for ddate in ddates:
                if ddate:
                    url = "https://www.pollstar.com/newtoursjson/?week=%s&pageIndex=0&pageSize=100"%ddate
                    yield Request(url, self.parse_next2)


    def parse_next1(self, response):

        sel = Selector(response)
        json_data = json.loads(response.body)
        if json_data:
            for j_data in json_data:
                ddate = response.meta['ddate']
                ref_url = response.meta['ref_url']
                rank = j_data.get('Count', '')
                chart_id =j_data.get('ID' , '')
                avg_gross = j_data.get('AvgGross', '')
                avgtix_sold = j_data.get('AvgTixSold', '')
                avgtix_price = j_data.get('AvgTixPrice', '')
                cities = j_data.get('Cities', '')
                last_week = j_data.get('LastWeek', '')
                this_week = j_data.get('ThisWeek', '')
                agt_name = j_data.get('AgtName', '')
                aux_info = {}
                if last_week:
                    aux_info.update({'LastWeek':last_week})
                if this_week:
                    aux_info.update({'ThisWeek':this_week})
                if agt_name:
                    aux_info.update({'AgtName':agt_name})
                if cities != 0:
                    aux_info.update({'cities':cities})
                if avgtix_price:
                    aux_info.update({'AvgTicketPrice':avgtix_price})
                aux_info.update({'json_link':response.url})
                chart_type = "Top 20 Artists"
                artistdetails = j_data.get('ArtistDetail', '')
                for artist in artistdetails:
                    artist_name = artist.get('Name', '')
                    artist_id = artist.get('ID', '')
                    artist_url = artist.get('Url', '')
                    if artist_id == 0:
                        artist_id = md5(artist_name)
                        values1 = (artist_id, MySQLdb.escape_string(normalize(artist_name)), normalize(response.url), artist_id)
                        self.cur.execute(artist1_query%values1)
                        self.con.commit()
                    values = (str(artist_id), 'artist', normalize(chart_type), normalize(ddate), rank, avg_gross, avgtix_sold, avgtix_price, cities,ref_url, str(artist_id), normalize(chart_type))
                    self.cur.execute(chart_query % values)
                    self.con.commit()
                    if artist_url:
                        artist_url = "https://www.pollstar.com%s"%artist_url
                        yield Request(artist_url, self.parse_artist, meta={'id':artist_id, 'name':artist_name, 'avggross':avg_gross,'avgtcks_sold':avgtix_sold, 'genres':'', 'aux_info':aux_info})
                    if artist_id:
                        link = "https://www.pollstar.com/artisteventsjson/?pageIndex=0&pageSize=100&mode=rb&artistId=%s&newOnly=0&fromDate=&toDate="%artist_id
                        self.get_page("pollstar_music_terminal", link, artist_id)

    def parse_next2(self, response):
        json_data = json.loads(response.body)
        if json_data:
            for j_data in json_data:
                artist_id = j_data.get('ArtistId', '')
                artist_name = j_data.get('ArtistName', '')
                rbcount = j_data.get('RBCount', '')
                thcount = j_data.get('THCount', '')
                bocount = j_data.get('BOCount', '')
                avggross = j_data.get('AvgGross', '')
                avgtcks_sold = j_data.get('AvgTicketsSold', '')
                artist_genre = j_data.get('ArtistPrimaryGenre', '')
                display_order = j_data.get('DisplayOrder', '')
                artist_url = j_data.get('Url', '')
                aux_info ={}
                if rbcount != 0:
                    aux_info.update({'RBCount':rbcount})
                if thcount != 0:
                    aux_info.update({'THCount':thcount})
                if bocount != 0:
                    aux_info.update({'BOCOUNT':bocount})
                aux_info.update({'json_link':response.url})
                if artist_url:
                    artist_url = 'https://www.pollstar.com%s'%artist_url
                    yield Request(artist_url, self.parse_artist, meta={'id':artist_id, 'name':artist_name, 'avggross':avggross, 'avgtcks_sold':avgtcks_sold, 'genres':artist_genre, 'aux_info':aux_info})
                if artist_id:
                    link = "https://www.pollstar.com/artisteventsjson/?pageIndex=0&pageSize=100&mode=rb&artistId=%s&newOnly=0&fromDate=&toDate="%artist_id
                    self.get_page("pollstar_music_terminal", link, artist_id)
    def parse_artist(self, response):

        sel = Selector(response)
        artist_id = response.meta['id']
        name = response.meta['name']
        avggross = response.meta['avggross']
        avgtix_sold = response.meta['avgtcks_sold']
        genre = response.meta['genres']
        aux_info = response.meta['aux_info']
        if not genre:
            genres = extract_list_data(sel, '//div[@class="contact-card__block-title"][contains(text(), "Genre")]/following-sibling::div[@class="contact-card__text"]/text()')
            if genres:
                genre = genres[0]
        genre = genre.replace(' / ', '<>')
        artist_image = extract_data(sel, '//div[@class="artist-image-container"]//img/@src')
        if artist_image:
            artist_image = "https://www.pollstar.com%s"%artist_image
        img_txt = extract_data(sel, '//div[@class="artist-image-container"]/div[@class="photo-credit"]//text()')
        website = ''
        websites = extract_list_data(sel, '//div[@class="contact-card__block-title"][contains(text(), "Website")]/following-sibling::div[@class="contact-card__text"]/a/@href')
        if websites:
            website = websites[0]
        if img_txt and artist_image:
            aux_info.update({'image_text':img_txt})
        brackets_info = ''.join(self.pattern3.findall(name))
        if brackets_info:
            aux_info.update({'brackets_data':brackets_info})
        name =  self.pattern3.sub('', name).strip()
        values = (str(artist_id), MySQLdb.escape_string(normalize(name)), avggross, normalize(genre), avgtix_sold, normalize(artist_image), normalize(website), MySQLdb.escape_string(json.dumps(aux_info)), normalize(response.url), str(artist_id))
        self.cur.execute(artist_query % values)
        self.con.commit()
