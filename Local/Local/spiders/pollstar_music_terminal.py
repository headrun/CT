#from juicer.utils import *
from scrapy.spider import BaseSpider
import MySQLdb

concert_query = 'insert into Concerts(id, title, venue_id, location_id, date, datetime, has_tickets, aux_info, reference_url,created_at, modified_at) values("%s", "%s", "%s", "%s", "%s", "%s", %d, "%s", "%s", now(), now()) on duplicate key update id="%s", venue_id="%s", location_id="%s", datetime="%s"'

conartist_query = 'insert into concert_artists(concert_id, artist_id, created_at, modified_at) values("%s", "%s", now(), now()) on duplicate key update modified_at=now()'

venue_query = 'insert into Venue(id, location_id, venue, capacity, website, image, latitude, longitude, aux_info, reference_url, created_at,modified_at) values("%s","%s", "%s", %d, "%s", "%s", %f, %f, "%s", "%s", now(), now()) on duplicate key update id="%s", location_id="%s"'

venue1_query = 'insert into Venue(id, location_id, venue, capacity, website, image, latitude, longitude, reference_url,created_at,modified_at) values("%s", "%s", "%s", %d, "%s", "%s", %f, %f, "%s", now(), now()) on duplicate key update id="%s", location_id="%s"'

location_query = 'insert into Location(id, location, image, reference_url, created_at, modified_at) values("%s", "%s", "%s", "%s", now(), now()) on duplicate key update id="%s"'

ticket_query = 'insert into Ticket(id, program_id, provider, description, logo, ticket_url, created_at, modified_at) values("%s", "%s", "%s", "%s", "%s", "%s", now(), now()) on duplicate key update id="%s" ,program_id="%s"'



class PollstarTerminal(BaseSpider):

    name = "pollstar_music_terminal"

    def __init__(self, *args, **kwargs):
        super(PollstarTerminal, self).__init__(*args, **kwargs)
        self.con, self.cur = get_mysql_connection("localhost","POLLSTARDB",'')
        #self.con = MySQLdb.connect(host="10.28.218.81", user="veveo", passwd="veveo123", db="POLLSTARDB")
        #self.cur = self.con.cursor()
        self.pattern1 = re.compile('q=(.*?)&')
        self.pattern2 = re.compile('\((.*)\)')

    def __del__(self):
        self.con.close()
        self.cur.close()

    def parse(self, response):
        try:
            json_data = json.loads(response.body)
        except:
            json_data = '' 
        if json_data:
            artist_id = response.meta['sk']
            print artist_id
            for j_data in json_data:
                aux_info = {}
                event_id = j_data.get('EventId', '')
                event_name = j_data.get('EventName', '')
                venue_url = j_data.get('VenueUrl', '')
                venue_id = venue_url.split('-')[-1]
                venue_name = j_data.get('VenueName', '')
                playdate = datetime.datetime.strptime(j_data.get('PlayDate', '').split()[-1], "%m/%d/%Y")
                play_date = playdate.strftime("%Y-%m-%d")
                play_datetime = playdate.strftime("%Y-%m-%d %H:%M:%S")
                city_url = j_data.get('CityUrl', '')
                location_id = city_url.split('-')[-1]
                location = j_data.get('Location', '')
                if venue_url:
                    venue_url = "https://www.pollstar.com%s"%venue_url
                    yield Request(venue_url, self.parse_venue, meta={'venue_id':venue_id, 'venue_name':venue_name, 'location_id':location_id}, dont_filter=True)
                if city_url and location_id != '0':
                    city_url = "https://www.pollstar.com%s"%city_url
                    yield Request(city_url, self.parse_city, meta={'location':location, 'location_id':location_id})
                url = j_data.get('Url', '')
                if url:
                    url = "https://www.pollstar.com%s"%url
                is_haveevent = j_data.get('isCurrentCustomerHaveEvent', '')
                has_tickets = j_data.get('HasTickets', '')
                if has_tickets:
                    tickets = 1
                else:
                    tickets = 0
                hours_old = j_data.get('HoursOld', '')
                support = j_data.get('Support', '')
                if hours_old:
                    aux_info.update({'hours_old':hours_old})
                if support:
                    aux_info.update({'support':support})
                aux_info.update({'json_link':response.url})
                brackets_info = ''.join(self.pattern2.findall(event_name))
                if brackets_info:
                    aux_info.update({'brackets_data':brackets_info})
                event_name = self.pattern2.sub('', event_name)
        
                values = (str(event_id), MySQLdb.escape_string(normalize(event_name)), str(venue_id), str(location_id), normalize(play_date), normalize(play_datetime), tickets, MySQLdb.escape_string(str(json.dumps(aux_info))), normalize(url), str(event_id), str(venue_id), str(location_id), normalize(play_datetime)) 
                self.cur.execute(concert_query % values)
                ca_values = (str(event_id), str(artist_id))
                self.cur.execute(conartist_query % ca_values)
                self.con.commit()
                if event_id and has_tickets:
                    if 'festival'  in url:
                        ticket_url = "https://www.pollstar.com/ticketsforfestivalinstancejson/?festivalInstanceId=%s"%event_id
                    else:
                        ticket_url = "https://www.pollstar.com/ticketsforeventjson/?eventId=%s"%event_id
                    yield Request(ticket_url, self.parse_next, meta={'event_id':event_id}, dont_filter=True)

    def parse_next(self, response):
        
        try:
            json_data = json.loads(response.body)
        except:
            json_data = ''
        if json_data:
            event_id = response.meta['event_id']
            for j_data in json_data:
                ticket_id = j_data.get('Id', '')
                provider = j_data.get('Provider', '')
                logo = j_data.get('Logo', '')
                desc = j_data.get('Description', '')
                url = j_data.get('Url', '')
                values = (str(ticket_id), str(event_id), normalize(provider), MySQLdb.escape_string(str(normalize(desc))), normalize(logo), normalize(url), str(ticket_id), str(event_id))
                self.cur.execute(ticket_query % values)
                self.con.commit()

    def parse_venue(self, response):
        
        sel = Selector(response)
        id_ = response.meta['venue_id']
        name = response.meta['venue_name']
        location_id = response.meta['location_id']
        image = extract_data(sel, '//img[@id="venueImage"]/@src')
        if image:
            image = "https://www.pollstar.com%s"%image
        map_link = extract_data(sel, '//div[contains(text(), "Venue Location")]/following-sibling::iframe/@src')
        websites_nodes = get_nodes(sel, '//div[@class="contact-card__block-title"][contains(text(), "Websites")]/following-sibling::div[@class="contact-card__text"]')
        website = ''
        if websites_nodes:
            websites_nodes = websites_nodes[0]
            website = extract_data(websites_nodes, './a/text()', '<>')
        capacity = extract_data(sel, '//div[@class="contact-card__block-title"][contains(text(), "Capacity")]/following-sibling::div[@class="contact-card__text"][1]//text()')
        if capacity:
            capacity = int(capacity)
        else:
            capacity = 0
        latitude = 0.0
        longitude = 0.0
        if map_link:
            latitude, longitude = ''.join(self.pattern1.findall(map_link)).split(',')
        brackets_info = ''.join(self.pattern2.findall(name))
        if brackets_info:
            aux_info = {'brackets_data':brackets_info}
        else:
            aux_info = ''
        name = self.pattern2.sub('', name)

        if aux_info:
            values = (str(id_), str(location_id), MySQLdb.escape_string(normalize(name)), capacity, normalize(website), normalize(image), float(latitude), float(longitude), MySQLdb.escape_string(json.dumps(aux_info)), normalize(response.url), str(id_), str(location_id))
            self.cur.execute(venue_query % values)
        else:
            values = (str(id_), str(location_id), MySQLdb.escape_string(normalize(name)), capacity, normalize(website), normalize(image), float(latitude), float(longitude), normalize(response.url), str(id_), str(location_id))
            self.cur.execute(venue1_query % values)
        self.con.commit()


    def parse_city(self, response):

        sel = Selector(response)
        location = response.meta['location']
        location_id = response.meta['location_id']
        image = extract_data(sel, '//img[@id="artistImage"]/@src')
        if image:
            image = "https://www.pollstar.com%s"%image
        values = (str(location_id), normalize(location), normalize(image), normalize(response.url), str(location_id))
        self.cur.execute(location_query % values)
        self.con.commit()
