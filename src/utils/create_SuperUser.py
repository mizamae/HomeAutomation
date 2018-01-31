import os
import sys
from os.path import dirname, join, exists

from django.core.management.commands import makemessages

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

             
print('usage: python HomeAutomation/src/create_SuperUser.py ')
    
BASE_DIR = join(dirname(__file__),'..')
os.chdir(BASE_DIR)
os.system("python manage.py createsuperuser ")