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
spiders_directory = '/root/headrun/airasia/airasia/spiders'
select_query = 'select * from cancellation_report where sk="%s"'
error_query = 'select * from error_report where pnr="%s"'

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
    os.chdir(spiders_directory)
    os.system('pwd')
    pnr = content.get('pnr', '')
    output_file = 'airasia_%s_%s.json'%(pnr, get_current_ts_with_ms())
    run_cmd = 'scrapy crawl airasia_browse -a jsons="%s"' % (content)
    try:
        os.system(run_cmd)
    except:
        print traceback.format_exc()
    fin_data_dict, error_dict = {}, {}
    con, cursor = create_cursor('TICKETCANCELLATION')
    cursor.execute(select_query%pnr)
    db_deta = cursor.fetchall()
    cursor.execute(error_query%pnr)
    error_data = cursor.fetchall()
    errors_lst = []
    if error_data:
        for err_ in error_data:
            err = err_[3]
            if err:   
                errors_lst.append(err)
    result_dict = {}
    if db_deta:
	data = db_deta[0]
	if data:
	    result_dict.update({'pnr':data[0],
				'airline':data[1],
				'cancellation_message':data[2],
				'cancellation_status':data[3],
				'destination':data[4],
                                'flight_id':data[5],
                                'manual_refund_queue':data[6],
                                'origin':data[8],
                                'pax_name':data[9],
                                'payment_status':data[10],
                                'cancellation_status_message':data[11],
                                'past_dated_booking':data[12],
                                'refund_computation_queue':data[13],
                                'tripid':data[14],
				'error': data[15],
                                'created_at':str(data[16]),
                                'modified_at':str(data[17])
				})
    else:
	result_dict.update({'pnr':pnr,
			    'airline': 'airasia',
			    'error':errors_lst,
			    'created_at':str(datetime.datetime.now()),
			    'modified_at':str(datetime.datetime.now())
			   })
    logging.debug(result_dict)
    cursor.close()
    con.close()
    return jsonify(result_dict)

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
			'005':'Itinerary exixts',
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
