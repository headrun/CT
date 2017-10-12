import json


d,cd='',''
dict_={}
with open('goMasterList.json') as json_data:
	d = json.load(json_data)
with open('cities_statesgoib.json') as json_data3:
	cd = json.load(json_data3)

import pdb;pdb.set_trace()
mmtid,cltpname='',''
for city_name, hotels in d.iteritems():
	city_code= cd.get(city_name,'')
	print city_name,city_code
	import pdb;pdb.set_trace()
	d_={}
	for hotel,details in hotels.iteritems():
		goid = details.get('goid','')
                cltpname = details.get('cltpname','')
		print goid,cltpname
		d_[goid] = [cltpname,city_code]
		dict_[city_name]=d_
		with open('GoiboCity_codes.json','w') as ftp:
			json.dump(dict_,ftp)

