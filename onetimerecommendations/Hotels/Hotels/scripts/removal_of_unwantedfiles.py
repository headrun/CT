import datetime
import commands
import os

def main():
    range_start = 0
    processed_paths = [os.path.join(os.path.dirname(os.getcwd()), 'spiders/OUTPUT/processed'), '/root/hotels_prod/Hotels/spiders/OUTPUT/processed', '/root/hotels/HOTELS/Hotels/Hotels/logs', '/root/hotels_prod/Hotels/logs']
    for processed_path in processed_paths:
	    if '/logs' in processed_path:
		range_start = 2
	    os.chdir(processed_path)
	    for i in range(range_start, 10):
		delete_date = datetime.datetime.now() + datetime.timedelta(days=-i)
		date_del = str(delete_date.date()).replace('-', '')
		if '/logs' in processed_path:
			date_del = str(delete_date.date())
		data_cmd = 'ls *%s*'%date_del
		status, data_lst = commands.getstatusoutput(data_cmd)
		if "No such file or director" not in data_lst:
			for f_ in data_lst.split('\n'):
			    if f_.endswith('.queries') or f_.endswith('.log'):
				    os.system('rm %s'%f_)
				    print f_
		else:   
			print 'no files'

if __name__ == '__main__':
   main()

