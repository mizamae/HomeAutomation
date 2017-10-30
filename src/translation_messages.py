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
    
# Parse command line parameters.
command_args = { 'make': 0,
                'compile': 1}

# sys.argv[0]=  HomeAutomation/src/translation_messages.py
# sys.argv[1]=  make|compile
# sys.argv[2]=  language code
             
if len(sys.argv) == 3 and sys.argv[1]=='make':
    command = command_args[sys.argv[1]]
    language = sys.argv[2]
elif len(sys.argv) == 2 and sys.argv[1]=='compile':
    command = command_args[sys.argv[1]]
else:
    print(bcolors.WARNING +'usage: python HomeAutomation/src/translation_messages.py [make|compile] [language]'+ bcolors.ENDC)
    print('example: ' + bcolors.BOLD + 'python HomeAutomation/src/translation_messages.py make es' + bcolors.ENDC+ ' - Makes the messages for language Spanish [es]')
    sys.exit(1)
    

# Build paths inside the project like this: join(BASE_DIR, "directory")
BASE_DIR = dirname(__file__)

project_root = BASE_DIR
print(project_root)
dirs = os.listdir(project_root)

os_base_dir=os.getcwd()
for app in dirs:
    app_path = os.path.join(project_root, app)
    
    locale_path = os.path.join(app_path, "locale")
    if(os.path.exists(locale_path)): #modify this condition for exclusion of specific folders
        print(bcolors.WARNING + locale_path + bcolors.ENDC)
        os.chdir(app_path)
        if command==0:
            os.system("python /usr/local/lib/python3.4/dist-packages/django/bin/django-admin.py makemessages -l "+ language)
        elif command==1:
            os.system("python /usr/local/lib/python3.4/dist-packages/django/bin/django-admin.py compilemessages")
        os_app_dir=os.getcwd()
        os.chdir(os_base_dir)
os.system("sudo chown -hR pi " + os_base_dir)
        
