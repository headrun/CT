
import MySQLdb
from xlsxwriter.workbook import Workbook
import csv

user = 'root' # your username
passwd = '' # your password
host = 'localhost' # your host
db = 'MMCTRP' # database where your table is stored

con = MySQLdb.connect(user=user, host=host, db=db)
cursor = con.cursor()
try:
    query = 'SELECT m.city,m.mmthotelname,c.ctthotelname,c.ctthotelid,m.mmthotelid,m.check_in,m.dx,m.los,c.pax,m.mmtroomtype,c.cttroomtype,'
    query+= 'm.mmtrate,c.cttrate,(CAST(m.b2cdiff as SIGNED) - CAST(c.b2cdiff as SIGNED))as b2cdiff,m.mmtinclusions,c.cttinclusions,m.mmtapprate,'
    query+= 'c.cttapprate,m.mobilediff,c.ctt_b2c_splashed_price,m.mmt_b2c_splashed_price,c.ctt_app_splashed_price,m.mmt_app_splashed_price,'
    query+= 'c.cttb2ctaxes,m.mmtb2ctaxes,c.ctt_apptaxes,m.mmt_apptaxes,c.rmtc,c.created_on,c.child,m.mmtcoupon_code,m.mmtcoupon_description,m.mmtcoupon_discount,m.mmtgst_included,m.mmttotalamt_aftergst'

    query+= ' from Makemytrip m,Cleartrip c where m.mmthotelname=c.ctthotelname and m.check_in=c.check_in and m.check_out=c.check_out and m.dx=c.dx'
    query+= ' and m.los=c.los and m.pax = c.pax;'

    '''
    query = 'SELECT m.city,m.mmthotelname,c.ctthotelname,m.mmthotelid,c.ctthotelid,m.check_in,m.mmtrate,c.cttrate,m.b2cdiff,c.b2cdiff,'
    query+= 'm.mmtinclusions,c.cttinclusions,m.dx,m.los,m.pax,c.pax,m.mmtroomtype,c.cttroomtype,m.mmtapprate,c.cttapprate,m.mobilediff,'
    query+= 'c.mobilediff,m.rmtc,c.rmtc,m.child,m.mmt_b2c_splashed_price,c.ctt_b2c_splashed_price,m.mmt_app_splashed_price,c.ctt_app_splashed_price,'
    query+= 'm.mmtb2ctaxes,c.cttb2ctaxes,m.mmt_apptaxes,c.ctt_apptaxes,m.mmtcoupon_code,c.cttcoupon_code,m.mmtcoupon_description,c.cttcoupon_description,'
    query+= 'm.mmt_amount,c.ctt_amount,m.created_on FROM MMTRIP m, CLEARTRIP c WHERE m.city = c.city and m.mmthotelname =c.ctthotelname, m.check_in = c.check_in'


    

    query = 'SELECT m.city,m.mmthotelname,m.mmthotelid,m.check_in,m.mmtrate,m.b2cdiff,m.mmtinclusions,m.dx,m.los,m.pax,m.mmtroomtype,'
    query+='m.mmtapprate,m.mobilediff,m.rmtc,m.child,m.mmt_b2c_splashed_price,m.mmt_app_splashed_price,m.mmtb2ctaxes,m.mmt_apptaxes,'
    query+='m.mmtcoupon_code,m.mmtcoupon_description,m.mmt_amount,c.ctthotelid,c.cttrate,'
    query+='c.b2cdiff,c.cttinclusions,c.pax,c.cttroomtype,c.cttapprate,c.mobilediff,c.rmtc,c.ctt_b2c_splashed_price,'
    query+='c.ctt_app_splashed_price,c.cttb2ctaxes,c.ctt_apptaxes,c.cttcoupon_code,c.cttcoupon_description,c.ctt_amount,m.created_on '
    query+='FROM MMTRIP m, CLEARTRIP c WHERE m.city = c.city;'
    '''
    cursor.execute(query)
    workbook = Workbook('MMCTRP.xlsx')
    worksheet = workbook.add_worksheet('MMTCLEAR')
    bold = workbook.add_format({'bold':True})
    date_format = workbook.add_format({'num_format':'dd/mm/YYY %T'})
    worksheet.write('A1','City',bold)
    worksheet.write('B1','CT Hotel Name',bold)
    worksheet.write('C1','MMT Hotel Name',bold)
    worksheet.write('D1','CT HotelId',bold)
    worksheet.write('E1','MMT HotelId',bold)
    worksheet.write('F1','Check-in',bold)
    worksheet.write('G1','DX',bold)
    worksheet.write('H1','LOS',bold)
    worksheet.write('I1','CT Pax',bold)
    worksheet.write('J1','MMT RoomType',bold)
    worksheet.write('K1','CT RoomType',bold)
    worksheet.write('L1','MMT Rate',bold)
    worksheet.write('M1','CT Rate',bold)
    worksheet.write('N1','B2C Diff',bold)
    worksheet.write('O1','MMT Inclusions',bold)
    worksheet.write('P1','CT Inclusions',bold)
    worksheet.write('Q1','MMT App Rate',bold)
    worksheet.write('R1','CT App Rate',bold)
    worksheet.write('S1','Mobile Diff',bold)
    worksheet.write('T1','CT_B2C_Slashed Price',bold)
    worksheet.write('U1','MMT_B2C_Slashed Price',bold)
    worksheet.write('V1','CT_APP_Slashed Price',bold)
    worksheet.write('W1','MMT_APP_Slashed Price',bold)
    worksheet.write('X1','CT B2C Taxes',bold)
    worksheet.write('Y1','MMT B2C Taxes',bold)
    worksheet.write('Z1','CT App Taxes',bold)

    worksheet.write('AA1','MMT App Taxes',bold)
    worksheet.write('AB1','RMTC',bold)
    worksheet.write('AC1','Created On',bold)
    worksheet.write('AD1','Child',bold)
    worksheet.write('AE1','MMT Coupon Code',bold)
    worksheet.write('AF1','Coupon Description',bold)
    worksheet.write('AG1','Coupon Discount Amount',bold)
    
    worksheet.write('AH1','GST Included',bold)
    worksheet.write('AI1','Total Amt After GST',bold)
    sql_data = cursor.fetchall()
    i=2
    
    for row in sql_data:
        worksheet.write_string('A'+str(i),row[0])

        worksheet.write_string('B'+str(i),row[1])
        worksheet.write_string('C'+str(i),row[2])
        worksheet.write_string('D'+str(i),str(row[3]))
        worksheet.write_string('E'+str(i),str(row[4]))

        worksheet.write_string('F'+str(i),str(row[5]))
        worksheet.write_string('G'+str(i),str(row[6]))
        worksheet.write_string('H'+str(i),str(row[7]))
        
        worksheet.write_string('I'+str(i),str(row[8]))

        worksheet.write_string('J'+str(i),str(row[9]))
        worksheet.write_string('K'+str(i),str(row[10]))
        worksheet.write_string('L'+str(i),str(row[11]))
        worksheet.write_string('M'+str(i),str(row[12]))
        worksheet.write_string('N'+str(i),str(row[13]))
        worksheet.write_string('O'+str(i),str(row[14]))

        worksheet.write_string('P'+str(i),str(row[15]))
        worksheet.write_string('Q'+str(i),str(row[16]))
        worksheet.write_string('R'+str(i),str(row[17]))
        worksheet.write_string('S'+str(i),str(row[18]))
        worksheet.write_string('T'+str(i),str(row[19]))
        worksheet.write_string('U'+str(i),str(row[20]))
        worksheet.write_string('V'+str(i),str(row[21]))
        worksheet.write_string('W'+str(i),str(row[22]))
        worksheet.write_string('X'+str(i),str(row[23]))
        worksheet.write_string('Y'+str(i),str(row[24]))
        worksheet.write_string('Z'+str(i),str(row[25]))
        worksheet.write_string('AA'+str(i),str(row[26]))

        worksheet.write_string('AB'+str(i),str(row[27]))

        worksheet.write_string('AC'+str(i),str(row[28]))
    
        worksheet.write_string('AD'+str(i),str(row[29]))
        worksheet.write_string('AE'+str(i),str(row[30]))
        worksheet.write_string('AF'+str(i),str(row[31]))
        worksheet.write_string('AG'+str(i),str(row[32]))

        worksheet.write_string('AH'+str(i),str(row[33]))
        worksheet.write_string('AI'+str(i),str(row[34]))
          
        
        
        
        i=i+1
        
                
    workbook.close()
    cursor.close()
    con.close()

except Exception, e:
    print str(e)

