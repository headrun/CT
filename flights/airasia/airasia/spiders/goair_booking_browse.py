from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector

class GoairBookBrowse(Spider):
    name = "goair_browse"
    start_urls = ["https://book.goair.in/"]
    handle_httpstatus_list = [404, 500]
    
    def __init__(self, *args, **kwargs):
        super(GoairBookBrowse, self).__init__(*args, **kwargs)

        self.passengers_dict = {"tripid":"", "outboundflightid":"G8 113", "outboundflightclass":"Economy", "inboundflightid":"G8 116", "inboundflightclass":"Economy", "pnr":"", "outboundmeal":["Jain Sandwich*1-Prasad K"], "inboundmeal":["Jain Sandwich*1-Prasad K"], "cleartripprice":"300000", "outboundbaggage":[], "inboundbaggage":[], "outbounddate":"2017-10-01", "inbounddate":"2017-10-05", "paxdetails":{"adults":"2", "child":"0", "infant":"0"}, "origin":"DEL", "destination":"BLR", "triptype":"Roundtrip", "countrycode":"IN", "countryisdcode":"91", "phonenumber":"", "emergencycontact":{"title":"MR", "firstname":"Charan", "lastname":"Malla", "countryisdcode":"91", "mobilenumber":"9876543210", "email":"bujji.charan@ymail.com", "landline":"2531479"}, "passengerdetails":[{"title":"MR", "gender":"1", "firstname":"Prasad", "lastname":"K", "dob":"1989-08-12"}, {"title":"MR", "gender":"1", "firstname":"Venu", "lastname":"E", "dob":"1992-08-12"}]}

    def parse(self, response):
        sel = Selector(response)
        origin_station = self.passengers_dict.get('origin','')
        destination_station = self.passengers_dict.get('destination','')
        trip_type = self.passengers_dict.get('triptype','')
        outbound_journey_date = self.passengers_dict.get('outbounddate','')
        inbound_journey_date = self.passengers_dict.get('inbounddate','')
        pax_details = self.passengers_dict.get('paxdetails','')
        adults = pax_details.get('adults','')
        children = pax_details.get('child','')
        infants = pax_details.get('infant','')
        no_of_passengers = int(adults) + int(children) + int(infants)
        if trip_type == 'Oneway':
            params = (
                    ('s', 'True'),
                    ('o1', origin_station),
                    ('d1', destination_station),
                    ('ADT', adults),
                    ('dd1', outbound_journey_date),
                    ('mon', 'true'),
                    )
        elif trip_type == 'Roundtrip':
            params = (
                    ('s', 'true'),
                    ('o1', origin_station),
                    ('d1', destination_station),
                    ('dd1', outbound_journey_date),
                    ('dd2', inbound_journey_date),
                    ('r', 'true'),
                    ('ADT', adults),
                    ('CHD', children),
                    ('inl', infants),
                    ('mon', 'true'),
                )
        next_url = 'https://book.goair.in/Flight/Select'
        yield FormRequest(next_url, callback=self.parse_select, formdata=params, method="GET", meta={'no_of_passengers':no_of_passengers})

    def parse_select(self, response):
        sel = Selector(response)
        no_of_passengers = int(response.meta['no_of_passengers'])
        trip_type = self.passengers_dict.get('triptype','')
        out_flight_number = '  '.join(self.passengers_dict.get('outboundflightid','').split(' ')) 
        in_flight_number = '  '.join(self.passengers_dict.get('inboundflightid','').split(' '))
        out_travel_class = self.passengers_dict.get('outboundflightclass','')
        in_travel_class = self.passengers_dict.get('inboundflightclass','')
        cleartrip_price = int(self.passengers_dict.get('cleartripprice',''))
        
        if trip_type == 'Oneway' and out_flight_number:
            if out_travel_class == 'Economy':
                try : price_diff = cleartrip_price - int(''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]//span[@class="js-extract-text"]/text()' % out_flight_number).extract()).replace(',','')) * no_of_passengers
                except: price_diff = ''
        
            elif out_travel_class == 'Business':
                try: price_diff = cleartrip_price - int(''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]//span[@class="js-extract-text"]/text()' % out_flight_number).extract()).replace(',','')) * no_of_passengers
                except : price_diff = ''

        if trip_type == 'Roundtrip' and in_flight_number:
            if out_travel_class == 'Economy' and in_travel_class =='Economy':
                try: price_diff = cleartrip_price - int(int(''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]//span[@class="js-extract-text"]/text()' % out_flight_number).extract()).replace(',','')) + int(''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]//span[@class="js-extract-text"]/text()' % in_flight_number).extract()).replace(',',''))) * no_of_passengers
                except: price_diff = ''
                
            elif out_travel_class == 'Business' and in_travel_class == 'Business':
                try:price_diff = cleartrip_price - int(int(''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]//span[@class="js-extract-text"]/text()' % out_flight_number).extract()).replace(',','')) + int(''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]//span[@class="js-extract-text"]/text()' % in_flight_number).extract()).replace(',',''))) * no_of_passengers
                except: price_diff = ''

            elif out_travel_class == 'Economy' and in_travel_class == 'Business':
                try: price_diff = cleartrip_price - int(int(''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]//span[@class="js-extract-text"]/text()' % out_flight_number).extract()).replace(',','')) + int(''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]//span[@class="js-extract-text"]/text()' % in_flight_number).extract()).replace(',',''))) * no_of_passengers
                except: price_diff = ''
                
            elif out_travel_class == 'Business' and in_travel_class == 'Economy':
                price_diff = cleartrip_price - int(int(''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]//span[@class="js-extract-text"]/text()' % out_flight_number).extract()).replace(',','')) + int(''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]//span[@class="js-extract-text"]/text()' % in_flight_number).extract()).replace(',',''))) * no_of_passengers
        
        
        if trip_type == 'Oneway' and out_travel_number:
            if out_travel_class == 'Economy' and price_diff>= -2000 and price_diff != '':
                price_key_value = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]/div[@class="fare-price-text  no-bundle"]/input/@value' % out_flight_number).extract())
                price_key_name = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]/div[@class="fare-price-text  no-bundle"]/input/@name' % out_flight_number).extract())
            
                additional_key = ''.join(sel.xpath('//div[@id="js_availability_container"]/form/input/@name').extract())
                additional_value = ''.join(sel.xpath('//div[@id="js_availability_container"]/form/input/@value').extract())
            
                data = [(additional_key, additional_value),
                        (price_key_name, price_key_value)]
                next_url = 'https://book.goair.in/Flight/Select'
                yield FormRequest(next_url, callback=self.parse_passenger, formdata=data, method="POST", meta={'no_of_passengers':no_of_passengers}, dont_filter=True)

            elif out_travel_class == 'Business' and price_diff >= -2000 and price_diff !='':
                price_key_value = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]/div[@class="fare-price-text  no-bundle"]/input/@value' % out_flight_number).extract())
                price_key_name = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]/div[@class="fare-price-text  no-bundle"]/input/@name' %  out_flight_number).extract())

                additional_key = ''.join(sel.xpath('//div[@id="js_availability_container"]/form/input/@name').extract())
                additional_value = ''.join(sel.xpath('//div[@id="js_availability_container"]/form/input/@value').extract())

                data = [(additional_key, additional_value),
                        (price_key_name, price_key_value)]
                next_url = 'https://book.goair.in/Flight/Select'
                yield FormRequest(next_url, callback=self.parse_passenger, formdata=data, method="POST", meta={'no_of_passengers':no_of_passengers}, dont_filter=True)


        elif trip_type =='Roundtrip' and in_flight_number:
            data = []
            additional_keys = sel.xpath('//form[@id="availabilityForm"]/input[@type="hidden"]/@name').extract()
            for key in additional_keys:
                data.append((key, ''))

            if out_travel_class == 'Economy' and in_travel_class == 'Economy' and price_diff >= -2000 and price_diff !='':
                out_price_key_value = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]/div[@class="fare-price-text  no-bundle"]/input/@value' % out_flight_number).extract())
                out_price_key_name = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]/div[@class="fare-price-text  no-bundle"]/input/@name' % out_flight_number).extract())

                in_price_key_value = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]/div[@class="fare-price-text  no-bundle"]/input/@value' %  in_flight_number).extract())

                in_price_key_name = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]/div[@class="fare-price-text  no-bundle"]/input/@name' % in_flight_number).extract())
                
                data.append((out_price_key_name, out_price_key_value))
                data.append((in_price_key_name, in_price_key_value))
                next_url = 'https://book.goair.in/Flight/Select'
                yield FormRequest(next_url, callback=self.parse_passenger, formdata=data, method="POST", meta={'no_of_passengers':no_of_passengers}, dont_filter=True)
            elif out_travel_class == 'Business' and in_travel_class == 'Business' and price_diff >= -2000 and price_diff != '':
                out_price_key_value = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]/div[@class="fare-price-text  no-bundle"]/input/@value' % out_flight_number).extract())
                out_price_key_name = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]/div[@class="fare-price-text  no-bundle"]/input/@name' % out_flight_number).extract())

                in_price_key_value = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]/div[@class="fare-price-text  no-bundle"]/input/@value' % in_flight_number).extract())
                in_price_key_name = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]/div[@class="fare-price-text  no-bundle"]/input/@name' % in_flight_number).extract())
                
                data.append((out_price_key_name, out_price_key_value))
                data.append((in_price_key_name, in_price_key_value))
                next_url = 'https://book.goair.in/Flight/Select'
                yield FormRequest(next_url, callback=self.parse_passenger, formdata=data, method="POST", meta={'no_of_passengers':no_of_passengers}, dont_filter=True)

            elif out_travel_class == 'Economy' and in_travel_class == 'Business' and price_diff >= -2000 and price_diff != '':
                out_price_key_value = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]/div[@class="fare-price-text  no-bundle"]/input/@value' % out_flight_number).extract())
                out_price_key_name = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]/div[@class="fare-price-text  no-bundle"]/input/@name' % out_flight_number).extract())
                in_price_key_value = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]/div[@class="fare-price-text  no-bundle"]/input/@value' % in_flight_number).extract())
                in_price_key_name = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]/div[@class="fare-price-text  no-bundle"]/input/@name' % in_flight_number).extract())

                data.append((out_price_key_name, out_price_key_value))
                data.append((in_price_key_name, in_price_key_value))
                next_url = 'https://book.goair.in/Flight/Select'
                yield FormRequest(next_url, callback=self.parse_passenger, formdata=data, method="POST", meta={'no_of_passengers':no_of_passengers}, dont_filter=True)

            elif out_travel_class == 'Business' and in_travel_class == 'Economy' and price_diff >= -2000 and price_diff != '':
                out_price_key_value = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]/div[@class="fare-price-text  no-bundle"]/input/@value' % out_flight_number).extract())
                out_price_key_name = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]/div[@class="fare-price-text  no-bundle"]/input/@name' % out_flight_number).extract())
                in_price_key_value = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]/div[@class="fare-price-text  no-bundle"]/input/@value' %  in_flight_number).extract())
                in_price_key_name = ''.join(sel.xpath('//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]/div[@class="fare-price-text  no-bundle"]/input/@name' %  in_flight_number).extract())

                data.append((out_price_key_name, out_price_key_value))
                data.append((in_price_key_name, in_price_key_value))
                next_url = 'https://book.goair.in/Flight/Select'
                yield FormRequest(next_url, callback=self.parse_passenger, formdata=data, method="POST", meta={'no_of_passengers':no_of_passengers}, dont_filter=True)

    def parse_passenger(self, response):
        sel = Selector(response)
        pax_count = response.meta['no_of_passengers']
        pass_count = len(self.passengers_dict.get('passengerdetails',''))
        if pax_count == pass_count:
            passenger_details = self.passengers_dict.get('passengerdetails','')
            contact_details = self.passengers_dict.get('emergencycontact','')
            pax_names = []
            data = []
            if passenger_details:
                for i,h in zip(passenger_details,range(len(passenger_details))):
                    data.append(('goAirPassengers[%d].Name.Title' % h , passenger_details[h].get('title')))
                    data.append(('goAirPassengers[%d].Name.First' % h, passenger_details[h].get('firstname')))
                    data.append(('goAirPassengers[%d].Name.Last' % h, passenger_details[h].get('lastname')))
                    data.append(('goAirPassengers[%d].Info.Gender' % h, passenger_details[h].get('gender')))
                    data.append(('goAirPassengers[%d].Info.Nationality' % h, 'IN'))
                    data.append(('goAirPassengers[%d].date_of_birth_day_%d' % (h,h), passenger_details[h].get('dob').split('-')[-1]))
                    data.append(('goAirPassengers[%d].date_of_birth_month_%d' % (h,h), passenger_details[h].get('dob').split('-')[1]))
                    data.append(('goAirPassengers[%d].date_of_birth_year_%d' % (h,h), passenger_details[h].get('dob').split('-')[0]))
                    data.append(('goAirPassengers[%d].TypeInfo.DateOfBirth', passenger_details[h].get('dob')))
                    pax_names.append(passenger_details[h].get('firstname') + ' ' + passenger_details[h].get('lastname'))
            
            if contact_details: 
                data.append(('goAirContact.TypeCode', 'P'))
                data.append(('goAirContact.CustomerNumber', ''))
                data.append(('goAirContact.Name.Title', contact_details.get('title')))
                data.append(('goAirContact.Name.First', contact_details.get('firstname')))
                data.append(('goAirContact.Name.Last', contact_details.get('lastname')))
                data.append(('goAirContact.MobileISDNumber', contact_details.get('countryisdcode')))
                data.append(('goAirContact.MobileNumber', contact_details.get('mobilenumber')))
                data.append(('goAirContact.EmailAddress', contact_details.get('email')))
                data.append(('goAirContact.EmergencyContactISDNumber', contact_details.get('countryisdcode')))
                data.append(('goAirContact.EmergencyContactAreaNumber', ''))
                data.append(('goAirContact.EmergencyNumber', contact_details.get('landline')))
                data.append(('goAirGstContact.HaveGst', 'false'))
                data.append(('goAirGstContact.CustomerNumber', ''))
                data.append(('goAirGstContact.CompanyName', ''))
                data.append(('goAirGstContact.EmailAddress', ''))
        
        next_url = 'https://book.goair.in/Passengers/Update'
        yield FormRequest(next_url, callback=self.parse_extras, formdata=data, method="POST", meta={'pax_names':pax_names})

    def parse_extras(self, response):
        sel = Selector(response)
        pax_names = response.meta['pax_names']
        trip_type = self.passengers_dict.get('triptype','')
        data = []
        out_travel_class = self.passengers_dict.get('outboundflightclass','')
        in_travel_class = self.passengers_dict.get('inboundflightclass','')
        out_journey = self.passengers_dict.get('origin','') + ' - ' + self.passengers_dict.get('destination','')
        in_journey = self.passengers_dict.get('desrination', '') + ' - ' + self.passengers_dict.get('origin','')
        out_meal_addons = self.passengers_dict.get('outboundmeal','')
        in_meal_addons = self.passengers_dict.get('inboundmeal','')
        out_baggage_addons = self.passengers_dict.get('outboundbaggage','')
        in_baggage_addons = self.passengers_dict.get('inboundbaggage','')
        if trip_type == 'Oneway' and out_travel_class == 'Economy' and out_meal_addons:
            for i in out_meal_addons:
                pass_name = i.split('-')[-1]
                count  = i.split('*')[-1].replace(pass_name,'').strip('-')
                item = i.split('*')[0]
                if pass_name in pax_names and item:
                    food_addon_value = ''.join(sel.xpath('//div[@class="mdl-cell mdl-cell--12-col mdl-cell--8-col-tablet mdl-cell--12-col-phone pax-name-container oneFlight-pos-adjustment"]/span[contains(text(),"%s")]/../..//div[@class="mdl-cell mdl-cell--12-col mdl-cell--8-col-tablet mdl-cell--12-col-phone"]//option[contains(text()," %s ")]/@value' % (pass_name,item)).extract()) + '|' + str(count)
                    data.append(('goAirSsr.SelectedJourneySsrs[0]', food_addon_value))
        
        if trip_type == 'Oneway' and out_baggage_addons:
            for i in out_baggage_addons:
                pass_name = i.split('-')[-1]
                count = i.split('*')[-1].replace(pass_name,'').strip('-')
                item = i.split('*')[0]
                if pass_name in pax_names and item:
                    baggage_addon_value = ''.join(sel.xpath('//div[@class="mdl-cell mdl-cell--12-col mdl-cell--8-col-tablet mdl-cell--12-col-phone pax-name-container oneFlight-pos-adjustment"]/span[contains(text(),"%s")]/../../div[@class="mdl-cell mdl-cell--12-col mdl-cell--8-col-tablet mdl-cell--12-col-phone"]//option[contains(text()," %s ")]/@value' % (pass_name,item)).extract()) + '|' + str(count)
                    data.append(('goAirSsr.SelectedJourneySsrs[0]', baggage_addon_value))
            
        if trip_type == 'Roundtrip' and out_travel_class == 'Economy' and out_meal_addons: #or in_meal_addons or out_baggage_addons or in_baggage_addons:
            for i in out_meal_addons:
                pass_name = i.split('-')[-1]
                count = i.split('*')[-1].replace(pass_name,'').strip('-')
                item = i.split('*')[0]
                if pass_name in pax_names and item:
                    food_addon_value = ''.join(sel.xpath('//span[contains(text(),"%s")]/../../div[@class="mdl-cell mdl-cell--12-col mdl-cell--8-col-tablet mdl-cell--12-col-phone"]//div[contains(text(),"%s")]/../../div[@class="mdl-grid mdl-grid--nesting ssr-forms"]//option[contains(text()," %s ")]/@value' % (pass_name,out_journey,item)).extract()) + '|' + str(count)
                    data.append(('goAirSsr.SelectedJourneySsrs[0]', food_addon_value))

        if trip_type == 'Roundtrip' and in_travel_class == 'Economy' and in_meal_addons:
            for i in in_meal_addons:
                pass_name = i.split('-')[-1]
                count = i.split('*')[-1].replace(pass_name,'').strip('-')
                item = i.split('*')[0]
                if pass_name in pax_names and item:

                    import pdb;pdb.set_trace()

        ins_aquation = ''.join(sel.xpath('//input[@id="remove_insurance_option"]/@name').extract())
        insu_qute_keys = sel.xpath('//div[@class="insurance-supplier-notes"]/../input/@name').extract()
        insu_qute_values = sel.xpath('//div[@class="insurance-supplier-notes"]/../input/@value').extract()
        insu_data = [(ins_aquation, 'False'),
                     ('goAirInsuranceQuote.Address.LineOne.Data', ''),
                     ('goAirInsuranceQuote.Address.PostalCode.Data', ''),
                     ('goAirInsuranceQuote.Address.LineTwo.Data', ''),
                     ('goAirInsuranceQuote.Address.City.Data', ''),
                     ('goAirInsuranceQuote.Address.Country.Data', ''),
                     ('goAirInsuranceQuote.Address.EmailAddress.Data', ''),
                    ]
        
        for i,j in zip(insu_qute_keys, insu_qute_values):
            insu_data.append((i,j))

        if data:
            for i in data:
                add_data = [i]
                next_url = 'https://book.goair.in/Ssrs/Apply'
                yield FormRequest(next_url, callback=self.parse_reload, formdata=add_data, method="POST", meta={'insu_data':insu_data})

        else:
            next_url = 'https://book.goair.in/Extras/Add'
            yield FormRequest(next_url, callback=self.parse_purchase, formdata=insu_data, method="POST")

    def parse_reload(self, response):
        sel = Selector(response)
        insu_data = response.meta['insu_data']
        next_url = 'https://book.goair.in/Extras/Add'
        yield FormRequest(next_url, callback=self.parse_purchase, formdata=insu_data, method="POST")
        
    def parse_purchase(self, response):
        sel = Selector(response)
        import pdb;pdb.set_trace()
