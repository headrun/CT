login_data_list = [
                ('__EVENTTARGET', 'ControlGroupLoginAgentView$AgentLoginView$LinkButtonLogIn'),
                ('__EVENTARGUMENT', ''),
                ('pageToken', ''),
                ('ControlGroupLoginAgentView$AgentLoginView$HFTimeZone', '330'),
                ]

view_state_path = '//input[@id="viewState"]/@value'

view_generator_path = '//input[@id="__VIEWSTATEGENERATOR"]/@value'

search_data_list = { 
                '__EVENTTARGET':'ControlGroupBookingListView$BookingListSearchInputView$LinkButtonFindBooking',
                '__EVENTARGUMENT':'',
                'pageToken':'',
                'ControlGroupBookingListView$BookingListSearchInputView$Search':'ForAgency',
                'ControlGroupBookingListView$BookingListSearchInputView$DropDownListTypeOfSearch':'1',
                }

table_nodes_path = '//table[@id="currentTravelTable"]//tbody//tr'

table_row_id_path = './/td[@class="smaller"]/a[contains(text(), "Modify")]/@id'

table_row_href_path = './/td[@class="smaller"]/a[contains(text(), "Modify")]/@href'

flight_date_path = './/td[1]//text()'

flight_origin_path = './/td[2]//text()'

flight_dest_path = './/td[3]//text()'

flight_booking_id_path = './/td[4]//text()'

pax_name_path = './/td[5]//text()'


booking_headers = { 
                        'origin': 'https://booking2.airasia.com',
                        'accept-encoding': 'gzip, deflate, br',
                        'accept-language': 'en-US,en;q=0.8',
                        'pragma': 'no-cache',
                        'upgrade-insecure-requests': '1',
                        'content-type': 'application/x-www-form-urlencoded',
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                        'cache-control': 'no-cache',
                        'authority': 'booking2.airasia.com',
                        'referer': 'https://booking2.airasia.com/BookingList.aspx',
                        }

booking_data_list = {  
                        '__EVENTTARGET':'ControlGroupBookingListView$BookingListSearchInputView',
                        'pageToken':'',
                        'ControlGroupBookingListView$BookingListSearchInputView$Search':'ForAgency',
                        'ControlGroupBookingListView$BookingListSearchInputView$DropDownListTypeOfSearch':'1',
                    }

 

pax_page_booking_id_path = '//span[@id="OptionalHeaderContent_lblBookingNumber"]//text()'

pax_page_amount_path = '//span[@id="OptionalHeaderContent_lblTotalPaid"]//text()'

pax_page_depart_loc_path = '//div[@class="booking-details-table"]//table/thead/tr/th[contains(text(), "Depart")]/following-sibling::th/text()'

pax_page_flight_id_path = '//div[@class="booking-details-table"]//table/thead/tr/th[contains(text(), "Depart")]/../../../tbody/tr/td[1]//text()[1]'

pax_page_fr_air_path = '//div[@class="booking-details-table"]//table/thead/tr/th[contains(text(), "Depart")]/../../../tbody/tr/td[2]//text()'

pax_page_to_air_path = '//div[@class="booking-details-table"]//table/thead/tr/th[contains(text(), "Depart")]/../../../tbody/tr/td[3]//text()'

pax_page_guest_name_path = '//span[@class="guest-detail-name"]//text()'

pax_page_mo_no_path = '//p[contains(text(), "Mobile phone")]//text()'

pax_page_email_path = '//p[contains(text(), "Email :")]//text()'

pax_page_payment_path = '//div[@class="left paymentCustom2"]//text()'

import sys
import os
import re
import time
import asyncore
import MySQLdb
import datetime
import logging

def textify(nodes, sep=' '):
    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]

    def _t(x):
        if isinstance(x, (str, unicode)):
            return [x]

        if hasattr(x, 'xmlNode'):
            if not x.xmlNode.get_type() == 'element':
                return [x.extract()]
        else:
            if isinstance(x.root, (str, unicode)):
                return [x.root]

        return (n.extract() for n in x.select('.//text()'))

    nodes = chain(*(_t(node) for node in nodes))
    nodes = (node.strip() for node in nodes if node.strip())

    return sep.join(nodes)

def xcode(text, encoding='utf8', mode='strict'):
    return text.encode(encoding, mode) if isinstance(text, unicode) else text


def compact(text, level=0):
    if text is None: return ''

    if level == 0:
        text = text.replace("\n", " ")
        text = text.replace("\r", " ")

    compacted = re.sub("\s\s(?m)", " ", text)
    if compacted != text:
        compacted = compact(compacted, level+1)

    return compacted.strip()

def clean(text):
    if not text: return text

    value = text
    value = re.sub("&amp;", "&", value)
    value = re.sub("&lt;", "<", value)
    value = re.sub("&gt;", ">", value)
    value = re.sub("&quot;", '"', value)
    value = re.sub("&apos;", "'", value)

    return value

def normalize(text):
    return clean(compact(xcode(text)))


