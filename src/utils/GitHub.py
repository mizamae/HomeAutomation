import re    
from sys import stdout as sys_stdout
from subprocess import Popen, PIPE
from django.utils.translation import ugettext as _    
from EventsAPP.consumers import PublishEvent

import logging

logger = logging.getLogger("project")

def getLatestRelease():
    from requests import Session
    
    url='https://api.github.com/repos/mizamae/HomeAutomation/releases/latest'
    
    response = Session().request("GET", url, data=None)
    result={'version':None,'description':None}
    if response.status_code == 200:
        if not response.text or response.text=='{}':
            pass
        else:
            jsonresponse = response.json()
            result['version']=jsonresponse['tag_name']
            result['description']=""
            #print("Version: " + jsonresponse['tag_name'] +" - "+jsonresponse['name'])
            #print("Features:")
            for line in jsonresponse['body'].splitlines():
                if line!="":
                    result['description']=result['description']+"    - " + line+"\n"
    return result
        
def checkDeveloperUpdates(root):
    PublishEvent(Severity=0,Text=_("Checking-out to the development branch"),Persistent=False,Code='GitHub-1')

    process = Popen("git checkout redesign", cwd=root, shell=True,
                    stdout=PIPE, stderr=PIPE,universal_newlines=True)
    stdout, err = process.communicate()
        
    cmd='git remote show origin'
    process = Popen(cmd, cwd=root, shell=True,
                    stdout=PIPE, stderr=PIPE,universal_newlines=True)
    stdout, err = process.communicate()

    process = Popen("git rev-parse --verify HEAD", cwd=root, shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
    dout, err = process.communicate()
    revision = (dout[:7] if dout and
                re.search(r"(?i)[0-9a-f]{32}", dout) else "-")
        
    if "local out of date" in stdout:
        PublishEvent(Severity=10,Text=_("There is a new development version to download."),Persistent=True,Code='GitHub-1',Webpush=True)
        return {'update':True,'tag':None}
    else:
        PublishEvent(Severity=1,Text=_("You are already on the latest development version " + revision),Persistent=True,Code='GitHub-1')
    return {'update':False,'tag':revision}

def checkReleaseUpdates(root,currentVersion):
    # SYNCHRONIZES THE TAGS FROM THE REMOTE
    cmd='git fetch --tags'
    process = Popen(cmd, cwd=root, shell=True,
                    stdout=PIPE, stderr=PIPE,universal_newlines=True)
    stdout, err = process.communicate()
    # GETS THE LAST EXISTING TAG
    cmd='git describe --tags $(git rev-list --tags --max-count=1)'
    process = Popen(cmd, cwd=root, shell=True,
                    stdout=PIPE, stderr=PIPE,universal_newlines=True)
    stdout, err = process.communicate()
    
    result=getLatestRelease()
    
    if not currentVersion in stdout:
        PublishEvent(Severity=10,Text=_("There is a new release version to download. Version code: " + stdout+"\n"+"Features:\n"+result['description']),
                     Persistent=True,Code='GitHub-1',Webpush=True)
        return {'update':True,'tag':stdout.replace('\n','')}
    else:
        PublishEvent(Severity=1,Text=_("You are already on the latest release version: " + stdout),Persistent=True,Code='GitHub-1')
    return {'update':False,'tag':None}

def updateDeveloper(root):
    """
    Updates the program via git pull.
    """
    PublishEvent(Severity=0,Text=_("Checking for updates..."),Persistent=False,Code='GitHub-1')

    process = Popen("git pull", cwd=root, shell=True,
                    stdout=PIPE, stderr=PIPE,universal_newlines=True)
    stdout, stderr = process.communicate()
    success = not process.returncode

    if success:
        updated = "Already" not in stdout
        process = Popen("git rev-parse --verify HEAD", cwd=root, shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
        stdout, err = process.communicate()
        revision = (stdout[:7] if stdout and
                    re.search(r"(?i)[0-9a-f]{32}", stdout) else "-")
        PublishEvent(Severity=0,Text=_("%s the latest development revision '%s'.") %
              (_("Already at") if not updated else _("Updated to"), revision),Persistent=updated,Code='GitHub-2')
        
        if updated:
            # CHECK IF THERE IS ANY UNAPPLIED MIGRATION
            process = Popen("python src/manage.py showmigrations --list", cwd=root, shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
            stdout, err = process.communicate()
            if err and (not 'UserWarning: ' in err):
                logger.debug('MIGRATIONS CHECK ERROR: ' + str(err))
                PublishEvent(Severity=5,Text=_("Error checking migrations: " + str(err)),Persistent=True,Code='MainAPPViews-4')
                
            migrations= "[ ]" in stdout
             
            if migrations:
                logger.debug('MIGRATIONS: ' + str(stdout))
                PublishEvent(Severity=0,Text=_("Updating DB with new migrations. Relax, it may take a while"),
                             Code='MainAPPViews-5',Persistent=False)
                process = Popen("python src/manage.py migrate", cwd=root, shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
                stdout, err = process.communicate()
                if ('UserWarning' in err) or (not err):
                    PublishEvent(Severity=0,Text=_("Django DB updated OK"),Persistent=False,Code='MainAPPViews-6')
                else:
                    PublishEvent(Severity=4,Text=_("Error applying the migration: " + str(err)),
                                 Code='MainAPPViews-7',Persistent=False)
                    logger.debug('MIGRATIONS APPLICATION ERROR: ' + str(err))
            
            process = Popen("python src/manage.py collectstatic --noinput", cwd=root, shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
            stdout, err = process.communicate()
            
            if 'static files copied to' in stdout and stdout[0]!='0':
                PublishEvent(Severity=0,Text=_("Static files copied"),Persistent=False,Code='MainAPPViews-9')
            elif err:
                PublishEvent(Severity=3,Text=_("Error copying static files - ") + str(err),Persistent=True,Code='MainAPPViews-9')
            
            PublishEvent(Severity=0,Text=_("Restart processes to apply the new changes"),Persistent=True,Code='MainAPPViews-8')
                
        return revision
    else:
        PublishEvent(Severity=2,Text=_("Problem occurred while updating program."),Persistent=False,Code='MainAPPViews-10')
        
        err = re.search(r"(?P<error>error:[^:]*files\swould\sbe\soverwritten"
                      r"\sby\smerge:(?:\n\t[^\n]+)*)", stderr)
        if err:
            if "untracked" in stderr:
                cmd = "git clean -df"
            else:
                cmd = "git reset --hard"

            process = Popen(cmd, cwd=root, shell=True,
                            stdout=PIPE, stderr=PIPE,universal_newlines=True)
            stdout, err = process.communicate()

            if "HEAD is now at" in stdout:
                #print("\nLocal copy reset to current git branch.")
                #print("Attemping to run update again...\n")
                PublishEvent(Severity=0,Text=_("Attempting to run update again..."),Persistent=False,Code='MainAPPViews-10')
            else:
                #print("Unable to reset local copy to current git branch.")
                PublishEvent(Severity=5,Text=_("Unable to reset local copy to current git branch."),Persistent=False,Code='MainAPPViews-11')
                

            updateDeveloper(root)
        else:
            #print("Please make sure that you have a 'git' package installed.")
            PublishEvent(Severity=5,Text=_("Please make sure that you have a 'git' package installed. Error: ") + str(stderr),
                         Code='MainAPPViews-12',Persistent=False)
            #print(stderr)
            
def updateRelease(root,tag):
    """
    Updates the program via git pull.
    """
    PublishEvent(Severity=0,Text=_("Downloading the release version ") + tag,Persistent=False,Code='GitHub-1')

    process = Popen("git fetch origin +refs/tags/"+tag+":refs/tags/"+tag, cwd=root, shell=True,
                    stdout=PIPE, stderr=PIPE,universal_newlines=True)
    stdout, stderr = process.communicate()
    success = not process.returncode

    if success:
        PublishEvent(Severity=0,Text=_("Checking-out to the release version ") + tag,Persistent=True,Code='GitHub-1')

        process = Popen("git checkout refs/tags/"+tag, cwd=root, shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
        stdout, err = process.communicate()
        
        if 'Previous HEAD position was' in err or 'HEAD is now at' in err:
            # CHECK IF THERE IS ANY UNAPPLIED MIGRATION
            process = Popen("python src/manage.py showmigrations --list", cwd=root, shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
            stdout, err = process.communicate()
            if err and (not 'UserWarning: ' in err):
                logger.debug('MIGRATIONS CHECK ERROR: ' + str(err))
                PublishEvent(Severity=5,Text=_("Error checking migrations: " + str(err)),Persistent=True,Code='MainAPPViews-4')
                 
            migrations= "[ ]" in stdout
              
            if migrations:
                logger.debug('MIGRATIONS: ' + str(stdout))
                PublishEvent(Severity=0,Text=_("Updating DB with new migrations. Relax, it may take a while"),
                             Code='MainAPPViews-5',Persistent=False)
                process = Popen("python src/manage.py migrate", cwd=root, shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
                stdout, err = process.communicate()
                if (not err) or ('UserWarning' in err):
                    PublishEvent(Severity=0,Text=_("Django DB updated OK"),Persistent=False,Code='MainAPPViews-6')
                else:
                    PublishEvent(Severity=4,Text=_("Error applying the migration: " + str(err)),
                                 Code='MainAPPViews-7',Persistent=False)
                    logger.debug('MIGRATIONS APPLICATION ERROR: ' + str(err))
                    return
             
            process = Popen("python src/manage.py collectstatic --noinput", cwd=root, shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
            stdout, err = process.communicate()
             
            if 'static files copied to' in stdout and stdout[0]!='0':
                PublishEvent(Severity=0,Text=_("Static files copied"),Persistent=False,Code='MainAPPViews-9')
            elif err:
                PublishEvent(Severity=3,Text=_("Error copying static files - ") + str(err),Persistent=True,Code='MainAPPViews-9')
             
            PublishEvent(Severity=0,Text=_("Restart processes to apply the new changes"),Persistent=True,Code='MainAPPViews-8')
                 
            return tag
        else:
            PublishEvent(Severity=10,Text=_("Error checking-out to ") + tag,Persistent=False,Code='MainAPPViews-8')
                 
            return None
    else:
        PublishEvent(Severity=2,Text=_("Problem occurred while updating program."),Persistent=False,Code='MainAPPViews-10')
         
        err = re.search(r"(?P<error>error:[^:]*files\swould\sbe\soverwritten"
                      r"\sby\smerge:(?:\n\t[^\n]+)*)", stderr)
        if err:
            if "untracked" in stderr:
                cmd = "git clean -df"
            else:
                cmd = "git reset --hard"
 
            process = Popen(cmd, cwd=root, shell=True,
                            stdout=PIPE, stderr=PIPE,universal_newlines=True)
            stdout, err = process.communicate()
 
            if "HEAD is now at" in stdout:
                #print("\nLocal copy reset to current git branch.")
                #print("Attemping to run update again...\n")
                PublishEvent(Severity=0,Text=_("Attemping to run update again..."),Persistent=False,Code='MainAPPViews-10')
            else:
                #print("Unable to reset local copy to current git branch.")
                PublishEvent(Severity=5,Text=_("Unable to reset local copy to current git branch."),Persistent=False,Code='MainAPPViews-11')
                return
 
            updateRelease(root,tag)
        else:
            #print("Please make sure that you have a 'git' package installed.")
            PublishEvent(Severity=5,Text=_("Please make sure that you have a 'git' package installed. Error: ") + str(stderr),
                         Code='MainAPPViews-12',Persistent=False)
            return None