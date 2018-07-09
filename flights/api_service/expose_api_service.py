import os
import sys
import random
import MySQLdb
import traceback
import datetime
from flask import Flask, render_template, request, jsonify
import subprocess
from logging_file import *
import json
import logging
import commands

from proxy_handler import http_proxy_ip

logging.basicConfig(filename='example.log',level=logging.DEBUG)

app = Flask(__name__)
#spiders_directory = '/root/headrun/airasia/airasia/spiders'
spiders_directory = '/root/scrapers/flights/booking_scrapers/booking_scrapers/spiders'
IPS_LIST = '/root/scrapers/flights/static_ips.list'

spiders_directory_cancellation = '/root/scrapers/flights/cancellation_scrapers/cancellation_scrapers/spiders'
splitcancel_spider_dir = '/root/scrapers/flights/splitcancellation_scrapers/splitcancellation_scrapers/spiders'

cnl_select_query = 'select * from airasia_cancellation_report where tripid="%s" and sk="%s"'

HTTP_PROXY = 'http://zagent300.luminati.io:24000'
#HTTP_PROXY = "http://cleartrip:x1WoHub492@%s" % random.choice(list(open('/root/scrapers/flights/api_service/static_ips.list'))).strip()

@app.route("/")
def welcome():
    return "Hello World!"

@app.route('/airasia/cancel/status', methods=['GET', 'POST'])
@app.route('/airasia/cancel', methods=['GET', 'POST'])
def add_message():
    create_logger_obj('airasia_cancelltion')
    try:
        content = request.get_json(silent=True)
        logging.debug('%s %s' % (datetime.datetime.now(), content))
    except Exception as e:
        content = {}
        content.update({"ErrorMessage":e.message})
        logging.debug( e.message)
        return jsonify(content)
    try:
        content = eval(content)
    except:
        logging.debug(content)
        pass
    logging.debug(content)
    print content
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(spiders_directory_cancellation)
    os.system('pwd')
    print os.system('pwd')
    pnr = content.get('trip_ref', '')
    ori_details = content.get('details', [])
    pcc, ori_pnr = ['']*2
    pcc, ori_pnr = ['']*2
    original_pnr = ori_details[0].get('pnr', '')
    if ori_details:
        if len(ori_details) >= 3:
            result_dic, fin_dict = {}, {}
            result_dic.update({'pcc': '',
                           'flight_no': [],
                           'pnr': '',
                           'errorMessage': 'Multiple PNR not acceptable',
                           'errorCode': '019',
                           'tripId': pnr,
                           'pricingDetails': {},
                           'account':'',
                        })
            fin_dict.update({'result':[result_dic]})
            logging.debug(fin_dict)
            return jsonify(fin_dict)
        else:
            ori_deta = ori_details[0]
            pcc = ori_deta.get('pcc', '')
            ori_pnr = ori_deta.get('pnr', '')
	    
    else:
        result_dic, fin_dict = {}, {}
        result_dic.update({'pcc': '',
                           'flight_no': [],
                           'pnr': '',
                           'errorMessage': 'No details found for cancellation',
                           'errorCode': '020',
                           'tripId': pnr,
                           'pricingDetails': {},
                           'account':'',
                        })
        logging.debug(fin_dict)
        fin_dict.update({'result':[result_dic]})
        return jsonify(fin_dict)
    output_file = 'airasia_%s_%s.json'%(pnr, get_current_ts_with_ms())
    if 'status' not in request.url:
	HTTP_PROXY = ''#http_proxy_ip()
        run_cmd = '/usr/local/bin/scrapy crawl airasia_browse -a jsons="%s"  --set HTTP_PROXY="%s"' % (content, HTTP_PROXY)
	#run_cmd = '/usr/local/bin/scrapy crawl airasia_browse -a jsons="%s"  --set HTTP_PROXY="http://cleartrip:x1WoHub492@%s"' % (content, random.choice(list(open('/root/scrapers/flights/static_ips.list'))).strip())
	#run_cmd = '/usr/local/bin/scrapy crawl airasia_browse -a jsons="%s" --set HTTP_PROXY="http://zagent300.luminati.io:24002"'%(content)
	#run_cmd = '/usr/local/bin/scrapy crawl airasia_browse -a jsons="%s"'%(content)
    else:
	logging.debug("Status request")
    try:
        os.system(run_cmd)
    except:
        print traceback.format_exc()
    fin_data_dict, error_dict = {}, {}
    con, cursor = create_cursor('TICKETCANCELLATION')
    cursor.execute(cnl_select_query%(pnr, original_pnr))
    db_data = cursor.fetchall()
    error_code_dict = {'014': 'Oneway single pax cancellation',
                        '002': 'Oneway multiple pax full cancellation',
                        '003': 'Oneway Split PNR cancellation',
                        '004': 'Oneway trip partial pax cancellation',
                        '005': 'Round trip partial sector cancellation',
                        '006': 'Round trip partial sector cancellation',
                        '007': 'Round trip full sector cancellation',
                        '008': 'Round trip partial pax cancellation',
                        '009': 'Round trip partial pax cancellation',
                        '010': 'Past dated Booking',
                        '026': 'Split PNR cancellation',
                        '012': 'No details found with PNR',
                        '013': 'Itinerary not matched',
                        '001': 'Scraper unable to login AirAsia',
                        '015': 'More than one results found with PNR',
                        '016': 'It does not have modify option',
                        '017': 'AirAsia travel date mismatch',
                        '018': 'Pax name not matched with AirAsia',
			'019': 'Test request',
			'020': 'Scraper failed to navigate ChangeItinerary page',
			'022': 'Regex not matched with AirAsia',
			'023': 'Two Pax presented with same name',
			'024': 'Flight Id not matched',
			'025': 'Response not loaded',
                        }
    if db_data:
        data = db_data[0]
        err_msg, error_code = data[15], ''
	if not err_msg:
	    err_msg, error_code = data[2], ''
    else:
	error_data = ''
	err_msg, error_code, error_data = ['']*3
    if err_msg:
        for key, err in error_code_dict.iteritems():
            if err in err_msg:
                error_code = key
                break
            else: error_code = ''
    else: error_code = ''
    result_dic = {}
    #cursor.close()
    #con.close()
    if db_data:
        if data[3] == '1' or data[3] == 1:
            err_msg, error_code = ['']*2
        result_dic, fin_dict = {}, {}
	try: flight_id = eval(data[5])
	except: flight_id = []
        result_dic.update({'pcc': pcc,
                           'flight_no': flight_id,
                           'pnr': data[0],
                           'errorMessage': err_msg,
                           'errorCode': error_code,
                           'tripId': data[14],
                           'pricingDetails': data[10],
                           'account':'',
                        })
        fin_dict.update({'result':[result_dic]})
        logging.debug(fin_dict)
	cursor.close()
	con.close()
        return jsonify(fin_dict)
    elif error_data:
        result_dic, fin_dict = {}, {}
        result_dic.update({'pcc': pcc,
                           'flight_no': [],
                           'pnr': [],
                           'errorMessage': err_msg,
                           'errorCode': error_code,
                           'tripId': pnr,
                           'pricingDetails': {},
                           'account':'',
                        })
        fin_dict.update({'result':[result_dic]})
        logging.debug(fin_dict)
	cursor.close()
	con.close()
        return jsonify(fin_dict)
    else:
        result_dic, fin_dict = {}, {}
        result_dic.update({'pcc': pcc,
                          'flight_no': [],
                           'pnr': [],
                           'errorMessage': 'Unexpected error',
                           'errorCode': '121',
                           'tripId': pnr,
                           'pricingDetails': {},
                           'account':'',
                        })
        fin_dict.update({'result':[result_dic]})
        logging.debug(fin_dict)
        logging.debug('%s %s' % (datetime.datetime.now(), fin_dict))
	try:
		insert_query = "insert into airasia_cancellation_report(sk, tripid, airline, cancellation_status, cancellation_status_mesg, error, created_at, modified_at) values(%s,%s,%s,%s,%s,%s,now(), now()) on duplicate key update modified_at=now(), sk=%s, tripid=%s, cancellation_status=%s, cancellation_status_mesg=%s, error=%s"
		vals = (
				origina_pnr, pnr, 'Airasia', '0', 'Cancellation Failed', 'Unexpected error',
				origina_pnr, pnr, '0', 'Cancellation Failed', 'Unexpected error')

		cursor.execute(insert_query, vals)
	except Exception as e:
		logging.debug(e.message)
		pass
	cursor.close()
	con.close()
        return jsonify(fin_dict)

@app.route('/airasia/status', methods=['GET', 'POST'])
@app.route('/airasia/booking', methods=['GET', 'POST'])
def add_booking():
    book_query = 'select * from airasia_booking_report where sk = "%s"'
    print 'came'
    try:
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
	content = request.get_json(silent=True)
    try:
        content = eval(content)
    except Exception as e:
	print e
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    create_logger_obj('airasia_booking')
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(spiders_directory)
    os.system('pwd')
    pnr = content.get('trip_ref', '')
    output_file = 'airasia_%s_%s.json'%(pnr, get_current_ts_with_ms())
    #os.chdir('/usr/local/bin')
    if 'status' not in request.url:
	HTTP_PROXY = ''#http_proxy_ip()
        run_cmd = 'export PATH=$PATH:/usr/local/bin;/usr/local/bin/scrapy crawl airasia_booking_selenium -a jsons="%s"  --set HTTP_PROXY="%s"' % (content, HTTP_PROXY)
	#run_cmd = '/usr/local/bin/scrapy crawl airasiabooking_browse -a jsons="%s"  --set HTTP_PROXY="http://cleartrip:x1WoHub492@%s"' % (content, random.choice(list(open('/root/scrapers/flights/static_ips.list'))).strip())
	#run_cmd = '/usr/local/bin/scrapy crawl airasiabooking_browse -a jsons="%s" --set HTTP_PROXY="http://zagent300.luminati.io:24002"'%(content)
	#run_cmd = '/usr/local/bin/scrapy crawl airasiabooking_browse -a jsons="%s"'%(content)
        try:
            os.system(run_cmd)
        except:
            print traceback.format_exc()
    fin_data_dict, error_dict = {}, {}
    departdate = content.get('departure_date', '')
    auto_pnr_exists = False
    origin = content.get('origin_code', '')
    destination = content.get('destination_code', '')
    all_segments = content.get('all_segments', [])
    if all_segments:
	all_seg = all_segments[0]
	pcc = ''.join(all_seg.keys())
    else: pcc = ''
    con, cursor = create_cursor('TICKETBOOKINGDB')
    cursor.execute(book_query%pnr)
    db_data = cursor.fetchall()
    book_fin_dict = {}
    if db_data:
        data = db_data[0]
    else: data = ['']*20
    try: tax_detais = json.loads(data[17])
    except: tax_detais = {}
    rslt, logs_ = [], []
    error_code_dict = {'003':'Booking Faild As its MultiCity trip',
			'002':'Request not found',
			'001':'Booking Scraper unable to login AirAsia',
			'004':'It does not have modify option PNR',
			'005':'Itinerary exists',
			'006':'No flights find in selected class',
			'007':'Could not find flights',
			'008':'Fare increased by Airline',
			'009':'Payment Failed',
			'011':'Internal server error',
			'013':'Test Booking',
			'014': 'Response not loaded',
			'015': 'Failed to search flights',
			'016': 'Failed to load flights response',
			'017': 'Failed to fill the pax details',
			'018': 'Add on page not loaded',
			'019': 'Failed to load payment page',
			'020': 'Failed to load AgencyAccount',
			}
    err_msg, error_code = data[15], ''
    if err_msg:
       for key, err in error_code_dict.iteritems():
          if err_msg in err:
              error_code = key
	      break
	  else: error_code = ''
    else: error_code = ''
    print error_code
    if db_data:
	if tax_detais:
            for key, vals_ in tax_detais.iteritems():
	        dict_, log_, sec_dict, sec_log_ = {}, {}, {}, {}
	        seg = vals_.get('seg', '')
	        auto_pnr_exists = vals_.get('AUTO_PNR_EXISTS', False)
		pcc = vals_.get('pcc', '')
	        total_price = vals_.get('total', '')
	        del vals_['seg']
	        try: del vals_['AUTO_PNR_EXISTS']
	        except: pass
	        try: del vals_['pcc_']
	        except: pass
	        try: del vals_['pcc']
		except: pass
	        del vals_['total']
	        if '<>' in key:
		    key, second_key = key.split('<>')
		    seg_lst = seg.split('-')
		    try:
	 	        seg = '-'.join(seg_lst[0:2])
		        second_seg = '-'.join(seg_lst[2:])
		    except: second_seg = ''
	        else:
		    second_seg, second_key = ['']*2
	        key = key.strip()
	        dict_.update({"pcc": pcc, "amount":data[10], "flight_no": [key.strip()],
			"errorMessage": data[15], "errorCode": error_code, "departDate": departdate,
			"pnrCaptured":data[3], "pricingDetails": vals_, "segments":[seg],
			"trip_id": content.get('trip_ref', ''), 'TotalFare':total_price})
	        log_.update({"pcc": pcc, "flight_no": key.strip(), "actualPrice":data[10], 'custPaidPrice':data[9]})
	        rslt.append(dict_)
	        logs_.append(log_)
	        second_key = second_key.replace(' ', '')
	        if second_key:
		    second_key = second_key.strip()
		    sec_dict.update({"pcc": pcc, "amount":'', "flight_no": [second_key.strip()],
                        "errorMessage": '', "errorCode": error_code, "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": {}, "segments":[second_seg],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':''})
		    sec_log_.update({"pcc": pcc, "flight_no": second_key.strip(), "actualPrice": '', 'custPaidPrice': ''})
		    rslt.append(sec_dict)
                    logs_.append(sec_log_)
	else:
	    dict_, log_ = {}, {}
            dict_.update({"pcc": pcc, "amount":data[10], "flight_no": [''],
                        "errorMessage": data[15], "errorCode": error_code, "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": {}, "segments":[''],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':''})
            log_.update({"pcc": pcc, "flight_no": '', "actualPrice":'', 'custPaidPrice':''})
            rslt.append(dict_)
            logs_.append(log_)
    else:
	dict_, log_ = {}, {}
	dict_.update({"pcc": pcc, "amount":data[10], "flight_no": [''],
                        "errorMessage": "Internal server error", "errorCode": '011', "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": {}, "segments":[''],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':''})
        log_.update({"pcc": pcc, "flight_no": '', "actualPrice":'', 'custPaidPrice':''})
        rslt.append(dict_)
        logs_.append(log_)
	try:
		insert_query = 'insert into airasia_booking_report(sk, error_message, status_message, created_at, modified_at) values(%s, "Unexpected error", "Booking Failed", now(), now()) on duplicate key update modified_at=now(), error_message="Unexpected error"'
		cursor.execute(insert_query %  content.get('trip_ref', ''))
	except:
		pass
    create_at, modified_at = data[18], data[19]
    if not create_at:
	create_at, modified_at = datetime.datetime.now(), datetime.datetime.now()
    book_fin_dict.update({'result':rslt, 'logReport':logs_, 'created_at': create_at,'modified_at':modified_at, 'auto_pnr_exists' : auto_pnr_exists})
    #logging.debug(book_fin_dict)
    logging.debug('%s %s' % (datetime.datetime.now(), book_fin_dict))
    cursor.close()
    con.close()
    return jsonify(book_fin_dict)



@app.route('/indigo/status', methods=['GET', 'POST'])
@app.route('/indigo/booking', methods=['GET', 'POST'])
def indigo_booking():
    book_query = 'select * from indigo_booking_report where sk = "%s"'
    print 'came'
    print request.get_json(silent=True)
    #return jsonify({"Message" : "Thanks"})
    auto_pnr_exists = False
    try:
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
        content = request.get_json(silent=True)
    try:
        content = eval(content)
    except Exception as e:
        print e
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    create_logger_obj('indigo_booking')
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(spiders_directory)
    os.system('pwd')
    pnr = content.get('trip_ref', '')
    output_file = 'indigo_%s_%s.json'%(pnr, get_current_ts_with_ms())
    if 'status' not in request.url:
	HTTP_PROXY = http_proxy_ip()
        run_cmd = '/usr/local/bin/scrapy crawl indigobooking_browse -a jsons="%s"  --set HTTP_PROXY="%s"' % (content, HTTP_PROXY)

        try:
            os.system(run_cmd)
            print run_cmd
        except:
            print traceback.format_exc()
    fin_data_dict, error_dict = {}, {}
    departdate = content.get('departure_date', '')
    origin = content.get('origin_code', '')
    destination = content.get('destination_code', '')
    all_segments = content.get('all_segments', [])
    if all_segments:
        all_seg = all_segments[0]
        pcc = ''.join(all_seg.keys())
    else: pcc = ''
    con, cursor = create_cursor('TICKETBOOKINGDB')
    cursor.execute(book_query%pnr)
    db_data = cursor.fetchall()
    book_fin_dict = {}
    if db_data:
        data = db_data[0]
    else: data = ['']*20
    try: tax_detais = json.loads(data[17])
    except: tax_detais = {}
    rslt, logs_ = [], []
    error_code_dict = {
			'001': 'Unable to login on Login ID',
                        '002': 'Request not found',#Not coded
			'003': 'Booking Faild As its MultiCity trip',
                        '004': 'It does not have modify option PNR',#Not necessary
                        '005': 'Itinerary exists',#Not necessary
			'006': 'Flight not found in selected class',
                        '007': 'Could not find flights',#Not coded, similarto above
                        '008': 'Fare increased by IndiGo',
                        '009': 'Payment Failed',
                        '010': 'Wrong input dict format',
                        '011': 'Internal server error',
			'012': 'Try again later',
			'013': 'Multi-city booking',
			'014': 'Check oneway meals',
			'015': 'Check oneway baggages',
			'016': 'Check return meals',
			'017': 'Check return baggages',
			'018': 'Meals site level issue, so not handled'
                        }
    err_msg, error_code = data[15], ''
    if err_msg:
       err_msg = err_msg.strip()
       for key, err in error_code_dict.iteritems():
          if err_msg == err:
              error_code = key
	  elif 'Login' in err_msg:
	      error_code = '001'
    if db_data:
        if tax_detais:
            for key, vals_ in tax_detais.iteritems():
		print key, vals_
		pcc = vals_['pcc']
		pcc_ = vals_.get('pcc_', '')
                key = key.replace(' ', '')
                dict_, log_, sec_dict, sec_log_ = {}, {}, {}, {}
                seg = vals_.get('seg', '')
                total_price = vals_.get('total', '')
                auto_pnr_exists = vals_.get('AUTO_PNR_EXISTS', False)
                del vals_['seg']
                try: del vals_['AUTO_PNR_EXISTS']
                except: pass
                del vals_['total']
                del vals_['pcc']
                try: del vals_['pcc_']
		except: pass
                if '<>' in key:
                    key, second_key = key.split('<>')
                    seg_lst = seg.split('-')
                    try:
                        seg = '-'.join(seg_lst[0:2])
                        second_seg = '-'.join(seg_lst[2:])
                    except: second_seg = ''
                else:
                    second_seg, second_key = ['']*2
		key = re.sub(key[1],key[1] + ' ', key)
                dict_.update({"pcc": pcc_, "amount":str(total_price), "flight_no": [key.strip()],
                        "errorMessage": data[15], "errorCode": error_code, "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": vals_, "segments":[seg],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':str(data[10])})
                #log_.update({"pcc": pcc, "flight_no": key.strip(), "actualPrice":data[10], 'custPaidPrice':data[9]})
		try:
			cust_paid_price = content['all_segments'][0][pcc]['amount']
		except:
			try: cust_paid_price = content['all_segments'][1][pcc]['amount']
			except: cust_paid_price = ''
                log_.update({"pcc": pcc_, "flight_no": key.strip(), "actualPrice": str(total_price), 'custPaidPrice': str(cust_paid_price)})

                rslt.append(dict_)
                logs_.append(log_)
                second_key = second_key.replace(' ', '')
                if second_key:
                    second_key = re.sub(second_key[1],second_key[1] + ' ', second_key)
                    sec_dict.update({"pcc": pcc_, "amount":'', "flight_no": [second_key.strip()],
                        "errorMessage": '', "errorCode": error_code, "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": {}, "segments":[second_seg],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':''})
                    sec_log_.update({"pcc": pcc_, "flight_no": second_key.strip(), "actualPrice": '', 'custPaidPrice': ''})
                    rslt.append(sec_dict)
                    logs_.append(sec_log_)
        else:
            dict_, log_ = {}, {}
            dict_.update({"pcc": pcc, "amount":str(data[10]), "flight_no": [''],
                        "errorMessage": data[15], "errorCode": error_code, "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": {}, "segments":[''],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':''})
            log_.update({"pcc": pcc, "flight_no": '', "actualPrice":'', 'custPaidPrice':''})
            rslt.append(dict_)
            logs_.append(log_)
    else:
        dict_, log_ = {}, {}
        dict_.update({"pcc": pcc, "amount":data[10], "flight_no": [''],
                        "errorMessage": "Internal server error", "errorCode": '011', "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": {}, "segments":[''],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':''})
        log_.update({"pcc": pcc, "flight_no": '', "actualPrice":'', 'custPaidPrice':''})
        rslt.append(dict_)
        logs_.append(log_)
	try:
		insert_query = 'insert into indigo_booking_report(sk, error_message, status_message, created_at, modified_at) values(%s, "Unexpected error", "Booking Failed", now(), now()) on duplicate key update modified_at=now(), error_message="Unexpected error"'
                cursor.execute(insert_query %  content.get('trip_ref', ''))
	except:
		pass
    create_at, modified_at = data[18], data[19]
    if not create_at:
        create_at, modified_at = datetime.datetime.now(), datetime.datetime.now()
    book_fin_dict.update({'result':rslt, 'logReport':logs_, 'created_at': create_at,'modified_at':modified_at, 'auto_pnr_exists' : auto_pnr_exists})
    logging.debug('%s %s' % (datetime.datetime.now(), book_fin_dict))
    cursor.close()
    con.close()
    print book_fin_dict
    return jsonify(book_fin_dict)

@app.route('/spicejet/status', methods=['GET', 'POST'])
@app.route('/spicejet/booking', methods=['GET', 'POST'])
def spicejet_booking():
    book_query = 'select * from spicejet_booking_report where sk = "%s"'
    print 'came'
    print request.get_json(silent=True)
    #return jsonify({"Message" : "Thanks"})
    auto_pnr_exists = False
    try:
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
        content = request.get_json(silent=True)
    try:
        content = eval(content)
    except Exception as e:
        print e
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    create_logger_obj('spicejet_booking')
    auto_pnr_exists = False
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(spiders_directory)
    os.system('pwd')
    pnr = content.get('trip_ref', '')
    output_file = 'spicejet_%s_%s.json'%(pnr, get_current_ts_with_ms())
    if 'status' not in request.url:
	HTTP_PROXY = http_proxy_ip()
        run_cmd = '/usr/local/bin/scrapy crawl spicejet_booking_browse -a jsons="%s"  --set HTTP_PROXY="%s"' % (content, HTTP_PROXY)

        try:
            os.system(run_cmd)
            print run_cmd
        except:
            print traceback.format_exc()
    fin_data_dict, error_dict = {}, {}
    departdate = content.get('departure_date', '')
    origin = content.get('origin_code', '')
    destination = content.get('destination_code', '')
    all_segments = content.get('all_segments', [])
    if all_segments:
        all_seg = all_segments[0]
        pcc = ''.join(all_seg.keys())
    else: pcc = ''
    con, cursor = create_cursor('TICKETBOOKINGDB')
    cursor.execute(book_query%pnr)
    db_data = cursor.fetchall()
    book_fin_dict = {}
    if db_data:
        data = db_data[0]
    else: data = ['']*20
    try: tax_detais = json.loads(data[17])
    except:
        try: tax_detais = eval(data[17])
        except: tax_detais = {}
    rslt, logs_ = [], []
    error_code_dict = {
            '001': 'Unable to login on Login ID',
                        '002': 'Request not found',#Not coded
            '003': 'Booking Faild As its MultiCity trip',
                        '004': 'It does not have modify option PNR',#Not necessary
                        '005': 'Itinerary exists',#Not necessary
            '006': 'Flight not found in selected class',
                        '007': 'Could not find flights',#Not coded, similarto above
                        '008': 'Fare increased by IndiGo',
                        '009': 'Payment Failed',
                        '010': 'Wrong input dict format',
                        '011': 'Internal server error',
            '012': 'Try again later',
            '013': 'Multi-city booking',
            '014': 'Check oneway meals',
            '015': 'Check oneway baggages',
            '016': 'Check return meals',
            '017': 'Check return baggages',
            '018': 'Meals site level issue, so not handled'
                        }
    err_msg, error_code = data[15], ''
    if err_msg:
        err_msg = err_msg.strip()
        for key, err in error_code_dict.iteritems():
	    if err_msg == err:
		error_code = key
	    elif 'Login' in err_msg:
		error_code = '001'
    if db_data:
        if tax_detais:
            for key, vals_ in tax_detais.iteritems():
        	print key, vals_
        	pcc = vals_['pcc']
        	pcc_ = vals_.get('pcc_', '')
                key = key.replace(' ', '')
                dict_, log_, sec_dict, sec_log_ = {}, {}, {}, {}
                seg = vals_.get('seg', '')
                total_price = vals_.get('total', '')
                auto_pnr_exists = vals_.get('AUTO_PNR_EXISTS', False)
                del vals_['seg']
                try: del vals_['AUTO_PNR_EXISTS']
                except: pass
                del vals_['total']
                del vals_['pcc']
                try: del vals_['pcc_']
        	except: pass
                if '<>' in key:
                    key, second_key = key.split('<>')
                    seg_lst = seg.split('-')
                    try:
                        seg = '-'.join(seg_lst[0:2])
                        second_seg = '-'.join(seg_lst[2:])
                    except: second_seg = ''
                else:
                    second_seg, second_key = ['']*2
		key = re.sub(key[1],key[1] + ' ', key)
                dict_.update({"pcc": pcc_, "amount":str(total_price), "flight_no": [key.strip()],
                        "errorMessage": data[15], "errorCode": error_code, "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": vals_, "segments":[seg],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':str(data[10])})
                #log_.update({"pcc": pcc, "flight_no": key.strip(), "actualPrice":data[10], 'custPaidPrice':data[9]})
        	try:
            		cust_paid_price = content['all_segments'][0][pcc]['amount']
        	except:
            		try: cust_paid_price = content['all_segments'][1][pcc]['amount']
            		except: cust_paid_price = ''
	    	log_.update({"pcc": pcc_, "flight_no": key.strip(), "actualPrice": str(total_price), 'custPaidPrice': str(cust_paid_price)})
	    	rslt.append(dict_)
	    	logs_.append(log_)
	    	second_key = second_key.replace(' ', '')
		if second_key:
			second_key = re.sub(second_key[1],second_key[1] + ' ', second_key)
			sec_dict.update({"pcc": pcc_, "amount":'', "flight_no": [second_key.strip()],
			"errorMessage": '', "errorCode": error_code, "departDate": departdate,
			"pnrCaptured":data[3], "pricingDetails": {}, "segments":[second_seg],
			"trip_id": content.get('trip_ref', ''), 'TotalFare':''})
			sec_log_.update({"pcc": pcc_, "flight_no": second_key.strip(), "actualPrice": '', 'custPaidPrice': ''})
			rslt.append(sec_dict)
			logs_.append(sec_log_)
        else:
            dict_, log_ = {}, {}
            dict_.update({"pcc": pcc, "amount":str(data[10]), "flight_no": [''],
                        "errorMessage": data[15], "errorCode": error_code, "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": {}, "segments":[''],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':''})
            log_.update({"pcc": pcc, "flight_no": '', "actualPrice":'', 'custPaidPrice':''})
            rslt.append(dict_)
            logs_.append(log_)
    else:
        dict_, log_ = {}, {}
        dict_.update({"pcc": pcc, "amount":data[10], "flight_no": [''],
                        "errorMessage": "Internal server error", "errorCode": '011', "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": {}, "segments":[''],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':''})
        log_.update({"pcc": pcc, "flight_no": '', "actualPrice":'', 'custPaidPrice':''})
        rslt.append(dict_)
        logs_.append(log_)
        try:
            insert_query = 'insert into spicejet_booking_report(sk, error_message, status_message, created_at, modified_at) values(%s, "Unexpected error", "Booking Failed", now(), now()) on duplicate key update modified_at=now(), error_message="Unexpected error"'
            cursor.execute(insert_query %  content.get('trip_ref', ''))
        except:
            pass
    create_at, modified_at = data[18], data[19]
    if not create_at:
        create_at, modified_at = datetime.datetime.now(), datetime.datetime.now()
    book_fin_dict.update({'result':rslt, 'logReport':logs_, 'created_at': create_at,'modified_at':modified_at, 'auto_pnr_exists' : auto_pnr_exists})
    logging.debug('%s %s' % (datetime.datetime.now(), book_fin_dict))
    cursor.close()
    con.close()
    print book_fin_dict
    return jsonify(book_fin_dict)


@app.route('/goair/status', methods=['GET', 'POST'])
@app.route('/goair/booking', methods=['GET', 'POST'])
def goair_booking():
    book_query = 'select * from goair_booking_report where sk = "%s"'
    print 'came'
    print request.get_json(silent=True)
    #return jsonify({"Message" : "Thanks"})
    try:
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
        content = request.get_json(silent=True)
    try:
        content = eval(content)
    except Exception as e:
        print e
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    create_logger_obj('goair_booking')
    auto_pnr_exists = False
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(spiders_directory)
    os.system('pwd')
    pnr = content.get('trip_ref', '')
    output_file = 'indigo_%s_%s.json'%(pnr, get_current_ts_with_ms())
    if 'status' not in request.url:
	HTTP_PROXY = http_proxy_ip()
        run_cmd = '/usr/local/bin/scrapy crawl goair_browse -a jsons="%s"  --set HTTP_PROXY="%s"' % (content, HTTP_PROXY)
        try:
            os.system(run_cmd)
            print run_cmd
        except:
            print traceback.format_exc()
    fin_data_dict, error_dict = {}, {}
    departdate = content.get('departure_date', '')
    origin = content.get('origin_code', '')
    destination = content.get('destination_code', '')
    all_segments = content.get('all_segments', [])
    if all_segments:
        all_seg = all_segments[0]
        pcc = ''.join(all_seg.keys())
    else: pcc = ''
    con, cursor = create_cursor('TICKETBOOKINGDB')
    cursor.execute(book_query%pnr)
    db_data = cursor.fetchall()
    book_fin_dict = {}
    if db_data:
        data = db_data[0]
    else: data = ['']*20
    try: tax_detais = eval(data[17])
    except Exception as e:
        tax_detais = {}
        print e
    rslt, logs_ = [], []
    error_code_dict = {
            '001': 'Unable to login on Login ID',
                        '002': 'Request not found',#Not coded
            '003': 'Booking Faild As its MultiCity trip',
                        '004': 'It does not have modify option PNR',#Not necessary
                        '005': 'Itinerary exists',#Not necessary
            '006': 'Flight not found in selected class',
                        '007': 'Could not find flights',#Not coded, similarto above
                        '008': 'Fare increased by IndiGo',
                        '009': 'Payment Failed',
                        '010': 'Wrong input dict format',
                        '011': 'Internal server error',
            '012': 'Try again later',
            '013': 'Multi-city booking',
            '014': 'Check oneway meals',
            '015': 'Check oneway baggages',
            '016': 'Check return meals',
            '017': 'Check return baggages',
            '018': 'Meals site level issue, so not handled'
                        }
    err_msg, error_code = data[15], ''
    if err_msg:
       err_msg = err_msg.strip()
       for key, err in error_code_dict.iteritems():
          if err_msg == err:
              error_code = key
          elif 'Login' in err_msg:
              error_code = '001'
    if db_data:
        if tax_detais:
            for key, vals_ in tax_detais.iteritems():
                print key, vals_
                pcc = vals_.get('pcc', '')
                pcc_ = vals_.get('pcc_', '')
                key = key.replace(' ', '')
                dict_, log_, sec_dict, sec_log_ = {}, {}, {}, {}
                seg = vals_.get('seg', '')
                total_price = vals_.get('total', '')
                auto_pnr_exists = vals_.get('AUTO_PNR_EXISTS', False)
                try:
                    del vals_['seg']
                    del vals_['total']
                    del vals_['pcc']
                except:
                    pass
                try: del vals_['AUTO_PNR_EXISTS']
                except: pass
                try: del vals_['pcc_']
                except: pass
                if '<>' in key:
                    key, second_key = key.split('<>')
                    seg_lst = seg.split('-')
                    try:
                        seg = '-'.join(seg_lst[0:2])
                        second_seg = '-'.join(seg_lst[2:])
                    except: second_seg = ''
                else:
                    second_seg, second_key = ['']*2
                key = key[:2] + ' ' + key[2:]
                dict_.update({"pcc": pcc_, "amount":str(total_price), "flight_no": [key.strip().replace('  ', ' ')],
                        "errorMessage": data[15], "errorCode": error_code, "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": vals_, "segments":[seg],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':str(data[10])})
                #log_.update({"pcc": pcc, "flight_no": key.strip(), "actualPrice":data[10], 'custPaidPrice':data[9]})
                try:
                    cust_paid_price = content['all_segments'][0][pcc]['amount']
                except:
                    try: cust_paid_price = content['all_segments'][1][pcc]['amount']
                    except: cust_paid_price = ''
                log_.update({"pcc": pcc_, "flight_no": key.strip(), "actualPrice": str(total_price), 'custPaidPrice': str(cust_paid_price)})
                rslt.append(dict_)
                logs_.append(log_)
                second_key = second_key.replace(' ', '')
                if second_key:
                        second_key = second_key[:2] + ' ' + second_key[2:]
                        sec_dict.update({"pcc": pcc_, "amount":'', "flight_no": [second_key.strip()],
                            "errorMessage": '', "errorCode": error_code, "departDate": departdate,
                            "pnrCaptured":data[3], "pricingDetails": {}, "segments":[second_seg],
                            "trip_id": content.get('trip_ref', ''), 'TotalFare':''})
                        sec_log_.update({"pcc": pcc_, "flight_no": second_key.strip(), "actualPrice": '', 'custPaidPrice': ''})
                        rslt.append(sec_dict)
                        logs_.append(sec_log_)
        else:
            dict_, log_ = {}, {}
            dict_.update({"pcc": pcc, "amount":str(data[10]), "flight_no": [''],
                    "errorMessage": data[15], "errorCode": error_code, "departDate": departdate,
                    "pnrCaptured":data[3], "pricingDetails": {}, "segments":[''],
                    "trip_id": content.get('trip_ref', ''), 'TotalFare':''})
            log_.update({"pcc": pcc, "flight_no": '', "actualPrice":'', 'custPaidPrice':''})
            rslt.append(dict_)
            logs_.append(log_)
    else:
        dict_, log_ = {}, {}
        dict_.update({"pcc": pcc, "amount":data[10], "flight_no": [''],
                        "errorMessage": "Internal server error", "errorCode": '011', "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": {}, "segments":[''],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':''})
        log_.update({"pcc": pcc, "flight_no": '', "actualPrice":'', 'custPaidPrice':''})
        rslt.append(dict_)
        logs_.append(log_)
        try:
            insert_query = 'insert into goair_booking_report(sk, error_message, status_message, created_at, modified_at) values(%s, "Unexpected error", "Booking Failed", now(), now()) on duplicate key update modified_at=now(), error_message="Unexpected error"'
            cursor.execute(insert_query %  content.get('trip_ref', ''))
        except:
            pass
    create_at, modified_at = data[18], data[19]
    if not create_at:
        create_at, modified_at = datetime.datetime.now(), datetime.datetime.now()
    book_fin_dict.update({'result':rslt, 'logReport':logs_, 'created_at': create_at,'modified_at':modified_at, 'auto_pnr_exists' : auto_pnr_exists})
    logging.debug('%s %s' % (datetime.datetime.now(), book_fin_dict))
    cursor.close()
    con.close()
    return jsonify(book_fin_dict)

@app.route('/airasia/amend/status', methods=['GET', 'POST'])
@app.route('/airasia/amend/booking', methods=['GET', 'POST'])
def airasia_amend_booking():
    amend_query = 'select * from airasiaamend_booking_report where sk = "%s" and pnr="%s"'
    amend_spider_dir = '/root/scrapers/flights/amend_scrapers/amend_scrapers/spiders'
    print 'came'
    print request.get_json(silent=True)
    create_logger_obj('airasia_amend')
    format_status = False
    try:
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
        content = request.get_json(silent=True)
    try:
        if type(content) != dict:
            content = eval(content)
    except Exception as e:
        wrong_format = e.message
        format_status = True
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    fin_amend_dict = {}
    created_at,  modified_at = datetime.datetime.now(), datetime.datetime.now()
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(amend_spider_dir)
    os.system('pwd')
    trip_ref = content.get('trip_ref', '')
    details = content.get('details', [])
    pcc, pnr = ['']*2
    result = []
    if details:
        details_dict = details[0]
        pcc = details_dict.get('pcc', '')
        pnr = details_dict.get('pnr', '')
    if not pcc or format_status:
        if format_status:
            error_code, error_msg = '010', 'Wrong input dict format'
        else:
            error_code, error_msg = '016', 'PCC not found'
        rslt_dict = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = error_code
        rslt_dict["errorMessage"] = error_msg
        rslt_dict["flight_no"] = ''
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["pricingDetails"] = {}
        rslt_dict["tripId"] = trip_ref
        rslt_dict["create_at"] = created_at
        rslt_dict["modified_at"] = modified_at
        result.append(rslt_dict)
        fin_amend_dict['result'] = result
        logging.debug(fin_amend_dict)
        return jsonify(fin_amend_dict)
    if 'status' not in request.url:
	HTTP_PROXY = http_proxy_ip()
        run_cmd = '/usr/local/bin/scrapy crawl airasiaamend_booking_browse -a jsons="%s"  --set HTTP_PROXY="%s"' % (content, HTTP_PROXY)
    else:
	logging.debug("atatus request")
    try:
        os.system(run_cmd)
    except:
        print traceback.format_exc()
    con, cursor = create_cursor('AMENDBOOKINGDB')
    cursor.execute(amend_query%(trip_ref, pnr))
    db_data = cursor.fetchall()
    book_fin_dict = {}
    if db_data:
        data = db_data[0]
    else: data = ['']*20
    try: tax_detais = json.loads(data[15])
    except: tax_detais = {}
    created_at, modified_at =  data[16], data[17]
    if not created_at:
        created_at,  modified_at = datetime.datetime.now(), datetime.datetime.now()
    try: flight_no = eval(data[3])
    except: flight_no = []
    rslt, logs_ = [], []
    error_code_dict = {
	'001' : 'Login Failed',
	'002' : 'PCC not avaialble',
	'003' : 'PNR not found',
	'004' : 'PNR details not found in SpiceJet',
	'005' : 'Multiple details found for PNR',
	'006' : 'PNR not have modify option',
	'007' : 'PNR got Cancelled',
	'008' : 'Response timeout from SpiceJet',
	'009' : 'Segments amend not acceptable',
	'010' : 'Flights not found',
	'016' : 'Payment Failed',
	'012' : 'Payment amount not found',
	'013' : 'Test booking',
	'014' : 'Fare increased by airline',
	'015' : 'Payment fail whereas payment success',
    }
    err_msg, error_code = data[13], ''
    if err_msg:
       err_msg = err_msg.strip()
       for key, err in error_code_dict.iteritems():
          if err in err_msg:
              error_code = key
              break
    fin_amend_dict = {}
    result = []
    if db_data:
        rslt_dict = {}
        if 'Success' in data[10]:
            error_code, err_msg = ['']*2
        try:cancel_tax = json.loads(tax_detais.get('cancel_charges', '{}'))
        except: cancel_tax = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = error_code
        rslt_dict["errorMessage"] = err_msg
        rslt_dict["flight_no"] = flight_no
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["pricingDetails"] = cancel_tax
        rslt_dict["tripId"] = trip_ref
        rslt_dict["create_at"] = created_at
        rslt_dict["modified_at"] = modified_at
        result.append(rslt_dict)
        fin_amend_dict['result'] = result
    else:
        rslt_dict = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = '011'
        rslt_dict["errorMessage"] = 'Unexpected Error'
        rslt_dict["flight_no"] = ''
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["pricingDetails"] = {}
        rslt_dict["tripId"] = trip_ref
        rslt_dict["create_at"] = created_at
        rslt_dict["modified_at"] = modified_at
        result.append(rslt_dict)
        fin_amend_dict['result'] = result
        try: 
            qry = 'insert into airasiaamend_booking_report(sk, airline, pnr, status_message, error_message, created_at, created_at) values(%s,%s,%s,%s,%s,now(), now()) on duplicate key update modified_at=now(), sk=%s, airline=%s, pnr=%s, status_message=%s, error_message=%s'
            vals = (
                    trip_ref, 'AirAsia', pnr, "Amend Failed", 'Unexpected Error',
                    trip_ref, 'AirAsia', pnr, "Amend Failed", 'Unexpected Error'
            )
            cursor.execute(qry, vals)
        except:
            print "Unexpected Error inserting failed."
            logging.debug("Unexpected Error inserting failed.")
    logging.debug(fin_amend_dict)
    cursor.close()
    con.close()
    return jsonify(fin_amend_dict)


@app.route('/goair/amend/status', methods=['GET', 'POST'])
@app.route('/goair/amend/booking', methods=['GET', 'POST'])
def goair_amend_booking():
    amend_query = 'select * from goairamend_booking_report where sk = "%s" and pnr="%s"'
    amend_spider_dir = '/root/scrapers/flights/amend_scrapers/amend_scrapers/spiders'
    print 'came'
    print request.get_json(silent=True)
    create_logger_obj('goair_amend')
    format_status = False
    try:
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
        content = request.get_json(silent=True)
    try:
        if type(content) != dict:
            content = eval(content)
    except Exception as e:
        wrong_format = e.message
        format_status = True
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    fin_amend_dict = {}
    created_at,  modified_at = datetime.datetime.now(), datetime.datetime.now()
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(amend_spider_dir)
    os.system('pwd')
    trip_ref = content.get('trip_ref', '')
    details = content.get('details', [])
    pcc, pnr = ['']*2
    result = []
    if details:
        details_dict = details[0]
        pcc = details_dict.get('pcc', '')
        pnr = details_dict.get('pnr', '')
    if not pcc or format_status:
        if format_status:
            error_code, error_msg = '010', 'Wrong input dict format'
        else:
            error_code, error_msg = '016', 'PCC not found'
        rslt_dict = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = error_code
        rslt_dict["errorMessage"] = error_msg
        rslt_dict["flight_no"] = ''
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["pricingDetails"] = {}
        rslt_dict["tripId"] = trip_ref
        rslt_dict["create_at"] = created_at
        rslt_dict["modified_at"] = modified_at
        result.append(rslt_dict)
        fin_amend_dict['result'] = result
        logging.debug(fin_amend_dict)
        return jsonify(fin_amend_dict)
    if 'status' not in request.url:
	HTTP_PROXY = http_proxy_ip()
        run_cmd = '/usr/local/bin/scrapy crawl goair_amendbooking_browse -a jsons="%s"  --set HTTP_PROXY="%s"' % (content, HTTP_PROXY)
    else:
	logging.debug("atatus request")
    try:
        os.system(run_cmd)
    except:
        print traceback.format_exc()
    con, cursor = create_cursor('AMENDBOOKINGDB')
    cursor.execute(amend_query%(trip_ref, pnr))
    db_data = cursor.fetchall()
    book_fin_dict = {}
    if db_data:
        data = db_data[0]
    else: data = ['']*20
    try: tax_detais = json.loads(data[15])
    except: tax_detais = {}
    created_at, modified_at =  data[16], data[17]
    if not created_at:
        created_at,  modified_at = datetime.datetime.now(), datetime.datetime.now()
    try: flight_no = eval(data[3])
    except: flight_no = []
    rslt, logs_ = [], []
    error_code_dict = {
        '001' : 'Login Failed',
	'002' : 'Change Booking button not presented',
	'003' : 'PNR details not found',
	'004' : 'PCC not available',
	'005' : 'Multi city',
	'006' : 'Flight not found',
	'007' : 'Segments amend not acceptable',
	'008' : 'Test Booking',
	'009' : 'No details for amend',
	'010' : 'Wrong input dict format',
	'011' : 'Internal server error',
	'012' : 'RequestVerificationToken not found in source page',
	'013' : 'Failed to navigate payment page',
	'014' : 'Total price not found',
	'015' : 'Fare increased by Airline',
    }
    err_msg, error_code = data[13], ''
    if err_msg:
       err_msg = err_msg.strip()
       for key, err in error_code_dict.iteritems():
          if err in err_msg:
              error_code = key
              break
    fin_amend_dict = {}
    result = []
    if db_data:
        rslt_dict = {}
        if 'Success' in data[10]:
            error_code, err_msg = ['']*2
        try:cancel_tax = json.loads(tax_detais.get('cancel_charges', '{}'))
        except: cancel_tax = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = error_code
        rslt_dict["errorMessage"] = err_msg
        rslt_dict["flight_no"] = flight_no
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["pricingDetails"] = cancel_tax
        rslt_dict["tripId"] = trip_ref
        rslt_dict["create_at"] = created_at
        rslt_dict["modified_at"] = modified_at
        result.append(rslt_dict)
        fin_amend_dict['result'] = result
    else:
        rslt_dict = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = '011'
        rslt_dict["errorMessage"] = 'Unexpected Error'
        rslt_dict["flight_no"] = ''
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["pricingDetails"] = {}
        rslt_dict["tripId"] = trip_ref
        rslt_dict["create_at"] = created_at
        rslt_dict["modified_at"] = modified_at
        result.append(rslt_dict)
        fin_amend_dict['result'] = result
        try:
            qry = 'insert into goairamend_booking_report(sk, airline, pnr, status_message, error_message, created_at, created_at) values(%s,%s,%s,%s,%s,now(), now()) on duplicate key update modified_at=now(), sk=%s, airline=%s, pnr=%s, status_message=%s, error_message=%s'
            vals = (
                    trip_ref, 'Goair', pnr, "Amend Failed", 'Unexpected Error',
                    trip_ref, 'Goair', pnr, "Amend Failed", 'Unexpected Error'
            )
            cursor.execute(qry, vals)
        except:
            print "Unexpected Error inserting failed."
            logging.debug("Unexpected Error inserting failed.")
    logging.debug(fin_amend_dict)
    cursor.close()
    con.close()
    return jsonify(fin_amend_dict)

@app.route('/spicejet/amend/status', methods=['GET', 'POST'])
@app.route('/spicejet/amend/booking', methods=['GET', 'POST'])
def spicejet_amend_booking():
    amend_query = 'select * from spicejetamend_booking_report where sk = "%s" and pnr="%s"'
    amend_spider_dir = '/root/scrapers/flights/amend_scrapers/amend_scrapers/spiders'
    print 'came'
    print request.get_json(silent=True)
    create_logger_obj('spicejet_amend')
    format_status = False
    try:
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
        content = request.get_json(silent=True)
    try:
        if type(content) != dict:
            content = eval(content)
    except Exception as e:
        wrong_format = e.message
        format_status = True
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    fin_amend_dict = {}
    created_at,  modified_at = datetime.datetime.now(), datetime.datetime.now()
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(amend_spider_dir)
    os.system('pwd')
    trip_ref = content.get('trip_ref', '')
    details = content.get('details', [])
    pcc, pnr = ['']*2
    result = []
    if details:
        details_dict = details[0]
        pcc = details_dict.get('pcc', '')
        pnr = details_dict.get('pnr', '')
    if not pcc or format_status:
        if format_status:
            error_code, error_msg = '010', 'Wrong input dict format'
        else:
            error_code, error_msg = '016', 'PCC not found'
        rslt_dict = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = error_code
        rslt_dict["errorMessage"] = error_msg
        rslt_dict["flight_no"] = ''
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["pricingDetails"] = {}
        rslt_dict["tripId"] = trip_ref
        rslt_dict["create_at"] = created_at
        rslt_dict["modified_at"] = modified_at
        result.append(rslt_dict)
        fin_amend_dict['result'] = result
        logging.debug(fin_amend_dict)
        return jsonify(fin_amend_dict)
    if 'status' not in request.url:
	HTTP_PROXY = http_proxy_ip()
        run_cmd = '/usr/local/bin/scrapy crawl spicejet_amendbooking_browse -a jsons="%s"  --set HTTP_PROXY="%s"' % (content, HTTP_PROXY)
    else:
	logging.debug("atatus request")
    try:
        os.system(run_cmd)
    except:
        print traceback.format_exc()
    con, cursor = create_cursor('AMENDBOOKINGDB')
    cursor.execute(amend_query%(trip_ref, pnr))
    db_data = cursor.fetchall()
    book_fin_dict = {}
    if db_data:
        data = db_data[0]
    else: data = ['']*20
    try: tax_detais = json.loads(data[15])
    except: tax_detais = {}
    created_at, modified_at =  data[16], data[17]
    if not created_at:
        created_at,  modified_at = datetime.datetime.now(), datetime.datetime.now()
    try: flight_no = eval(data[3])
    except: flight_no = []
    rslt, logs_ = [], []
    error_code_dict = {
	'001' : 'Login Failed',
	'002' : 'PCC not avaialble',
	'003' : 'PNR not found',
	'004' : 'PNR details not found in SpiceJet',
	'005' : 'Multiple details found for PNR',
	'006' : 'PNR not have modify option',
	'007' : 'PNR got Cancelled',
	'008' : 'Response timeout from SpiceJet',
	'009' : 'Segments amend not acceptable',
	'010' : 'Flights not found',
	'016' : 'Payment Failed',
	'012' : 'Payment amount not found',
	'013' : 'Test booking',
	'014' : 'Fare increased by airline',
	'015' : 'Payment fail whereas payment success',
    }
    err_msg, error_code = data[13], ''
    if err_msg:
       err_msg = err_msg.strip()
       for key, err in error_code_dict.iteritems():
          if err in err_msg:
              error_code = key
              break
    fin_amend_dict = {}
    result = []
    if db_data:
        rslt_dict = {}
        if 'Success' in data[10]:
            error_code, err_msg = ['']*2
        try:cancel_tax = json.loads(tax_detais.get('cancel_charges', '{}'))
        except: cancel_tax = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = error_code
        rslt_dict["errorMessage"] = err_msg
        rslt_dict["flight_no"] = flight_no
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["pricingDetails"] = cancel_tax
        rslt_dict["tripId"] = trip_ref
        rslt_dict["create_at"] = created_at
        rslt_dict["modified_at"] = modified_at
        result.append(rslt_dict)
        fin_amend_dict['result'] = result
    else:
        rslt_dict = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = '011'
        rslt_dict["errorMessage"] = 'Unexpected Error'
        rslt_dict["flight_no"] = ''
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["pricingDetails"] = {}
        rslt_dict["tripId"] = trip_ref
        rslt_dict["create_at"] = created_at
        rslt_dict["modified_at"] = modified_at
        result.append(rslt_dict)
        fin_amend_dict['result'] = result
        try:
            qry = 'insert into spicejetamend_booking_report(sk, airline, pnr, status_message, error_message, created_at, created_at) values(%s,%s,%s,%s,%s,now(), now()) on duplicate key update modified_at=now(), sk=%s, airline=%s, pnr=%s, status_message=%s, error_message=%s'
            vals = (
                    trip_ref, 'Spicejet', pnr, "Amend Failed", 'Unexpected Error',
                    trip_ref, 'Spicejet', pnr, "Amend Failed", 'Unexpected Error'
            )
            cursor.execute(qry, vals)
        except:
            print "Unexpected Error inserting failed."
            logging.debug("Unexpected Error inserting failed.")

    logging.debug(fin_amend_dict)
    cursor.close()
    con.close()
    return jsonify(fin_amend_dict)

@app.route('/indigo/amend/status', methods=['GET', 'POST'])
@app.route('/indigo/amend/booking', methods=['GET', 'POST'])
def indigo_amend_booking():
    amend_query = 'select * from indigoamend_booking_report where sk = "%s" and pnr="%s"'
    amend_spider_dir = '/root/scrapers/flights/amend_scrapers/amend_scrapers/spiders'
    print 'came'
    print request.get_json(silent=True)
    create_logger_obj('indigo_amend')
    format_status = False
    try:
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
        content = request.get_json(silent=True)
    try:
        if type(content) != dict:
            content = eval(content)
    except Exception as e:
        wrong_format = e.message
        format_status = True
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    fin_amend_dict = {}
    created_at,  modified_at = datetime.datetime.now(), datetime.datetime.now()
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(amend_spider_dir)
    os.system('pwd')
    trip_ref = content.get('trip_ref', '')
    details = content.get('details', [])
    pcc, pnr = ['']*2
    result = []
    if details:
        details_dict = details[0]
        pcc = details_dict.get('pcc', '')
        pnr = details_dict.get('pnr', '')
    if not pcc or format_status:
        if format_status:
            error_code, error_msg = '010', 'Wrong input dict format'
        else:
            error_code, error_msg = '016', 'PCC not found'
        rslt_dict = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = error_code
        rslt_dict["errorMessage"] = error_msg
        rslt_dict["flight_no"] = ''
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["pricingDetails"] = {}
        rslt_dict["tripId"] = trip_ref
        rslt_dict["create_at"] = created_at
        rslt_dict["modified_at"] = modified_at
        result.append(rslt_dict)
        fin_amend_dict['result'] = result
        logging.debug(fin_amend_dict)
        return jsonify(fin_amend_dict)
    if 'status' not in request.url:
	HTTP_PROXY = http_proxy_ip()
        run_cmd = '/usr/local/bin/scrapy crawl indigo_amendbooking_browse -a jsons="%s"  --set HTTP_PROXY="%s"' % (content, HTTP_PROXY)
    else:
	logging.debug("Status request")
    try:
        os.system(run_cmd)
    except:
        print traceback.format_exc()
    con, cursor = create_cursor('AMENDBOOKINGDB')
    cursor.execute(amend_query%(trip_ref, pnr))
    db_data = cursor.fetchall()
    book_fin_dict = {}
    if db_data:
        data = db_data[0]
    else: data = ['']*20
    try: tax_detais = json.loads(data[15])
    except: tax_detais = {}
    created_at, modified_at =  data[16], data[17]
    if not created_at:
        created_at,  modified_at = datetime.datetime.now(), datetime.datetime.now()
    try: flight_no = eval(data[3])
    except: flight_no = []
    rslt, logs_ = [], []
    error_code_dict = {
	'001' : 'Login Failed',
	'002' : 'change flight option',
	'003' : 'details not found',
	'004' : 'navigate Rebook',
	'005' : 'Multi city',
	'006' : 'Flight not found',
	'007' : 'flight modification',
	'008' : 'Test Booking',
	'009' : 'Selecting Flight',
	'010' : 'Wrong input dict format',
	'011' : 'Internal server error',
	'012' : 'end flight details',
	'013' : 'Payment page',
	'014' : 'Price Due amount not found',
	'015' : 'Fare increased by Airline',
    }
    err_msg, error_code = data[13], ''
    if err_msg:
       err_msg = err_msg.strip()
       for key, err in error_code_dict.iteritems():
          if err in err_msg:
              error_code = key
              break
    fin_amend_dict = {}
    result = []
    if db_data:
        rslt_dict = {}
        if 'Success' in data[10]:
            error_code, err_msg = ['']*2
        try:cancel_tax = json.loads(tax_detais.get('cancel_charges', '{}'))
        except: cancel_tax = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = error_code
        rslt_dict["errorMessage"] = err_msg
        rslt_dict["flight_no"] = flight_no
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["pricingDetails"] = cancel_tax
        rslt_dict["tripId"] = trip_ref
        rslt_dict["create_at"] = created_at
        rslt_dict["modified_at"] = modified_at
        result.append(rslt_dict)
        fin_amend_dict['result'] = result
    else:
        rslt_dict = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = '011'
        rslt_dict["errorMessage"] = 'Unexpected Error'
        rslt_dict["flight_no"] = ''
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["pricingDetails"] = {}
        rslt_dict["tripId"] = trip_ref
        rslt_dict["create_at"] = created_at
        rslt_dict["modified_at"] = modified_at
        result.append(rslt_dict)
        fin_amend_dict['result'] = result
        try:
            qry = 'insert into indigoamend_booking_report(sk, airline, pnr, status_message, error_message, created_at, created_at) values(%s,%s,%s,%s,%s,now(), now()) on duplicate key update modified_at=now(), sk=%s, airline=%s, pnr=%s, status_message=%s, error_message=%s'
            vals = (
                    trip_ref, 'Indigo', pnr, "Amend Failed", 'Unexpected Error',
                    trip_ref, 'Indigo', pnr, "Amend Failed", 'Unexpected Error'
            )
            cursor.execute(qry, vals)
        except:
            print "Unexpected Error inserting failed."
            logging.debug("Unexpected Error inserting failed.")
    logging.debug(fin_amend_dict)
    cursor.close()
    con.close()
    return jsonify(fin_amend_dict)

@app.route('/indigo/split/cancel/status', methods=['GET', 'POST'])
@app.route('/indigo/split/cancel', methods=['GET', 'POST'])
@app.route('/indigo/cancel/status', methods=['GET', 'POST'])
@app.route('/indigo/cancel', methods=['GET', 'POST'])
def indigo_split_booking():
    splitcancel_query = 'select * from indigosplit_cancellation_report where sk = "%s" and pnr="%s"'
    print 'came'
    format_status = False
    indigolog = create_logger_obj('indigosplit_cancel')
    try:
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
        content = request.get_json(silent=True)
    try:
        if type(content) != dict:
            content = eval(content)
    except Exception as e:
        wrong_format = e.message
        format_status = True
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    indigolog.debug('%s %s' % (datetime.datetime.now(), content))

    fin_splitcancel_dict = {}
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(splitcancel_spider_dir)
    os.system('pwd')
    trip_ref = content.get('trip_ref', '')
    details = content.get('details', [])
    pcc, pnr = ['']*2
    result = []
    if details:
        details_dict = details[0]
        pcc = details_dict.get('pcc', '')
        pnr = details_dict.get('pnr', '')
    if not pcc or format_status:
        if format_status:
            error_code, error_msg = '010', 'Wrong input dict format'
        else:
            error_code, error_msg = '016', 'PCC not found'
        rslt_dict = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = error_code
        rslt_dict["errorMessage"] = error_msg
        rslt_dict["flight_no"] = ''
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["splitPNR"] = pnr
        rslt_dict["pricingDetails"] = {}
        rslt_dict["tripId"] = trip_ref
        result.append(rslt_dict)
        fin_splitcancel_dict['result'] = result
        logging.debug(fin_splitcancel_dict)
        return jsonify(fin_splitcancel_dict)
    if 'status' not in request.url:
	    HTTP_PROXY = http_proxy_ip()
            run_cmd = '/usr/local/bin/scrapy crawl indigosplit_cancallation_browse -a jsons="%s"  --set HTTP_PROXY="%s"' % (content, HTTP_PROXY)
            try:
                os.system(run_cmd)
            except:
                print traceback.format_exc()
    else:
        logging.debug("Status Request")
    con, cursor = create_cursor('SPLITCANCELLATIONDB')
    cursor.execute(splitcancel_query%(trip_ref, pnr))
    db_data = cursor.fetchall()
    book_fin_dict = {}
    if db_data:
        data = db_data[0]
    else: data = ['']*20
    try: tax_detais = json.loads(data[9])
    except: tax_detais = {}
    try: flight_no = eval(data[5])
    except: flight_no = []
    rslt, logs_ = [], []
    error_code_dict = {
        '001' : 'Login Failed',
        '002' : 'Wrong input dict format',
        '003' : 'Unexpected error',
    }
    err_msg, error_code = data[6], ''
    if err_msg:
       err_msg = err_msg.strip()
       for key, err in error_code_dict.iteritems():
          if err in err_msg:
              error_code = key
              break
          elif 'Login' in err_msg:
              error_code = '001'
              break
    fin_splitcancel_dict = {}
    result = []
    if db_data:
        rslt_dict = {}
        if 'Success' in data[7]:
            error_code, err_msg = ['']*2
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = error_code
        rslt_dict["errorMessage"] = err_msg
        rslt_dict["flight_no"] = flight_no
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["pricingDetails"] = data[9]
        rslt_dict["splitPNR"] = data[3]
        rslt_dict["tripId"] = trip_ref
        #result.append(rslt_dict)
        #fin_splitcancel_dict['result'] = result

    else:
        rslt_dict = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = '011'
        rslt_dict["errorMessage"] = 'Unexpected error'
	rslt_dict["flight_no"] = ''
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["splitPNR"] = ''
        rslt_dict["pricingDetails"] = {}
        rslt_dict["tripId"] = trip_ref
        #result.append(rslt_dict)
        #fin_splitcancel_dict['result'] = result

        try:
                insert_query = 'insert into indigosplit_cancellation_report (sk, airline, error_message, created_at, modified_at) values (%s, "indigo", "Unexpected error", now(), now()) on duplicate key update modified_at=now(), sk = "%s", error_message="Unexpected error"'
                cursor.execute(insert_query %  (content.get('trip_ref', ''), content.get('trip_ref', '')))
        except:
                pass

    #if data and 'FULL' in data[10]['details'][0]['cancellation_type']['type']:
    #print eval(data[10])
    if data and 'FULL' in data[10]:
        rslt_dict.pop('splitPNR')
    result.append(rslt_dict)
    fin_splitcancel_dict['result'] = result

    cursor.close()
    con.close()
    logging.debug('%s %s' % (datetime.datetime.now(), fin_splitcancel_dict))
    indigolog.debug(fin_splitcancel_dict)
    return jsonify(fin_splitcancel_dict)

@app.route('/spicejet/split/cancel/status', methods=['GET', 'POST'])
@app.route('/spicejet/split/cancel', methods=['GET', 'POST'])
@app.route('/spicejet/cancel/status', methods=['GET', 'POST'])
@app.route('/spicejet/cancel', methods=['GET', 'POST'])
def spicejet_split_booking():
    splitcancel_query = 'select * from spicejet_cancellation_report where sk = "%s" and pnr="%s"'
    print 'came'
    format_status = False
    sglog = create_logger_obj('spicejetsplit_cancel')
    try:
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
        content = request.get_json(silent=True)
    try:
        if type(content) != dict:
            content = eval(content)
    except Exception as e:
        wrong_format = e.message
        format_status = True
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    sglog.debug('%s %s' % (datetime.datetime.now(), content))

    fin_splitcancel_dict = {}
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(splitcancel_spider_dir)
    os.system('pwd')
    trip_ref = content.get('trip_ref', '')
    details = content.get('details', [])
    pcc, pnr = ['']*2
    result = []
    if details:
        details_dict = details[0]
        pcc = details_dict.get('pcc', '')
        pnr = details_dict.get('pnr', '')
    if not pcc or format_status:
        if format_status:
            error_code, error_msg = '010', 'Wrong input dict format'
        else:
            error_code, error_msg = '016', 'PCC not found'
        rslt_dict = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = error_code
        rslt_dict["errorMessage"] = error_msg
        rslt_dict["flight_no"] = ''
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["splitPNR"] = pnr
        rslt_dict["pricingDetails"] = {}
        rslt_dict["tripId"] = trip_ref
        result.append(rslt_dict)
        fin_splitcancel_dict['result'] = result
        logging.debug(fin_splitcancel_dict)
        return jsonify(fin_splitcancel_dict)
    if 'status' not in request.url:
	HTTP_PROXY = http_proxy_ip()
        run_cmd = '/usr/local/bin/scrapy crawl spicejetsplit_cancallation_browse -a jsons="%s"  --set HTTP_PROXY="%s"' % (content, HTTP_PROXY)
        try:
            os.system(run_cmd)
        except:
            print traceback.format_exc()
    else:
        logging.debug("Status Request")
    con, cursor = create_cursor('SPLITCANCELLATIONDB')
    cursor.execute(splitcancel_query%(trip_ref, pnr))
    db_data = cursor.fetchall()
    book_fin_dict = {}
    if db_data:
        data = db_data[0]
    else: data = ['']*20
    try: tax_detais = json.loads(data[9])
    except: tax_detais = {}
    try: flight_no = eval(data[5])
    except: flight_no = []
    rslt, logs_ = [], []
    error_code_dict = {
        '001' : 'Login Failed',
        '002' : 'Wrong input dict format',
        '003' : 'Unexpected error',
    }
    err_msg, error_code = data[6], ''
    if err_msg:
       err_msg = err_msg.strip()
       for key, err in error_code_dict.iteritems():
          if err in err_msg:
              error_code = key
              break
          elif 'Login' in err_msg:
              error_code = '001'
              break
    fin_splitcancel_dict = {}
    result = []
    if db_data:
        rslt_dict = {}
        if 'Success' in data[7]:
            error_code, err_msg = ['']*2
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = error_code
        rslt_dict["errorMessage"] = err_msg
        rslt_dict["flight_no"] = flight_no
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["pricingDetails"] = data[9]
        rslt_dict["splitPNR"] = data[3]
        rslt_dict["tripId"] = trip_ref
        #result.append(rslt_dict)
        #fin_splitcancel_dict['result'] = result
    else:
        rslt_dict = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = '011'
        rslt_dict["errorMessage"] = 'Unexpected error'
        rslt_dict["flight_no"] = ''
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["splitPNR"] = ''
        rslt_dict["pricingDetails"] = {}
        rslt_dict["tripId"] = trip_ref
        #result.append(rslt_dict)
        #fin_splitcancel_dict['result'] = result
        try:
                insert_query = 'insert into spicejet_cancellation_report (sk, airline, error_message, created_at, modified_at) values (%s, "spicejet", "Unexpected error", now(), now()) on duplicate key update modified_at=now(), sk = "%s", error_message="Unexpected error"'
                cursor.execute(insert_query %  (content.get('trip_ref', ''), content.get('trip_ref', '')))
        except Exception as e:
                sglog.debug(e)
                logging.debug(e)
                pass
    if data and 'FULL' in data[10]:
        rslt_dict.pop('splitPNR')
    result.append(rslt_dict)
    fin_splitcancel_dict['result'] = result
    cursor.close()
    con.close()
    logging.debug('%s %s' % (datetime.datetime.now(), fin_splitcancel_dict))
    sglog.debug(fin_splitcancel_dict)
    return jsonify(fin_splitcancel_dict)



@app.route('/jetairways/webcheckin/status', methods=['GET', 'POST'])
@app.route('/jetairways/webcheckin', methods=['GET', 'POST'])
def jetairwayswebcheckin():
    book_query = 'select * from jetairways_webcheckin_status where sk = "%s"'
    spiders_directory = "/root/scrapers/flights/webcheckin_scrapers/webcheckin_scrapers/spiders"
    print 'came'
    try:
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
        content = request.data
    try:
        if type(content) != dict:
            content = eval(content)
    except Exception as e:
        print e
    print content
    create_logger_obj('jetairways_webcheckin')
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    os.chdir(spiders_directory)
    os.system('pwd')
    pnr = content.get('pnr', '')
    if 'status' not in request.url:
	HTTP_PROXY = http_proxy_ip()
        run_cmd = '/usr/local/bin/scrapy crawl jetairwayscheckin_browse -a jsons="%s" --set HTTP_PROXY="%s"' % (content, HTTP_PROXY)
        try:
            os.system(run_cmd)
        except:
            print traceback.format_exc()
    print "scrapper runs complete"
    error_code_dict = {'001':'dict format is wrong in given inputs',
                        '002':'inputs keys in json dict are not specified properly',
                        '003':'different url pattern for this PNR',
                        '004':'unexpected error',
                        '005':'could not locate your reservation',
                        '006':'web check-in for your flight is currently closed',
                        '007':'checked-in already',
                        '007':'Seat is not selected',
                        '008':'checked_in_successfully',
                        }

    con, cursor = create_cursor('WEBCHECKINDB')
    cursor.execute(book_query%pnr)
    db_data = cursor.fetchall()
    webcheckin_dict = {}
    if db_data:
        data = db_data[0]
    else:
        insert_query = 'insert into jetairways_webcheckin_status (sk, tripid, airline, status_message, error_message, created_at, modified_at) values(%s,%s,%s,%s,%s,now(),now())  on duplicate key update modified_at=now(), sk=%s, tripid=%s, status_message=%s, error_message=%s'
        vals = (content.get('pnr', ''), content.get('trip_ref', ''), "jetairways", "Failed", "Unexpected Error",
                content.get('pnr', ''), content.get('trip_ref', ''), "Failed", "Unexpected Error",
                )
        cursor.execute(insert_query, vals)
        data = ['']*6
    err_msg, error_code = data[4], ''
    if err_msg:
       for key, err in error_code_dict.iteritems():
          if err_msg in err:
              error_code = key
              break
          else: error_code = ''
    else: error_code = ''
    if not data[0]:
        err_msg, error_code = 'Bad Request', '005'
        statusmessage  = 'Web checkin failed'
    else: statusmessage = data[3]
    if not err_msg:
        err_msg, error_code = 'Bad Request', '005'
        statusmessage  = 'Web checkin failed'
    else: statusmessage = data[3]
    if not err_msg:
        err_msg = 'Unforseen error'
        error_code = '100'
    if 'Success' in statusmessage:
        err_msg, error_code = '', ''
    create_at, modified_at = datetime.datetime.now(), datetime.datetime.now()
    webcheckin_dict.update({"errorMessage": err_msg, "errorCode":error_code,
                            "pnr":pnr, 'statusMessage': statusmessage,
                            'created_at':create_at, 'modified_at':modified_at})

    cursor.close()
    con.close()
    logging.debug('%s %s' % (datetime.datetime.now(), webcheckin_dict))
    print webcheckin_dict
    return jsonify(webcheckin_dict)


@app.route('/goair/webcheckin/status', methods=['GET', 'POST'])
@app.route('/goair/webcheckin', methods=['GET', 'POST'])
def goairwebcheckin():
    book_query = 'select * from goair_webcheckin_status where sk = "%s"'
    spiders_directory = "/root/scrapers/flights/webcheckin_scrapers/webcheckin_scrapers/spiders"
    print 'came'
    try:
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
        content = request.data
    try:
        if type(content) != dict:
            content = eval(content)
    except Exception as e:
        print e
    print content
    create_logger_obj('goair_webcheckin')
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    os.chdir(spiders_directory)
    os.system('pwd')
    pnr = content.get('pnr', '')
    if 'status' not in request.url:
	HTTP_PROXY = http_proxy_ip()
        run_cmd = '/usr/local/bin/scrapy crawl goairwebcheckin_browse -a jsons="%s" --set HTTP_PROXY="%s"' % (content, HTTP_PROXY)
        try:
            os.system(run_cmd)
        except:
            print traceback.format_exc()
    print "scrapper runs complete"
    error_code_dict = {'001':'Email is mandatory',
                        '002':'InternalError from GoAir',
                        '003':'CheckIn button not presented',
                        '004':'No Pax presented for webcheckin',
                        '005':'Failed to navigate Confirmation page',
                        '006':'Failed to navigate Seatmap page',
                        '007':'Seat not selected',
                        '008':'Selected Payment Seats',
                        '009':'Checkin Failed whereas checkin success',
                        '010':'Unforseen error',
			'011':'Unexpected Error',
			'012':'Booking validation failed',
			'013':'Reprint',
                        }

    con, cursor = create_cursor('WEBCHECKINDB')
    cursor.execute(book_query%pnr)
    db_data = cursor.fetchall()
    webcheckin_dict = {}
    if db_data:
        data = db_data[0]
    else:
        insert_query = 'insert into goair_webcheckin_status (sk, tripid, airline, status_message, error_message, created_at, modified_at) values(%s,%s,%s,%s,%s,now(),now())  on duplicate key update modified_at=now(), sk=%s, tripid=%s, status_message=%s, error_message=%s'
        vals = (content.get('pnr', ''), content.get('trip_ref', ''), "GoAir", "Failed", "Unexpected Error",
                content.get('pnr', ''), content.get('trip_ref', ''), "Failed", "Unexpected Error",
                )
        cursor.execute(insert_query, vals)
        data = ['']*6
    err_msg, error_code = data[4], ''
    if err_msg:
       for key, err in error_code_dict.iteritems():
          if err_msg in err:
              error_code = key
              break
          else: error_code = ''
    else: error_code = ''
    if not data[0]:
        err_msg, error_code = 'Unexpected Error', '011'
        statusmessage  = 'Failed'
    else: statusmessage = data[3]
    if not err_msg:
        err_msg, error_code = 'Unexpected Error', '011'
        statusmessage  = 'Failed'
    else: statusmessage = data[3]
    if not err_msg:
        err_msg = 'Unforseen error'
        error_code = '100'
    if 'Success' in statusmessage:
        err_msg, error_code = '', ''
    create_at, modified_at = datetime.datetime.now(), datetime.datetime.now()
    webcheckin_dict.update({"errorMessage": err_msg, "errorCode":error_code,
                            "pnr":pnr, 'statusMessage': statusmessage,
                            'created_at':create_at, 'modified_at':modified_at})

    cursor.close()
    con.close()
    logging.debug('%s %s' % (datetime.datetime.now(), webcheckin_dict))
    print webcheckin_dict
    return jsonify(webcheckin_dict)

@app.route('/indigo/webcheckin/status', methods=['GET', 'POST'])
@app.route('/indigo/webcheckin', methods=['GET', 'POST'])
def indigowebcheckin():
    book_query = 'select * from indigo_webcheckin_status where sk = "%s"'
    spiders_directory = "/root/scrapers/flights/webcheckin_scrapers/webcheckin_scrapers/spiders"
    print 'came'
    try:
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
        content = request.data
    try:
	if type(content) != dict:
            content = eval(content)
    except Exception as e:
        print e
    print content
    create_logger_obj('indigo_webcheckin')
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(spiders_directory)
    os.system('pwd')
    pnr = content.get('pnr', '')
    HTTP_PROXY = http_proxy_ip()
    run_cmd = '/usr/local/bin/scrapy crawl indigocheckin_browse -a jsons="%s"  --set HTTP_PROXY="%s"' % (content, HTTP_PROXY)
    if 'status' not in request.url:
        try:
            os.system(run_cmd)
        except:
            print traceback.format_exc()
    print "scrapper runs complete"
    error_code_dict = {'001':'Request not found',
                        '002':'Seat not selected',
                        '003':'IndiGo server error',
                        '004':'Booking Retrieve Error',
                        }
    con, cursor = create_cursor('WEBCHECKINDB')
    cursor.execute(book_query%pnr)
    db_data = cursor.fetchall()
    webcheckin_dict = {}
    if db_data:
        data = db_data[0]
    else: data = ['']*6
    err_msg, error_code = data[3], ''
    if err_msg:
       for key, err in error_code_dict.iteritems():
          if err_msg in err:
              error_code = key
          else: error_code = ''
    else: error_code = ''
    if not data[0]:
        err_msg, error_code = 'Bad Request', '005'
        statusmessage  = 'Web checkin failed'
    else: statusmessage = data[2]
    if not err_msg:
        err_msg = 'Unforseen error'
        error_code = '100'
    if 'successful' in statusmessage:
        err_msg, error_code = '', ''
    create_at, modified_at = datetime.datetime.now(), datetime.datetime.now()
    webcheckin_dict.update({"errorMessage": err_msg, "errorCode":error_code,
                            "pnr":pnr, 'statusMessage': statusmessage,
                            'created_at':create_at, 'modified_at':modified_at})

    cursor.close()
    con.close()
    logging.debug('%s %s' % (datetime.datetime.now(), webcheckin_dict))
    print webcheckin_dict
    return jsonify(webcheckin_dict)

@app.route('/spicejet/webcheckin/status', methods=['GET', 'POST'])
@app.route('/spicejet/webcheckin', methods=['GET', 'POST'])
def spicejetwebcheckin():
    book_query = 'select * from spicejet_webcheckin_status where sk = "%s"'
    spiders_directory = "/root/scrapers/flights/webcheckin_scrapers/webcheckin_scrapers/spiders"
    print 'came'
    try:
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
        content = request.data
    try:
        if type(content) != dict:
            content = eval(content)
    except Exception as e:
        print e
    print content
    create_logger_obj('spicejet_webcheckin')
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    os.chdir(spiders_directory)
    os.system('pwd')
    pnr = content.get('pnr', '')
    if 'status' not in request.url:
        run_cmd = '/usr/local/bin/scrapy crawl spicejetcheckin_selenium -a jsons="%s"'%content
        try:
            os.system(run_cmd)
        except:
            print traceback.format_exc()
    print "scrapper runs complete"
    error_code_dict = {'001':'Email is mandatory',
                        '002':'Failed to fetch PNR details',
                        '003':'Terms & Conditions not found',
                        '004':'BoardingPassRequest',
                        '005':'User Already checked in',
                        '006':'Assign Seat to Begin Check-in',
                        '007':'PNR got cancelled',
                        '008':'Failed to navigate Addons page',
                        '009':'Failed to submit webcheckin',
                        '010':'Unforseen error',
                        }

    con, cursor = create_cursor('WEBCHECKINDB')
    cursor.execute(book_query%pnr)
    db_data = cursor.fetchall()
    webcheckin_dict = {}
    if db_data:
        data = db_data[0]
    else:
        insert_query = 'insert into spicejet_webcheckin_status (sk, tripid, airline, status_message, error_message, created_at, modified_at) values(%s,%s,%s,%s,%s,now(),now())  on duplicate key update modified_at=now(), sk=%s, tripid=%s, status_message=%s, error_message=%s'
        vals = (content.get('pnr', ''), content.get('trip_ref', ''), "Spicejet", "Failed", "Unexpected Error",
                content.get('pnr', ''), content.get('trip_ref', ''), "Failed", "Unexpected Error",
                )
        cursor.execute(insert_query, vals)
        data = ['']*6
    #err_msg, error_code = data[4], ''
    cursor.execute(book_query%pnr)
    db_data = cursor.fetchall()
    if db_data:
	data = db_data[0]
    else: data = ['']*6
    err_msg, error_code = data[4], ''
    if err_msg:
       for key, err in error_code_dict.iteritems():
          if err_msg in err:
              error_code = key
	      break
          else: error_code = ''
    else: error_code = ''
    statusmessage = data[3]
    '''
    if not data[0]:
        err_msg, error_code = 'Bad Request', '005'
        statusmessage  = 'Web checkin failed'
    else: statusmessage = data[3]
    if not err_msg:
        err_msg, error_code = 'Bad Request', '005'
        statusmessage  = 'Web checkin failed'
    else: statusmessage = data[3]
    '''
    if not err_msg:
        err_msg = 'Unforseen error'
        error_code = '100'
    if 'successful' in statusmessage:
        err_msg, error_code = '', ''
    create_at, modified_at = datetime.datetime.now(), datetime.datetime.now()
    webcheckin_dict.update({"errorMessage": err_msg, "errorCode":error_code,
                            "pnr":pnr, 'statusMessage': statusmessage,
                            'created_at':create_at, 'modified_at':modified_at})

    cursor.close()
    con.close()
    logging.debug('%s %s' % (datetime.datetime.now(), webcheckin_dict))
    print webcheckin_dict
    return jsonify(webcheckin_dict)

@app.route('/airasia/status', methods=['GET', 'POST'])
def AirasiaStatus():
    book_query = 'select * from airasia_booking_report where sk = "%s"'
    print 'came'
    try:
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
        content = request.get_json(silent=True)
    try:
        content = eval(content)
    except Exception as e:
        print e
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    create_logger_obj('airasia_status')
    pnr = content.get('trip_ref', '')
    fin_data_dict, error_dict = {}, {}
    departdate = content.get('departure_date', '')
    origin = content.get('origin_code', '')
    destination = content.get('destination_code', '')
    all_segments = content.get('all_segments', [])
    if all_segments:
        all_seg = all_segments[0]
        pcc = ''.join(all_seg.keys())
    else: pcc = ''
    con, cursor = create_cursor('TICKETBOOKINGDB')
    cursor.execute(book_query%pnr)
    db_data = cursor.fetchall()
    book_fin_dict = {}
    if db_data:
        data = db_data[0]
    else: data = ['']*20
    try: tax_detais = json.loads(data[17])
    except: tax_detais = {}
    rslt, logs_ = [], []
    error_code_dict = {'003':'Booking Faild As its MultiCity trip',
                        '002':'Request not found',
                        '010':'Booking Scraper unable to login AirAsia',
                        '004':'It does not have modify option PNR',
                        '005':'Itinerary exists',
                        '006':'No flights find in selected class',
                        '007':'Could not find flights',
                        '008':'Fare increased by Airline',
                        '009':'Payment Failed',
                        '011':'Internal server error',
                        '013':'Test Booking',
                        }
    err_msg, error_code = data[15], ''
    if err_msg:
       for key, err in error_code_dict.iteritems():
          if err_msg in err:
              error_code = key
              break
          else: error_code = ''
    else: error_code = ''
    print error_code
    if db_data:
        if tax_detais:
            for key, vals_ in tax_detais.iteritems():
                dict_, log_, sec_dict, sec_log_ = {}, {}, {}, {}
                seg = vals_.get('seg', '')
                pcc = vals_.get('pcc', '')
                total_price = vals_.get('total', '')
                del vals_['seg']
                del vals_['pcc']
                del vals_['total']
                if '<>' in key:
                    key, second_key = key.split('<>')
                    seg_lst = seg.split('-')
                    try:
                        seg = '-'.join(seg_lst[0:2])
                        second_seg = '-'.join(seg_lst[2:])
                    except: second_seg = ''
                else:
                    second_seg, second_key = ['']*2
                key = key.strip()
                dict_.update({"pcc": pcc, "amount":data[10], "flight_no": [key.strip()],
                        "errorMessage": data[15], "errorCode": error_code, "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": vals_, "segments":[seg],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':total_price})
                log_.update({"pcc": pcc, "flight_no": key.strip(), "actualPrice":data[10], 'custPaidPrice':data[9]})
                rslt.append(dict_)
                logs_.append(log_)
                second_key = second_key.replace(' ', '')
                if second_key:
                    second_key = second_key.strip()
                    sec_dict.update({"pcc": pcc, "amount":'', "flight_no": [second_key.strip()],
                        "errorMessage": '', "errorCode": error_code, "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": {}, "segments":[second_seg],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':''})
                    sec_log_.update({"pcc": pcc, "flight_no": second_key.strip(), "actualPrice": '', 'custPaidPrice': ''})
                    rslt.append(sec_dict)
                    logs_.append(sec_log_)
        else:
            dict_, log_ = {}, {}
            dict_.update({"pcc": pcc, "amount":data[10], "flight_no": [''],
                        "errorMessage": data[15], "errorCode": error_code, "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": {}, "segments":[''],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':''})
            log_.update({"pcc": pcc, "flight_no": '', "actualPrice":'', 'custPaidPrice':''})
            rslt.append(dict_)
            logs_.append(log_)
    else:
        dict_, log_ = {}, {}
        dict_.update({"pcc": pcc, "amount":data[10], "flight_no": [''],
                        "errorMessage": "Trip details not found", "errorCode": '500', "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": {}, "segments":[''],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':''})
        log_.update({"pcc": pcc, "flight_no": '', "actualPrice":'', 'custPaidPrice':''})
        rslt.append(dict_)
        logs_.append(log_)
    create_at, modified_at = data[18], data[19]
    if not create_at:
        create_at, modified_at = datetime.datetime.now(), datetime.datetime.now()
    book_fin_dict.update({'result':rslt, 'logReport':logs_, 'created_at': create_at,'modified_at':modified_at})
    logging.debug(book_fin_dict)
    cursor.close()
    con.close()
    return jsonify(book_fin_dict)

@app.route('/goair/split/cancel/status', methods=['GET', 'POST'])
@app.route('/goair/split/cancel', methods=['GET', 'POST'])
@app.route('/goair/cancel/status', methods=['GET', 'POST'])
@app.route('/goair/cancel', methods=['GET', 'POST'])
def goair_split_booking():
    splitcancel_query = 'select * from goairsplit_cancellation_report where sk = "%s" and pnr="%s"'
    print 'came'
    format_status = False
    sglog = create_logger_obj('goairsplit_cancel')
    try: 
        content = request.args.get('content', {}).replace('\n', '').strip()
    except:
        content = request.get_json(silent=True)
    if not content:
        content = request.get_json(silent=True)
    try: 
        if type(content) != dict:
            content = eval(content)
    except Exception as e:
        wrong_format = e.message
        format_status = True 
    logging.debug('%s %s' % (datetime.datetime.now(), content))
    sglog.debug('%s %s' % (datetime.datetime.now(), content))

    fin_splitcancel_dict = {} 
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(splitcancel_spider_dir)
    os.system('pwd')
    trip_ref = content.get('trip_ref', '')
    details = content.get('details', [])
    pcc, pnr = ['']*2
    result = [] 
    if details:
        details_dict = details[0]
        pcc = details_dict.get('pcc', '')
        pnr = details_dict.get('pnr', '')
    if not pcc or format_status:
        if format_status:
            error_code, error_msg = '010', 'Wrong input dict format'
        else:
            error_code, error_msg = '016', 'PCC not found'
        rslt_dict = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = error_code
        rslt_dict["errorMessage"] = error_msg
        rslt_dict["flight_no"] = ''
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["splitPNR"] = pnr
        rslt_dict["pricingDetails"] = {}
        rslt_dict["tripId"] = trip_ref
        result.append(rslt_dict)
        fin_splitcancel_dict['result'] = result
        logging.debug(fin_splitcancel_dict)
        return jsonify(fin_splitcancel_dict)
    if 'status' not in request.url:
	HTTP_PROXY = http_proxy_ip()
        run_cmd = '/usr/local/bin/scrapy crawl goair_splitcancel_browse -a jsons="%s"  --set HTTP_PROXY="%s"' % (content, HTTP_PROXY)
        try:
            os.system(run_cmd)
        except:
            print traceback.format_exc()
    else:
        logging.debug("Status Request")
    con, cursor = create_cursor('SPLITCANCELLATIONDB')
    cursor.execute(splitcancel_query%(trip_ref, pnr))
    db_data = cursor.fetchall()
    book_fin_dict = {}
    if db_data:
        data = db_data[0]
    else: data = ['']*20
    try: tax_detais = json.loads(data[9])
    except: tax_detais = {}
    try: flight_no = eval(data[5])
    except: flight_no = []
    rslt, logs_ = [], []
    error_code_dict = {
        '001' : 'Login Failed',
        '002' : 'Wrong input dict format',
        '003' : 'Unexpected error',
    }
    err_msg, error_code = data[6], ''
    if err_msg:
       err_msg = err_msg.strip()
       for key, err in error_code_dict.iteritems():
          if err in err_msg:
              error_code = key
              break
          elif 'Login' in err_msg:
              error_code = '001'
              break
    fin_splitcancel_dict = {}
    result = []
    if db_data:
        rslt_dict = {}
        if 'Success' in data[7]:
            error_code, err_msg = ['']*2
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = error_code
        rslt_dict["errorMessage"] = err_msg
        rslt_dict["flight_no"] = flight_no
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["pricingDetails"] = data[9]
        rslt_dict["splitPNR"] = data[3]
        rslt_dict["tripId"] = trip_ref
        #result.append(rslt_dict)
        #fin_splitcancel_dict['result'] = result
    else:
        rslt_dict = {}
        rslt_dict["account"] = ""
        rslt_dict["errorCode"] = '011'
        rslt_dict["errorMessage"] = 'Unexpected error'
        rslt_dict["flight_no"] = ''
        rslt_dict["pcc"] = pcc
        rslt_dict["pnr"] = pnr
        rslt_dict["splitPNR"] = ''
        rslt_dict["pricingDetails"] = {}
        rslt_dict["tripId"] = trip_ref
        #result.append(rslt_dict)
        #fin_splitcancel_dict['result'] = result
        try:
                insert_query = 'insert into goairsplit_cancellation_report (sk, airline, error_message, created_at, modified_at) values (%s, "Goair", "Unexpected error", now(), now()) on duplicate key update modified_at=now(), sk = "%s", error_message="Unexpected error"'
                cursor.execute(insert_query %  (content.get('trip_ref', ''), content.get('trip_ref', '')))
        except:
                pass
    if data and 'FULL' in data[10]:
        rslt_dict.pop('splitPNR')
    result.append(rslt_dict)
    fin_splitcancel_dict['result'] = result
    cursor.close()
    con.close()
    logging.debug('%s %s' % (datetime.datetime.now(), fin_splitcancel_dict))
    sglog.debug(fin_splitcancel_dict)
    return jsonify(fin_splitcancel_dict)


def get_current_ts_with_ms():
    dt = datetime.datetime.now().strftime("%Y%m%dT%H%M%S%f")
    return str(dt)

def create_cursor(db_name):
    try:
            conn = MySQLdb.connect(user='root',host='159.89.175.210', db=db_name, passwd='root')
            conn.set_character_set('utf8')
            cursor = conn.cursor()
            cursor.execute('SET NAMES utf8;')
            cursor.execute('SET CHARACTER SET utf8;')
            cursor.execute('SET character_set_connection=utf8;')
    except:
            import traceback; print traceback.format_exc()
            sys.exit(-1)

    return conn, cursor

@app.route('/healthcheck')
def health():
    response = {"status" : "ok"}
    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
