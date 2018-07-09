Setup explanations:

1/ Clone this project to a Ubuntu machine and do the following.

Server Installation setup: (Ubuntu)


Pip Install:
curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
python get-pip.py

apt-get install python

sudo apt-get install python-pip python-dev build-essential 

sudo pip install Scrapy==1.4.0

sudo apt-get install mysql-server


CREATE USER 'scraper'@'localhost' IDENTIFIED BY 'scr4book';
GRANT ALL PRIVILEGES ON * . * TO 'scraper'@'localhost';
FLUSH PRIVILEGES;


apt-get install python-dev libmysqlclient-dev
pip install Flask=0.12.0
pip install uWSGI==2.0.15

apt-get install nginx

pip install MySQL-python

uwsgi -s /tmp/uwsgi_airasia_flask.sock -w expose_api_service:app -C666 -p 16

Machine setup done.

2/ Add a conf file inside the /etc/nginx/sites-enabled folder. [airasia.conf file inside api_service repository in this project needs to be added]
3/ Once the above is done, scrapper machine is ready. 