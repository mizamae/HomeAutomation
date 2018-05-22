import re    
from sys import stdout as sys_stdout
from subprocess import Popen, PIPE
from django.utils.translation import ugettext as _    
from EventsAPP.consumers import PublishEvent

import logging

logger = logging.getLogger("project")

def checkUpdates(root):
    cmd='git remote show origin'
    process = Popen(cmd, cwd=root, shell=True,
                    stdout=PIPE, stderr=PIPE,universal_newlines=True)
    stdout, err = process.communicate()

    if "local out of date" in stdout:
        process = Popen("git rev-parse --verify HEAD", cwd=root, shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
        stdout, err = process.communicate()
        revision = (stdout[:7] if stdout and
                    re.search(r"(?i)[0-9a-f]{32}", stdout) else "-")
        PublishEvent(Severity=10,Text=_("There is a new version to download. Version code: " + revision),Persistent=True,Code='GitHub-1')
        return True
    return False

def update(root):
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
        PublishEvent(Severity=0,Text=_("%s the latest source revision '%s'.") %
              (_("Already at") if not updated else _("Updated to"), revision),Persistent=False,Code='GitHub-2')
        
        if updated:
            # CHECK IF THERE IS ANY UNAPPLIED MIGRATION
            process = Popen("python src/manage.py showmigrations --list", cwd=root, shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
            stdout, err = process.communicate()
            if err:
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
                if not err:
                    PublishEvent(Severity=0,Text=_("Django DB updated OK"),Persistent=False,Code='MainAPPViews-6')
                else:
                    PublishEvent(Severity=4,Text=_("Error applying the migration: " + str(err)),
                                 Code='MainAPPViews-7',Persistent=False)
                    logger.debug('MIGRATIONS APPLICATION ERROR: ' + str(err))
                    return
            
            PublishEvent(Severity=0,Text=_("Restart processes to apply the new changes"),Persistent=False,Code='MainAPPViews-8')
            import os
            os.system("python HomeAutomation/src/manage.py collectstatic --noinput")
            os.system("sudo systemctl restart daphne worker")
    else:
        PublishEvent(Severity=2,Text=_("Problem occurred while updating program."),Persistent=False,Code='MainAPPViews-9')
        
        err = re.search(r"(?P<error>error:[^:]*files\swould\sbe\soverwritten"
                      r"\sby\smerge:(?:\n\t[^\n]+)*)", stderr)
        if err:
            def question():
                """Asks question until a valid answer of y or n is provided."""
                print("\nWould you like to overwrite your changes and set "
                      "your local copy to the latest commit?")
                sys_stdout.write("ALL of your local changes will be deleted"
                                 " [Y/n]: ")
                ans = raw_input()

                if not ans:
                    ans = "y"

                if ans.lower() == "n":
                    return False
                elif ans.lower() == "y":
                    return True
                else:
                    #print("Did not understand your answer! Try again.")
                    question()

            #print("%s" % err.group("error"))

            # if not question():
                # return

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

            update(root)
        else:
            #print("Please make sure that you have a 'git' package installed.")
            PublishEvent(Severity=5,Text=_("Please make sure that you have a 'git' package installed. Error: ") + str(stderr),
                         Code='MainAPPViews-12',Persistent=False)
            #print(stderr)