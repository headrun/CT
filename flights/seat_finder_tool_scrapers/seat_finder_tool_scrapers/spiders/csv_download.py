import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import datetime
import codecs
import sys,getopt
import os
from ConfigParser import SafeConfigParser
from seat_finder_common_utils import *
_cfg = SafeConfigParser()
_cfg.read('../../../seat_finder_names.cfg')

class CsvDownload:
    def main(self,argv):
        date_minus = 0
        current_path = os.getcwd()
        path_to_save = ''
        opts, args = getopt.getopt(argv,"d:s:",["-d=","-s"])
        sources_handled = ['GOAIR','INDIGO','SPICEJET','AIRASIA']
        if opts:
            for opt, arg in opts:
                if opt=='-d':
                    date_minus = arg
                elif opt=='-s':
                    source = arg
                    source_upper = source.upper()
                    if source_upper in sources_handled:
                        path_to_save=current_path+'/'+source_upper+'_CSV'+'/yet_to_process/'
                    else:
                        print "New carrier is given as an option: Add the carrier in the sources_handled_list"
                        return
                else:
                    print "Wrong Option variable given. Use only -d and -s. Option given are %s"%(opt)
                    return
        else:
            print "No Options Given"
            return

        if not os.path.exists(path_to_save):
            os.makedirs(path_to_save)
        else:
            pass

        print "DateCheck:%s, Carrier:%s"%(str(date_minus),source)
        csv_datecheck = datetime.date.today()+ datetime.timedelta(int(date_minus))
        csv_date = csv_datecheck.strftime('%d-%b-%Y')
        try:
            user_name = _cfg.get('summary_login_credentials','login_name')
            password = _cfg.get('summary_login_credentials','login_pwd')
        except:
            print "No credentials found in cfg file"
            return
        try:
            main_response = requests.get('http://summary.cleartrip.com/mis_reports/%s'%csv_date, auth=HTTPBasicAuth(user_name,password))
        except:
            print "Not able to access http://summary.cleartrip.com/mis_reports/"
            return
        if main_response.status_code==200:
            soup = BeautifulSoup(main_response.content,'html5lib')
            links = soup.findAll('a')
            csv_links = [main_response.url+ link['href'] for link in links if link['href'].startswith('Travel_Check_air') if link['href'].endswith('csv')]
            csv_link =  csv_links[0]
            if not csv_link:
                print "No CSV for the checked date:%s"%csv_date
                self.send_mail('No CSV','No csv found on %s'%csv_date)
            else:
                print "csv: %s"%csv_link
                response = requests.get(csv_link, auth=HTTPBasicAuth(user_name, password))
                if response.status_code==200:
                    output_name = csv_link.split('/')[-1]
                    path_file = path_to_save +output_name
                    file_ = codecs.open(path_file,"w", "utf-8")
                    file_.write(response.text)
                    file_.close()
                    print "Downloaded"
                else:
                    print "Unable to download CSV. Response status is %s"%response.status_code
                    return
        else:
            print "Unable to login to mis_reports. Response Status is %s"%main_response.status_code
            return
if __name__=="__main__":
    print "Note:-s Option should be among indigo,goair,spicjet and airasia"
    CsvDownload().main(sys.argv[1:])
