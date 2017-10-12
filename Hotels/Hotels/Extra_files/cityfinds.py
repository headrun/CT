
import json

'''
with open('cities_statesgoib.json') as states_data:
	d = json.loads(states_data)
        lists_ = d.keys()
	print lists_
	
	valueslist_ = d.values()
	import pdb;pdb.set_trace()
	for keys,values in zip(lists_,valueslist_):
		print keys,values
                '''

	
with open('cities_statesgoib.json') as states_data:
	d = json.load(states_data)
	import pdb;pdb.set_trace()
	for city_name,hotel_details in self.d.iteritems():
		city_name=city_name
		
		for hotel_id,hotel_data in hotel_details.iteritems():
			hotel_id=hotel_id
			hotel_name=hotel_data[0]
			city_code=hotel_data[1]

