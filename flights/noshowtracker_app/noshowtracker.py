from math import ceil
from werkzeug import secure_filename
import ast
from flask import Flask,render_template,redirect,jsonify,flash
from flask import request
import MySQLdb
import json
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

app = Flask(__name__)
app.secret_key = '_5#y2L"F4Q8z\n\xec]/'
application = app
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@app.route("/noshowtracker/",methods=('GET','POST'))
def seatfinder():
    main_list = []
    conn = MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'root', db = 'SEATFINDERDB', charset="utf8", use_unicode=True)
    cur = conn.cursor()
    cur.execute('select sk,airline,pnr,pcc,ticket_number,status,remarks,request_input from seat_finder where aux_info="" and status="closed"  and airline!="SpiceJet" order by airline,created_at;')
    rows = cur.fetchall()
    print "db rows:%s"%len(rows)

    cur.execute('select sk,agent, airline,pnr,pcc,ticket_number,status,remarks,booking_date,travelling_date,final_status from agent_called where final_status ="Pending" order by airline,created_at;')
    pending_rows = cur.fetchall()
    print "pending_rows:%s"%len(pending_rows)
    for pending_row in pending_rows:
	booking_no,agent_name,airline,pnr,pcc,ticket_number,status,remarks,booking_date,departure_date,calling_status= pending_row
	new_pending_row = [booking_no,airline,pnr,pcc,ticket_number,status,remarks,booking_date,departure_date,agent_name,calling_status]
	main_list.append(new_pending_row)

    search_date = request.form.to_dict().get('date','') 
    amount_new_value = request.form.to_dict().get('amount_value','')
    whole_row = request.form.to_dict().get('delete',[])
    genyses_new_ext = request.form.to_dict().get('genyses_ext_number','')
    trip_status = request.form.to_dict().get('trip_status_list','')
    calling_new_status = request.form.to_dict().get('calling_status_list','')
    total_rows = rows#+pending_rows
    whole_row = ast.literal_eval(str(whole_row))
    if whole_row:
	whole_row = [x.strip() for x in whole_row]
	booking_no_html , airline_html , pnr_html ,  pcc_html , ticket_number_html ,  status_html , remarks_html , booking_date_html , departure_date_html, agent_name_html,calling_name_html = whole_row
	print pnr_html
    else:
	calling_name_html=''
  
    if calling_new_status=='Pending' and calling_name_html=='Pending':
	total_rows = rows+pending_rows
    elif calling_new_status!='Pending' and calling_name_html!='' and calling_name_html=='Pending':
	total_rows = rows+pending_rows


    print "total rows: %s" %len(total_rows)
    agent_new_name = request.form.to_dict().get('agent_list','')
    find_list = []
    for row in total_rows:
	if len(row)==8:
		booking_no,airline,pnr,pcc,ticket_number,status,remarks,request_input = row
		booking_date = json.loads(request_input)['transaction_date']
        	departure_date = json.loads(request_input)['departure_date']

	elif len(row)==11:
		booking_no, agent_name,airline,pnr,pcc,ticket_number,status,remarks,booking_date,departure_date,calling_status = row

	sk=booking_no
	if request.method=='POST' and calling_new_status:
		whole_row = ast.literal_eval(str(whole_row))
		whole_row = [x.strip() for x in whole_row]
		booking_no_html , airline_html , pnr_html ,  pcc_html , ticket_number_html ,  status_html , remarks_html , booking_date_html , departure_date_html, agent_name_html,calling_name_html = whole_row
		if pnr==pnr_html:
			find_list.append('Yes')
			print "got some input from user: %s"%pnr
			aux_info = str({'status':'action performed - %s'%calling_new_status})
                        update_query = 'update seat_finder set aux_info="%s" where pnr="%s" and airline="%s" and ticket_number="%s";'%(aux_info,pnr,airline,ticket_number)
			cur.execute(update_query)

			insert_query = 'insert into agent_called(sk,agent,airline,pnr,pcc,ticket_number, status,remarks,booking_date,travelling_date,amount,final_status,genyses_extension_number,created_at,modified_at) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), pnr=%s, ticket_number=%s,amount=%s,final_status=%s,genyses_extension_number=%s'
                        vals = (str(sk),str(agent_new_name),str(airline),str(pnr),str(pcc),str(ticket_number),str(status), str(remarks),str(booking_date),str(departure_date),str(amount_new_value),str(calling_new_status), str(genyses_new_ext),str(pnr),str(ticket_number),str(amount_new_value),str(calling_new_status),str(genyses_new_ext))
			print vals
			try:
				cur.execute(insert_query, vals)
        		except Exception as e:
                		print 'some insert error'
        		conn.commit()
			return redirect("/noshowtracker/")
			
	elif request.method=='GET':
	    agent_name =''
	    calling_status=''
	    new_row = [booking_no,airline,pnr,pcc,ticket_number,status,remarks,booking_date,departure_date,agent_name,calling_status]
	    main_list.append(new_row)
	   
  
    if len(find_list)==0 and request.method=='POST':
	flash('Submitted PNR is already processed')
	return redirect("/noshowtracker/")

    print len(main_list)
    return render_template('noshowtracker.html',records=main_list)
    cur.close()
    conn.close()


@app.route("/noshowtracker/upload_csv",methods=('GET','POST'))
def upload_csv():
   if request.method=='POST':
	file_ = request.files.to_dict().get('fileupload','')
	if file_:
		filename = file_.filename
		file_.save('csv/%s'%filename)
		file_with_path = 'csv/%s'%filename
		import csv
		import codecs
		with codecs.open(file_with_path,'r',encoding='utf-8', errors='ignore') as csvfile:
			plots=csv.reader(csvfile,delimiter=',')
                        first_row = plots.next()
			for row in plots:
				total_refund_amount,pnr = '',''
				#if 'pnr' not in row and 'PNR' not in row and 'Reference' not in row:
				if row!=first_row:
					if 'AIRASIA' in filename.upper() and len(row)==4:
						print 'yes'
						date, pnr, total_refund_amount, rem = row
					elif 'GOAIR' in filename.upper() and len(row)==9:
						Row,deposit_date,date,type_,detail,total_refund_amount,currency,reference,status_type=  row
						pnr = reference
					elif 'INDIGO' in filename.upper() and len(row)==8:
						Trans_Date, pnr, Pax_Name,Nbr_of_Pax,Arc_Iata,Payment_Nbr,Type_Code,total_refund_amount = row
					elif 'SPICEJET' in filename.upper():
						pnr = row[1]
						total_refund_amount =  row[4]
					else:   
						flash('Please check if the proper sheet is uploaded')
						return redirect("/noshowtracker/upload_csv")
					total_refund_amount = total_refund_amount.strip('-')
					transaction_id =''
					airline = filename.split('_')[1].split('Report')[0]
					conn = MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'root', db = 'SEATFINDERDB', charset="utf8", use_unicode=True)
					cur = conn.cursor()
					insert_query = 'insert into finance_uploads(pnr,airline,status,total_refund_amount,created_at,modified_at) values(%s,%s,%s,%s,now(),now()) on duplicate key update modified_at=now(), pnr=%s,airline=%s,total_refund_amount=%s'
					vals = (str(pnr),str(airline),'',str(total_refund_amount),str(pnr),str(airline),str(total_refund_amount))
					try:
						cur.execute(insert_query, vals)
					except Exception as e:
						print e			
						print 'some insert error'
					conn.commit()

		flash('%s uploaded successfully'%filename)
                return redirect("/noshowtracker/upload_csv")
	else:
		flash('Upload a file before submitting')
		return redirect("/noshowtracker/upload_csv")
   return render_template('finance_upload_csv.html') 


if __name__ == "__main__":
    app.run(debug = True, host = '0.0.0.0')
    #app.run(debug = True, host = '0.0.0.0',port=5005)
