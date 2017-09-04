import os
import sys
import MySQLdb
import traceback
import datetime
from flask import Flask, render_template, request, jsonify
import subprocess# import STDOUT, check_output
import json

app = Flask(__name__)
spiders_directory = '/root/headrun/airasia/airasia/spiders'
select_query = 'select * from cancellation_report where sk="%s"'
error_query = 'select * from error_report where pnr="%s"'

@app.route("/")
def welcome():
    return "Hello World!"

@app.route('/api', methods=['GET', 'POST'])
def add_message():
    '''
    try:
        content = request.get_json(silent=True)
    except:
	content = {}
    '''
    content = {"origin": "DEL", "flightid": "I5-779", "cancellationdetails": {"return": {"infants": ["Mstr. Madhav Rai"], "audlt": ["Mr. Rajat Rai", "Mrs. Radhika Rai"], "children": []}, "oneway": {"infants": ["Mstr. Madhav Rai"], "audlt": ["Mrs. Radhika Rai", "Mr. Rajat Rai"], "children": []}}, "pnr": "VMKY4D", "tripid": "17073034354", "cancellationdatetime": "2017-08-28 10:30:00", "paxdetails": {"return": {"infants": ["Mstr. Madhav Rai"], "audlt": ["Mr. Rajat Rai", "Mrs. Prapanna Khanna ", "Mr. Bhanu Gora", "Mrs. Hinshu kaur Bedi", "Ms. Manika Khanna", "Mrs. Radhika Rai", "Mr. Paras Khanna "], "children": []}, "oneway": {"Infants": ["Mstr. Madhav Rai"], "audlt": ["Mr. Rajat Rai", "Mrs. Prapanna Khanna ", "Mr. Bhanu Gora", "Mrs. Hinshu kaur Bedi", "Ms. Manika Khanna", "Mrs. Radhika Rai", "Mr. Paras Khanna "], "children": []}}, "destination": "GOI", "contactdetails": {"MobilePhone": "", "Email": ""}, "airline": "Air Asia", "paxtype": "", "departuredatetime": "2017-09-09 05:10:00", "trip_type":"", "via":""}	
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
    con, cursor = create_cursor()
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
    return jsonify(result_dict)

def get_current_ts_with_ms():
    dt = datetime.datetime.now().strftime("%Y%m%dT%H%M%S%f")
    return str(dt)

def create_cursor():
    try:
            conn = MySQLdb.connect(user='root',host='localhost', db='TICKETCANCELLATION', passwd='')
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
