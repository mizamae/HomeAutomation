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

# sys.argv[0]=  test_coverage_report.py
# sys.argv[1]=  app_name

if len(sys.argv) > 2:
    target_app = sys.argv[1]
    report = sys.argv[2]
elif len(sys.argv)==2:
    target_app = sys.argv[1]
    report = None
else:
    print('usage: python HomeAutomation/src/test_coverage_report.py appName [html]#')
    print('example: python HomeAutomation/src/test_coverage_report.py *  - Makes the coverage analysis for all the apps')
    sys.exit(1)
    

# Build paths inside the project like this: join(BASE_DIR, "directory")
BASE_DIR = join(dirname(__file__),'..')

project_root = BASE_DIR
print(project_root)
dirs = os.listdir(project_root)
os.chdir(BASE_DIR)

for app in dirs:
    if target_app=="*": # coverage for all apps is requested
        init_app = os.path.abspath(os.path.join(app, '__init__.py'))
        app_name=os.path.basename(app)
        #print(init_app)
        if (os.path.isfile(init_app)):
            print(bcolors.BOLD +'##### MAKING COVERAGE FOR APP: ' + app + ' #####'+ bcolors.ENDC)
            print(bcolors.OKGREEN +"Executing: coverage run --source='./"+ target_app.replace('*',app_name)+"' manage.py test "+ target_app.replace('*',app_name) + bcolors.ENDC)
            os.system("coverage run --source='./"+ target_app.replace('*',app_name)+"' manage.py test "+ target_app.replace('*',app_name))
            if report==None:
                os.system("coverage report")
            elif report=='html':
                os.system("coverage html -d ./"+ target_app.replace('*',app_name)+"/coverage")
    else:   # coverage for only one app is requested
        app_name=os.path.basename(app)
        if app_name==target_app:
            print(bcolors.BOLD +'##### MAKING COVERAGE FOR APP: ' + app + ' #####'+bcolors.ENDC)
            os.system("coverage run --source='./"+ target_app.replace('*',app_name)+"' manage.py test "+ target_app.replace('*',app_name))
            if report==None:
                os.system("coverage report")
            elif report=='html':
                os.system("coverage html -d ./"+ target_app.replace('*',app_name)+"/coverage")
            break
    