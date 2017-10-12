import MySQLdb
import csv
import os
import datetime

user = 'root' # your username
passwd = '' # your password
host = 'localhost' # your host
db = 'MMCTRP' # database where your table is stored

con = MySQLdb.connect(user=user, host=host, db=db)
cursor = con.cursor()



fields = ['City', 'CT Hotel Name', 'GO Hotel Name', 'CT HotelId', 'GO HotelId', 'Check-in', 'DX', 'LOS', 'CT Pax', 'GO RoomType', 'CT RoomType', 'GO Rate', 'CT Rate','B2C Diff', 'GO Inclusions', 'CT Inclusions', 'GO App Rate', 'CT App Rate', 'Mobile Diff', 'Offer', 'Created On', 
'GOIB GST Included', 'GO Coupon code', 'GO Coupon Description' , 'GO Coupon Discount Amount']

try:
    query = 'SELECT g.city,g.gbthotelname,c.ctthotelname,c.ctthotelid,g.gbthotelid,g.check_in,g.dx,g.los,c.pax,g.gbtroomtype,c.cttroomtype,'
    query+= 'g.gbtrate,c.cttrate,(CAST(g.b2cdiff as Decimal(6,1)) - CAST(c.b2cdiff as Decimal(6,1))) as b2cdiff,'
    query+= 'g.gbtinclusions,c.cttinclusions,g.gbtapprate,c.cttapprate,g.mobilediff,g.gbtcoupon_discount,g.created_on,g.gbtgst_included, g.gbtcoupon_code, g.gbtcoupon_description, g.gbtcoupon_discount'
    query+= ' from Goibibotrip g,Cleartrip c where g.gbthotelname=c.ctthotelname and g.check_in=c.check_in and g.check_out=c.check_out'
    query+= ' and g.dx=c.dx and g.los=c.los and g.pax=c.pax and c.city=g.city;'
    cursor.execute(query)
    
    CSV_PATH="/NFS/data/HOTELS_SCRAPED_DATA/GOIBIBO/"
    mydir = os.path.join(CSV_PATH, datetime.datetime.now().strftime('%Y/%m/%d'))
    os.makedirs(mydir)
  
    #filename = "/NFS/data/HOTELS_SCRAPED_DATA/MMT/%s/GOBCT.csv"%s(os.makedirs(datetime.datetime.today().strftime("%Y/%m/%d")))
    
    filename = "GOIBIBO.csv"
    sql_data = cursor.fetchall()
    with open(os.path.join(mydir, filename), 'w+') as csvfile:
	csvwriter = csv.writer(csvfile)
	csvwriter.writerow(fields)
	for sql_data1 in sql_data:
		sql_data1=list(sql_data1)
		if (sql_data1[11]=="Sold Out") or (sql_data1[12]=='NR'):
			for n,i in enumerate(sql_data1):
				if n==13:
					sql_data1[n]="N/A"
		sql_data1=tuple(sql_data1)
		csvwriter.writerow(sql_data1)
    cursor.close()
    con.close()
except Exception, e:
    print str(e)
