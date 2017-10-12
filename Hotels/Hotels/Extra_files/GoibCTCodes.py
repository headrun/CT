import json
from scrapy.spiders import Spider
from scrapy.selector import Selector
from scrapy.http import Request
import datetime
import urllib


class ClearStates(Spider):
	name ='goibstates'
	allowed_domains=['voyager.goibibo.com']
	

	def __init__(self,*args,**kwargs):
		super(ClearStates,self).__init__(*args,**kwargs)
		self.dict_={}
		self.missing_=[]
	

	def start_requests(self):
  		d=''
		with open('goMasterList.json') as states_data:
			d = json.load(states_data)
		lists_ = d.keys()
		
		
		lists_node = lists_[-1]
		for list_ in lists_:
			if list_==lists_node:
				stop=True
			else:
				stop=False
			city_name=list_.lower()

			form ={"search_query":city_name,"limit":10,"qt":"N","inc_ggl_res":"true"}
			data= json.dumps(form)
			links ='https://voyager.goibibo.com/api/v1/hotels_search/find_node_by_name/?params=%s'%(data)
			yield Request(links, callback = self.parse_states, meta={'city_name':list_,'stop':stop})
	

	def parse_states(self,response):
		data = json.loads(response.body)
		
		city_name= response.meta.get('city_name','')
		try:
			
			state =data['data']['r'][0]['_id']
			print city_name,state

			self.dict_[city_name]=state

			print self.dict_

		except:
			self.missing_.append(city_name)
		if response.meta['stop']==True:
			with open('cities_statesgoib.json','w') as city_status:
				json.dump(self.dict_, city_status)
				





