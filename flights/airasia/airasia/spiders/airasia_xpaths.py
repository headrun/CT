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

pax_page_flight_id_path = '//div[@class="booking-details-table"]//table/thead/tr/th[contains(text(), "Depart")]/../../../tbody[1]/tr/td[1]//text()[1]'

pax_page_fr_air_path = '//div[@class="booking-details-table"]//table/thead/tr/th[contains(text(), "Depart")]/../../../tbody[1]/tr/td[2]//text()'

pax_page_to_air_path = '//div[@class="booking-details-table"]//table/thead/tr/th[contains(text(), "Depart")]/../../../tbody[1]/tr/td[3]//text()'

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

def get_compact_traceback(e=''):
    except_list = [asyncore.compact_traceback()]
    return "Error: %s Traceback: %s" % (str(e), str(except_list))

def create_logger_obj(source):
    cur_dt = str(datetime.datetime.now().date())
    LOGS_DIR = '/root/headrun/airasia/airasia/logs'
    log_file_name = "spider_%s_%s.log" % (source, cur_dt)
    log = initialize_logger(os.path.join(LOGS_DIR, log_file_name))
    return log

def initialize_logger(file_name, log_level_list=[]):
    logger = logging.getLogger()
    try:
        add_logger_handler(logger, file_name, log_level_list)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        e = sys.exc_info()[2]
        time_str = time.strftime("%Y%m%dT%H%M%S", time.localtime())
        exception_str = "%s: %s: Exception: %s" % (time_str, sys.argv, get_compact_traceback(e))
        #print exception_str

    return logger


def add_logger_handler(logger, file_name, log_level_list=[]):
    success_cnt, handler = 3, None

    for i in xrange(success_cnt):
        try:
            handler = logging.FileHandler(file_name)
            break
        except (KeyboardInterrupt, SystemExit):
            raise
        except: pass

    if not handler: return

    formatter = logging.Formatter('%(asctime)s.%(msecs)d: %(filename)s: %(lineno)d: %(funcName)s: %(levelname)s: %(message)s', "%Y%m%d%H%M%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    set_logger_log_level(logger, log_level_list)

    if handler.stream:
        set_close_on_exec(handler.stream)


agency_viewstate = '/wEPDwUBMGQYAQUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFisFVUNPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kUGF5bWVudElucHV0Vmlld1BheW1lbnRWaWV3JFJhZGlvQnV0dG9uX0FYSVNfQkFOSy1BWElTX0JBTksFVUNPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kUGF5bWVudElucHV0Vmlld1BheW1lbnRWaWV3JFJhZGlvQnV0dG9uX0FYSVNfQkFOSy1BWElTX0JBTksFV0NPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kUGF5bWVudElucHV0Vmlld1BheW1lbnRWaWV3JFJhZGlvQnV0dG9uX0lDSUNJX0JBTkstSUNJQ0lfQkFOSwVXQ09OVFJPTEdST1VQUEFZTUVOVEJPVFRPTSRQYXltZW50SW5wdXRWaWV3UGF5bWVudFZpZXckUmFkaW9CdXR0b25fSUNJQ0lfQkFOSy1JQ0lDSV9CQU5LBWlDT05UUk9MR1JPVVBQQVlNRU5UQk9UVE9NJFBheW1lbnRJbnB1dFZpZXdQYXltZW50VmlldyRSYWRpb0J1dHRvbl9TVEFURV9CQU5LX09GX0lORElBLVNUQVRFX0JBTktfT0ZfSU5ESUEFaUNPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kUGF5bWVudElucHV0Vmlld1BheW1lbnRWaWV3JFJhZGlvQnV0dG9uX1NUQVRFX0JBTktfT0ZfSU5ESUEtU1RBVEVfQkFOS19PRl9JTkRJQQVVQ09OVFJPTEdST1VQUEFZTUVOVEJPVFRPTSRQYXltZW50SW5wdXRWaWV3UGF5bWVudFZpZXckUmFkaW9CdXR0b25fSERGQ19CQU5LLUhERkNfQkFOSwVVQ09OVFJPTEdST1VQUEFZTUVOVEJPVFRPTSRQYXltZW50SW5wdXRWaWV3UGF5bWVudFZpZXckUmFkaW9CdXR0b25fSERGQ19CQU5LLUhERkNfQkFOSwVbQ09OVFJPTEdST1VQUEFZTUVOVEJPVFRPTSRQYXltZW50SW5wdXRWaWV3UGF5bWVudFZpZXckUmFkaW9CdXR0b25fRkVERVJBTF9CQU5LLUZFREVSQUxfQkFOSwVbQ09OVFJPTEdST1VQUEFZTUVOVEJPVFRPTSRQYXltZW50SW5wdXRWaWV3UGF5bWVudFZpZXckUmFkaW9CdXR0b25fRkVERVJBTF9CQU5LLUZFREVSQUxfQkFOSwVZQ09OVFJPTEdST1VQUEFZTUVOVEJPVFRPTSRQYXltZW50SW5wdXRWaWV3UGF5bWVudFZpZXckUmFkaW9CdXR0b25fSU5ESUFOX0JBTkstSU5ESUFOX0JBTksFWUNPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kUGF5bWVudElucHV0Vmlld1BheW1lbnRWaWV3JFJhZGlvQnV0dG9uX0lORElBTl9CQU5LLUlORElBTl9CQU5LBWtDT05UUk9MR1JPVVBQQVlNRU5UQk9UVE9NJFBheW1lbnRJbnB1dFZpZXdQYXltZW50VmlldyRSYWRpb0J1dHRvbl9JTkRJQU5fT1ZFUlNFQVNfQkFOSy1JTkRJQU5fT1ZFUlNFQVNfQkFOSwVrQ09OVFJPTEdST1VQUEFZTUVOVEJPVFRPTSRQYXltZW50SW5wdXRWaWV3UGF5bWVudFZpZXckUmFkaW9CdXR0b25fSU5ESUFOX09WRVJTRUFTX0JBTkstSU5ESUFOX09WRVJTRUFTX0JBTksFZUNPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kUGF5bWVudElucHV0Vmlld1BheW1lbnRWaWV3JFJhZGlvQnV0dG9uX1NPVVRIX0lORElBTl9CQU5LLVNPVVRIX0lORElBTl9CQU5LBWVDT05UUk9MR1JPVVBQQVlNRU5UQk9UVE9NJFBheW1lbnRJbnB1dFZpZXdQYXltZW50VmlldyRSYWRpb0J1dHRvbl9TT1VUSF9JTkRJQU5fQkFOSy1TT1VUSF9JTkRJQU5fQkFOSwVpQ09OVFJPTEdST1VQUEFZTUVOVEJPVFRPTSRQYXltZW50SW5wdXRWaWV3UGF5bWVudFZpZXckUmFkaW9CdXR0b25fQ0lUWV9VTklPTl9CQU5LX0xURC1DSVRZX1VOSU9OX0JBTktfTFREBWlDT05UUk9MR1JPVVBQQVlNRU5UQk9UVE9NJFBheW1lbnRJbnB1dFZpZXdQYXltZW50VmlldyRSYWRpb0J1dHRvbl9DSVRZX1VOSU9OX0JBTktfTFRELUNJVFlfVU5JT05fQkFOS19MVEQFU0NPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kUGF5bWVudElucHV0Vmlld1BheW1lbnRWaWV3JFJhZGlvQnV0dG9uX0NDQVZFTlVFLUNDQVZFTlVFBVNDT05UUk9MR1JPVVBQQVlNRU5UQk9UVE9NJFBheW1lbnRJbnB1dFZpZXdQYXltZW50VmlldyRSYWRpb0J1dHRvbl9DQ0FWRU5VRS1DQ0FWRU5VRQVfQ09OVFJPTEdST1VQUEFZTUVOVEJPVFRPTSRQYXltZW50SW5wdXRWaWV3UGF5bWVudFZpZXckUmFkaW9CdXR0b25SVVBBWVBheW1lbnRfQ0NBVkVOVUUtQ0NBVkVOVUUFX0NPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kUGF5bWVudElucHV0Vmlld1BheW1lbnRWaWV3JFJhZGlvQnV0dG9uUlVQQVlQYXltZW50X0NDQVZFTlVFLUNDQVZFTlVFBVhDT05UUk9MR1JPVVBQQVlNRU5UQk9UVE9NJENvbnRhY3RCaWxsaW5nSW5wdXRQYXltZW50VmlldyRSYWRpb0J1dHRvbl9BWElTX0JBTkstQVhJU19CQU5LBVhDT05UUk9MR1JPVVBQQVlNRU5UQk9UVE9NJENvbnRhY3RCaWxsaW5nSW5wdXRQYXltZW50VmlldyRSYWRpb0J1dHRvbl9BWElTX0JBTkstQVhJU19CQU5LBVpDT05UUk9MR1JPVVBQQVlNRU5UQk9UVE9NJENvbnRhY3RCaWxsaW5nSW5wdXRQYXltZW50VmlldyRSYWRpb0J1dHRvbl9JQ0lDSV9CQU5LLUlDSUNJX0JBTksFWkNPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kQ29udGFjdEJpbGxpbmdJbnB1dFBheW1lbnRWaWV3JFJhZGlvQnV0dG9uX0lDSUNJX0JBTkstSUNJQ0lfQkFOSwVsQ09OVFJPTEdST1VQUEFZTUVOVEJPVFRPTSRDb250YWN0QmlsbGluZ0lucHV0UGF5bWVudFZpZXckUmFkaW9CdXR0b25fU1RBVEVfQkFOS19PRl9JTkRJQS1TVEFURV9CQU5LX09GX0lORElBBWxDT05UUk9MR1JPVVBQQVlNRU5UQk9UVE9NJENvbnRhY3RCaWxsaW5nSW5wdXRQYXltZW50VmlldyRSYWRpb0J1dHRvbl9TVEFURV9CQU5LX09GX0lORElBLVNUQVRFX0JBTktfT0ZfSU5ESUEFWENPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kQ29udGFjdEJpbGxpbmdJbnB1dFBheW1lbnRWaWV3JFJhZGlvQnV0dG9uX0hERkNfQkFOSy1IREZDX0JBTksFWENPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kQ29udGFjdEJpbGxpbmdJbnB1dFBheW1lbnRWaWV3JFJhZGlvQnV0dG9uX0hERkNfQkFOSy1IREZDX0JBTksFXkNPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kQ29udGFjdEJpbGxpbmdJbnB1dFBheW1lbnRWaWV3JFJhZGlvQnV0dG9uX0ZFREVSQUxfQkFOSy1GRURFUkFMX0JBTksFXkNPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kQ29udGFjdEJpbGxpbmdJbnB1dFBheW1lbnRWaWV3JFJhZGlvQnV0dG9uX0ZFREVSQUxfQkFOSy1GRURFUkFMX0JBTksFXENPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kQ29udGFjdEJpbGxpbmdJbnB1dFBheW1lbnRWaWV3JFJhZGlvQnV0dG9uX0lORElBTl9CQU5LLUlORElBTl9CQU5LBVxDT05UUk9MR1JPVVBQQVlNRU5UQk9UVE9NJENvbnRhY3RCaWxsaW5nSW5wdXRQYXltZW50VmlldyRSYWRpb0J1dHRvbl9JTkRJQU5fQkFOSy1JTkRJQU5fQkFOSwVuQ09OVFJPTEdST1VQUEFZTUVOVEJPVFRPTSRDb250YWN0QmlsbGluZ0lucHV0UGF5bWVudFZpZXckUmFkaW9CdXR0b25fSU5ESUFOX09WRVJTRUFTX0JBTkstSU5ESUFOX09WRVJTRUFTX0JBTksFbkNPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kQ29udGFjdEJpbGxpbmdJbnB1dFBheW1lbnRWaWV3JFJhZGlvQnV0dG9uX0lORElBTl9PVkVSU0VBU19CQU5LLUlORElBTl9PVkVSU0VBU19CQU5LBWhDT05UUk9MR1JPVVBQQVlNRU5UQk9UVE9NJENvbnRhY3RCaWxsaW5nSW5wdXRQYXltZW50VmlldyRSYWRpb0J1dHRvbl9TT1VUSF9JTkRJQU5fQkFOSy1TT1VUSF9JTkRJQU5fQkFOSwVoQ09OVFJPTEdST1VQUEFZTUVOVEJPVFRPTSRDb250YWN0QmlsbGluZ0lucHV0UGF5bWVudFZpZXckUmFkaW9CdXR0b25fU09VVEhfSU5ESUFOX0JBTkstU09VVEhfSU5ESUFOX0JBTksFbENPTlRST0xHUk9VUFBBWU1FTlRCT1RUT00kQ29udGFjdEJpbGxpbmdJbnB1dFBheW1lbnRWaWV3JFJhZGlvQnV0dG9uX0NJVFlfVU5JT05fQkFOS19MVEQtQ0lUWV9VTklPTl9CQU5LX0xURAVsQ09OVFJPTEdST1VQUEFZTUVOVEJPVFRPTSRDb250YWN0QmlsbGluZ0lucHV0UGF5bWVudFZpZXckUmFkaW9CdXR0b25fQ0lUWV9VTklPTl9CQU5LX0xURC1DSVRZX1VOSU9OX0JBTktfTFREBVZDT05UUk9MR1JPVVBQQVlNRU5UQk9UVE9NJENvbnRhY3RCaWxsaW5nSW5wdXRQYXltZW50VmlldyRSYWRpb0J1dHRvbl9DQ0FWRU5VRS1DQ0FWRU5VRQVWQ09OVFJPTEdST1VQUEFZTUVOVEJPVFRPTSRDb250YWN0QmlsbGluZ0lucHV0UGF5bWVudFZpZXckUmFkaW9CdXR0b25fQ0NBVkVOVUUtQ0NBVkVOVUUFSENPTlRST0xHUk9VUFBBWU1FTlRGTElHSFRBTkRQUklDRSRGbGlnaHREaXNwbGF5UGF5bWVudFZpZXdDRyRTdXJ2ZXlCb3gkMIOd3OjEwoUYxoZoaSm6MWYWh23/'
