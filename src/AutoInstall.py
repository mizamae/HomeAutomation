import os
import sys
from os.path import dirname, join, exists
from django.conf import settings

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    

# Build paths inside the project like this: join(BASE_DIR, "directory")
BASE_DIR = dirname(os.path.abspath(__file__))
REQUIREMENTS_DIR = join(BASE_DIR,'HomeAutomation')
MANAGE_DIR = join(REQUIREMENTS_DIR,'src')
DAPHNE_DIR = join(REQUIREMENTS_DIR,'docs','Daphne')
GUNICORN_DIR = join(REQUIREMENTS_DIR,'docs','Gunicorn')
NGINX_DIR = join(REQUIREMENTS_DIR,'docs','Nginx')

print(BASE_DIR)
os.chdir(BASE_DIR)

print(bcolors.BOLD +'##### Updating-Upgrading apt-get #####'+bcolors.ENDC)
cmd="sudo apt-get update"
os.system(cmd)
cmd="sudo apt-get upgrade"
os.system(cmd)
print(bcolors.BOLD +'##### Installing pip3 and making python3 as default python #####'+bcolors.ENDC)
cmd="sudo apt-get install python3-pip"
os.system(cmd)
cmd="sudo ln -sf /usr/bin/python3 /usr/bin/python"
os.system(cmd)
print(bcolors.BOLD +'##### Installing dependencies for Pillow image lib #####'+bcolors.ENDC)
cmd="sudo apt-get install libopenjp2-7-dev libjpeg-dev libtiff4 libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.5-dev tk8.5-dev python-tk"
os.system(cmd)
print(bcolors.BOLD +'##### Installing Pandas #####'+bcolors.ENDC)
cmd="sudo apt-get install python3-pandas python3-numpy python3-scipy"
os.system(cmd)
cmd="sudo easy_install --upgrade pytz"
os.system(cmd)
print(bcolors.BOLD +'##### Installing Redis-server and Django-Redis #####'+bcolors.ENDC)
cmd="sudo apt-get install redis-server"
os.system(cmd)
cmd="sudo pip3 install django-redis"
os.system(cmd)
print(bcolors.BOLD +'##### Installing GIT #####'+bcolors.ENDC)
cmd="sudo apt-get install git"
os.system(cmd)
print(bcolors.BOLD +'##### Cloning repository from GIT #####'+bcolors.ENDC)
cmd="git clone https://github.com/mizamae/HomeAutomation.git"
os.system(cmd)
print(bcolors.BOLD +'##### Installing requirements #####'+bcolors.ENDC)
cmd="sudo pip3 install -r "+join(REQUIREMENTS_DIR,"requirements.txt")
os.system(cmd)
print(bcolors.BOLD +'##### Installing Daphne #####'+bcolors.ENDC)
cmd="sudo apt-get install daphne"
os.system(cmd)
cmd="sudo pip3 install -U asgi_redis"
os.system(cmd)
cmd="sudo mv "+join(DAPHNE_DIR,'daphne.service')+" "+join('etc','systemd','system')
os.system(cmd)
cmd="sudo mv "+join(DAPHNE_DIR,'worker.service')+" "+join('etc','systemd','system')
os.system(cmd)
cmd="sudo systemctl start daphne"
os.system(cmd)
cmd="sudo systemctl enable "
os.system(cmd)
print(bcolors.BOLD +'##### Installing Gunicorn #####'+bcolors.ENDC)
cmd="sudo apt-get install gunicorn"
os.system(cmd)
cmd="sudo mv "+join(GUNICORN_DIR,'gunicorn.service')+" "+join('etc','systemd','system')
os.system(cmd)
cmd="sudo systemctl start gunicorn"
os.system(cmd)
cmd="sudo systemctl enable gunicorn"
os.system(cmd)
print(bcolors.BOLD +'##### Making and applying DB migrations #####'+bcolors.ENDC)
cmd="python3 "+join(MANAGE_DIR,'utils','migrations_handler.py')+" make"
os.system(cmd)
cmd="python3 "+join(MANAGE_DIR,'utils','migrations_handler.py')+" migrate"
os.system(cmd)
print(bcolors.BOLD +'##### Installing and configuring Nginx #####'+bcolors.ENDC)
cmd="sudo apt-get install nginx"
os.system(cmd)
cmd="sudo mv "+join(NGINX_DIR,'HomeAutomation.nginxconf')+" "+join('','etc','nginx','sites-available')
os.system(cmd)
cmd="sudo ln -s "+join('etc','nginx','sites-available','HomeAutomation.nginxconf')+" "+join('','etc','nginx','sites-enabled')
os.system(cmd)
print(bcolors.BOLD +'##### Installing Apache-utils #####'+bcolors.ENDC)
cmd="sudo apt-get install apache2-utils"
os.system(cmd)