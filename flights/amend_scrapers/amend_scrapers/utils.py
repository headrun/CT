import sys
import os
import re
import time
import asyncore
import MySQLdb
import datetime
import logging

import ast
from collections import Counter
from ConfigParser import SafeConfigParser
import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import smtplib
from operator import itemgetter


_cfg = SafeConfigParser()
_cfg.read('airline_names.cfg')
'''
def send_mail(source, sub, error_msg=''):
        recievers_list = []
        if 'Login' in sub:
            recievers_list = ast.literal_eval(_cfg.get('amend_common', 'login_recievers_list'))
            import way2sms
            obj = way2sms.sms('9442843049', 'bhava')
            phones = ast.literal_eval(_cfg.get('amend_common', 'phones'))
            for i in phones:
                sent = obj.send(i, 'Unable to login to %s,Please check'%source)
                if sent:
                    print 'Sent sms successfully'
        recievers_list = ast.literal_eval(_cfg.get('amend_common', 'recievers_list'))
        sender, receivers = 'prasadk@notemonk.com', ','.join(recievers_list)
        ccing = []
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Amend QA TEST %s : %s On %s'%(source, sub, str(datetime.datetime.now().date()))
        mas = '<p>%s</p>' % error_msg
        msg['From'] = sender
        msg['To'] = receivers
        msg['Cc'] = ','.join(ccing)
        tem = MIMEText(''.join(mas), 'html')
        msg.attach(tem)
        s = smtplib.SMTP('smtp.gmail.com:587')
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(sender, 'amma@nanna')
        s.sendmail(sender, (recievers_list + ccing), msg.as_string())
        s.quit()
'''
def textify(nodes, sep=' '):
    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]

    def _t(x):
        if isinstance(x, (str, unicode)):
            return [x]

        if hasattr(x, 'xmlNode'):
            if not x.xmlNode.get_type() == 'element':
                return [x.extract()]
        else:
            if isinstance(x.root, (str, unicode)):
                return [x.root]

        return (n.extract() for n in x.select('.//text()'))

    nodes = chain(*(_t(node) for node in nodes))
    nodes = (node.strip() for node in nodes if node.strip())

    return sep.join(nodes)

def xcode(text, encoding='utf8', mode='strict'):
    return text.encode(encoding, mode) if isinstance(text, unicode) else text


def compact(text, level=0):
    if text is None: return ''

    if level == 0:
        text = text.replace("\n", " ")
        text = text.replace("\r", " ")

    compacted = re.sub("\s\s(?m)", " ", text)
    if compacted != text:
        compacted = compact(compacted, level+1)

    return compacted.strip()

def clean(text):
    if not text: return text

    value = text
    value = re.sub("&amp;", "&", value)
    value = re.sub("&lt;", "<", value)
    value = re.sub("&gt;", ">", value)
    value = re.sub("&quot;", '"', value)
    value = re.sub("&apos;", "'", value)

    return value

def normalize(text):
    return clean(compact(xcode(text)))

def get_compact_traceback(e=''):
    except_list = [asyncore.compact_traceback()]
    return "Error: %s Traceback: %s" % (str(e), str(except_list))

def create_logger_obj(source):
    cur_dt = str(datetime.datetime.now().date())
    LOGS_DIR = os.path.join(os.path.dirname(os.getcwd()), 'logs') 
    log_file_name = "spider_%s_%s.log" % (source, cur_dt)
    log = initialize_logger(os.path.join(LOGS_DIR, log_file_name))
    return log

def initialize_logger(file_name, log_level_list=[]):
    logger = logging.getLogger()
    try:
        add_logger_handler(logger, file_name, log_level_list)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        e = sys.exc_info()[2]
        time_str = time.strftime("%Y%m%dT%H%M%S", time.localtime())
        exception_str = "%s: %s: Exception: %s" % (time_str, sys.argv, get_compact_traceback(e))
        #print exception_str

    return logger


def add_logger_handler(logger, file_name, log_level_list=[]):
    success_cnt, handler = 3, None

    for i in xrange(success_cnt):
        try:
            handler = logging.FileHandler(file_name)
            break
        except (KeyboardInterrupt, SystemExit):
            raise
        except: pass

    if not handler: return

    formatter = logging.Formatter('%(asctime)s.%(msecs)d: %(filename)s: %(lineno)d: %(funcName)s: %(levelname)s: %(message)s', "%Y%m%d%H%M%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    set_logger_log_level(logger, log_level_list)

    if handler.stream:
        set_close_on_exec(handler.stream)
