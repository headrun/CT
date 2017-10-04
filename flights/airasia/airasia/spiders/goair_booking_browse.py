from scrapy.spider import Spider
from scrapy.http import FormRequest
from scrapy.selector import Selector
from goair_xpath import *

class GoairBookBrowse(Spider):
    name = "goair_browse"
    start_urls = ["https://www.goair.in/"]
    handle_httpstatus_list = [404, 500]

    def __init__(self, *args, **kwargs):
        super(GoairBookBrowse, self).__init__(*args, **kwargs)
        self.passengers_dict = kwargs.get('jsons',{})
        self.default_dob = '1987-09-08'

    '''def parse(self, response):
        sel = Selector(response)
        req_token_key = ''.join(sel.xpath('//form[@action="/Agent/Login"]/input/@name').extract())
        req_token_value = ''.join(sel.xpath('//form[@action="/Agent/Login"]/input/@value').extract())
        data = [
		    (req_token_key, req_token_value),
  		    ('starterAgentLogin.Username', 'cleartrip2'),
  		    ('starterAgentLogin.Password', 'Goair@456')
		    ]
	    next_url = 'https://book.goair.in/Agent/Login'
	    yield FormRequest(next_url, callback=self.login_parse, formdata=data, method='POST')
    
    def login_parse(self, response):
        sel = Selector(response)
	    import pdb;pdb.set_trace()'''

    def parse(self, response):
        if self.passengers_dict:
            try: book_dict = eval(self.passengers_dict)
            except: book_dict = {}
        origin_station = book_dict.get('origin', '')
        destination_station = book_dict.get('destination', '')
        trip_type = book_dict.get('triptype', '')
        outbound_journey_date = book_dict.get('outbounddate', '')
        inbound_journey_date = book_dict.get('inbounddate', '')
        pax_details = book_dict.get('paxdetails', '')
        adults = pax_details.get('adults', '')
        children = pax_details.get('child', '')
        infants = pax_details.get('infant', '')
        no_of_passengers = int(adults) + int(children) + int(infants)

        if trip_type == 'Oneway':
            params = (
                    ('s', 'True'),
                    ('o1', origin_station),
                    ('d1', destination_station),
                    ('ADT', adults),
                    ('CHD', children),
                    ('inl', infants),
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
        yield FormRequest(next_url, callback=self.parse_select, formdata=params, method="GET", meta={'no_of_passengers':no_of_passengers, 'infants':infants, 'book_dict':book_dict})

    def parse_select(self, response):
        sel = Selector(response)
        no_of_passengers = response.meta['no_of_passengers']
        book_dict = response.meta['book_dict']
        infants = response.meta['infants']
        trip_type = book_dict.get('triptype', '')
        out_flight_number = '  '.join(book_dict.get('outboundflightid', '').split(' '))
        in_flight_number = '  '.join(book_dict.get('inboundflightid', '').split(' '))
        out_travel_class = book_dict.get('outboundflightclass', '')
        in_travel_class = book_dict.get('inboundflightclass', '')
        flight_numbers = sel.xpath('//div[@class="mdl-typography--body-1 lower-head-text"]/text()').extract()

        if trip_type == 'Oneway' and out_flight_number in flight_numbers:
            additional_key = ''.join(sel.xpath(oneway_additional_key_xpath).extract())
            additional_value = ''.join(sel.xpath(oneway_additional_value_xpath).extract())
            data = [(additional_key, additional_value)]

            if out_travel_class == 'Economy':
                price_key_value = ''.join(sel.xpath(economy_price_key_value_xpath % out_flight_number).extract())
                price_key_name = ''.join(sel.xpath(economy_price_key_name_xpath % out_flight_number).extract())
                data.append((price_key_name, price_key_value))
                next_url = 'https://book.goair.in/Flight/Select'
                yield FormRequest(next_url, callback=self.parse_passenger, formdata=data, method="POST", meta={'no_of_passengers':no_of_passengers, 'infants':infants, 'book_dict':book_dict}, dont_filter=True)

            elif out_travel_class == 'Business':
                price_key_value = ''.join(sel.xpath(business_price_key_value_xpath % out_flight_number).extract())
                price_key_name = ''.join(sel.xpath(business_price_key_name_xpath %  out_flight_number).extract())
                data.append((price_key_name, price_key_value))
                next_url = 'https://book.goair.in/Flight/Select'
                yield FormRequest(next_url, callback=self.parse_passenger, formdata=data, method="POST", meta={'no_of_passengers':no_of_passengers, 'infants':infants, 'book_dict':book_dict}, dont_filter=True)


        elif trip_type == 'Roundtrip' and in_flight_number and out_flight_number in flight_numbers:
            data = []
            additional_keys = sel.xpath(roundtrip_additional_keys_xpath).extract()
            for key in additional_keys:
                data.append((key, ''))

            if out_travel_class == 'Economy' and in_travel_class == 'Economy':
                out_price_key_value = ''.join(sel.xpath(economy_price_key_value_xpath % out_flight_number).extract())
                out_price_key_name = ''.join(sel.xpath(economy_price_key_name_xpath % out_flight_number).extract())

                in_price_key_value = ''.join(sel.xpath(economy_price_key_value_xpath %  in_flight_number).extract())
                in_price_key_name = ''.join(sel.xpath(economy_price_key_name_xpath % in_flight_number).extract())

                data.append((out_price_key_name, out_price_key_value))
                data.append((in_price_key_name, in_price_key_value))
                next_url = 'https://book.goair.in/Flight/Select'
                yield FormRequest(next_url, callback=self.parse_passenger, formdata=data, method="POST", meta={'no_of_passengers':no_of_passengers, 'infants':infants, 'book_dict':book_dict}, dont_filter=True)

            elif out_travel_class == 'Business' and in_travel_class == 'Business':
                out_price_key_value = ''.join(sel.xpath(business_price_key_value_xpath % out_flight_number).extract())
                out_price_key_name = ''.join(sel.xpath(business_price_key_name_xpath % out_flight_number).extract())

                in_price_key_value = ''.join(sel.xpath(business_price_key_value_xpath % in_flight_number).extract())
                in_price_key_name = ''.join(sel.xpath(business_price_key_name_xpath % in_flight_number).extract())

                data.append((out_price_key_name, out_price_key_value))
                data.append((in_price_key_name, in_price_key_value))
                next_url = 'https://book.goair.in/Flight/Select'
                yield FormRequest(next_url, callback=self.parse_passenger, formdata=data, method="POST", meta={'no_of_passengers':no_of_passengers, 'infants':infants, 'book_dict':book_dict}, dont_filter=True)

            elif out_travel_class == 'Economy' and in_travel_class == 'Business':
                out_price_key_value = ''.join(sel.xpath(economy_price_key_value_xpath % out_flight_number).extract())
                out_price_key_name = ''.join(sel.xpath(economy_price_key_name_xpath % out_flight_number).extract())

                in_price_key_value = ''.join(sel.xpath(business_price_key_value_xpath % in_flight_number).extract())
                in_price_key_name = ''.join(sel.xpath(business_price_key_name_xpath % in_flight_number).extract())

                data.append((out_price_key_name, out_price_key_value))
                data.append((in_price_key_name, in_price_key_value))
                next_url = 'https://book.goair.in/Flight/Select'
                yield FormRequest(next_url, callback=self.parse_passenger, formdata=data, method="POST", meta={'no_of_passengers':no_of_passengers, 'infants':infants, 'book_dict':book_dict}, dont_filter=True)

            elif out_travel_class == 'Business' and in_travel_class == 'Economy':
                out_price_key_value = ''.join(sel.xpath(business_price_key_value_xpath % out_flight_number).extract())
                out_price_key_name = ''.join(sel.xpath(business_price_key_name_xpath % out_flight_number).extract())

                in_price_key_value = ''.join(sel.xpath(economy_price_key_value_xpath %  in_flight_number).extract())
                in_price_key_name = ''.join(sel.xpath(economy_price_key_name_xpath %  in_flight_number).extract())

                data.append((out_price_key_name, out_price_key_value))
                data.append((in_price_key_name, in_price_key_value))
                next_url = 'https://book.goair.in/Flight/Select'
                yield FormRequest(next_url, callback=self.parse_passenger, formdata=data, method="POST", meta={'no_of_passengers':no_of_passengers, 'infants':infants, 'book_dict':book_dict}, dont_filter=True)

        else:
            print "we're unable to fetch the flight details"

    def parse_passenger(self, response):
        pax_count = response.meta['no_of_passengers']
        book_dict = response.meta['book_dict']
        infants = int(response.meta['infants'])
        pass_count = len(book_dict.get('passengerdetails', ''))
        infant_list = ['Yes', 'yes', 'ok', 'OK', 'true', 'True', 'YES']
        if pax_count != pass_count:
            print "Please Enter the acccurate persons count"
        else:
            passenger_details = book_dict.get('passengerdetails', '')
            contact_details = book_dict.get('emergencycontact', '')
            infants_details = []
            pax_names = []
            data = []
            if passenger_details:
                for h, i in enumerate(passenger_details):
                    if i.get('gender', '') == 'Male': gender = '1'
                    else: gender = '2'
                    if i.get('isInfant') not in infant_list:
                        data.append(('goAirPassengers[%s].Name.Title' % h, i.get('title')))
                        data.append(('goAirPassengers[%s].Name.First' % h, i.get('firstname')))
                        data.append(('goAirPassengers[%s].Name.Last' % h, i.get('lastname')))
                        data.append(('goAirPassengers[%s].Info.Gender' % h, gender))
                        data.append(('goAirPassengers[%s].Info.Nationality' % h, 'IN'))
                        if i.get('dob', '') != '':
                            data.append(('goAirPassengers[%s].date_of_birth_day_%s' % (h, h), i.get('dob', '').split('-')[-1]))
                            data.append(('goAirPassengers[%s].date_of_birth_month_%s' % (h, h), i.get('dob', '').split('-')[1]))
                            data.append(('goAirPassengers[%s].date_of_birth_year_%s' % (h, h), i.get('dob', '').split('-')[0]))
                            data.append(('goAirPassengers[%s].TypeInfo.DateOfBirth' % h, i.get('dob', '')))

                        else:
                            data.append(('goAirPassengers[%s].date_of_birth_day_%s' % (h, h), self.default_dob.split('-')[-1]))
                            data.append(('goAirPassengers[%s].date_of_birth_month_%s' % (h, h), self.default_dob.split('-')[1]))
                            data.append(('goAirPassengers[%s].date_of_birth_year_%s' % (h, h), self.default_dob.split('-')[0]))

                        if h == 0:
                            contact_details.update({'title':i.get('title'), 'firstname':i.get('firstname'), 'lastname':i.get('lastname')})
                        pax_names.append(i.get('firstname') + ' ' + i.get('lastname'))

                    else:
                        infants_details.append(i)

            if infants_details and len(infants_details) == infants:
                for h, i in enumerate(infants_details):
                    if i.get('gender', '') == 'Male': gender = '1'
                    else: gender = '2'
                    data.append(('goAirPassengers.Infants[%s].Name.First' % h, i.get('firstname')))
                    data.append(('goAirPassengers.Infants[%s].Name.Last' % h, i.get('lastname')))
                    data.append(('goAirPassengers.Infants[%s].Gender' % h, gender))
                    data.append(('goAirPassengers.Infants[%s].Nationality' % h, 'IN'))
                    data.append(('goAirPassengers.Infants[%s].infant_date_of_birth_day_%s' % (h, h), i.get('dob').split('-')[-1]))
                    data.append(('goAirPassengers.Infants[%s].infant_date_of_birth_month_%s' % (h, h), i.get('dob').split('-')[1]))
                    data.append(('goAirPassengers.Infants[%s].infant_date_of_birth_year_%s' % (h, h), i.get('dob').split('-')[0]))
                    data.append(('goAirPassengers.Infants[%s].DateOfBirth' % h, i.get('dob')))
                    data.append(('goAirPassengers.Infants[%s].AttachedPassengerNumber' % h, '%s' % h))

            if contact_details:
                data.append(('goAirContact.TypeCode', 'P'))
                data.append(('goAirContact.CustomerNumber', ''))
                data.append(('goAirContact.ImFirstPassenger', 'on'))
                data.append(('goAirContact.Name.Title', contact_details.get('title')))
                data.append(('goAirContact.Name.First', contact_details.get('firstname')))
                data.append(('goAirContact.Name.Last', contact_details.get('lastname')))
                data.append(('goAirContact.MobileISDNumber', contact_details.get('countryisdcode')))
                data.append(('goAirContact.MobileNumber', contact_details.get('mobilenumber')))
                data.append(('goAirContact.EmailAddress', contact_details.get('email')))
                data.append(('goAirContact.EmergencyContactISDNumber', contact_details.get('countryisdcode')))
                data.append(('goAirContact.EmergencyContactAreaNumber', ''))
                data.append(('goAirContact.EmergencyNumber', book_dict.get('tripid')))
                data.append(('goAirGstContact.HaveGst', 'false'))
                data.append(('goAirGstContact.CustomerNumber', ''))
                data.append(('goAirGstContact.CompanyName', ''))
                data.append(('goAirGstContact.EmailAddress', ''))
        next_url = 'https://book.goair.in/Passengers/Update'
        yield FormRequest(next_url, callback=self.parse_extras, formdata=data, method="POST", meta={'pax_names':pax_names, 'book_dict':book_dict})

    def parse_extras(self, response):
        sel = Selector(response)
        book_dict = response.meta['book_dict']
        import pdb;pdb.set_trace()
        pax_names = response.meta['pax_names']
        trip_type = book_dict.get('triptype', '')
        error_text = ' '.join(sel.xpath(error_text_xpath).extract()).replace('\n', '').replace('  ', '')
        if not error_text:
            data = []
            out_travel_class = book_dict.get('outboundflightclass', '')
            in_travel_class = book_dict.get('inboundflightclass', '')
            out_journey = book_dict.get('origin', '') + ' - ' + book_dict.get('destination', '')
            in_journey = book_dict.get('desrination', '') + ' - ' + book_dict.get('origin', '')
            out_meal_addons = book_dict.get('outboundmeal', '')
            in_meal_addons = book_dict.get('inboundmeal', '')
            out_baggage_addons = book_dict.get('outboundbaggage', '')
            in_baggage_addons = book_dict.get('inboundbaggage', '')

            if trip_type == 'Oneway' and out_travel_class == 'Economy' and out_meal_addons:
                for i in out_meal_addons:
                    pass_name = i.split('-')[-1]
                    count = i.split('*')[-1].replace(pass_name, '').strip('-')
                    item = i.split('*')[0]
                    if pass_name in pax_names and item:
                        food_addon_value = ''.join(sel.xpath(oneway_addon_value_xpath % (pass_name, item)).extract()) + '|' + str(count)
                        data.append(('goAirSsr.SelectedJourneySsrs[0]', food_addon_value))

            if trip_type == 'Oneway' and out_baggage_addons:
                for i in out_baggage_addons:
                    pass_name = i.split('-')[-1]
                    count = i.split('*')[-1].replace(pass_name, '').strip('-')
                    item = i.split('*')[0]
                    if pass_name in pax_names and item:
                        baggage_addon_value = ''.join(sel.xpath(oneway_addon_value_xpath % (pass_name, item)).extract()) + '|' + str(count)
                        data.append(('goAirSsr.SelectedJourneySsrs[0]', baggage_addon_value))

            if trip_type == 'Roundtrip' and out_travel_class == 'Economy' and out_meal_addons:
                for i in out_meal_addons:
                    out_pass_name = i.split('-')[-1]
                    out_count = i.split('*')[-1].replace(out_pass_name, '').strip('-')
                    out_item = i.split('*')[0]
                    if out_pass_name in pax_names and out_item:
                        out_food_addon_value = ''.join(sel.xpath(rountrip_addon_value_xpath % (out_pass_name, out_journey, out_item)).extract()) + '|' + str(out_count)
                        data.append(('goAirSsr.SelectedJourneySsrs[0]', out_food_addon_value))

            if trip_type == 'Roundtrip' and in_travel_class == 'Economy' and in_meal_addons:
                for i in in_meal_addons:
                    in_pass_name = i.split('-')[-1]
                    in_count = i.split('*')[-1].replace(in_pass_name, '').strip('-')
                    in_item = i.split('*')[0]
                    if in_pass_name in pax_names and in_item:
                        in_food_addon_value = ''.join(sel.xpath(rountrip_addon_value_xpath % (in_pass_name, in_journey, in_item)).extract()) + '|' + str(in_count)
                        data.append(('goAirSsr.SelectedJourneySsrs[0]', in_food_addon_value))

            if trip_type == 'Rountrip' and out_baggage_addons or in_baggage_addons:
                for i in out_baggage_addons:
                    out_pass_name = i.split('-')[-1]
                    out_count = i.split('*')[-1].replace(out_pass_name, '').strip('-')
                    out_item = i.split('*')[0]
                    if out_pass_name in pax_names and out_item:
                        out_baggage_addon_value = ''.join(sel.xpath(rountrip_addon_value_xpath % (out_pass_name, out_journey, out_item)).extract()) + '|' + str(out_count)
                        data.append(('goAirSsr.SelectedJourneySsrs[0]', out_baggage_addon_value))

                for i in in_baggage_addons:
                    in_pass_name = i.split('-')[-1]
                    in_count = i.split('*')[-1].replace(in_pass_name, '').strip('-')
                    in_item = i.split('*')[0]
                    if in_pass_name in pax_names and in_item:
                        in_baggage_addon_value = ''.join(sel.xpath(rountrip_addon_value_xpath % (in_pass_name, in_journey, in_item)).extract()) + '|' + str(in_count)
                        data.append(('goAirSsr.SelectedJourneySsrs[0]', in_baggage_addon_value))

            ins_aquation = ''.join(sel.xpath(insu_aquation_xpath).extract())
            insu_qute_keys = sel.xpath(insu_qute_keys_xpath).extract()
            insu_qute_values = sel.xpath(insu_qute_values_xpath).extract()
            insu_data = [(ins_aquation, 'False'),
                     ('goAirInsuranceQuote.Address.LineOne.Data', ''),
                     ('goAirInsuranceQuote.Address.PostalCode.Data', ''),
                     ('goAirInsuranceQuote.Address.LineTwo.Data', ''),
                     ('goAirInsuranceQuote.Address.City.Data', ''),
                     ('goAirInsuranceQuote.Address.Country.Data', ''),
                     ('goAirInsuranceQuote.Address.EmailAddress.Data', ''),
                    ]

            for i, j in zip(insu_qute_keys, insu_qute_values):
                insu_data.append((i, j))

            if data:
                for i in data:
                    add_data = [i]
                    next_url = 'https://book.goair.in/Ssrs/Apply'
                    yield FormRequest(next_url, callback=self.parse_reload, formdata=add_data, method="POST", meta={'insu_data':insu_data})

            else:
                next_url = 'https://book.goair.in/Extras/Add'
                yield FormRequest(next_url, callback=self.parse_purchase, formdata=insu_data, method="POST", meta='book_dict')
        else:
            print "Please Check the Provided Passenger Details.", error_text

    def parse_reload(self, response):
        import pdb;pdb.set_trace()
        insu_data = response.meta['insu_data']
        next_url = 'https://book.goair.in/Extras/Add'
        yield FormRequest(next_url, callback=self.parse_purchase, formdata=insu_data, method="POST")

    def parse_purchase(self, response):
        sel = Selector(response)
        book_dict = response.meta['book_dict']
        final_price = int(''.join(sel.xpath(final_price_xpath).extract()).replace(' INR', '').replace(',', ''))
        cleartrip_price = book_dict.get('cleartripprice', '')
        import pdb;pdb.set_trace()
