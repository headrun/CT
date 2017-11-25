import datetime
import commands
import os

def main():
    processed_path = os.path.join(os.path.dirname(os.getcwd()), 'spiders/OUTPUT/processed')
    os.chdir(processed_path)
    delete_date = datetime.datetime.now() + datetime.timedelta(days=-2)
    date_del = str(delete_date.date()).replace('-', '')
    data_cmd = 'ls *%s*'%date_del
    status, data_lst = commands.getstatusoutput(data_cmd)
    for f_ in data_lst.split('\n'):
	os.system('rm %s'%f_)

if __name__ == '__main__':
   main()
