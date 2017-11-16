import os
import sys
import MySQLdb
import traceback
import datetime
from flask import Flask, render_template, request, jsonify
import subprocess
from logging_file import *
import json
import logging
import commands
logging.basicConfig(filename='example.log',level=logging.DEBUG)

app = Flask(__name__)
#spiders_directory = '/root/headrun/airasia/airasia/spiders'
spiders_directory = '/root/scrapers/flights/booking_scrapers/booking_scrapers/spiders'
spiders_directory_cancellation = '/root/headrun/airasia/airasia/spiders'
#spiders_directory = '/home/aravind/prod/scrapers/flights/booking_scrapers/booking_scrapers/spiders'
select_query = 'select * from cancellation_report where sk="%s"'
error_query = 'select * from error_report where pnr="%s"'

cnl_select_query = 'select * from cancellation_report where tripid="%s"'
cnl_error_query = 'select * from error_report where tripid="%s"'

@app.route("/")
def welcome():
    return "Hello World!"

@app.route('/airasia/cancel', methods=['GET', 'POST'])
def add_message():
    try:
        content = request.get_json(silent=True)
        logging.debug(content)
    except Exception as e:
        content = {}
        content.update({"ErrorMessage":e.message})
        logging.debug( e.message)
        return jsonify(content)
    try:
        content = eval(content)
    except:
        pass
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(spiders_directory_cancellation)
    os.system('pwd')
    print os.system('pwd')
    pnr = content.get('trip_ref', '')
    ori_details = content.get('details', [])
    pcc, ori_pnr = ['']*2
    if ori_details:
        if len(ori_details) > 2:
            result_dic, fin_dict = {}, {}
            result_dic.update({'pcc': '',
                           'flight_no': '',
                           'pnr': '',
                           'errorMessage': 'Multiple PNR not acceptable',
                           'errorCode': '019',
                           'tripId': pnr,
                           'pricingDetails': {},
                           'account':'',
                        })
            logging.debug(fin_dict)
            fin_dict.update({'result':[result_dic]})
            return jsonify(fin_dict)
        else:
            ori_deta = ori_details[0]
            pcc = ori_deta.get('pcc', '')
            ori_pnr = ori_deta.get('ori_deta', '')
    else:
        result_dic, fin_dict = {}, {}
        result_dic.update({'pcc': '',
                           'flight_no': '',
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
    run_cmd = 'scrapy crawl airasia_browse -a jsons="%s"' % (content)
    try:
        os.system(run_cmd)
    except:
        print traceback.format_exc()
    fin_data_dict, error_dict = {}, {}
    con, cursor = create_cursor('TICKETCANCELLATION')
    cursor.execute(cnl_select_query%pnr)
    db_data = cursor.fetchall()
    cursor.execute(cnl_error_query%pnr)
    error_data = cursor.fetchall()
    error_code_dict = {'001': 'Oneway single pax cancellation',
                        '002': 'Oneway multiple pax full cancellation',
                        '003': 'Oneway Split PNR cancellation',
                        '004': 'Oneway trip partial pax cancellation',
                        '005': 'Round trip partial sector cancellation',
                        '006': 'Round trip partial sector cancellation',
                        '007': 'Round trip full sector cancellation',
                        '008': 'Round trip partial pax cancellation',
                        '009': 'Round trip partial pax cancellation',
                        '010': 'Past dated Booking',
                        '011': 'Split PNR cancellation',
                        '012': 'No details found with PNR',
                        '013': 'itinerary does not matched',
                        '014': 'Scraper unable to login AirAsia',
                        '015': 'More than one results found with PNR',
                        '016': 'It does not have modify option',
                        '017': 'AirAsia travel date not found',
                        '018': 'Pax name not matched with AirAsia',
                        }
    if db_data:
        data = db_data[0]
        err_msg, error_code = data[2], ''
    elif error_data:
        err_data = error_data[0]
        err_msg, error_code = err_data[3], ''
    else: err_msg, error_code = ['']*2
    if err_msg:
        for key, err in error_code_dict.iteritems():
            if err in err_msg:
                error_code = key
                break
            else: error_code = ''
    else: error_code = ''
    result_dic = {}
    cursor.close()
    con.close()
    if db_data:
        if data[3] == '1' or data[3] == 1:
            err_msg, error_code = ['']*2
        result_dic, fin_dict = {}, {}
        result_dic.update({'pcc': pcc,
                           'flight_no': data[5],
                           'pnr': data[0],
                           'errorMessage': err_msg,
                           'errorCode': error_code,
                           'tripId': data[14],
                           'pricingDetails': data[10],
                           'account':'',
                        })
        logging.debug(fin_dict)
        fin_dict.update({'result':[result_dic]})
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
        logging.debug(fin_dict)
        fin_dict.update({'result':[result_dic]})
        return jsonify(fin_dict)
    else:
        result_dic, fin_dict = {}, {}
        result_dic.update({'pcc': pcc,
                           'flight_no': [],
                           'pnr': [],
                           'errorMessage': 'Internal Server Error',
                           'errorCode': '121',
                           'tripId': pnr,
                           'pricingDetails': {},
                           'account':'',
                        })
        logging.debug(fin_dict)
        fin_dict.update({'result':[result_dic]})
        return jsonify(fin_dict)

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
    create_logger_obj('airasia_booking')
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(spiders_directory)
    os.system('pwd')
    pnr = content.get('trip_ref', '')
    output_file = 'airasia_%s_%s.json'%(pnr, get_current_ts_with_ms())
    run_cmd = 'scrapy crawl airasiabooking_browse -a jsons="%s"' % (content)
    try:
        os.system(run_cmd)
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
    error_code_dict = {'003':'Booking Faild As its MultiCity trip',
			'002':'Request not found',
			'010':'Booking Scraper unable to login AirAsia',
			'004':'It does not have modify option PNR',
			'005':'Itinerary exists',
			'006':'No flights find in selected class',
			'007':'Could not find flights',
			'008':'Fare increased by Airline',
			'009':'Payment Failed',
			'011': 'Internal server error'
			}
    err_msg, error_code = data[15], ''
    if err_msg:
       for key, err in error_code_dict.iteritems():
          if err_msg in err:
              error_code = key
	  else: error_code = ''
    else: error_code = ''
    print error_code
    if db_data:
	if tax_detais:
            for key, vals_ in tax_detais.iteritems():
	        key = key.replace(' ', '')
	        dict_, log_, sec_dict, sec_log_ = {}, {}, {}, {}
	        seg = vals_.get('seg', '')
	        total_price = vals_.get('total', '')
	        del vals_['seg']
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
	        key = re.sub(key[1],key[1] + ' ', key)
	        dict_.update({"pcc": pcc, "amount":data[10], "flight_no": [key.strip()],
			"errorMessage": data[15], "errorCode": error_code, "departDate": departdate,
			"pnrCaptured":data[3], "pricingDetails": vals_, "segments":[seg],
			"trip_id": content.get('trip_ref', ''), 'TotalFare':total_price})
	        log_.update({"pcc": pcc, "flight_no": key.strip(), "actualPrice":data[10], 'custPaidPrice':data[9]})
	        rslt.append(dict_)
	        logs_.append(log_)
	        second_key = second_key.replace(' ', '')
	        if second_key:
		    second_key = re.sub(second_key[1],second_key[1] + ' ', second_key)
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
    create_at, modified_at = data[18], data[19]
    if not create_at:
	create_at, modified_at = datetime.datetime.now(), datetime.datetime.now()
    book_fin_dict.update({'result':rslt, 'logReport':logs_, 'created_at': create_at,'modified_at':modified_at})
    logging.debug(book_fin_dict)
    cursor.close()
    con.close()
    return jsonify(book_fin_dict)

@app.route('/indigo/booking', methods=['GET', 'POST'])
def indigo_booking():
    book_query = 'select * from indigo_booking_report where sk = "%s"'
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
    logging.debug(content)
    create_logger_obj('indigo_booking')
    logging.debug(content)
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(spiders_directory)
    os.system('pwd')
    pnr = content.get('trip_ref', '')
    output_file = 'indigo_%s_%s.json'%(pnr, get_current_ts_with_ms())
    run_cmd = 'scrapy crawl indigobooking_browse -a jsons="%s"' % (content)
    try:
        os.system(run_cmd)
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
			'101': 'IndiGo Booking Scraper Login Failed',
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
    if db_data:
        if tax_detais:
            for key, vals_ in tax_detais.iteritems():
		print key, vals_
		pcc = vals_['pcc']
                key = key.replace(' ', '')
                dict_, log_, sec_dict, sec_log_ = {}, {}, {}, {}
                seg = vals_.get('seg', '')
                total_price = vals_.get('total', '')
                del vals_['seg']
                del vals_['total']
                del vals_['pcc']
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
                dict_.update({"pcc": pcc, "amount":str(total_price), "flight_no": [key.strip()],
                        "errorMessage": data[15], "errorCode": error_code, "departDate": departdate,
                        "pnrCaptured":data[3], "pricingDetails": vals_, "segments":[seg],
                        "trip_id": content.get('trip_ref', ''), 'TotalFare':data[10]})
                #log_.update({"pcc": pcc, "flight_no": key.strip(), "actualPrice":data[10], 'custPaidPrice':data[9]})
		try:
			cust_paid_price = content['all_segments'][0][pcc]['amount']
		except:
			cust_paid_price = content['all_segments'][1][pcc]['amount']
                log_.update({"pcc": pcc, "flight_no": key.strip(), "actualPrice": str(total_price), 'custPaidPrice': str(cust_paid_price)})

                rslt.append(dict_)
                logs_.append(log_)
                second_key = second_key.replace(' ', '')
                if second_key:
                    second_key = re.sub(second_key[1],second_key[1] + ' ', second_key)
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
    create_at, modified_at = data[18], data[19]
    if not create_at:
        create_at, modified_at = datetime.datetime.now(), datetime.datetime.now()
    book_fin_dict.update({'result':rslt, 'logReport':logs_, 'created_at': create_at,'modified_at':modified_at})
    logging.debug(book_fin_dict)
    cursor.close()
    con.close()
    print book_fin_dict
    return jsonify(book_fin_dict)

@app.route('/indigo/webcheckin', methods=['GET', 'POST'])
def add_indigo_webcheckin():
    book_query = 'select * from indigo_webcheckin_status where sk = "%s"'
    return
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
    create_logger_obj('indigo_webcheckin')
    os.system('source /root/cleartrip/bin/activate')
    os.chdir(spiders_directory)
    os.system('pwd')
    pnr = content.get('pnr', '')
    run_cmd = 'scrapy crawl indiocheckin_browse -a jsons="%s"' % (content)
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
    return jsonify(webcheckin_dict)		
	

def get_current_ts_with_ms():
    dt = datetime.datetime.now().strftime("%Y%m%dT%H%M%S%f")
    return str(dt)

def create_cursor(db_name):
    try:
            conn = MySQLdb.connect(user='root',host='localhost', db=db_name, passwd='')
            conn.set_character_set('utf8')
            cursor = conn.cursor()
            cursor.execute('SET NAMES utf8;')
            cursor.execute('SET CHARACTER SET utf8;')
            cursor.execute('SET character_set_connection=utf8;')
    except:
            import traceback; print traceback.format_exc()
            sys.exit(-1)

    return conn, cursor


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
