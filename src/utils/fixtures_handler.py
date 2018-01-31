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
    
# Parse command line parameters.
command_args = { 'dump': 0,
                'load': 1}

# sys.argv[0]=  HomeAutomation/src/migrations_handler.py
# sys.argv[1]=  make|migrate
# sys.argv[2]=  app_name

literals=[]  
#--natural-foreign for permissions dumping           
if sys.argv[1]=='dump':
    command = command_args[sys.argv[1]]
    if len(sys.argv) >= 3: 
        target_app = sys.argv[2]
        for arg in sys.argv[2:]:    
            literals.append(arg)
    elif len(sys.argv) == 2:
        target_app = '*'
elif sys.argv[1]=='load':
    command = command_args[sys.argv[1]]
    if len(sys.argv) == 2 :
        literals=[]
    else:
        for arg in sys.argv[2:]:    
            literals.append(arg)
                
else:
    print('usage: python HomeAutomation/src/fixtures_handler.py [dump|load] [app] #')
    print('example: python HomeAutomation/src/fixtures_handler.py dump - Dumps the DB of all the apps')
    print('example: python HomeAutomation/src/fixtures_handler.py load flush - Dumps the DB of all the apps')
    sys.exit(1)
    

# Build paths inside the project like this: join(BASE_DIR, "directory")
BASE_DIR = join(dirname(__file__),'..')

project_root = BASE_DIR
print(project_root)
dirs = os.listdir(project_root)
os.chdir(BASE_DIR)

if command==0:  # dump
    if target_app=="*": # dump fixtures for all apps is requested
        fixtures_root=join(BASE_DIR ,'fixtures')
        if not os.path.isdir(fixtures_root):
            os.makedirs(fixtures_root)
        print(bcolors.BOLD +'##### DUMPING FIXTURE FOR ENTIRE PROJECT #####'+bcolors.ENDC)
        cmd="python manage.py dumpdata  --format=json --indent=4 -o " + \
                     fixtures_root +'\\'+'FullDB.json '
        for literal in literals:
            cmd+= literal+ ' ' 
        os.system(cmd)
    else:
        app_name=target_app
        print(bcolors.BOLD +'##### DUMPING FIXTURE FOR APP ' + app_name + ' #####'+bcolors.ENDC)
        fixtures_root=join(BASE_DIR,app_name ,'fixtures')
        if not os.path.isdir(fixtures_root):
            os.makedirs(fixtures_root)
        cmd="python manage.py dumpdata "+ app_name + " --format=json --indent=4 -o " + \
                     fixtures_root +'\\'+app_name+'.json '
        for literal in literals:
            cmd+= literal+ ' ' 
        os.system(cmd)
elif command==1:
    if 'flush' in literals:
        literals.remove('flush')
        print(bcolors.BOLD +'##### FLUSHING DB  #####'+bcolors.ENDC)
        cmd="python manage.py flush "
        os.system(cmd)
    print(bcolors.BOLD +'##### LOADING FIXTURES  #####'+bcolors.ENDC)
    cmd="python manage.py loaddata "
    for literal in literals:
        cmd+=literal+' '
    os.system(cmd)
        