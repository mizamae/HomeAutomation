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
                'migrate': 1}

# sys.argv[0]=  HomeAutomation/src/migrations_handler.py
# sys.argv[1]=  make|migrate
# sys.argv[2]=  app_name
             
if len(sys.argv) == 3 and sys.argv[1]=='make':
    command = command_args[sys.argv[1]]
    target_app = sys.argv[2]
elif len(sys.argv) == 2 and sys.argv[1]=='make':
    command = command_args[sys.argv[1]]
    target_app = '*'
elif len(sys.argv) == 2 and sys.argv[1]=='migrate':
    command = command_args[sys.argv[1]]
else:
    print('usage: python HomeAutomation/src/migrations_handler.py [make|migrate] [app] #')
    print('example: python HomeAutomation/src/migrations_handler.py make - Makes the migrations to all the apps')
    sys.exit(1)
    

# Build paths inside the project like this: join(BASE_DIR, "directory")
BASE_DIR = join(dirname(__file__),'..')

project_root = BASE_DIR
print(project_root)
dirs = os.listdir(project_root)
os.chdir(BASE_DIR)

if command==0:
    for app in dirs:
        if target_app=="*": # migrations for all apps is requested
            init_app = os.path.abspath(os.path.join(app, '__init__.py'))
            app_name=os.path.basename(app)
            #print(init_app)
            if (os.path.isfile(init_app)):
                print(bcolors.BOLD +'##### MAKING MIGRATIONS FOR APP: ' + app + ' #####'+ bcolors.ENDC)
                print(bcolors.OKGREEN +'Executing: python manage.py makemigrations '+ target_app.replace('*',app_name) + bcolors.ENDC)
                os.system("python manage.py makemigrations "+ target_app.replace('*',app_name))
        else:   # migration for only one app is requested
            app_name=os.path.basename(app)
            if app_name==target_app:
                print(bcolors.BOLD +'##### MAKING MIGRATIONS FOR APP: ' + app + ' #####'+bcolors.ENDC)
                os.system("python manage.py makemigrations "+ target_app.replace('*',''))
                break
            
elif command==1:
    print(bcolors.BOLD +'##### MIGRATING APPS #####'+bcolors.ENDC)
    os.system("python manage.py migrate")
    print(bcolors.BOLD +'##### SYNCING DB #####'+bcolors.ENDC)
    os.system("python manage.py migrate --run-syncdb")
        
